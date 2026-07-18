# CONFIDENCE_FUSION.md

> Dedicated specification for the Confidence-Aware Decision Fusion module — the project's primary research contribution. See [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) §5 for the short cross-reference version and [AGENTS.md](./AGENTS.md) §5 for the engineering-facing summary; this document is the authoritative source for both. Method signatures mirrored exactly in [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) §5. The design below resolves [DECISIONS.md](./DECISIONS.md) ADR-020 (heterogeneous-output fusion) and ADR-019 (`reasoning`/`confidence_summary` composition).

## Purpose

Fuse the three agents' recommendations into a single portfolio allocation, weighted by calibrated confidence — not by equal weight, and not by a learned RL policy.

## Why This Is Independent From PPO (ADR-014, ADR-015)

PPO trains the three specialized agents. It does not perform fusion. Never describe PPO as "combining the agents." Fusion is a distinct, deterministic, downstream computation, kept independently inspectable and testable via calibration diagnostics and ablations without being entangled with RL training variance.

## The Heterogeneity Problem, Resolved (ADR-020)

The three agents' native `recommendation` values are not directly combinable:

| Agent | Native recommendation shape |
|---|---|
| Market Analysis | Categorical per asset: BUY / SELL / HOLD |
| Risk Assessment | Continuous per asset: `{"expected_volatility": float, "risk_score": float}` |
| Portfolio Allocation | Continuous per asset: a weight (already allocation-shaped) |

`Σ(Recommendation × Confidence) / Σ(Confidence)` is undefined if applied directly to these three different shapes. The resolution: convert each agent's native recommendation into a **common intermediate representation** — `AssetWeightProposal` — before applying the formula.

### `AssetWeightProposal`

```
AssetWeightProposal = dict[str, float]   # asset -> weight, all >= 0, sums to 1.0 (± 1e-6 tolerance)
```

Every agent's recommendation is transformed into this shape by a dedicated, deterministic transform function, owned by this module (not by the agents themselves — this keeps each agent's public output contract unchanged and confines heterogeneity-handling to the one module whose job is combining heterogeneous inputs).

### Transform Functions

**Market Analysis → proposal:**
```
raw_score[asset]     = +1 if BUY, 0 if HOLD, -1 if SELL
clipped[asset]       = max(raw_score[asset], 0)
if sum(clipped) > 0:
    proposal[asset]  = clipped[asset] / sum(clipped)
else:
    proposal[asset]  = 1 / N   for all assets in the universe   # equal-weight fallback
    # logged: metadata["market_fallback"] = "no_buy_signal_equal_weight"
```

**Risk Assessment → proposal:**
```
inv[asset]      = 1 / (epsilon + risk_score[asset])     # epsilon from configs/agents.yaml, e.g. 1e-6
proposal[asset] = inv[asset] / sum(inv)                  # lower risk -> higher weight
```

**Portfolio Allocation → proposal:**
```
clipped[asset] = max(recommendation[asset], 0)
if sum(clipped) > 0:
    proposal[asset] = clipped[asset] / sum(clipped)
else:
    proposal[asset] = 1 / N   # equal-weight fallback, logged
```

### Fusion Formula, Applied to Proposals

```
for asset in universe:
    final_allocation[asset] = (
        sum over agents of ( proposal_agent[asset] * calibrated_confidence_agent )
    ) / (
        sum over agents of calibrated_confidence_agent
    )
```

**Mathematical guarantee:** since every `proposal_agent` sums to 1 across assets, `final_allocation` is *guaranteed* to sum to 1 across assets too:

```
Σ_asset Σ_agent (proposal_agent[asset] · conf_agent)
  = Σ_agent ( conf_agent · Σ_asset proposal_agent[asset] )
  = Σ_agent ( conf_agent · 1 )
  = Σ_agent conf_agent
```

