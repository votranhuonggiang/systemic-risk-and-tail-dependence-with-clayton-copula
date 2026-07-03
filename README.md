# Systemic Risk and Tail Dependence with Clayton Copula

This repository contains the research code and documentation for a thesis project on systemic downside risk in the Vietnamese stock market. The project models lower-tail dependence among HOSE-listed stocks with the Clayton copula, builds filtered financial networks, and compares tail-risk signals against conventional Pearson correlation.

**Project distinction:** Top 1 thesis/project, graded **9.3/10**.

## Research Overview

The project studies whether lower-tail dependence provides a better view of crash transmission than standard correlation-based methods.

Main research questions:

1. What is the degree of lower-tail dependence among HOSE-listed stocks?
2. Which stocks and sectors contribute most to market-wide downside risk?
3. Does Clayton copula tail dependence capture downside co-movement more effectively than Pearson correlation?

The empirical setting is the Ho Chi Minh City Stock Exchange (HOSE), with a final sample of **193 stocks** across **11 GICS sectors** over **2016-2025**.

## Methodology

The research pipeline combines time-series filtering, copula dependence estimation, network filtering, and systemic importance scoring:

1. Compute daily log returns for selected HOSE stocks.
2. Filter returns with GJR-GARCH(1,1) using skewed-t innovations.
3. Convert standardized residuals into pseudo-uniform observations.
4. Estimate pairwise Clayton copula lower-tail dependence coefficients.
5. Build Planar Maximally Filtered Graphs (PMFG) from:
   - Pearson correlation network
   - Clayton lower-tail dependence network
6. Compute weighted network centrality measures.
7. Construct a Systemic Importance Index (SII) using PCA.
8. Compare networks and validate crisis-period explanatory power.

## Key Findings

- The full-sample median Clayton lower-tail dependence is **0.099**, indicating moderate average dependence but strong crash-link potential in the tail.
- Tail dependence rises sharply during crisis regimes, especially the 2025 Trump Tariff shock, where median lower-tail dependence reaches **0.694**.
- Financials and Real Estate form a persistent systemic core, while Materials and Utilities become more important in specific crisis regimes.
- The Pearson network misses a large share of crash-relevant links. During COVID-19, the Jaccard similarity between Pearson and Clayton PMFG networks is only **0.125**.
- The tail-based Systemic Importance Index performs better in crisis validation regressions, especially during the Bond Shock, where it explains **34.2%** of cross-sectional crisis losses.

## Repository Structure

```text
.
├── architecture.md              # Detailed research architecture and execution plan
├── RESULTS_SUMMARY.md           # Main empirical result summary
├── Writing_research/            # Thesis writing assets and references
├── analyze_top_pairs.py         # Top lower-tail dependence pair analysis
├── analyze_top_5pct.py          # Extreme-pair analysis
├── calc_lambda_stats.py         # Clayton lambda statistics
├── calc_pearson_stats.py        # Pearson correlation statistics
├── plotting_results.py          # Main figure-generation script
├── gen_*                        # Table and figure generation utilities
└── tmp_*                        # Temporary analysis/check scripts
```

Some scripts expect local `data/` and `output/` folders containing prepared inputs and generated stage outputs. These large or private research artifacts may be excluded from the public repository.

## Main Outputs

The project produces:

- sector-level lower-tail dependence heatmaps;
- PMFG network visualizations;
- stock-level and sector-level SII rankings;
- top intra-sector and cross-sector crash-risk pairs;
- Jaccard comparisons between Pearson and Clayton networks;
- crisis validation regression summaries.

For the compact empirical synthesis, see [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md). For the full research design and pipeline logic, see [architecture.md](architecture.md).

## Requirements

The analysis scripts use Python and common scientific-computing packages:

```bash
pip install pandas numpy scipy statsmodels scikit-learn networkx matplotlib seaborn pillow arch
```

## Example Usage

Run selected analysis and plotting scripts from the repository root:

```bash
python analyze_top_pairs.py
python calc_lambda_stats.py
python plotting_results.py
python gen_top_pair_ranking_grid.py
```

The exact execution order depends on the availability of prepared stage outputs under `output/`.

## Academic Context

This project was developed as a finance/econometrics thesis on systemic risk and tail dependence in an emerging equity market. The main contribution is showing that Clayton lower-tail dependence reveals crash-transmission channels that conventional correlation networks can miss.

