"""Confidence Estimation & Calibration — one combined module (ADR-022).

Owns ``OutcomeLabelGenerator`` (ADR-024) which is reused, never reimplemented,
by ``EvaluationEngine``.

Reference: docs/architecture/AGENTS.md §4,
docs/architecture/INTERFACE_CONTRACTS.md §4,
docs/architecture/MODULE_SPECIFICATIONS.md §4.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    CalibratedConfidence,
    LabelNotYetResolvableError,
)
from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    ConfidenceConfig,
)

logger = logging.getLogger(__name__)

_VOL_NORMALIZATION_FACTOR = 10.0


# ---------------------------------------------------------------------------
# Outcome Label Generator  (ADR-024)
# ---------------------------------------------------------------------------

class OutcomeLabelGenerator:
    """Generates per-recommendation outcome labels and gates calibration-fold
    eligibility.

    Owned by ``ConfidenceEngine``.  Reused, never reimplemented, by
    ``EvaluationEngine`` (ADR-024).

    ``realized_data`` passed to ``generate_label`` is assumed to be a
    DataFrame with a ``DatetimeIndex`` and columns named after each ticker
    in the universe, containing **close prices**.  Labels are computed from
    price changes over the recommendation's label horizon.
    """

    def __init__(self, agent_configs: dict[str, AgentHyperparameters]) -> None:
        """
        Args:
            agent_configs: mapping from ``agent_name`` (e.g. ``"market_agent"``,
                ``"risk_agent"``, ``"allocation_agent"``) to its corresponding
                ``AgentHyperparameters`` (which carries ``label_horizon_days``).
        """
        self._agent_configs = dict(agent_configs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_label(
        self,
        agent_name: str,
        agent_output: AgentOutput,
        realized_data: pd.DataFrame,
    ) -> float:
        """Generate the outcome label for a past recommendation.

        Args:
            agent_name: which agent produced the recommendation.
            agent_output: the ``AgentOutput`` whose ``recommendation``
                contains the agent-specific payload and whose ``timestamp``
                identifies the prediction time.
            realized_data: DataFrame with ``DatetimeIndex`` and ticker
                columns, containing close prices covering at least the
                label horizon after ``recommendation.timestamp``.

        Returns:
            A scalar label in ``[0, 1]`` — per-agent semantics:

            *market_agent* — fraction of assets where the directional
            recommendation (BUY/SELL/HOLD) agrees with the sign of the
            forward return over the horizon.

            *risk_agent* — ``1.0`` if the realized volatility (computed
            from daily absolute returns over the horizon, normalised to
            ``[0, 1]``) falls within a band of width 0.2 around the
            predicted ``expected_volatility``, else ``0.0``.

            *allocation_agent* — ``1.0`` if the return of the proposed
            weight vector exceeds that of an equal-weight reference
            portfolio over the horizon, else ``0.0``.

        Raises:
            LabelNotYetResolvableError: if ``realized_data`` does not
                cover the full label horizon.
            ValueError: if ``agent_name`` is unknown.
        """
        config = self._agent_configs.get(agent_name)
        if config is None:
            raise ValueError(f"Unknown agent '{agent_name}' — no config registered.")

        horizon = timedelta(days=config.label_horizon_days)
        ts = agent_output.timestamp

        if realized_data.index.max() < ts + horizon:
            raise LabelNotYetResolvableError(
                f"Realized data ends at {realized_data.index.max()}, "
                f"need data through at least {ts + horizon} "
                f"({config.label_horizon_days}d horizon) for '{agent_name}'."
            )

        horizon_data = realized_data.loc[ts : ts + horizon].copy()
        if len(horizon_data) < 2:
            return 0.0

        if agent_name == "market_agent":
            return self._label_market(agent_output, horizon_data)
        elif agent_name == "risk_agent":
            return self._label_risk(agent_output, horizon_data, config.epsilon)
        elif agent_name == "allocation_agent":
            return self._label_allocation(agent_output, horizon_data)
        else:
            raise ValueError(f"Unsupported agent_name '{agent_name}'.")

    def is_eligible_for_fold(
        self,
        recommendation: AgentOutput,
        label_horizon: timedelta,
        fold_training_window_end: datetime,
    ) -> bool:
        """Check whether a (confidence, label) pair may be used for
        calibration fitting in a given walk-forward fold.

        Implements the ADR-024 leakage rule exactly:

            ``recommendation.timestamp + label_horizon <= fold_training_window_end``

        Returns:
            ``True`` if the pair is eligible (no leakage), ``False``
            otherwise.
        """
        return recommendation.timestamp + label_horizon <= fold_training_window_end

    # ------------------------------------------------------------------
    # Per-agent label logic
    # ------------------------------------------------------------------

    @staticmethod
    def _label_market(
        agent_output: AgentOutput,
        horizon_data: pd.DataFrame,
    ) -> float:
        """Fraction of assets where direction matches forward-return sign."""
        rec = agent_output.recommendation
        correct = 0
        total = 0
        first = horizon_data.iloc[0]
        last = horizon_data.iloc[-1]

        for asset, direction in rec.items():
            if asset not in horizon_data.columns:
                continue
            if first[asset] == 0:
                continue
            forward_ret = (last[asset] / first[asset]) - 1.0

            if direction == "BUY":
                correct += 1.0 if forward_ret > 0 else 0.0
            elif direction == "SELL":
                correct += 1.0 if forward_ret < 0 else 0.0
            else:
                correct += 0.5
            total += 1

        return correct / total if total > 0 else 0.5

    @staticmethod
    def _label_risk(
        agent_output: AgentOutput,
        horizon_data: pd.DataFrame,
        epsilon: float,
    ) -> float:
        """1.0 if realised volatility within predicted band, else 0.0.

        The "predicted band" is centred on ``expected_volatility`` with a
        fixed half-width of 0.2 (chosen as a reasonable default for
        volatility normalised to ``[0, 1]``).
        """
        _BAND_HALF_WIDTH = 0.2
        rec = agent_output.recommendation
        results: list[float] = []
        prices = horizon_data.values.astype(np.float64)
        daily_frac_returns = np.diff(prices, axis=0) / (prices[:-1] + 1e-12)

        for i, (asset, scores) in enumerate(rec.items()):
            if asset not in horizon_data.columns:
                continue
            predicted_vol = scores.get("expected_volatility", 0.0)

            if daily_frac_returns.shape[0] < 1:
                results.append(0.0)
                continue

            asset_rets = daily_frac_returns[:, horizon_data.columns.get_loc(asset)]
            realised_raw = float(np.mean(np.abs(asset_rets)))
            realised_vol = min(realised_raw * _VOL_NORMALIZATION_FACTOR, 1.0)

            lower = max(0.0, predicted_vol - _BAND_HALF_WIDTH)
            upper = min(1.0, predicted_vol + _BAND_HALF_WIDTH)
            results.append(1.0 if lower <= realised_vol <= upper else 0.0)

        return float(np.mean(results)) if results else 0.0

    @staticmethod
    def _label_allocation(
        agent_output: AgentOutput,
        horizon_data: pd.DataFrame,
    ) -> float:
        """1.0 if proposed weights outperform equal-weight, else 0.0."""
        rec = agent_output.recommendation
        if len(horizon_data) < 2:
            return 0.5

        first = horizon_data.iloc[0]
        last = horizon_data.iloc[-1]

        forward_returns: dict[str, float] = {}
        for asset in rec:
            if asset not in horizon_data.columns or first[asset] == 0:
                continue
            forward_returns[asset] = (last[asset] / first[asset]) - 1.0

        if not forward_returns:
            return 0.5

        weights = np.array([rec[a] for a in forward_returns], dtype=np.float64)
        rets = np.array(list(forward_returns.values()), dtype=np.float64)
        proposed_ret = float(np.dot(weights, rets))
        eq_ret = float(np.mean(rets))

        return 1.0 if proposed_ret > eq_ret else 0.0


# ---------------------------------------------------------------------------
# Confidence Engine — estimation + calibration (ADR-022)
# ---------------------------------------------------------------------------

class ConfidenceEngine:
    """Confidence Estimation & Calibration — one combined module.

    Responsibilities:
      1. ``estimate_raw_confidence`` — combine historical accuracy, reward
         stability, and prediction consistency into a scalar raw confidence
         per agent.
      2. ``fit_calibration`` — fit a Platt or temperature scaling model on
         eligible (confidence, label) pairs for the current walk-forward
         fold.
      3. ``calibrate`` — apply the fitted calibration mapping and produce
         a ``CalibratedConfidence`` with ECE, Brier and reliability-diagram
         diagnostics.

    Never makes an investment decision (AGENTS.md §4).
    """

    def __init__(
        self,
        outcome_label_generator: OutcomeLabelGenerator,
        config: ConfidenceConfig,
    ) -> None:
        self._label_gen = outcome_label_generator
        self._config = config

        # Rolling per-agent label history used by ``estimate_raw_confidence``.
        self._label_history: dict[str, list[float]] = {}

        # Fitted calibration model per agent (``None`` until ``fit_calibration``).
        self._calibration_models: dict[str, Any] = {}
        # Data used for fitting, retained for diagnostic computation.
        self._calibration_fit_data: dict[str, dict[str, np.ndarray]] = {}

        # Track whether ``fit_calibration`` has been called (leakage guard).
        self._is_fitted: bool = False
        self._fitted_agents: set[str] = set()

    # ------------------------------------------------------------------
    # Label history management
    # ------------------------------------------------------------------

    def record_outcome(self, agent_name: str, label: float) -> None:
        """Record a resolved outcome label for use in historical accuracy.

        Args:
            agent_name: which agent the label belongs to.
            label: the outcome label (output of
                ``OutcomeLabelGenerator.generate_label``).
        """
        if agent_name not in self._label_history:
            self._label_history[agent_name] = []
        self._label_history[agent_name].append(label)

    # ------------------------------------------------------------------
    # Raw confidence estimation
    # ------------------------------------------------------------------

    def estimate_raw_confidence(
        self,
        agent_outputs: list[AgentOutput],
        prediction_consistencies: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Compute raw confidence for each agent.

        Args:
            agent_outputs: one ``AgentOutput`` per agent.  Each must carry
                ``metadata["reward_stability"]``.
            prediction_consistencies: optional mapping ``agent_name ->``
                current ``prediction_consistency()`` value.  Defaults to
                ``0.0`` for agents not present.

        Returns:
            ``dict[str, float]`` mapping each ``agent_name`` to its raw
            confidence scalar.
        """
        pcs = prediction_consistencies or {}
        result: dict[str, float] = {}

        w_hist = self._config.historical_accuracy_weight
        w_rs = self._config.reward_stability_weight
        w_pc = self._config.prediction_consistency_weight
        total_w = w_hist + w_rs + w_pc

        for ao in agent_outputs:
            name = ao.agent_name

            # --- historical accuracy ---
            hist = self._label_history.get(name, [])
            if len(hist) > 0:
                hist_acc = float(np.mean(hist))
            else:
                hist_acc = 0.5
                logger.warning(
                    "Cold-start for agent '%s': no historical labels yet, "
                    "using uninformative-prior fallback 0.5.",
                    name,
                )

            # --- reward stability ---
            rs = ao.metadata.get("reward_stability", 0.0)

            # --- prediction consistency ---
            pc = pcs.get(name, 0.0)

            raw = (w_hist * hist_acc + w_rs * rs + w_pc * pc) / total_w
            raw = float(np.clip(raw, 0.0, 1.0))
            result[name] = raw

        return result

    # ------------------------------------------------------------------
    # Calibration fitting
    # ------------------------------------------------------------------

    def fit_calibration(self, training_window_data: Any) -> None:
        """Fit the calibration mapping STRICTLY on eligible pairs.

        ``training_window_data`` must be a ``list[tuple[str, float, float]]``
        where each tuple is ``(agent_name, raw_confidence, label)``.  The
        caller is responsible for having already filtered through
        ``OutcomeLabelGenerator.is_eligible_for_fold()`` — pairs that fail
        that check **must not** be passed here.

        For each agent with sufficient data (>= 5 pairs), fits the
        configured calibration method (Platt or temperature scaling).
        Agents with insufficient data retain the identity mapping.

        Must be called exactly once per walk-forward fold.
        """
        if not isinstance(training_window_data, list):
            raise TypeError(
                "training_window_data must be a list of (agent_name, raw_conf, label) tuples."
            )

        by_agent: dict[str, list[tuple[float, float]]] = {}
        for agent_name, raw_conf, label in training_window_data:
            if agent_name not in by_agent:
                by_agent[agent_name] = []
            by_agent[agent_name].append((raw_conf, label))

        for agent_name, pairs in by_agent.items():
            confs = np.array([p[0] for p in pairs], dtype=np.float64)
            labels = np.array([p[1] for p in pairs], dtype=np.float64)

            if len(confs) < 5:
                logger.warning(
                    "Agent '%s' has only %d calibration pairs (< 5); "
                    "falling back to identity mapping.",
                    agent_name,
                    len(confs),
                )
                self._calibration_models[agent_name] = None
                self._calibration_fit_data[agent_name] = {
                    "confs": confs,
                    "labels": labels,
                }
                continue

            if self._config.calibration_method == "platt":
                model = self._fit_platt(confs, labels)
            else:
                model = self._fit_temperature(confs, labels)

            self._calibration_models[agent_name] = model
            self._calibration_fit_data[agent_name] = {
                "confs": confs,
                "labels": labels,
            }
            self._fitted_agents.add(agent_name)

        self._is_fitted = True

    # ------------------------------------------------------------------
    # Calibration application
    # ------------------------------------------------------------------

    def calibrate(
        self,
        raw_confidence: dict[str, float],
    ) -> dict[str, CalibratedConfidence]:
        """Apply the fitted calibration mapping.

        Args:
            raw_confidence: ``{agent_name: raw_confidence_float}``.

        Returns:
            ``{agent_name: CalibratedConfidence}`` with per-agent calibrated
            values and diagnostics (ECE, Brier score, reliability-curve
            artifact path).

        Raises:
            RuntimeError: if ``fit_calibration()`` has not been called first.
        """
        if not self._is_fitted:
            raise RuntimeError(
                "fit_calibration() must be called before calibrate(). "
                "See INTERFACE_CONTRACTS.md §4 integration requirement."
            )

        results: dict[str, CalibratedConfidence] = {}

        for agent_name, raw_conf in raw_confidence.items():
            model = self._calibration_models.get(agent_name)
            fit_data = self._calibration_fit_data.get(agent_name)

            if model is None or fit_data is None:
                calibrated = raw_conf
            else:
                calibrated = self._apply_model(model, raw_conf)

            calibrated = float(np.clip(calibrated, 0.0, 1.0))

            ece, brier = _compute_calibration_diagnostics(
                fit_data["confs"] if fit_data is not None else np.array([]),
                fit_data["labels"] if fit_data is not None else np.array([]),
                model,
            )

            results[agent_name] = CalibratedConfidence(
                agent_name=agent_name,
                calibrated_confidence=calibrated,
                diagnostics={
                    "ece": float(ece),
                    "brier_score": float(brier),
                    "reliability_curve_ref": "",
                },
                timestamp=datetime.now(),
            )

        return results

    # ------------------------------------------------------------------
    # Calibration method implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _fit_platt(
        confs: np.ndarray,
        labels: np.ndarray,
    ) -> Any:
        """Fit Platt scaling via scikit-learn ``LogisticRegression``.

        The raw confidence is treated as a single feature; the fitted model
        maps it to a calibrated probability.
        """
        try:
            from sklearn.linear_model import LogisticRegression
        except ImportError:
            raise ImportError(
                "scikit-learn is required for Platt scaling calibration."
            )

        X = confs.reshape(-1, 1).clip(1e-12, 1 - 1e-12)
        logits = np.log(X / (1.0 - X))
        model = LogisticRegression(C=1e6, solver="lbfgs")
        model.fit(logits, labels)
        return model

    @staticmethod
    def _fit_temperature(confs: np.ndarray, labels: np.ndarray) -> float:
        """Fit temperature scaling via scalar optimisation.

        Returns:
            The optimal temperature ``T``.
        """
        try:
            from scipy.optimize import minimize_scalar
        except ImportError:
            raise ImportError(
                "scipy is required for temperature scaling calibration."
            )

        safe = np.clip(confs, 1e-12, 1 - 1e-12)
        logits = np.log(safe / (1.0 - safe))

        def nll(t: float) -> float:
            p = 1.0 / (1.0 + np.exp(-logits / max(t, 1e-12)))
            p = np.clip(p, 1e-12, 1 - 1e-12)
            return -float(np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p)))

        result = minimize_scalar(nll, bounds=(0.1, 10.0), method="bounded")
        return float(result.x) if result.success else 1.0

    @staticmethod
    def _apply_model(model: Any, raw_conf: float) -> float:
        """Apply a fitted calibration model to a single raw confidence."""
        if model is None:
            return raw_conf

        if isinstance(model, float):
            safe = np.clip(raw_conf, 1e-12, 1 - 1e-12)
            logit = np.log(safe / (1.0 - safe))
            p = 1.0 / (1.0 + np.exp(-logit / max(model, 1e-12)))
            return float(p)

        X = np.array([[raw_conf]]).clip(1e-12, 1 - 1e-12)
        logits = np.log(X / (1.0 - X))
        proba = model.predict_proba(logits)[0, 1]
        return float(proba)


