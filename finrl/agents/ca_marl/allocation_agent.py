"""Portfolio Allocation RL Agent.

Learns per-asset allocation weights from engineered features (including
regime features), trained via Stable-Baselines3 PPO within the FinRL
ecosystem.

Reference: docs/architecture/AGENTS.md §3,
docs/architecture/INTERFACE_CONTRACTS.md §3,
docs/architecture/MODULE_SPECIFICATIONS.md §3.
"""

from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    InsufficientHistoryError,
)
from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    PPOConfig,
)


# ---------------------------------------------------------------------------
# Regime-column detection (shared heuristic with market_agent.py / risk_agent.py)
# ---------------------------------------------------------------------------

_regime_column_cache: dict[str, list[str]] = {}


def _find_regime_columns(features: pd.DataFrame) -> list[str]:
    """Return the subset of columns that correspond to regime features.

    Regime features are documented in ADR-016 and ARCHITECTURE.md §2 as:
      - bull/bear indicator
      - volatility regime
      - trend regime
      - market-state features
    """
    cache_key = str(id(features))
    if cache_key in _regime_column_cache:
        return _regime_column_cache[cache_key]

    keywords = ["bull", "bear", "regime", "market_state", "marketstate"]
    cols = [c for c in features.columns if any(k in c.lower() for k in keywords)]
    _regime_column_cache[cache_key] = cols
    return cols


# ---------------------------------------------------------------------------
# Internal Gymnasium environment for portfolio-allocation RL training
# ---------------------------------------------------------------------------

class _PortfolioAllocationEnv(gym.Env):
    """Gymnasium environment for training the Portfolio Allocation RL agent.

    **Observation** — engineered feature vector (including regime features)
    at the current timestep.

    **Action** — per-asset allocation weight *i* at index ``action[i]``.
    Values can be negative (the agent is **not** constrained to produce
    long-only or sum-to-one weights at this layer — that enforcement is
    deferred authoritatively to the Risk Management Layer per ADR-019 and
    INTERFACE_CONTRACTS.md §3).

    **Reward** — portfolio return: ``sum(weights × forward_return)`` per
    asset.  The "risk-adjusted" aspect (MODULE_SPECIFICATIONS.md §3) is
    implemented as a mild L2-concentration penalty on the weight vector.
    """

    _RISK_PENALTY_LAMBDA = 0.01

    def __init__(
        self,
        features: np.ndarray,
        forward_returns: np.ndarray,
        n_assets: int,
    ) -> None:
        super().__init__()

        self._features = features.astype(np.float32)
        self._forward_returns = forward_returns.astype(np.float32)
        self._n_assets = n_assets
        self._current_step: int = 0

        feature_dim = self._features.shape[1]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(feature_dim,), dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(n_assets,), dtype=np.float32,
        )

    def step(self, action: np.ndarray) -> tuple:
        action = np.asarray(action, dtype=np.float32).flatten()
        reward = self._compute_reward(action)
        self._current_step += 1
        terminated = self._current_step >= len(self._features) - 1
        truncated = False
        if terminated:
            obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        else:
            obs = self._features[self._current_step]
        return obs, float(reward), terminated, truncated, {}

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self._current_step = 0
        return self._features[0], {}

    def _compute_reward(self, action: np.ndarray) -> float:
        forward_ret = self._forward_returns[self._current_step]
        portfolio_return = float(np.dot(action, forward_ret))
        concentration_penalty = (
            self._RISK_PENALTY_LAMBDA * float(np.sum(action ** 2)) / self._n_assets
        )
        return portfolio_return - concentration_penalty


# ---------------------------------------------------------------------------
# Portfolio Allocation Agent
# ---------------------------------------------------------------------------

