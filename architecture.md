# ARCHITECTURE.md

# Paper: Lower-Tail Dependence and Sectoral Systemic Risk on HOSE

# Hướng dẫn đầy đủ cho AI thực thi nghiên cứu

---

## 0. TỔNG QUAN PAPER

### Tiêu đề gợi ý

"Modeling Systemic Risk and Tail Dependence in an Emerging Stock Market: Evidence from Vietnam"

### Ba Research Questions

- **RQ1:** What is the degree of lower-tail dependence among HOSE-listed stocks?
- **RQ2:** Which sectors contribute most to market-wide downside risk and crash transmission on HOSE?
- **RQ3:** Does lower-tail copula dependence capture downside co-movement more effectively than conventional correlation?

### Hai Pipeline

- **Pipeline A (Baseline):** Pearson correlation → PMFG_corr → SII_corr
- **Pipeline B (Main):** Clayton copula → λ_L matrix → PMFG_tail → SII_tail

### Target Journal

Emerging Markets Review / Pacific-Basin Finance Journal / Finance Research Letters

---

## 1. DATA

### 1.1 Universe

- **Giai đoạn:** January 2016 – December 2025

* **Selection Pool:** Start with all eligible **HOSE-listed stocks** (Exchanges: HSX) that have sufficient data.
* **Sector Weighting:**
  - Calculate total market cap for each sector (using HOSE pool): $MCAP_s = \sum_{i \in s} MCAP_i$
  - Calculate sector weight: $Weight_s = \frac{MCAP_s}{\sum_s MCAP_s}$
  - Determine number of stocks: $n_s = \text{round}(N \times Weight_s)$ where $N$ is total target sample size.
  - **Note:** $n_s$ can be zero for sectors with very small market capitalization; no minimum stock count per sector is enforced.
* **Stock Selection (within each sector):**
  - **Rank by Size:** Rank $i$ by latest Market Capitalization (descending).
  - **Rank by Liquidity:** Rank $i$ by Average Trading Value ($Price \times Volume$) over the selection period (descending).
  - **Combined Rank:** $Combined\_Rank_i = \frac{Rank\_MCAP_i + Rank\_Liquidity_i}{2}$
  - **Selection:** Keep top $n_s$ stocks with lowest combined scores.

### 1.2 Tiêu chí chọn cổ phiếu

```
CompositeRank_i = [Rank(AvgDailyVolume_i) + Rank(MarketCap_i)] / 2
```

- Lấy top $n_s$ composite rank trong mỗi sector
- **Điều kiện bắt buộc:** ≥ 80% non-missing price observations over full window. Yêu cầu khắt khe này loại bỏ nhiều "ông lớn" niêm yết hoặc chuyển sàn sau 2018 (ví dụ: TCB, VPB, VHM, GVR).
- Loại stocks IPO sau 2018 (listing history < 7 năm)
- **Tác động của bộ lọc:** Từ 405 mã ban đầu, 212 mã bị loại, chốt lại tập mẫu **193 mã**. Rất nhiều ngân hàng lớn bị loại do không đủ lịch sử dữ liệu để đánh giá rủi ro đuôi qua trọn vẹn chu kỳ 2016-2025.

### 1.3 Log Returns

```
r_{i,t} = ln(P_{i,t} / P_{i,t-1}) × 100
```

### 1.4 Sub-periods (5 regimes)

| Regime       | Window                                  | Mục đích             |
| ------------ | --------------------------------------- | ----------------------- |
| Normal       | 2016-01-01 – 2018-03-31, 2020-01-04 – 2022-08-31, & 2023-01-01 – 2025-03-31 | Baseline ổn định     |
| Trade War    | 2018-04-01 – 2018-10-31                 | Geopolitical shock      |
| COVID-19     | 2020-01-01 – 2020-03-31                 | Systemic domestic shock |
| Bond Shock   | 2022-09-01 – 2022-11-16                 | Credit & Trust shock    |
| Trump Tariff | 2025-04-01 – 2025-04-20                 | Recent external shock   |

