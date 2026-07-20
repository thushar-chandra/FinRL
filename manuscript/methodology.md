## 3 Methodology

### 3.1 System Overview

CA-MARL is a seven-stage pipeline that transforms raw market data into a confidence-weighted portfolio allocation.

The pipeline begins with data ingestion. A Data Pipeline downloads, validates, and versions historical market data (v1.0.0, SHA-256 verified). Feature Engineering next computes technical indicators and return and volatility statistics as inputs for the downstream agents.

Three specialised reinforcement learning agents---Market Analysis, Risk Assessment, and Portfolio Allocation---each trained via Proximal Policy Optimisation (PPO; Schulman et al., 2017), consume the shared feature set and produce heterogeneous recommendations. The Confidence Estimation and Calibration module then computes a calibrated confidence score per agent from three signals: historical accuracy, reward stability, and prediction consistency.

The Confidence-Aware Decision Fusion module transforms each agent's recommendation into a common weight-vector representation and combines them using a deterministic confidence-weighted formula. The Risk Management Layer enforces portfolio-level constraints---long-only, sum-to-one, per-asset exposure limits---on the fused allocation. Finally, the Evaluation engine computes financial performance metrics, calibration diagnostics, and baseline comparisons.

A walk-forward runner orchestrates the full train-infer-evaluate cycle per chronological fold, managing data splits, calibration eligibility, and result accumulation. Figure 4 depicts the temporal structure of the walk-forward schedule.

### 3.2 Reinforcement Learning Agents

Each of the three specialised agents is a PPO-trained policy receiving the same feature input: technical indicators and volatility and return statistics. No agent receives another agent's output as input, avoiding the moving-target training problem that would arise if one agent's observation space depended on two simultaneously-updating policies. Agents may share training infrastructure or be trained independently, at the implementation's discretion.

**Market Analysis Agent.** This agent learns a per-asset directional recommendation (BUY, SELL, or HOLD) from the feature stream. Its reward function is shaped by the subsequent realised return, following the precedent of DeepTrader (Wang et al., 2021). The native output is a categorical label per asset, which is not directly combinable with the other agents' continuous outputs.

**Risk Assessment Agent.** This agent learns to estimate per-asset risk scores and expected volatility. The reward signal rewards forecast accuracy---whether the realised volatility over the label horizon falls within a band around the prediction---rather than portfolio return. This isolates risk estimation from return maximisation.

**Portfolio Allocation Agent.** This agent learns per-asset allocation weights directly. The output is a continuous weight vector that is not guaranteed to satisfy long-only or sum-to-one constraints at this layer, as constraint enforcement is deferred to the Risk Management Layer. The reward is the risk-adjusted realised return of the proposed weights.

Every agent exposes two signals consumed by the confidence estimator: the inverse variance of recent realised rewards (reward stability) and a prediction-consistency score measuring output stability under small input perturbations.

### 3.3 Confidence Estimation and Calibration

The Confidence Estimation and Calibration module quantifies the trustworthiness of each agent's recommendation. It first combines three signals into a raw confidence score per agent, then calibrates that score onto a probability-like scale via Platt scaling.

**Raw confidence.** Three inputs are combined via a weighted average with pre-specified weights:

\[
\hat{c}_i = \frac{w_{\text{hist}} \cdot a_i + w_{\text{rs}} \cdot r_i + w_{\text{pc}} \cdot p_i}{w_{\text{hist}} + w_{\text{rs}} + w_{\text{pc}}}
\]

where \(\hat{c}_i\) is the raw (uncalibrated) confidence for agent \(i\), \(a_i\) is its historical accuracy, \(r_i\) is its reward stability, and \(p_i\) is its prediction consistency. The combination weights are \(w_{\text{hist}} = 0.4\), \(w_{\text{rs}} = 0.3\), and \(w_{\text{pc}} = 0.3\). Raw confidence is clipped to \([0, 1]\).

*Historical accuracy* is the rolling empirical correctness rate of the agent's past recommendations, measured against validated outcome labels (described below). Agents with no resolved labels (cold-start) receive an uninformative prior of \(a_i = 0.5\).

*Reward stability* is the inverse variance of the agent's recent realised rewards, normalised to \([0, 1]\). It captures whether the agent's training process has converged to a stable region of the policy space.

*Prediction consistency* measures output stability under small input perturbations. For continuous outputs (risk scores, weights), consistency is \(p_i = 1 - \text{CV}\), where CV is the coefficient of variation across \(k = 5\) samples from nearby historical states. For categorical outputs (BUY/SELL/HOLD), it is the fraction of samples agreeing with the modal recommendation.

