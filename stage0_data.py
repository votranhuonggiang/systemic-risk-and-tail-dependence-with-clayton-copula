import os
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════
TOTAL_N         = 350                           # Target total stocks for the universe
START_DATE      = '2016-01-01'
END_DATE        = '2025-12-31'
MIN_COVERAGE    = 0.80                           # 80% of trading days required

# Helper function to query QuestDB
def query_questdb(sql_query):
    """Execute a raw SQL query against QuestDB"""
    host = os.environ.get("QUEST_DB_URL", "http://localhost:9000")
    auth = (os.getenv("QUESTDB_USERNAME"), os.getenv("QUESTDB_PASSWORD"))

    try:
        response = requests.get(
            host + "/exec", params={"query": sql_query}, auth=auth
        ).json()

        if "dataset" not in response or "columns" not in response:
            print(f"Error or no data: {response}")
            return pd.DataFrame()

        df = pd.DataFrame(
            response["dataset"],
            columns=pd.DataFrame(response["columns"])["name"].values,
        )
        return df

    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# ── Queries ────────────────────────────────────────────────────────────────
QUERY_GET_SYMBOLS = f"""
    SELECT DISTINCT symbol 
    FROM raw_historical_list 
    WHERE exchange IN ('HSX') 
      AND timestamp <= '{END_DATE}'
      AND LENGTH(symbol) = 3
"""

# ══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════
os.makedirs("data",          exist_ok=True)
os.makedirs("output/stage0", exist_ok=True)

def normalise_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df.columns = df.columns.str.lower().str.strip()
    rename_map = {
        "stock_code": "ticker", "symbol": "ticker", "stockcode": "ticker",
        "trading_date": "date", "trade_date": "date", "tradingdate": "date",
        "adj_close": "adjusted_close", "close_adj": "adjusted_close",
        "industry": "sector_name", "sector": "sector_name", "icb": "sector_name",
        "marketcap": "market_cap",
    }
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

# 0.0 Get symbols
print(f"0.0  Fetching active HSX symbol list up to {END_DATE} …")
symbols_df = query_questdb(QUERY_GET_SYMBOLS)
active_symbols = symbols_df["symbol"].tolist()
symbols_str = "(" + ", ".join([f"'{s}'" for s in active_symbols]) + ")"

# 0.1 Fetch OHLCV
print(f"0.1  Fetching OHLCV from {START_DATE} to {END_DATE} …")
YOUR_QUERY_OHLCV = f"""
    SELECT symbol AS ticker, timestamp AS date, close AS adjusted_close, volume 
    FROM raw_eod 
    WHERE timestamp >= '{START_DATE}' AND timestamp <= '{END_DATE}'
      AND symbol IN {symbols_str}
"""
ohlcv = normalise_cols(query_questdb(YOUR_QUERY_OHLCV))
ohlcv["date"] = pd.to_datetime(ohlcv["date"])

# 0.2 Coverage Filter (80%)
print("0.2  Applying 80% coverage filter …")
total_days = ohlcv["date"].nunique()
counts = ohlcv.groupby("ticker")["adjusted_close"].count()
eligible_tickers = counts[counts >= total_days * MIN_COVERAGE].index.tolist()
ohlcv = ohlcv[ohlcv["ticker"].isin(eligible_tickers)]
eligible_str = "(" + ", ".join([f"'{s}'" for s in eligible_tickers]) + ")"

# 0.3 Fetch Sector & MCAP for eligible only
print("0.3  Fetching Sector and Market Cap data …")
QUERY_SECTOR = f"SELECT symbol AS ticker, timestamp AS date, level_1_industry AS sector_name FROM raw_symbol_industry WHERE timestamp <= '{END_DATE}' AND symbol IN {eligible_str}"
sector = normalise_cols(query_questdb(QUERY_SECTOR))

# Translate sectors to English
VIET_TO_ENG = {
    "Bất động sản": "Real Estate",
    "Chăm sóc sức khỏe": "Health Care",
    "Công nghiệp": "Industrials",
    "Công nghệ thông tin": "Info Tech",
    "Dịch vụ truyền thông": "Media Svc",
    "Nguyên vật liệu": "Materials",
    "Năng lượng": "Energy",
    "Tiêu dùng không thiết yếu": "Cons. Disc.",
    "Tiêu dùng thiết yếu": "Cons. Staples",
    "Tiện ích": "Utilities",
    "Tài chính": "Financials"
}
if not sector.empty:
    sector["sector_name"] = sector["sector_name"].map(VIET_TO_ENG).fillna(sector["sector_name"])
    sector = sector.sort_values("date").groupby("ticker").last().reset_index()

QUERY_MCAP = f"SELECT symbol AS ticker, timestamp AS date, market_cap FROM raw_market_cap WHERE timestamp <= '{END_DATE}' AND symbol IN {eligible_str}"
mcap = normalise_cols(query_questdb(QUERY_MCAP))
if not mcap.empty:
    mcap = mcap.sort_values("date").groupby("ticker").last().reset_index()

# 0.4 Stratified Sampling Logic
print("0.4  Implementing stratified sampling …")

# Compute liquidity (average trading value)
ohlcv["trading_value"] = ohlcv["adjusted_close"] * ohlcv["volume"]
liquidity = ohlcv.groupby("ticker")["trading_value"].mean().reset_index().rename(columns={"trading_value": "avg_trading_value"})

# Merge all metrics
df = sector.merge(liquidity, on="ticker").merge(mcap, on="ticker")
df = df.dropna(subset=["avg_trading_value", "market_cap", "sector_name"])

# Calculate sector weights and n_s
sector_mcap = df.groupby("sector_name")["market_cap"].sum().reset_index()
total_market_mcap = sector_mcap["market_cap"].sum()
sector_mcap["weight"] = sector_mcap["market_cap"] / total_market_mcap
sector_mcap["n_s"] = (sector_mcap["weight"] * TOTAL_N).round().astype(int)

# Map n_s back to main dataframe
df = df.merge(sector_mcap[["sector_name", "n_s"]], on="sector_name")

# 0.5 Ranking within sectors
print("0.5  Computing combined rank within sectors …")
df["rank_mcap"] = df.groupby("sector_name")["market_cap"].rank(ascending=False, method="min")
df["rank_liquidity"] = df.groupby("sector_name")["avg_trading_value"].rank(ascending=False, method="min")
df["combined_score"] = (df["rank_mcap"] + df["rank_liquidity"]) / 2
df["combined_rank"] = df.groupby("sector_name")["combined_score"].rank(ascending=True, method="first")

# Select top n_s for each sector
universe = df[df["combined_rank"] <= df["n_s"]].copy()

print(f"\nFinal Universe: {len(universe)} stocks across {universe['sector_name'].nunique()} sectors.")
print(universe.groupby("sector_name")["ticker"].count())

# 0.6 Save Data
universe.to_csv("data/universe.csv", index=False)
universe[["ticker","sector_name"]].to_csv("data/sector_map.csv", index=False)
prices_wide = ohlcv[ohlcv["ticker"].isin(universe["ticker"])].pivot_table(index="date", columns="ticker", values="adjusted_close").sort_index()
prices_wide = prices_wide.ffill(limit=5)
prices_wide.to_csv("data/prices.csv")

print("\nStage 0 complete.")