### 1.5 Bối cảnh các sự kiện vĩ mô/niềm tin và biến động VN-Index

Dưới đây là bảng thống kê chi tiết về các cú sốc thị trường chính trong giai đoạn nghiên cứu (không bao gồm sự kiện thắt chặt tiền tệ 2022).

| Sự kiện                                                         | Đỉnh trước cú giảm (điểm; ngày) | Đáy trong giai đoạn (điểm; ngày) | Giảm từ đỉnh → đáy (điểm) | Hồi về đỉnh cũ (ngày hồi; số ngày từ đáy)                                                                                                                                                                                    |
| ----------------------------------------------------------------- | ---------------------------------------: | --------------------------------------: | ---------------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Trade war 2018                                                    |                        1.211; 10/04/2018 |                         888; 30/10/2018 |                                323 | **N/A** (chưa tìm được nguồn xác nhận “ngày VN-Index vượt lại 1.211”). Mốc gần nhất có ngày/điểm rõ: VN-Index đóng cửa 1.200,94 ngày 18/03/2021 → ~**870 ngày** từ 30/10/2018 đến 18/03/2021. |
| COVID-19 (2020)                                                   |                        991,46;20/01/2020 |                      659,21; 24/03/2020 |                             332,25 | Đóng cửa ngày 30/11/2020 “trên mức 1.000 điểm” (tức là đã vượt lại mốc 991,46). Số ngày từ đáy 24/03/2020 → 30/11/2020 ≈**251 ngày**.                                                                    |
| Tân Hoàng Minh & Vạn Thịnh Phát (cú sốc trái phiếu 2022) |                     1.536,45; 10/01/2022 |                      873,78; 16/11/2022 |                             662,67 | VN-Index “lần đầu chạm 1.600” ngày 11/08/2025 ⇒ chắc chắn đã vượt lại 1.536,45. Số ngày từ 16/11/2022 → 11/08/2025 ≈**999 ngày**.                                                                             |
| Thuế đối ứng Mỹ 46% (Apr–May 2025)                          |                       ~1.315; 02/04/2025 |                   *1.070*; 09/04/2025 |                                250 | VN-Index đóng cửa 1.347,25 ngày 21/05/2025 ⇒ vượt lại ~1.343. Số ngày từ 03/04/2025 → 21/05/2025 ≈**62 ngày**.                                                                                                       |

**Ghi chú quan trọng:**

- Đỉnh/đáy được trích dẫn có thể là giá trong phiên hoặc giá đóng cửa tùy theo nguồn báo chí.
- Với sự kiện thuế quan 2025, đáy được xác định chính xác theo ngày là phiên giảm mạnh 03/04/2025.

---

## 2. STEP 1 — GJR-GARCH FILTERING

### 2.1 Mục đích

Loại bỏ serial dependence và conditional heteroskedasticity trước khi ước lượng copula.

### 2.2 Model spec

**Conditional mean:**

```
r_{i,t} = μ_i + ε_{i,t}
```

**Innovation:**

```
ε_{i,t} = σ_{i,t} · z_{i,t},    z_{i,t} ~ skewed-t(0, 1, ν, ξ)
```

**Conditional variance (GJR-GARCH(1,1)):**

```
σ²_{i,t} = ω_i + α_i·ε²_{i,t-1} + γ_i·ε²_{i,t-1}·𝟙{ε_{i,t-1}<0} + β_i·σ²_{i,t-1}
```

- `α_i` : ARCH effect
- `β_i` : volatility persistence
- `γ_i` : leverage/asymmetry (expect γ > 0 for most stocks)
- `ν`   : degrees of freedom (tail thickness)
- `ξ`   : skewness parameter

### 2.3 Estimation

- Method: Maximum Likelihood Estimation (MLE)
- Library gợi ý: `rugarch` (R) hoặc `arch` (Python)
- Ước lượng **từng stock riêng lẻ** (univariate)

### 2.4 Standardized Residuals

```
ẑ_{i,t} = ε̂_{i,t} / σ̂_{i,t}
```

