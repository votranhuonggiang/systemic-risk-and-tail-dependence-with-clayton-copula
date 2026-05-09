import os
import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms.planarity import check_planarity
import config

def build_pmfg(weights_df, sort_ascending=True):
    """
    Build PMFG from a weight matrix.
    If sort_ascending=True (e.g. for distance), smaller values come first.
    If sort_ascending=False (e.g. for lambda_L), larger values come first.
    """
    tickers = weights_df.columns
    n = len(tickers)
    
    # Create list of edges with weights
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((tickers[i], tickers[j], weights_df.iloc[i, j]))
            
    # Sort edges
    edges.sort(key=lambda x: x[2], reverse=not sort_ascending)
    
    # Initialize planar graph
    G = nx.Graph()
    G.add_nodes_from(tickers)
    
    max_edges = 3 * (n - 2)
    edge_count = 0
    
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
        is_planar, _ = check_planarity(G)
        
        if is_planar:
            edge_count += 1
        else:
            G.remove_edge(u, v)
            
        if edge_count >= max_edges:
            break
            
    return G

def compute_centrality(G, weight_attr='weight', invert_weight=False):
    """
    Compute 4 centrality measures.
    weight_attr: name of the weight attribute.
    invert_weight: if True, use 1/weight for closeness (for distance-based metrics).
    """
    # 1. Weighted Degree (Strength)
    degree = dict(G.degree(weight=weight_attr))
    
    # For distance-based metrics (betweenness/closeness), we need distances.
    # If G was built with lambda_L (weights), distance = 1/weight.
    if not invert_weight:
        # Weights are already distances (Pearson distance)
        dist_G = nx.Graph()
        dist_G.add_nodes_from(G.nodes())
        for u, v, d in G.edges(data=True):
            # Ensure strictly positive for Dijkstra
            dist_G.add_edge(u, v, weight=max(d[weight_attr], 0) + 1e-10)
    else:
        # Weights are similarities (lambda_L), convert to distance
        dist_G = nx.Graph()
        dist_G.add_nodes_from(G.nodes())
        for u, v, d in G.edges(data=True):
            w = d[weight_attr]
            # Safety clip for similarity to be > 0 for distance calculation
            dist_w = 1.0 / max(w, 1e-9)
            dist_G.add_edge(u, v, distance=dist_w + 1e-10)
        weight_attr = 'distance'

    # 2. Betweenness
    try:
        betweenness = nx.betweenness_centrality(dist_G, weight=weight_attr, normalized=True)
    except Exception as e:
        print(f"      Warning: Betweenness failed: {e}")
        betweenness = {n: 0 for n in dist_G.nodes()}
    
    # 3. Closeness
    try:
        closeness = nx.closeness_centrality(dist_G, distance=weight_attr)
    except Exception as e:
        print(f"      Warning: Closeness failed: {e}")
        closeness = {n: 0 for n in dist_G.nodes()}
    
    # 4. Eigenvector
    try:
        # Eigenvector usually uses weights (similarities)
        if invert_weight:
            # Use original G which has lambda_L as weight
            eigenvector = nx.eigenvector_centrality_numpy(G, weight='weight')
        else:
            # Pearson distance graph, need to convert back to correlation for eigenvector?
            sim_G = nx.Graph()
            for u, v, d in G.edges(data=True):
                dist = d[weight_attr]
                # distance = sqrt(2(1-rho)) -> rho = 1 - distance^2 / 2
                rho = 1 - (dist**2) / 2
                sim_G.add_edge(u, v, weight=max(rho, 0))
            eigenvector = nx.eigenvector_centrality_numpy(sim_G, weight='weight')
    except Exception as e:
        print(f"      Warning: Eigenvector failed: {e}")
        eigenvector = {n: 0 for n in G.nodes()}
        
    df = pd.DataFrame({
        'degree': degree,
        'betweenness': betweenness,
        'closeness': closeness,
        'eigenvector': eigenvector
    })
    
    return df

def run_stage3():
    print("Stage 3: PMFG Construction & Centrality ...")
    
    regimes = ["full_sample"] + [r.lower().replace(" ", "_") for r in config.REGIMES.keys()]
    
    for regime in regimes:
        print(f"  Processing regime: {regime} ...")
        
        # --- Pipeline A: Pearson ---
        p_path = os.path.join(config.STAGE_DIRS['stage2'], f"pearson_{regime}.csv")
        if os.path.exists(p_path):
            p_corr = pd.read_csv(p_path, index_col=0)
            # Convert to distance: d = sqrt(2*(1-rho))
            p_dist = np.sqrt(2 * (1 - p_corr).clip(lower=0))
            
            print(f"    Building PMFG_corr ...")
            G_corr = build_pmfg(p_dist, sort_ascending=True)
            nx.write_weighted_edgelist(G_corr, os.path.join(config.STAGE_DIRS['stage3'], f"pmfg_corr_{regime}.edgelist"))
            
            print(f"    Computing centrality for PMFG_corr ...")
            cent_corr = compute_centrality(G_corr, invert_weight=False)
            cent_corr.to_csv(os.path.join(config.STAGE_DIRS['stage3'], f"centrality_corr_{regime}.csv"))
            
        # --- Pipeline B: Clayton ---
        l_path = os.path.join(config.STAGE_DIRS['stage2'], f"clayton_tail_{regime}.csv")
        if os.path.exists(l_path):
            l_tail = pd.read_csv(l_path, index_col=0)
            
            print(f"    Building PMFG_tail ...")
            G_tail = build_pmfg(l_tail, sort_ascending=False)
            nx.write_weighted_edgelist(G_tail, os.path.join(config.STAGE_DIRS['stage3'], f"pmfg_tail_{regime}.edgelist"))
            
            print(f"    Computing centrality for PMFG_tail ...")
            cent_tail = compute_centrality(G_tail, invert_weight=True)
            cent_tail.to_csv(os.path.join(config.STAGE_DIRS['stage3'], f"centrality_tail_{regime}.csv"))

    print("Stage 3 complete.")

if __name__ == "__main__":
    run_stage3()
