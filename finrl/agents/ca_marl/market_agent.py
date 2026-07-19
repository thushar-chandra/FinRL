"""Market Analysis RL Agent.

A market-direction recommendation policy (BUY/SELL/HOLD per asset) trained
via Stable-Baselines3 PPO within the FinRL ecosystem.

Reference: docs/architecture/AGENTS.md §1,
docs/architecture/INTERFACE_CONTRACTS.md §1,
docs/architecture/MODULE_SPECIFICATIONS.md §1.
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


# Cache for storing parsed regime-bucket columns so we do not re-parse on
# every call to _extract_regime_bucket.  Reset whenever a new feature set
# is provided.
_regime_column_cache: dict[str, list[str]] = {}


def _find_regime_columns(features: pd.DataFrame) -> list[str]:
    """Return the subset of columns that correspond to regime features.

    Regime features are documented in ADR-016 and ARCHITECTURE.md §2 as:
      - bull/bear indicator
      - volatility regime
      - trend regime
      - market-state features

    This heuristic picks columns whose names contain any of the recognised
    keywords.  The exact naming convention is resolved when the feature
    engineering module is implemented.
    """
    cache_key = id(features)
    if cache_key in _regime_column_cache:
        return _regime_column_cache[cache_key]

    keywords = ["bull", "bear", "regime", "market_state", "marketstate"]
    cols = [c for c in features.columns if any(k in c.lower() for k in keywords)]
    _regime_column_cache[cache_key] = cols
    return cols


# ---------------------------------------------------------------------------
# Internal Gymnasium environment for market-timing RL training
# ---------------------------------------------------------------------------

class _MarketTimingEnv(gym.Env):
    """Gymnasium environment for training the Market Analysis RL agent.

    **Observation** — engineered feature vector (including regime features)
    at the current timestep.

    **Action** — per-asset categorical choice:
        ``0`` → SELL, ``1`` → HOLD, ``2`` → BUY.

    **Reward** — directional-accuracy-weighted return.  For each asset the
    sign of *(action − 1)* is multiplied by the one-step forward return so
    that correct directional predictions receive a positive reward and
    incorrect predictions receive a negative reward.
    """

    _ACTION_SELL = 0
    _ACTION_HOLD = 1
    _ACTION_BUY = 2

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
        self.action_space = spaces.MultiDiscrete([3] * n_assets)

    def step(self, action: np.ndarray) -> tuple:
        action = np.asarray(action, dtype=np.int32).flatten()
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
        direction = action.astype(np.float32) - 1.0
        ret = self._forward_returns[self._current_step]
        return float(np.mean(direction * ret))


# ---------------------------------------------------------------------------
# Market Analysis Agent
# ---------------------------------------------------------------------------

class MarketAnalysisAgent:
    """Market-direction RL agent trained via PPO.

    Produces a per-asset BUY / SELL / HOLD recommendation from engineered
    features (including regime features).  Feeds ``AgentOutput`` to
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
        """
        Args:
            feature_columns: column names of the engineered feature
                DataFrame that define the observation space.
            universe: list of asset tickers that define the action space
                and the keys of the output recommendation dict.
            agent_config: per-agent hyperparameters (label horizon,
                reward stability window, epsilon).
            ppo_config: PPO hyperparameters forwarded to
                ``stable_baselines3.PPO``.
        """
        self._feature_columns = list(feature_columns)
        self._universe = list(universe)
        self._agent_config = agent_config
        self._ppo_config = ppo_config

        # Underlying policy model (``None`` until the first call to
        # ``train()`` or ``load()``).
        self._model: PPO | None = None

        # Rolling reward history used by ``_compute_reward_stability()``.
        # Reset on each call to ``train()``.
        self._reward_history: list[float] = []

        # Historical feature matrix stored during ``train()``.
        # Used by ``prediction_consistency()`` to find nearby states.
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
                ``(T, n_features)``.  Must contain the columns declared
                in ``feature_columns`` plus any regime-feature columns.
            forward_returns: per-asset one-step forward returns with
                shape ``(T, n_assets)`` and columns matching ``universe``.
                ``forward_returns[t, a]`` is the return of asset ``a``
                from step ``t`` to ``t + 1``.
            total_timesteps: number of PPO training timesteps forwarded
                to ``model.learn()``.

        Returns:
            A dict containing training metadata (e.g. final mean reward).

        Raises:
            ValueError: if the feature DataFrame is empty or does not
                contain the required columns.
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

        # Store historical features for later use by
        # ``prediction_consistency()``.
        self._historical_features = features.copy()

        # Build the Gymnasium environment.
        feature_array = features[self._feature_columns].values
        ret_array = forward_returns[self._universe].values
        n_assets = len(self._universe)

        env = _MarketTimingEnv(feature_array, ret_array, n_assets)
        vec_env = DummyVecEnv([lambda: env])

        # Create the PPO model.
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

        # Train and collect rewards for stability tracking.
        self._reward_history = []
        callback = _RewardCaptureCallback(self._reward_history)
        self._model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            reset_num_timesteps=True,
        )

        metadata = {
            "total_timesteps": total_timesteps,
            "final_mean_reward": (
                float(np.mean(self._reward_history[-100:]))
                if len(self._reward_history) >= 100
                else float(np.mean(self._reward_history))
            ),
        }
        return metadata

    # ------------------------------------------------------------------
    # Public inference interface  (INTERFACE_CONTRACTS.md §1)
    # ------------------------------------------------------------------

    def predict(self, features: pd.DataFrame) -> AgentOutput:
        """Produce a BUY / SELL / HOLD recommendation for each asset.

        Args:
            features: engineered feature DataFrame for the current
                timestep.  May contain multiple rows — only the last
                row is used as the current observation.

        Returns:
            ``AgentOutput`` whose ``recommendation`` is a dict mapping
            each ticker in ``universe`` to ``"BUY"``, ``"SELL"``, or
            ``"HOLD"``.

        Raises:
            InsufficientHistoryError: if the agent has not been trained
                yet or the feature DataFrame is too short relative to the
                warm-up period.
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

        # Use the last row as the current observation.
        last_row = features[self._feature_columns].iloc[-1:].values
        if last_row.shape[0] == 0:
            raise InsufficientHistoryError(
                "Feature slice is empty after column filtering."
            )

        action, _ = self._model.predict(last_row, deterministic=True)
        action = np.asarray(action, dtype=np.int32).flatten()

        recommendation: dict[str, str] = {}
        for i, ticker in enumerate(self._universe):
            recommendation[ticker] = self._action_to_label(int(action[i]))

        reward_stability = self._compute_reward_stability()

        return AgentOutput(
            agent_name="market_agent",
            recommendation=recommendation,
            raw_confidence=0.0,
            reasoning=self._build_reasoning(recommendation, reward_stability),
            timestamp=pd.Timestamp.now(),
            metadata={
                "reward_stability": reward_stability,
            },
        )

    def prediction_consistency(self, features: pd.DataFrame, k: int) -> float:
        """Evaluate prediction consistency (ADR-023).

        Samples the trained policy on *k* nearby historical states within
        the same regime bucket as ``features`` (the current state).
        Returns the fraction of those *k* samples that agree with the
        modal (most common) recommendation — a scalar in ``[0, 1]``.

        Args:
            features: feature DataFrame for the current timestep whose
                regime bucket is used for neighbour selection.
            k: number of nearby states to sample.

        Returns:
            Consistency score in ``[0, 1]``.  Returns ``0.0`` if fewer
            than 2 historical states are available or if no neighbours
            can be found in the same regime bucket.

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

        actions: list[np.ndarray] = []
        for _, row in neighbours.iterrows():
            obs = row[self._feature_columns].values.reshape(1, -1).astype(np.float32)
            act, _ = self._model.predict(obs, deterministic=False)
            actions.append(np.asarray(act, dtype=np.int32).flatten())

        # Compute per-asset modal-agreement fraction then average.
        action_array = np.stack(actions, axis=0)  # (k, n_assets)
        consistency = _categorical_modal_agreement(action_array)
        return float(consistency)

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

        Regime features (bull/bear, volatility regime, trend regime,
        market-state) are ordinary engineered columns.  When available,
        they are concatenated into a bucket key.  Falls back to the
        string ``"default"`` when no regime columns are present.
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

    def _action_to_label(self, action: int) -> str:
        if action == self._ACTION_SELL:
            return "SELL"
        if action == self._ACTION_HOLD:
            return "HOLD"
        return "BUY"

    @staticmethod
    def _build_reasoning(
        recommendation: dict[str, str],
        reward_stability: float,
    ) -> str:
        """Compose a human-readable reasoning string."""
        n_buy = sum(1 for v in recommendation.values() if v == "BUY")
        n_sell = sum(1 for v in recommendation.values() if v == "SELL")
        n_hold = sum(1 for v in recommendation.values() if v == "HOLD")
        return (
            f"MarketAnalysisAgent: {n_buy} BUY, {n_sell} SELL, {n_hold} HOLD "
            f"(reward_stability={reward_stability:.4f})"
        )

    # Sentinel constants for action-space labels.
    _ACTION_SELL = 0
    _ACTION_HOLD = 1
    _ACTION_BUY = 2