### 2.5 Pseudo-Uniform Transform (PIT)

```
u_{i,t} = rank(ẑ_{i,t}) / (T + 1)
```

- Kết quả: u_{i,t} ∈ (0,1) — đây là input cho copula estimation

### 2.6 Diagnostics (bắt buộc báo cáo)

| Test               | Applied to | Pass criterion | Mục đích               |
| ------------------ | ---------- | -------------- | ------------------------- |
| Ljung-Box (lag 10) | ẑ_{i,t}   | p > 0.05       | No serial autocorrelation |
| Ljung-Box (lag 10) | ẑ²_{i,t} | p > 0.05       | No remaining ARCH effects |
| Kolmogorov-Smirnov | u_{i,t}    | p > 0.05       | Uniformity of PIT series  |

**Báo cáo:** Tỷ lệ % stocks pass mỗi test, breakdown theo sector → Table 1 trong paper.

---

## 3. STEP 2A — PIPELINE A: PEARSON CORRELATION

### 3.1 Công thức

```
ρ_{ij} = Σ(ẑ_{i,t} - z̄_i)(ẑ_{j,t} - z̄_j) / sqrt[Σ(ẑ_{i,t}-z̄_i)² · Σ(ẑ_{j,t}-z̄_j)²]
```

Tính trên **standardized residuals** ẑ (không phải raw returns).

### 3.2 Output

- Ma trận N×N Pearson correlation → dùng để build PMFG_corr
- Convert sang distance: `d_{ij} = sqrt(2·(1 - ρ_{ij}))`

---

## 4. STEP 2B — PIPELINE B: CLAYTON COPULA

### 4.1 Lý do chọn Clayton

- Thuộc họ Archimedean
- Chỉ capture **lower-tail dependence** (λ_U = 0 by construction)
- Phù hợp nhất với crash co-movement trong equity markets
- Không capture upper-tail → đây là feature, không phải bug, vì mục tiêu là downside risk

### 4.2 Bivariate Clayton Copula

```
C(u_i, u_j; θ) = (u_i^{-θ} + u_j^{-θ} - 1)^{-1/θ},    θ > 0
```

### 4.3 Ước lượng θ_

```
θ̂_MoM = 2τ̂ / (1 - τ̂)
```

trong đó τ̂ là Kendall's tau

### 4.4 Lower-Tail Dependence Coefficient

```
λ^L_{ij} = 2^{-1/θ_{ij}}
```

- λ^L_{ij} ∈ (0, 0.5] khi θ > 0
- λ^L = 0 nghĩa là tail independence
- Cao hơn = hai stocks có xu hướng crash cùng nhau mạnh hơn

### 4.5 Output

- Ma trận N×N của λ^L_{ij} → dùng trực tiếp làm edge weights trong PMFG_tail
- **Không** convert sang distance — dùng λ^L trực tiếp (larger = stronger = retained first)

### 4.6 Xử lý τ̂ ≤ 0

* Nếu τ̂_{ij} ≤ 0: set θ̂_{ij} = 0 và λ^L_{ij} = 0 (cặp này không có lower-tail dependence)
* **Không loại** cặp này khỏi sample — giữ lại với weight = 0 trong PMFG (sẽ không được chọn vào graph)
* Báo cáo tỷ lệ % pairs có τ̂ ≤ 0 trong descriptive statistics

---

## 5. STEP 3 — PMFG CONSTRUCTION

### 5.1 Giải thích PMFG

Planar Maximally Filtered Graph giữ lại các edges mạnh nhất trong khi đảm bảo graph là **planar** (có thể vẽ trên mặt phẳng không có edges cắt nhau). Kết quả: sparse network dễ interpret, giữ được clustering structure tốt hơn MST.

### 5.2 Số edges trong PMFG

```
|E| = 3(N - 2)
```

Ví dụ: N=193 → 573 edges.

### 5.3 Algorithm (áp dụng cho cả hai pipeline)

