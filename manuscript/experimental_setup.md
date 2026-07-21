## 4 Experimental Setup

### 4.1 Dataset

We evaluate CA-MARL on 19 Indian large-cap equities that are constituents of the Nifty 50 index: Reliance Industries, TCS, HDFC Bank, Infosys, ICICI Bank, Hindustan Unilever, ITC, State Bank of India, Bharti Airtel, Kotak Mahindra Bank, Larsen & Toubro, Wipro, Axis Bank, Titan, Asian Paints, Maruti Suzuki, Sun Pharma, NTPC, and Power Grid Corporation. The universe is frozen as of January 1, 2024, to prevent hindsight bias. Daily OHLCV data is sourced from Yahoo Finance (via the `yfinance` library) and spans January 1, 2020 to June 27, 2024, yielding 1,111 trading days. The dataset is versioned (v1.0.0, SHA-256 verified) and remains fixed across all experiments.

From the raw OHLCV data, eight technical indicators are computed per asset using the `stockstats` library: MACD, Bollinger Bands (upper and lower), relative strength index (RSI-30), commodity channel index (CCI-30), directional movement index (DX-30), and simple moving averages of the closing price (30-day and 60-day). The final feature matrix has 152 dimensions (19 assets \(\times\) 8 indicators). Missing values arising from indicator computation are forward-filled and backward-filled. No regime features, volatility indices, or turbulence indices are included in the feature set.

### 4.2 Walk-Forward Validation

We use 4-fold chronological walk-forward validation with non-overlapping test windows. Each fold consists of three contiguous windows: a training window of 504 trading days (~2 years), a validation window of 63 days (~3 months), and a test window of 126 days (~6 months). The stride between successive folds equals the test window length (126 days), so test windows do not overlap. Agents are retrained from scratch on each fold's training window. The walk-forward design ensures that every evaluation is conducted on data unseen during training, and the chronological split respects the temporal ordering of financial time series.

### 4.3 Training Configuration

Each agent is trained using Proximal Policy Optimisation (Schulman et al., 2017) via Stable-Baselines3 with a learning rate of $3 \times 10^{-4}$, $n$-steps of 128, and a minibatch size of 32. The discount factor is $\gamma = 0.99$, GAE parameter $\lambda = 0.95$, and the clipping range is 0.2. Each agent receives 5,000 timesteps of training per fold. Confidence estimation uses the following weights: historical accuracy 0.4, reward stability 0.3, prediction consistency 0.3. Calibration uses Platt scaling with a minimum of five pairs per agent before a non-identity mapping is fitted. The prediction consistency parameter is $k = 5$ samples. The label horizon is 5 trading days for all agents. Random seeds 42 through 46 are used to characterise training variance.

### 4.4 Baselines

We compare CA-MARL against three baselines computed on the same walk-forward test windows: (1) equal-weight (1/N), which allocates capital uniformly across all assets at each rebalancing date; (2) buy-and-hold, which purchases an equal-weighted portfolio at the start of each test window and holds until the end; and (3) static mean-variance optimisation (MVO; Markowitz, 1952), which computes a mean-variance efficient portfolio using sample mean and covariance estimated on the training window and holds it through the test window without rebalancing. DeepTrader (Wang et al., 2021) and MARS (Chen et al., 2026) were planned as additional baselines but could not be reliably reproduced within the project timeline; we compare architecturally rather than empirically.

### 4.5 Ablation Studies

Four ablation studies isolate the contribution of individual architectural components. (1) **Equal-weight fusion:** replaces the confidence-weighted fusion formula with an unweighted average of the three agent proposals. (2) **No calibration:** uses raw (uncalibrated) confidence in place of calibrated confidence for fusion. (3) **Shuffled confidence:** randomly permutes the calibrated confidence values across agents before fusion, testing whether the specific confidence values are functionally load-bearing. (4) **Drop-one-agent:** removes each of the three agents (market, risk, allocation) in turn, fusing the remaining two. All ablations use a single temporal 80/20 train/test split, not the walk-forward protocol, and are therefore reported as exploratory results without statistical replication.

### 4.6 Evaluation Metrics

Financial performance is measured using five annualised metrics: Sharpe ratio, Sortino ratio, maximum drawdown, portfolio volatility, and cumulative return. Calibration quality is measured using Expected Calibration Error (ECE; Naeini et al., 2015) and Brier score per agent. All financial metrics are computed on the test window of each fold.

### 4.7 Statistical Methodology

We use five random seeds (42--46) across four walk-forward folds, yielding 20 paired observations of each metric. CA-MARL is compared against the equal-weight baseline using a paired permutation test (100,000 permutations) and a two-tailed sign test. Effect size is reported as Cohen's $d$. The null hypothesis is that CA-MARL and equal-weight have identical Sharpe ratio distributions. To test for a regime effect across folds, we use a Kruskal-Wallis test on Sharpe ratios grouped by fold, with post-hoc pairwise comparisons. Confidence intervals are computed using the normal approximation. All statistical analyses use a significance threshold of $\alpha = 0.05$.
