import os

# ══════════════════════════════════════════════════════════════════════════
# SUB-PERIOD DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════
REGIMES = {
    "Normal": [
        ("2016-01-01", "2018-03-31"),
        ("2020-01-04", "2022-08-31"),
        ("2023-01-01", "2025-03-31")
    ],
    "Trade War": [
        ("2018-04-01", "2018-10-31")
    ],
    "COVID-19": [
        ("2020-01-01", "2020-03-31")
    ],
    "Bond Shock": [
        ("2022-09-01", "2022-11-16")
    ],
    "Trump Tariff": [
        ("2025-04-01", "2025-04-20")
    ]
}

# ══════════════════════════════════════════════════════════════════════════
# DIRECTORIES
# ══════════════════════════════════════════════════════════════════════════
DATA_DIR = "data"
OUTPUT_DIR = "output"
STAGE_DIRS = {
    "stage0": os.path.join(OUTPUT_DIR, "stage0"),
    "stage1": os.path.join(OUTPUT_DIR, "stage1"),
    "stage2": os.path.join(OUTPUT_DIR, "stage2"),
    "stage3": os.path.join(OUTPUT_DIR, "stage3"),
    "stage4": os.path.join(OUTPUT_DIR, "stage4"),
    "stage5": os.path.join(OUTPUT_DIR, "stage5")
}

for d in STAGE_DIRS.values():
    os.makedirs(d, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════
LAG_LJUNG_BOX = 10
SIGNIFICANCE_LEVEL = 0.05