**Bước 1:** Sort tất cả pairs theo edge weight (giảm dần cho Clayton λ^L; tăng dần cho Pearson distance d_{ij}).

**Bước 2:** Khởi tạo graph rỗng G = (V, ∅).

**Bước 3:** Lần lượt thêm edge theo thứ tự ưu tiên:

```
for each candidate edge (i,j) in sorted order:
    G_temp = G ∪ {(i,j)}
    if is_planar(G_temp):
        G = G_temp
    if |E(G)| == 3(N-2):
        break
```

**Bước 4:** Output: PMFG_corr (từ Pearson) và PMFG_tail (từ Clayton λ^L).

### 5.4 Library gợi ý

- Python: `networkx` có `check_planarity()` — dùng Boyer-Myrvold algorithm

### 5.5 Edge weights trong PMFG

- **PMFG_corr:** edge weight = ρ_{ij} (Pearson correlation, bản gốc, không phải distance)
- **PMFG_tail:** edge weight = λ^L_{ij} (Clayton lower-tail coefficient)

---

## 6. STEP 4 — CENTRALITY MEASURES

Tính 4 centrality metrics cho mỗi node i trong mỗi PMFG (áp dụng cho cả hai pipeline).

### 6.1 Weighted Degree Centrality

```
C_D,i = Σ_{j ∈ N_i} w_{ij}
```

Tổng sức mạnh của tất cả direct connections. Node có C_D cao = nhiều strong links.

### 6.2 Betweenness Centrality

```
C_B,i = Σ_{s≠i≠t} σ_{st}(i) / σ_{st}
```

- σ_{st} = số shortest paths từ s đến t
- σ_{st}(i) = số paths đó đi qua i
- Node có C_B cao = "bridge" — bỏ nó đi thì network bị phân mảnh

### 6.3 Closeness Centrality

```
C_C,i = (N-1) / Σ_{j≠i} d(i,j)
```

- d(i,j) = shortest path distance (dùng inverse weight: d = 1/w)
- Node có C_C cao = trung bình gần mọi node khác → shock lan nhanh

### 6.4 Eigenvector Centrality

```
C_E,i = (1/λ) · Σ_{j ∈ N_i} A_{ij} · C_E,j
```

- A = adjacency matrix (weighted)
- λ = largest eigenvalue
- Node có C_E cao = kết nối với các node quan trọng khác (recursive influence)

### 6.5 Implementation notes

- Dùng weighted versions của tất cả 4 metrics
- Normalize từng metric về [0,1] trước khi đưa vào PCA
- Library: `networkx` (Python) hoặc `igraph` (R)

---

## 7. STEP 5 — SYSTEMIC IMPORTANCE INDEX (SII)

### 7.1 Construction via PCA

```
SII_i = w_D·C_D,i + w_B·C_B,i + w_C·C_C,i + w_E·C_E,i
```

- w_D, w_B, w_C, w_E = loadings của **first principal component** từ PCA
- PCA applied to normalized 4×N centrality matrix
- First PC thường explain ≥ 50% variance — báo cáo % explained

### 7.2 Hai versions

- **SII_corr** từ PMFG_corr (Pipeline A)
- **SII_tail** từ PMFG_tail (Pipeline B)

### 7.3 Sector-level SII

```
SII_sector_s = mean(SII_i) for all i in sector s
```

Dùng để rank sectors và track sector rotation qua sub-periods.

---

## 8. STEP 6 — ANALYSIS & RESULTS

### 8.1 RQ1: Mức độ lower-tail dependence

**Deliverables:**

(a) **Descriptive statistics của λ^L_{ij}:**

- Mean, median, std, 10th/90th percentile toàn bộ pairs
- So sánh intra-sector pairs vs cross-sector pairs (paired t-test hoặc Wilcoxon)
- Hypothesis: intra-sector λ^L > cross-sector λ^L

(b) **Heatmap 11×11 sector-level λ^L:**

- Entry (s1, s2) = mean λ^L của tất cả pairs giữa sector s1 và s2
- Diagonal = intra-sector mean
- Figure chính cho RQ1

