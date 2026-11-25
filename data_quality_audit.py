
from pathlib import Path
import pandas as pd

# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

# LOAD BOTH WORKBOOK SHEETS
print("Loading Online Retail II dataset...")

sheets = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)

print("\nDATASET LOADED")
print(f"Total records: {len(df):,}")

# 1. INVOICE INVESTIGATION
print("\n" + "=" * 65)
print("1. INVOICE INVESTIGATION")
print("=" * 65)

df["Invoice"] = df["Invoice"].astype(str).str.strip()

cancellations = df["Invoice"].str.startswith("C", na=False)

print(f"Cancellation records: {cancellations.sum():,}")
print(f"Other invoice records: {(~cancellations).sum():,}")

# 2. QUANTITY INVESTIGATION
print("\n" + "=" * 65)
print("2. QUANTITY INVESTIGATION")
print("=" * 65)

print(f"Negative quantities: {(df['Quantity'] < 0).sum():,}")
print(f"Zero quantities: {(df['Quantity'] == 0).sum():,}")
print(f"Positive quantities: {(df['Quantity'] > 0).sum():,}")

print("\nNegative quantity examples:")
print(df.loc[df["Quantity"] < 0].head(10).to_string(index=False))

# 3. PRICE INVESTIGATION
print("\n" + "=" * 65)
print("3. PRICE INVESTIGATION")
print("=" * 65)

print(f"Negative prices: {(df['Price'] < 0).sum():,}")
print(f"Zero prices: {(df['Price'] == 0).sum():,}")
print(f"Positive prices: {(df['Price'] > 0).sum():,}")

print("\nNegative price examples:")
print(df.loc[df["Price"] < 0].head(10).to_string(index=False))

print("\nHighest price records:")
print(
    df.nlargest(10, "Price")[
        ["Invoice", "StockCode", "Description", "Quantity", "Price"]
    ].to_string(index=False)
)

# 4. CUSTOMER DATA INVESTIGATION
print("\n" + "=" * 65)
print("4. CUSTOMER DATA INVESTIGATION")
print("=" * 65)

missing_customers = df["Customer ID"].isna()

print(f"Records without Customer ID: {missing_customers.sum():,}")
print(f"Records with Customer ID: {(~missing_customers).sum():,}")

print("\nCountries with most records missing Customer IDs:")

missing_by_country = (
    df.loc[missing_customers]
    .groupby("Country")
    .size()
    .sort_values(ascending=False)
)

print(missing_by_country.head(10).to_string())

# 5. DUPLICATE INVESTIGATION
print("\n" + "=" * 65)
print("5. DUPLICATE INVESTIGATION")
print("=" * 65)

duplicate_mask = df.duplicated(keep=False)

print(f"Records involved in duplicate groups: {duplicate_mask.sum():,}")

print("\nDuplicate examples:")
print(df.loc[duplicate_mask].head(10).to_string(index=False))

# 6. DATE INVESTIGATION
print("\n" + "=" * 65)
print("6. DATE INVESTIGATION")
print("=" * 65)

print(f"Earliest transaction: {df['InvoiceDate'].min()}")
print(f"Latest transaction: {df['InvoiceDate'].max()}")

print("\nRecords by year:")
print(df.groupby(df["InvoiceDate"].dt.year).size().to_string())

# 7. TRANSACTION VALUE INVESTIGATION
print("\n" + "=" * 65)
print("7. TRANSACTION VALUE INVESTIGATION")
print("=" * 65)

df["LineValue"] = df["Quantity"] * df["Price"]

print(f"Negative line values: {(df['LineValue'] < 0).sum():,}")
print(f"Zero line values: {(df['LineValue'] == 0).sum():,}")
print(f"Positive line values: {(df['LineValue'] > 0).sum():,}")

# 8. FINAL AUDIT SUMMARY
print("\n" + "=" * 65)
print("DATA QUALITY AUDIT COMPLETED")
print("=" * 65)