**Outcome labels.** Outcome labels provide the ground truth against which historical accuracy is measured and on which calibration is fitted. A label for a recommendation made at time \(t\) is generated once realised market data covering the label horizon of \(t_{\text{horizon}} = 5\) trading days becomes available. The label definitions differ by agent:

| Agent | Outcome label |
|-------|-------|
| Market Analysis | Fraction of assets where directional recommendation agrees with the sign of the forward return over the horizon |
| Risk Assessment | \(1.0\) if realised volatility falls within a band of width \(0.2\) centred on the predicted expected volatility, else \(0.0\) |
| Portfolio Allocation | \(1.0\) if the realised return of the proposed weights exceeds that of an equal-weight reference portfolio over the horizon, else \(0.0\) |

**Data-leakage prevention.** A temporal eligibility rule prevents future information from contaminating calibration fitting. A (confidence, label) pair is eligible for calibration in walk-forward fold \(F\) only if

\[
t_{\text{rec}} + t_{\text{horizon}} \leq T_F
\]

where \(t_{\text{rec}}\) is the recommendation timestamp and \(T_F\) is the end of fold \(F\)'s training window. Pairs whose label horizon extends beyond the training window are deferred to a later fold. The same label-generation logic is reused during evaluation, guaranteeing identical definitions of correctness at training and test time.

**Calibration mapping.** Raw confidence \(\hat{c}_i\) is mapped to calibrated confidence \(c_i\) via Platt scaling (Platt, 1999), implemented as logistic regression on logit-transformed values. Agents with fewer than five calibration pairs retain the identity mapping, i.e., \(c_i = \hat{c}_i\). Diagnostic metrics---Expected Calibration Error (ECE; Naeini et al., 2015; Guo et al., 2017) and Brier score---are computed per agent using equal-width binning with ten bins.

### 3.4 Confidence-Aware Decision Fusion

The fusion module combines the three agents' heterogeneous outputs into a single portfolio allocation using calibrated confidence. It is a deterministic computation---PPO trains the agents but does not perform fusion.

Each agent's native recommendation is first transformed into a common intermediate representation: a proposal vector \(p_i\) for agent \(i\) that is a non-negative weight vector over the \(N\) assets and sums to \(1.0\). Three agent-specific transform functions produce these proposals:

- **Market agent.** The categorical recommendation (BUY, SELL, or HOLD per asset) is mapped to numerical scores: BUY \(\rightarrow +1\), HOLD \(\rightarrow 0\), SELL \(\rightarrow -1\). Negative scores are clipped to zero and the vector is renormalised to sum to \(1.0\). If all assets are non-positive, an equal-weight proposal is used.
- **Risk agent.** Per-asset risk scores are inverted as \(1 / (\epsilon + s_j)\), where \(s_j\) is the risk score for asset \(j\) and \(\epsilon = 10^{-6}\), then renormalised so assets with lower predicted risk receive higher weight.
- **Allocation agent.** Native allocation weights are defensively clipped to non-negative values and renormalised. If the sum is zero, an equal-weight proposal is used.

The three proposals are combined via confidence-weighted averaging:

\[
w^*_j = \frac{\sum_{i=1}^{3} c_i \cdot p_{i,j}}{\sum_{i=1}^{3} c_i} \qquad \text{for each asset } j
\]

where \(c_i\) is agent \(i\)'s calibrated confidence and \(p_{i,j}\) is that agent's proposal weight for asset \(j\). Since each proposal vector sums to \(1.0\) across assets, the weighted average is guaranteed to sum to \(1.0\) by construction:

\[
\sum_{j=1}^{N} w^*_j = \frac{\sum_{i=1}^{3} c_i \cdot \left(\sum_{j=1}^{N} p_{i,j}\right)}{\sum_{i=1}^{3} c_i}
= \frac{\sum_{i=1}^{3} c_i \cdot 1}{\sum_{i=1}^{3} c_i} = 1.
\]

If the sum of confidences is zero (e.g., all agents are in cold-start), the module falls back to an unweighted average of the three proposals, flagged in the output metadata.

The module also composes a human-readable reasoning string---each agent's reasoning annotated with its confidence, sorted by descending confidence---and a confidence summary dictionary for auditability.

### 3.5 Risk Management Layer

The Risk Management Layer enforces portfolio-level constraints on the fused allocation \(w^*\) before it is returned as the Final Portfolio Recommendation. Three constraints are applied deterministically: long-only (\(w^*_j \geq 0\) for all \(j\)), sum-to-one (\(\sum_{j=1}^{N} w^*_j = 1\)), and a maximum exposure cap of \(0.4\) (\(40\%\)) per asset. The layer projects the fused weight vector onto the long-only simplex via clipping and renormalisation. The reasoning and confidence summary fields from fusion are passed through unchanged; this layer transforms only the allocation vector itself.
