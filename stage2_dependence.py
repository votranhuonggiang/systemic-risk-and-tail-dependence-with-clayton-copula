import os
import pandas as pd
import numpy as np
from scipy.stats import kendalltau
import config
import itertools

def get_regime_data(df, regime_name):
    windows = config.REGIMES.get(regime_name, [])
    if not windows:
        return df
    
    parts = []
    for start, end in windows:
        parts.append(df.loc[start:end])
    
    return pd.concat(parts).sort_index()

def compute_matrices(residuals, pit, name):
    print(f"  Computing matrices for {name} ...")
    tickers = residuals.columns
    n = len(tickers)
    
    # 1. Pearson Correlation
    pearson_corr = residuals.corr(method='pearson')
    
    # 2. Kendall's Tau
    # Use pandas native if possible for speed, or loop if needed.
    # Kendall tau can be slow.
    print(f"    Calculating Kendall's tau matrix (N={n}) ...")
    kendall_corr = pit.corr(method='kendall')
    
    # 3. Clayton Theta and Lambda_L
    # theta = 2*tau / (1 - tau)
    # lambda_L = 2^(-1/theta)
    
    theta_matrix = (2 * kendall_corr) / (1 - kendall_corr)
    # If tau <= 0, theta should be 0 (already handled by the formula if tau is 0, 
    # but for tau < 0 we want to set theta to 0 as per architecture)
    theta_matrix[kendall_corr <= 0] = 0
    
    # lambda_L = 2^(-1/theta)
    # Handle theta = 0 (lambda_L = 0)
    lambda_l_matrix = np.power(2, -1.0 / theta_matrix.replace(0, np.nan))
    lambda_l_matrix = lambda_l_matrix.fillna(0)
    
    # Ensure diagonal is 1.0 (perfect tail dependence with self)
    for i in range(len(lambda_l_matrix)):
        lambda_l_matrix.iloc[i, i] = 1.0
    
    return pearson_corr, kendall_corr, lambda_l_matrix

def run_stage2():
    print("Stage 2: Dependence Estimation ...")
    
    # 1. Load Data
    resid_path = os.path.join(config.STAGE_DIRS['stage1'], "standardized_residuals.csv")
    pit_path = os.path.join(config.STAGE_DIRS['stage1'], "pit_series.csv")
    
    if not os.path.exists(resid_path):
        print(f"Error: Stage 1 outputs not found.")
        return
        
    residuals = pd.read_csv(resid_path, index_col=0, parse_dates=True)
    pit = pd.read_csv(pit_path, index_col=0, parse_dates=True)
    
    regimes = ["Full Sample"] + list(config.REGIMES.keys())
    
    for regime in regimes:
        if regime == "Full Sample":
            res_regime = residuals
            pit_regime = pit
        else:
            res_regime = get_regime_data(residuals, regime)
            pit_regime = get_regime_data(pit, regime)
            
        if res_regime.empty:
            print(f"  Warning: No data for regime {regime}. Skipping.")
            continue
            
        p_corr, k_tau, l_tail = compute_matrices(res_regime, pit_regime, regime)
        
        # Save matrices
        regime_slug = regime.lower().replace(" ", "_")
        p_corr.to_csv(os.path.join(config.STAGE_DIRS['stage2'], f"pearson_{regime_slug}.csv"))
        k_tau.to_csv(os.path.join(config.STAGE_DIRS['stage2'], f"kendall_{regime_slug}.csv"))
        l_tail.to_csv(os.path.join(config.STAGE_DIRS['stage2'], f"clayton_tail_{regime_slug}.csv"))
        
    print("Stage 2 complete.")

if __name__ == "__main__":
    run_stage2()
