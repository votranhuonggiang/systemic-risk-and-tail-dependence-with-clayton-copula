import os
import pandas as pd
import numpy as np
from arch import arch_model
from scipy.stats import kstest, rankdata
from statsmodels.stats.diagnostic import acorr_ljungbox
import config
import warnings

# Suppress warnings from arch model convergence
warnings.filterwarnings("ignore")

def run_stage1():
    print("Stage 1: GJR-GARCH Filtering ...")
    
    # 1. Load Data
    prices_path = os.path.join(config.DATA_DIR, "prices.csv")
    if not os.path.exists(prices_path):
        print(f"Error: {prices_path} not found. Run stage0 first.")
        return

    prices = pd.read_csv(prices_path, index_col=0, parse_dates=True)
    
    # 2. Compute Log Returns
    returns = np.log(prices / prices.shift(1)).dropna(how='all') * 100
    
    # FILTER: Clip extreme artificial returns (e.g. from unadjusted stock splits)
    # HOSE max limit is +/- 7%. We use 7.5% to allow for small rounding errors.
    # We replace outliers with NaN so they are ignored, then ffill to not break time series too much
    returns = returns.where((returns >= -7.5) & (returns <= 7.5), np.nan)
    returns = returns.ffill().fillna(0) # Fill remaining NaNs so GARCH doesn't crash
    
    tickers = returns.columns
    
    residuals_df = pd.DataFrame(index=returns.index)
    pit_df = pd.DataFrame(index=returns.index)
    
    diagnostics = []
    
    print(f"Processing {len(tickers)} stocks ...")
    
    for i, ticker in enumerate(tickers):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(tickers)} ...")
            
        y = returns[ticker]
        
        # 3. Fit GJR-GARCH(1,1) with Skewed-t
        # p=1 (ARCH), q=1 (GARCH), o=1 (Asymmetry/GJR)
        model = arch_model(y, p=1, q=1, o=1, dist='skewt', mean='Constant')
        
        try:
            res = model.fit(disp='off', show_warning=False)
            
            if res.convergence_flag != 0:
                # If it didn't converge, try with different options or simpler model?
                # For now, we'll just note it and move on.
                pass
                
            # 4. Standardized Residuals
            std_resid = res.resid / res.conditional_volatility
            residuals_df[ticker] = std_resid
            
            # 5. Pseudo-Uniform Transform (PIT)
            # u = rank(z) / (T + 1)
            u = rankdata(std_resid) / (len(std_resid) + 1)
            pit_df[ticker] = u
            
            # 6. Diagnostics
            # Ljung-Box on z (lag 10)
            lb_z = acorr_ljungbox(std_resid.dropna(), lags=[config.LAG_LJUNG_BOX], return_df=True)
            p_lb_z = lb_z['lb_pvalue'].values[0]
            
            # Ljung-Box on z^2 (lag 10)
            lb_z2 = acorr_ljungbox((std_resid**2).dropna(), lags=[config.LAG_LJUNG_BOX], return_df=True)
            p_lb_z2 = lb_z2['lb_pvalue'].values[0]
            
            # Kolmogorov-Smirnov on u
            ks_stat, p_ks = kstest(u, 'uniform')
            
            diagnostics.append({
                'ticker': ticker,
                'converged': res.convergence_flag == 0,
                'lb_z_p': p_lb_z,
                'lb_z2_p': p_lb_z2,
                'ks_u_p': p_ks,
                'alpha': res.params.get('alpha[1]', np.nan),
                'beta': res.params.get('beta[1]', np.nan),
                'gamma': res.params.get('gamma[1]', np.nan),
                'nu': res.params.get('nu', np.nan),
                'lambda': res.params.get('lambda', np.nan)
            })
            
        except Exception as e:
            print(f"  Failed for {ticker}: {e}")
            continue

    # 7. Save Results
    residuals_df.to_csv(os.path.join(config.STAGE_DIRS['stage1'], "standardized_residuals.csv"))
    pit_df.to_csv(os.path.join(config.STAGE_DIRS['stage1'], "pit_series.csv"))
    
    diag_df = pd.DataFrame(diagnostics)
    diag_df.to_csv(os.path.join(config.STAGE_DIRS['stage1'], "garch_diagnostics.csv"), index=False)
    
    # 8. Report Pass Rates
    print("\nDiagnostics Summary:")
    print(f"  Total stocks attempted: {len(tickers)}")
    print(f"  Successfully processed: {len(diag_df)}")
    
    if not diag_df.empty:
        pass_lb_z = (diag_df['lb_z_p'] > config.SIGNIFICANCE_LEVEL).mean() * 100
        pass_lb_z2 = (diag_df['lb_z2_p'] > config.SIGNIFICANCE_LEVEL).mean() * 100
        pass_ks = (diag_df['ks_u_p'] > config.SIGNIFICANCE_LEVEL).mean() * 100
        
        print(f"  Ljung-Box (z) pass rate:  {pass_lb_z:.2f}%")
        print(f"  Ljung-Box (z^2) pass rate: {pass_lb_z2:.2f}%")
        print(f"  KS (uniformity) pass rate: {pass_ks:.2f}%")

if __name__ == "__main__":
    run_stage1()