class PortfolioAllocationAgent:
    """Portfolio-allocation RL agent trained via PPO.

    Produces per-asset allocation weights from engineered features
    (including regime features).  Raw weights are **not** guaranteed
    long-only or sum-to-one — that enforcement is authoritatively
    deferred to the Risk Management Layer.  Feeds ``AgentOutput`` to
    Confidence Estimation & Calibration and to Confidence-Aware Decision
    Fusion.  Does **not** call other agents (ADR-025).
    """

    def __init__(
        self,
        feature_columns: list[str],
        universe: list[str],
        agent_config: AgentHyperparameters,
        ppo_config: PPOConfig,
    ) -> None:
        self._feature_columns = list(feature_columns)
        self._universe = list(universe)
        self._agent_config = agent_config
        self._ppo_config = ppo_config

        self._model: PPO | None = None
        self._reward_history: list[float] = []
        self._historical_features: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public training interface
    # ------------------------------------------------------------------

    def train(
        self,
        features: pd.DataFrame,
        forward_returns: pd.DataFrame,
        total_timesteps: int = 20000,
    ) -> dict[str, Any]:
        """Train the PPO policy on historical feature data.

        Args:
            features: engineered feature DataFrame with shape
                ``(T, n_features)``.
            forward_returns: per-asset one-step forward returns with
                shape ``(T, n_assets)`` and columns matching ``universe``.
            total_timesteps: number of PPO training timesteps forwarded
                to ``model.learn()``.

        Returns:
            A dict containing training metadata (e.g. final mean reward).

        Raises:
            ValueError: if the feature DataFrame is empty.
            InsufficientHistoryError: if the number of timesteps is below
                the warm-up threshold.
        """
        if features.empty:
            raise ValueError("Feature DataFrame is empty.")

        n_timesteps = len(features)
        min_required = self._agent_config.label_horizon_days + 10
        if n_timesteps < min_required:
            raise InsufficientHistoryError(
                f"Feature history has {n_timesteps} timesteps; "
                f"need at least {min_required} (label_horizon_days "
                f"{self._agent_config.label_horizon_days} + 10)."
            )

        self._historical_features = features.copy()

        feature_array = features[self._feature_columns].values
        ret_array = forward_returns[self._universe].values
        n_assets = len(self._universe)

        env = _PortfolioAllocationEnv(feature_array, ret_array, n_assets)
        vec_env = DummyVecEnv([lambda: env])

        self._model = PPO(
            policy="MlpPolicy",
            env=vec_env,
            learning_rate=self._ppo_config.learning_rate,
            n_steps=self._ppo_config.n_steps,
            batch_size=self._ppo_config.batch_size,
            gamma=self._ppo_config.gamma,
            gae_lambda=self._ppo_config.gae_lambda,
            clip_range=self._ppo_config.clip_range,
            ent_coef=self._ppo_config.ent_coef,
            vf_coef=self._ppo_config.vf_coef,
            max_grad_norm=self._ppo_config.max_grad_norm,
            verbose=0,
        )

        self._reward_history = []
        callback = _RewardCaptureCallback(self._reward_history)
        self._model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            reset_num_timesteps=True,
        )

        return {
            "total_timesteps": total_timesteps,
            "final_mean_reward": (
                float(np.mean(self._reward_history[-100:]))
                if len(self._reward_history) >= 100
                else float(np.mean(self._reward_history))
            ),
        }

    # ------------------------------------------------------------------
    # Public inference interface (INTERFACE_CONTRACTS.md §3)
    # ------------------------------------------------------------------

    def predict(self, features: pd.DataFrame) -> AgentOutput:
        """Produce per-asset allocation weights.

        Args:
            features: engineered feature DataFrame for the current
                timestep.  May contain multiple rows — only the last
                row is used as the current observation.

        Returns:
            ``AgentOutput`` whose ``recommendation`` is a dict mapping
            each ticker in ``universe`` to a raw allocation weight
            (float).  The raw output is **not** guaranteed long-only
            or sum-to-one — enforcement is deferred to the Risk
            Management Layer.

        Raises:
            InsufficientHistoryError: if the agent has not been trained
                yet or the feature DataFrame is empty.
        """
        if self._model is None:
            raise InsufficientHistoryError(
                "Agent has not been trained or loaded. "
                "Call train() or load() before predict()."
            )

        if features.empty:
            raise InsufficientHistoryError(
                "Empty feature DataFrame provided to predict()."
            )

        last_row = features[self._feature_columns].iloc[-1:].values
        if last_row.shape[0] == 0:
            raise InsufficientHistoryError(
                "Feature slice is empty after column filtering."
            )

        action, _ = self._model.predict(last_row, deterministic=True)
        action = np.asarray(action, dtype=np.float32).flatten()

        recommendation: dict[str, float] = {}
        for i, ticker in enumerate(self._universe):
            recommendation[ticker] = float(action[i])

        reward_stability = self._compute_reward_stability()

        return AgentOutput(
            agent_name="allocation_agent",
            recommendation=recommendation,
            raw_confidence=0.0,
            reasoning=self._build_reasoning(recommendation, reward_stability),
            timestamp=pd.Timestamp.now(),
            metadata={
                "reward_stability": reward_stability,
                "tie_break_reason": "",
            },
        )

    def prediction_consistency(self, features: pd.DataFrame, k: int) -> float:
        """Evaluate prediction consistency (ADR-023).

        Samples the trained policy on *k* nearby historical states within
        the same regime bucket as ``features``.  Returns a scalar in
        ``[0, 1]`` computed as ``1 - coefficient_of_variation`` across the
        *k* continuous weight samples (same continuous-output variant as
        ``RiskAssessmentAgent``).

        Args:
            features: feature DataFrame for the current timestep whose
                regime bucket is used for neighbour selection.
            k: number of nearby states to sample.

        Returns:
            Consistency score in ``[0, 1]``.  Returns ``0.0`` if fewer
            than 2 historical states are available.

        Raises:
            InsufficientHistoryError: if the agent has not been trained.
        """
        if self._model is None:
            raise InsufficientHistoryError(
                "Agent has not been trained or loaded. "
                "Call train() or load() before prediction_consistency()."
            )
        if self._historical_features is None or len(self._historical_features) < 2:
            return 0.0

        current_bucket = self._extract_regime_bucket(features)
        neighbours = self._find_k_neighbours(current_bucket, k)
        if len(neighbours) < 2:
            return 0.0

        samples: list[np.ndarray] = []
        for _, row in neighbours.iterrows():
            obs = row[self._feature_columns].values.reshape(1, -1).astype(np.float32)
            act, _ = self._model.predict(obs, deterministic=False)
            samples.append(np.asarray(act, dtype=np.float32).flatten())

        sample_array = np.stack(samples, axis=0)
        return float(_continuous_coefficient_of_variation(sample_array))

    # ------------------------------------------------------------------
    # Model persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Persist the trained PPO model to disk.

        Args:
            path: filesystem path for the model zip file.

        Raises:
            InsufficientHistoryError: if there is no trained model.
        """
        if self._model is None:
            raise InsufficientHistoryError("No trained model to save.")
        self._model.save(str(path))

    def load(self, path: str | Path) -> None:
        """Load a previously saved PPO model from disk.

        Args:
            path: filesystem path to the model zip file.
        """
        self._model = PPO.load(str(path))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_reward_stability(self) -> float:
        """Return the reward-stability signal for confidence estimation.

        Computed as ``1 / variance(recent rewards)`` over the most recent
        ``reward_stability_window`` entries.  Returns ``0.0`` when there
        is insufficient history.
        """
        window = self._agent_config.reward_stability_window
        if len(self._reward_history) < 2:
            return 0.0
        recent = self._reward_history[-window:]
        variance = float(np.var(recent)) if len(recent) > 1 else 0.0
        if variance < 1e-12:
            return 0.0
        return 1.0 / variance

    def _extract_regime_bucket(self, features: pd.DataFrame) -> str:
        """Derive a regime-bucket label from the current state.

        Concatenates regime feature values into a bucket key.  Falls back
        to ``"default"`` when no regime columns are present.
        """
        regime_cols = _find_regime_columns(features)
        if not regime_cols or features.empty:
            return "default"
        last = features.iloc[-1]
        vals = [str(last[c]) for c in regime_cols if c in features.columns]
        return "_".join(vals) if vals else "default"

    def _find_k_neighbours(self, bucket: str, k: int) -> pd.DataFrame:
        """Return up to *k* historical rows belonging to *bucket*.

        Rows are ordered by temporal proximity (closest to the end of
        the historical record first).  Returns an empty DataFrame when
        no matching rows exist.
        """
        if self._historical_features is None or self._historical_features.empty:
            return pd.DataFrame()
        hist = self._historical_features
        if bucket != "default":
            mask = hist.apply(
                lambda r: self._extract_regime_bucket(r.to_frame().T) == bucket,
                axis=1,
            )
            hist = hist[mask]
        return hist.tail(k)

    @staticmethod
    def _build_reasoning(
        recommendation: dict[str, float],
        reward_stability: float,
    ) -> str:
        """Compose a human-readable reasoning string."""
        weights = list(recommendation.values())
        n_assets = len(weights)
        avg_weight = float(np.mean(weights))
        max_weight = float(np.max(weights))
        min_weight = float(np.min(weights))
        return (
            f"PortfolioAllocationAgent: {n_assets} assets, "
            f"avg_weight={avg_weight:.4f}, max={max_weight:.4f}, min={min_weight:.4f} "
            f"(reward_stability={reward_stability:.4f})"
        )


# ---------------------------------------------------------------------------
# SB3 callback — reward capture for stability tracking
# ---------------------------------------------------------------------------

class _RewardCaptureCallback:
    """Minimal SB3 callback that appends per-step rewards to *target*."""

    def __init__(self, target: list[float]) -> None:
        self._target = target

    def __call__(self, locals_: dict[str, Any], globals_: dict[str, Any]) -> bool:
        rewards = locals_.get("rewards")
        if rewards is not None:
            self._target.append(float(np.mean(rewards)))
        return True


# ---------------------------------------------------------------------------
# Consistency utility (ADR-023, continuous-output variant)
# ---------------------------------------------------------------------------

def _continuous_coefficient_of_variation(samples: np.ndarray) -> float:
    """Return ``1 - mean(CV)`` across output dimensions.

    ``samples`` has shape ``(k, n_outputs)``.  Coefficient of variation is
    computed per output dimension as ``std / mean``, then clipped to
    ``[0, 1]`` to avoid blow-up near zero means.  The per-dimension scores
    are averaged and inverted so that higher values mean more consistent.
    """
    k = samples.shape[0]
    if k < 2:
        return 0.0

    means = np.mean(samples, axis=0)
    stds = np.std(samples, axis=0)

    safe_mean = np.where(np.abs(means) > 1e-12, np.abs(means), 1.0)
    cv = stds / safe_mean
    cv = np.clip(cv, 0.0, 1.0)
    return 1.0 - float(np.mean(cv))