# Concretise the sentinels on the class so they are accessible externally.
MarketAnalysisAgent.ACTION_SELL = 0
MarketAnalysisAgent.ACTION_HOLD = 1
MarketAnalysisAgent.ACTION_BUY = 2


# ---------------------------------------------------------------------------
# SB3 callback — reward capture for stability tracking
# ---------------------------------------------------------------------------

class _RewardCaptureCallback:
    """Minimal SB3 callback that appends per-step rewards to *target*.

    ``PPO.learn()`` invokes ``on_step()`` after every environment step;
    we grab the reward from the local variables dict where SB3 stores it.
    """

    def __init__(self, target: list[float]) -> None:
        self._target = target

    def __call__(self, locals_: dict[str, Any], globals_: dict[str, Any]) -> bool:
        rewards = locals_.get("rewards")
        if rewards is not None:
            self._target.append(float(np.mean(rewards)))
        return True


# ---------------------------------------------------------------------------
# Consistency utility (ADR-023)
# ---------------------------------------------------------------------------

def _categorical_modal_agreement(samples: np.ndarray) -> float:
    """Return the average fraction of samples agreeing with the mode.

    ``samples`` has shape ``(k, n_assets)`` with integer action labels.
    For each asset, the modal (most frequent) action is computed across
    the *k* samples.  The per-asset agreement fraction is averaged across
    assets.
    """
    k = samples.shape[0]
    if k < 2:
        return 0.0
    agreements: list[float] = []
    for col in range(samples.shape[1]):
        col_actions = samples[:, col]
        values, counts = np.unique(col_actions, return_counts=True)
        mode_count = int(counts.max())
        agreements.append(mode_count / k)
    return float(np.mean(agreements))