Dividing by `Σ_agent conf_agent` yields exactly 1. `final_allocation` therefore never needs an extra renormalization step for this property specifically (the Risk Management Layer still re-validates it defensively, per its own authoritative-enforcement responsibility — that's a safety net, not a required correction).

### Worked Numeric Example

Universe: `{A, B}`. Confidences (calibrated, scalar per agent): Market = 0.6, Risk = 0.8, Allocation = 0.5.

- Market recommendation: `{A: BUY, B: SELL}` → clipped `{A: 1, B: 0}` → proposal `{A: 1.0, B: 0.0}`.
- Risk recommendation: `{A: {risk_score: 0.1}, B: {risk_score: 0.4}}` → inv `{A: 10, B: 2.5}` (ε=0.01, ≈) → proposal `{A: 0.8, B: 0.2}`.
- Allocation recommendation (native weights): `{A: 0.3, B: 0.7}` → already valid → proposal `{A: 0.3, B: 0.7}`.

```
final_allocation[A] = (1.0*0.6 + 0.8*0.8 + 0.3*0.5) / (0.6+0.8+0.5)
                     = (0.60 + 0.64 + 0.15) / 1.9
                     = 1.39 / 1.9 ≈ 0.7316

final_allocation[B] = (0.0*0.6 + 0.2*0.8 + 0.7*0.5) / 1.9
                     = (0 + 0.16 + 0.35) / 1.9
                     = 0.51 / 1.9 ≈ 0.2684
```

Check: `0.7316 + 0.2684 = 1.0`. ✓ This exact worked example should become the first golden-value unit test for `ConfidenceAwareFusion.fuse()`.

## `reasoning` and `confidence_summary` Composition (ADR-019)

`FusedDecision` carries `reasoning: str` and `confidence_summary: dict[str, float]` — both populated here, not invented later by the Risk Management Layer (which only passes them through unchanged):

```
reasoning = "; ".join(
    f"{agent_name}({confidence:.2f}): {agent_output.reasoning}"
    for (agent_name, confidence, agent_output) in the three (agent, calibrated_confidence, AgentOutput) triples,
    sorted by confidence descending
)

confidence_summary = calibrated_confidence dict, i.e. {agent_name: calibrated_confidence, ...}, unchanged
```

This is deterministic and fully specified — no "by magic" fields remain between `FusedDecision` and `FinalRecommendation` (see `INTERFACE_CONTRACTS.md` §5–§6 and `DECISIONS.md` ADR-019).

## Edge Cases

- **`Σ(Confidence) = 0`** (all three agents report zero calibrated confidence, e.g., cold-start): fall back to an equal-weight average of the three `AssetWeightProposal` vectors (not the raw recommendations) rather than a division-by-zero failure. Logged and recorded in `fusion_metadata["fallback_used"] = True`.
- **Per-agent proposal fallback** (Market has no BUY signals, Allocation sums to 0): each transform function has its own documented equal-weight fallback (see above), independently logged.
- **Universe mismatch** (an agent's recommendation doesn't cover every asset in `universe`): treat missing assets as weight 0 in that agent's proposal before renormalization — implementation detail, but must not silently drop assets from the final output.

## Relationship to Confidence Estimation & Calibration

This module strictly consumes `ConfidenceEngine`'s output (calibrated confidence, scalar per agent — see `INTERFACE_CONTRACTS.md` §4) — it does not compute or adjust confidence itself. If confidence values look wrong at fusion time, the bug is upstream, not here.

## Testing Approach

Deterministic module — exhaustively unit-testable:
- The worked numeric example above, as an exact golden-value test.
- Each transform function's fallback path (no-BUY-signal, zero-sum allocation).
- The `Σ(Confidence) = 0` fallback path.
- Equivalence to equal-weight averaging of proposals when all three confidences are equal (this is also the basis of the shuffled-confidence ablation in `EXPERIMENT_PLAN.md`).
- `reasoning` string composition ordering (descending confidence) and `confidence_summary` pass-through correctness.

See `TESTING_STRATEGY.md` for the full test suite this module participates in.

## Future Work (Explicitly Out of Current Scope)

A learned fusion mechanism (e.g., a small model or RL policy that learns fusion weights instead of using the fixed formula above) remains flagged as a plausible future direction in `DECISIONS.md`'s Assumption Audit. **It is not part of the current architecture.** Any move toward a learned fusion mechanism requires a new ADR, not a quiet implementation change.

---

**Related documents:** [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) · [AGENTS.md](./AGENTS.md) · [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [DECISIONS.md](./DECISIONS.md) · [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md) · [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)