(c) **Sub-period evolution:**

- Tính mean λ^L theo từng sub-period
- Test: λ^L_COVID > λ^L_Normal (Wilcoxon signed-rank test)
- Báo cáo p-value và effect size

(d) **Distribution plot:**

- Histogram của λ^L toàn thị trường (full sample)
- Overlay normal period vs COVID period → cho thấy right shift khi crisis

### 8.2 RQ2: Sector nào systemic nhất?

**Deliverables:**

(a) **Top 10 stocks by SII_tail** (full sample):

- Table: Rank | Stock | Sector | SII_tail | SII_corr | Rank_corr | Rank diff
- Highlight case studies có rank divergence lớn giữa hai pipeline

(b) **Sector SII_tail rankings** qua 4 sub-periods:

- Table 4×11: rows = sub-periods, columns = sectors, entries = sector SII_tail rank
- Identify "persistent core" sectors vs "crisis-rotating" sectors

(c) **Sectoral network graph** (Figure chính của RQ2):

- 10 nodes = 10 sectors
- Edge weight = mean λ^L giữa hai sectors
- Node size = sector-level SII_tail
- Vẽ riêng cho Normal và COVID để thấy densification

(d) **Sub-period narrative:**

- COVID: Financials–Real Estate nexus tighten
- Trade War & Trump Tariff: Materials/Energy/Industrials nổi lên
- Giải thích cơ chế kinh tế cho từng pattern

### 8.3 RQ3: Clayton có tốt hơn Pearson không?

**Deliverables:**

(a) **Jaccard Similarity Index:**

```
J(E_corr, E_tail) = |E_corr ∩ E_tail| / |E_corr ∪ E_tail|
```

- Tính cho full sample và từng sub-period
- J thấp (~0.5) → hai mạng nhìn thị trường rất khác nhau

(b) **Spearman rank correlation giữa SII_corr và SII_tail:**

- Overall correlation + breakdown theo sector
- Identify stocks có |rank_corr - rank_tail| lớn nhất → case studies

(c) **Crisis validation regression (key test):**

```
R̄_{i,crisis} = α + β_corr·SII_{i,corr} + β_tail·SII_{i,tail} + ε_i
```

- Chạy riêng cho từng sub-period
- Dependent variable: average daily log-return trong crisis window
- All SII regressors cross-sectionally standardized (zero mean, unit variance)
- Heteroskedasticity-robust standard errors
- **Key prediction:** β_tail < 0 và significant trong COVID-19
- **Sign flip:** β_corr > 0 nhưng β_tail < 0 → Clayton identifies true crash risk; Pearson misleads

---

## 9. TABLES VÀ FIGURES

### Tables (gợi ý)

| Table    | Nội dung                                                                                           |
| -------- | --------------------------------------------------------------------------------------------------- |
| Table 1  | Sample composition by sector (N stocks, % HOSE market cap)                                          |
| Table 2  | Descriptive statistics of daily log-returns by sector                                               |
| Table 3  | GJR-GARCH parameter estimates (median per sector) + diagnostics pass rates                          |
| Table 4  | Pairwise Clayton λ^L statistics: full sample + sub-period breakdown                                |
| Table 5  | PMFG topology metrics: avg clustering, avg path length, by pipeline × sub-period, and whole period |
| Table 6  | Jaccard similarity index: PMFG_corr vs PMFG_tail, by sub-period                                     |
| Table 7  | Top 10 stocks by SII_tail with cross-framework rank comparison                                      |
| Table 8  | Sector SII_tail rankings across 4 sub-periods                                                       |
| Table 9  | Spearman rank correlation: SII_corr vs SII_tail                                                     |
| Table 10 | Crisis validation regression results (4 sub-periods)                                                |

### Figures (gợi ý)

