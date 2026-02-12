import pandas as pd
import sys
import os

# Adjust path to find data relative to this script
# Layout: src/validation/check_data.py
# Data: data/processed/features.csv
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
file_path = os.path.join(base_dir, 'data', 'processed', 'features.csv')

print(f"Reading from: {file_path}")

try:
    df = pd.read_csv(file_path)
    print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
except Exception as e:
    print(f"Error loading dataset: {e}")
    sys.exit(1)

# 1. Negative values check
non_negative_cols = ['revenue', 'total_assets', 'equity', 'revenue_3y_ago', 'capital_employed']
print("\n--- 1. Negative Values Check ---")
for col in non_negative_cols:
    if col in df.columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            print(f"FAIL: {col} has {neg_count} negative values.")
            print(df[df[col] < 0][['ticker', col]])
        else:
            print(f"PASS: {col} has no negative values.")
    else:
        print(f"WARNING: Column {col} not found.")

# 2. Ratios check
print("\n--- 2. Ratios Check ---")
if 'roe' in df.columns:
    outliers = df[(df['roe'] > 5.0) | (df['roe'] < -1.0)]
    if not outliers.empty:
        print(f"Observed extreme ROE values:")
        print(outliers[['ticker', 'roe']])
    else:
        print("ROE looks within normal bounds (-100% to 500%).")

if 'debt_to_equity' in df.columns:
    neg_de = df[df['debt_to_equity'] < 0]
    if not neg_de.empty:
        print(f"FAIL: debt_to_equity has negative values.")
        print(neg_de[['ticker', 'debt_to_equity']])
    else:
        print("PASS: debt_to_equity is non-negative.")

# 3. Missing values
print("\n--- 3. Missing Values Check ---")
missing = df.isnull().sum()
missing = missing[missing > 0]
if not missing.empty:
    print("Found missing values:")
    print(missing)
    for col in missing.index:
        print(f"Missing {col} for: {df[df[col].isnull()]['ticker'].tolist()}")
else:
    print("No missing values found.")

# 4. Duplicates
print("\n--- 4. Duplicate Companies Check ---")
if 'ticker' in df.columns:
    dupes = df[df.duplicated('ticker')]
    if not dupes.empty:
        print("Found duplicate tickers:")
        print(dupes['ticker'])
    else:
        print("No duplicate tickers found.")

# 5. Zero values
print("\n--- 5. Zero Values Check ---")
critical_metrics = ['revenue', 'total_assets']
for col in critical_metrics:
    if col in df.columns:
        zeros = (df[col] == 0).sum()
        if zeros > 0:
            print(f"FAIL: {col} has {zeros} zero values.")
            print(df[df[col] == 0]['ticker'])
        else:
            print(f"PASS: {col} has no zero values.")