# ---------------------------------------------------------------------------
# Diagnostics helpers
# ---------------------------------------------------------------------------

def _compute_calibration_diagnostics(
    confs: np.ndarray,
    labels: np.ndarray,
    model: Any,
    n_bins: int = 10,
) -> tuple[float, float]:
    """Compute Expected Calibration Error and Brier score.

    Args:
        confs: raw confidence values used during fitting.
        labels: binary outcome labels.
        model: fitted calibration model (``None``, ``float`` for temperature,
            or sklearn estimator for Platt).
        n_bins: number of equal-width bins for ECE.

    Returns:
        ``(ece, brier_score)``.
    """
    if len(confs) == 0:
        return 0.0, 0.0

    calibrated = np.array(
        [ConfidenceEngine._apply_model(model, c) for c in confs]
    )

    brier = float(np.mean((calibrated - labels) ** 2))

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (calibrated >= bin_edges[i]) & (calibrated < bin_edges[i + 1])
        n_in_bin = int(np.sum(mask))
        if n_in_bin == 0:
            continue
        bin_acc = float(np.mean(labels[mask]))
        bin_conf = float(np.mean(calibrated[mask]))
        ece += n_in_bin * abs(bin_acc - bin_conf)
    ece /= len(calibrated)

    return ece, brier