| Figure           | Nội dung                                                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fig 1            | Histogram của λ^L: full sample vs Normal vs COVID overlay                                                                                          |
| Fig 2            | Heatmap 11×11 sector-level mean λ^L (full sample)                                                                                                  |
| Fig 3            | Sectoral network graph: 4 sub-periods (2×2 grid — Normal / Trade War / COVID / Trump Tariff); node size = sector SII_tail, edge weight = mean λ^L |
| Fig 4            | PMFG_tail topology: 4 sub-periods (2×2 grid); nodes colour-coded by GICS sector                                                                     |
| Fig 5            | PMFG_tail with SII scores: 4 sub-periods (2×2 grid); node size + colour = SII_tail                                                                  |
| Fig 6            | Sector SII_tail heatmap qua 4 sub-periods (sector rotation chart)                                                                                    |
| Fig 7 (Appendix) | Master grid: PMFG_tail topology × 4 sub-periods (full detail, larger format)                                                                        |

## 10. ESTIMATION SEQUENCE (thứ tự thực thi)

```
1. Load & clean price data (HOSE, 2016–2025)
2. Stock selection: composite rank per sector → final sample
3. Compute log returns r_{i,t}
4. For each stock i:
   a. Estimate GJR-GARCH(1,1) with skewed-t → get σ̂_{i,t}
   b. Compute standardized residuals ẑ_{i,t}
   c. Apply PIT → u_{i,t}
   d. Run diagnostics (LB on ẑ, LB on ẑ², KS on u)
5. For each pair (i,j):
   a. Compute Pearson ρ_{ij} from ẑ series
   b. Compute Kendall's τ̂_{ij} from (u_i, u_j)
   c. Derive θ̂_{ij} = 2·τ̂_{ij} / (1 - τ̂_{ij}); if τ̂ ≤ 0 then θ̂ = 0
   d. Derive λ^L_{ij} = 2^{-1/θ̂_{ij}}; if θ̂ = 0 then λ^L = 0
6. Build PMFG_corr from ρ matrix (via distance d_{ij})
7. Build PMFG_tail from λ^L matrix
8. Compute 4 centrality measures on each PMFG
9. Run PCA → SII_corr and SII_tail for each stock
10. Compute sector-level SII
11. Repeat steps 5–10 for each sub-period window
12. Run all analysis: descriptive λ^L, Jaccard, Spearman, crisis regression
```

---

## 11. SOFTWARE & PACKAGES

### Python (recommended)

```python
# Data
pandas, numpy, yfinance / vnstock

# GARCH
arch  # GJR-GARCH with skewed-t

# Copula
scipy.optimize  # MLE for Clayton
statsmodels  # Kendall tau for MoM

# Network
networkx  # PMFG construction, centrality measures
# Note: networkx has check_planarity() built-in

# PCA
sklearn.decomposition.PCA

# Visualization
matplotlib, seaborn  # heatmaps, histograms
networkx + matplotlib  # network graphs
```

---

## 12. KEY ASSUMPTIONS & LIMITATIONS (cần nêu trong paper)

1. **Pairwise copula estimation:** Bỏ qua higher-dimensional dependence structure
2. **Static copula:** θ không time-varying trong mỗi sub-period window
3. **Clayton chỉ capture lower-tail:** Upper-tail co-movement bị bỏ qua hoàn toàn (đây là intentional trade-off)
4. **HOSE only:** Kết quả không nhất thiết generalize sang HNX hoặc OTC
5. **Price-based SII:** Không capture fundamental balance sheet linkages (interbank lending, cross-ownership)
6. **Trump Tariff sub-period chỉ có ~40 trading days** → kết quả cần interpret với caution

---

## 13. HYPOTHESES CHÍNH CẦN TEST

| Hypothesis                                                    | Test                                     | Expected result                                        |
| ------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------ |
| H1: Lower-tail dependence tồn tại và có cấu trúc sector | Intra vs cross-sector λ^L Wilcoxon test | Intra-sector λ^L > cross-sector, p < 0.05             |
| H2: Financials–Real Estate là systemic core                 | SII_tail sector rankings (full sample)   | Financials top 2, Real Estate top 3                    |
| H3: Lower-tail dependence tăng trong crisis                  | λ^L_COVID vs λ^L_Normal Wilcoxon       | λ^L_COVID > λ^L_Normal, p < 0.05                     |
| H4: Clayton SII dự báo crash losses tốt hơn Pearson       | Crisis regression, COVID window          | β_tail < 0 và significant; β_corr không âm        |
| H5: Network structure phản ứng khác nhau với loại shock  | Sub-period topology comparison           | COVID → dense core; Trade War/Tariff → fragmentation |

