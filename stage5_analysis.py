import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import statsmodels.api as sm
import config

def compute_jaccard(edges1, edges2):
    e1 = set(tuple(sorted(edge[:2])) for edge in edges1)
    e2 = set(tuple(sorted(edge[:2])) for edge in edges2)
    intersection = len(e1.intersection(e2))
    union = len(e1.union(e2))
    return intersection / union if union > 0 else 0

def run_stage5():
    print("Stage 5: Analysis & Results ...")
    
    # Load Sector Map
    sector_map = pd.read_csv(os.path.join(config.DATA_DIR, "sector_map.csv"), index_col='ticker')
    
    # 1. RQ1: Descriptive Stats of lambda_L
    print("  Analysis RQ1: Lower-tail dependence ...")
    l_full_path = os.path.join(config.STAGE_DIRS['stage2'], "clayton_tail_full_sample.csv")
    if os.path.exists(l_full_path):
        l_tail = pd.read_csv(l_full_path, index_col=0)
        # Exclude diagonal
        mask = np.ones(l_tail.shape, dtype=bool)
        np.fill_diagonal(mask, 0)
        l_values = l_tail.values[mask]
        
        print(f"    Full Sample Lambda_L: Mean={np.mean(l_values):.4f}, Std={np.std(l_values):.4f}")
        
        # Fig 1: Histogram
        plt.figure(figsize=(10, 6))
        sns.histplot(l_values, bins=50, kde=True)
        plt.title("Distribution of Clayton Lower-Tail Dependence (λL) - Full Sample")
        plt.xlabel("λL")
        plt.savefig(os.path.join(config.STAGE_DIRS['stage5'], "fig1_lambda_dist.png"))
        plt.close()

        # Fig 2: Sector-level Heatmap
        # Merge with sector
        sector_l = l_tail.copy()
        sector_l.index = sector_l.index.map(sector_map['sector_name'])
        sector_l.columns = sector_l.columns.map(sector_map['sector_name'])
        sector_heatmap = sector_l.groupby(level=0).mean().T.groupby(level=0).mean()
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(sector_heatmap, annot=True, cmap="YlOrRd", fmt=".3f")
        plt.title("Sector-level Mean Lower-Tail Dependence (λL)")
        plt.savefig(os.path.join(config.STAGE_DIRS['stage5'], "fig2_sector_heatmap.png"))
        plt.close()
        
    # 2. RQ2: Top 10 Stocks
    print("  Analysis RQ2: Systemic Importance ...")
    sii_tail_full = pd.read_csv(os.path.join(config.STAGE_DIRS['stage4'], "sii_tail_full_sample.csv"), index_col=0)
    sii_corr_full = pd.read_csv(os.path.join(config.STAGE_DIRS['stage4'], "sii_corr_full_sample.csv"), index_col=0)
    
    comparison = sii_tail_full[['SII', 'sector_name']].rename(columns={'SII': 'SII_tail'})
    comparison['SII_corr'] = sii_corr_full['SII']
    comparison['rank_tail'] = comparison['SII_tail'].rank(ascending=False)
    comparison['rank_corr'] = comparison['SII_corr'].rank(ascending=False)
    comparison['rank_diff'] = comparison['rank_tail'] - comparison['rank_corr']
    
    top_10 = comparison.sort_values('rank_tail').head(10)
    top_10.to_csv(os.path.join(config.STAGE_DIRS['stage5'], "top10_stocks.csv"))
    print("    Top 10 systemic stocks saved.")

    # 3. RQ3: Jaccard Similarity
    print("  Analysis RQ3: Pipeline Comparison ...")
    jaccard_results = []
    regimes = ["full_sample"] + [r.lower().replace(" ", "_") for r in config.REGIMES.keys()]
    
    for regime in regimes:
        e_corr_path = os.path.join(config.STAGE_DIRS['stage3'], f"pmfg_corr_{regime}.edgelist")
        e_tail_path = os.path.join(config.STAGE_DIRS['stage3'], f"pmfg_tail_{regime}.edgelist")
        
        if os.path.exists(e_corr_path) and os.path.exists(e_tail_path):
            with open(e_corr_path, 'r') as f:
                edges_corr = [line.split() for line in f]
            with open(e_tail_path, 'r') as f:
                edges_tail = [line.split() for line in f]
                
            j = compute_jaccard(edges_corr, edges_tail)
            jaccard_results.append({'regime': regime, 'jaccard': j})
            
    j_df = pd.DataFrame(jaccard_results)
    j_df.to_csv(os.path.join(config.STAGE_DIRS['stage5'], "jaccard_similarity.csv"), index=False)
    
    # 4. Crisis Validation Regression
    print("  Running Crisis Validation Regression ...")
    prices = pd.read_csv(os.path.join(config.DATA_DIR, "prices.csv"), index_col=0, parse_dates=True)
    returns = np.log(prices / prices.shift(1)).dropna() * 100
    
    regression_results = []
    
    # Crisis regimes for regression
    for regime in ["COVID-19", "Trade War", "Bond Shock", "Trump Tariff"]:
        regime_slug = regime.lower().replace(" ", "_")
        
        # Load SII for this regime
        sii_tail_path = os.path.join(config.STAGE_DIRS['stage4'], f"sii_tail_{regime_slug}.csv")
        sii_corr_path = os.path.join(config.STAGE_DIRS['stage4'], f"sii_corr_{regime_slug}.csv")
        
        if not os.path.exists(sii_tail_path) or not os.path.exists(sii_corr_path):
            continue
            
        sii_tail = pd.read_csv(sii_tail_path, index_col=0)
        sii_corr = pd.read_csv(sii_corr_path, index_col=0)
        
        # Get average returns during crisis
        reg_returns = []
        windows = config.REGIMES[regime]
        for start, end in windows:
            reg_returns.append(returns.loc[start:end])
        
        if not reg_returns:
            continue
            
        avg_returns = pd.concat(reg_returns).mean()
        
        # Prepare Data for Regression
        data = pd.DataFrame({
            'return': avg_returns,
            'sii_tail': sii_tail['SII'],
            'sii_corr': sii_corr['SII']
        }).dropna()
        
        # Standardize regressors
        data['sii_tail'] = (data['sii_tail'] - data['sii_tail'].mean()) / data['sii_tail'].std()
        data['sii_corr'] = (data['sii_corr'] - data['sii_corr'].mean()) / data['sii_corr'].std()
        
        # Run Regression
        X = data[['sii_tail', 'sii_corr']]
        X = sm.add_constant(X)
        y = data['return']
        
        model = sm.OLS(y, X).fit(cov_type='HC3')
        
        regression_results.append({
            'regime': regime,
            'beta_tail': model.params['sii_tail'],
            'p_tail': model.pvalues['sii_tail'],
            'beta_corr': model.params['sii_corr'],
            'p_corr': model.pvalues['sii_corr'],
            'rsquared': model.rsquared
        })
        
    reg_res_df = pd.DataFrame(regression_results)
    reg_res_df.to_csv(os.path.join(config.STAGE_DIRS['stage5'], "crisis_regression.csv"), index=False)
    print("    Crisis regression results saved.")

if __name__ == "__main__":
    run_stage5()
