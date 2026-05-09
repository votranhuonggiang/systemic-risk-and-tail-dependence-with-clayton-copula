import os
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import config

def compute_sii(centrality_df):
    """
    Compute SII using PCA on 4 centrality measures.
    """
    if centrality_df.empty:
        return pd.DataFrame()
        
    tickers = centrality_df.index
    
    # 1. Normalize metrics
    scaler = StandardScaler()
    X = scaler.fit_transform(centrality_df)
    
    # 2. PCA
    pca = PCA(n_components=1)
    sii_values = pca.fit_transform(X).flatten()
    
    # Ensure loadings are positive (SII should increase with centrality)
    # Check the sum of loadings
    if np.sum(pca.components_[0]) < 0:
        sii_values = -sii_values
        
    res = pd.DataFrame({
        'SII': sii_values
    }, index=tickers)
    
    # Report explained variance
    explained_var = pca.explained_variance_ratio_[0]
    
    return res, explained_var

def run_stage4():
    print("Stage 4: Systemic Importance Index (SII) ...")
    
    # Load Sector Map
    sector_map_path = os.path.join(config.DATA_DIR, "sector_map.csv")
    if not os.path.exists(sector_map_path):
        print(f"Error: sector_map.csv not found.")
        return
    sector_map = pd.read_csv(sector_map_path, index_col='ticker')
    
    regimes = ["full_sample"] + [r.lower().replace(" ", "_") for r in config.REGIMES.keys()]
    
    all_sii_results = []
    
    for regime in regimes:
        print(f"  Processing regime: {regime} ...")
        
        for pipeline in ['corr', 'tail']:
            cent_path = os.path.join(config.STAGE_DIRS['stage3'], f"centrality_{pipeline}_{regime}.csv")
            if not os.path.exists(cent_path):
                continue
                
            cent_df = pd.read_csv(cent_path, index_col=0)
            
            sii_df, var_exp = compute_sii(cent_df)
            print(f"    SII_{pipeline} ({regime}): Explained Variance = {var_exp:.2%}")
            
            # Merge with sector
            sii_df = sii_df.join(sector_map)
            sii_df['regime'] = regime
            sii_df['pipeline'] = pipeline
            
            # Save individual result
            sii_df.to_csv(os.path.join(config.STAGE_DIRS['stage4'], f"sii_{pipeline}_{regime}.csv"))
            
            # Aggregate for sector level
            sector_sii = sii_df.groupby('sector_name')['SII'].mean().reset_index()
            sector_sii['regime'] = regime
            sector_sii['pipeline'] = pipeline
            sector_sii.to_csv(os.path.join(config.STAGE_DIRS['stage4'], f"sector_sii_{pipeline}_{regime}.csv"), index=False)
            
            all_sii_results.append(sii_df)

    # Combined results
    if all_sii_results:
        master_sii = pd.concat(all_sii_results)
        master_sii.to_csv(os.path.join(config.STAGE_DIRS['stage4'], "master_sii.csv"))

    print("Stage 4 complete.")

if __name__ == "__main__":
    run_stage4()