---

## 14. POLICY IMPLICATIONS (viết trong Conclusion)

Kết quả của paper nên dẫn đến 3 khuyến nghị policy cụ thể:

1. **SSC nên tích hợp lower-tail dependence metrics** vào hệ thống giám sát SIFI, không chỉ dùng correlation-based measures
2. **Macroprudential focus:** Financials–Real Estate nexus cần stricter cross-sectoral capital buffers vì đây là systemic core ổn định nhất qua mọi sub-period
3. **Origin-specific policy response:** Shock từ broad economic halt (COVID) → cần broad liquidity backstop tập trung vào banking hub; shock từ trade policy → cần targeted support cho Materials/Energy/Industrials

---

## 15. TỔNG KẾT KẾT QUẢ THỰC NGHIỆM (Key Findings)

Dưới đây là tóm tắt các kết quả quan trọng nhất thu được từ bộ dữ liệu HOSE (N=193 stocks, 2016-2025).

### 15.1 RQ1: Đặc điểm Lower-Tail Dependence
- **Sự tồn tại:** Median Clayton $\lambda_L$ đạt 0.099, cho thấy tính độc lập tương đối trong điều kiện bình thường nhưng rủi ro "đồng crash" tiềm ẩn cực lớn.
- **Biến động:** $\lambda_L$ tăng vọt gấp **7 lần** (lên 0.694) trong cú sốc thuế quan Mỹ (Trump Tariff), xác nhận thị trường HOSE cực kỳ nhạy cảm với các đợt repricing từ bên ngoài.
- **Cấu trúc Sector:** Nhóm **Financials** và **Real Estate** vẫn là lõi hệ thống, nhưng nhóm **Materials** (với đại diện AAA) nổi lên như một trạm trung chuyển rủi ro (hub) mới.

### 15.2 RQ2: Các thực thể có tầm quan trọng hệ thống (SII)
- **Persistent Core:** SSI và HCM duy trì vị thế dẫn dắt mạng lưới rủi ro đuôi qua hầu hết các giai đoạn.
- **Regime Rotation:** 
    - *Bond Shock:* **LDG** và **SCR** chiếm lĩnh top đầu, phản ánh sự đổ vỡ niềm tin tập trung vào mảng BĐS đòn bẩy cao.
    - *Trump Tariff:* **KSB** và **GAS** vươn lên, cho thấy sự xoay trục rủi ro sang các ngành thâm dụng vốn và năng lượng.
- **Systemic Hubs:** **AAA** là mã xuất hiện nhiều nhất trong các cặp rủi ro cực đoan (hub), vượt qua cả các mã chứng khoán truyền thống.

### 15.3 RQ3: Hiệu quả của Clayton Copula so với Pearson Correlation
- **Sự khác biệt mạng lưới:** Pearson Correlation bỏ lỡ đến **87%** các kết nối rủi ro thực sự trong giai đoạn COVID-19 (Jaccard = 0.125).
- **Kiểm định Crisis Validation:** 
    - Chỉ số $SII_{tail}$ giải thích đến **34%** biến động sụt giảm giá trong cú sốc Trái phiếu ($R^2=0.342$), trong khi chỉ số dựa trên tương quan truyền thống hoàn toàn mất tác dụng ($p > 0.5$).
- **Kết luận:** Mô hình Clayton Copula là công cụ bắt buộc phải có để nhận diện các "đường dây" lây lan rủi ro mà các phương pháp truyền thống không thể nhìn thấy.

---

*End of architecture.md*
*Analysis: HOSE-only, N=193*

