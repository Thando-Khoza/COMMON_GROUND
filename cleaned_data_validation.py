
from pathlib import Path

import pandas as pd


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "online_retail_cleaned.csv"


# LOAD CLEANED DATASET
df = pd.read_csv(
    DATA_FILE,
    parse_dates=["InvoiceDate"]
)


print("=" * 70)
print("COMMON GROUND | CLEANED DATA VALIDATION")
print("=" * 70)


# 1. DATASET OVERVIEW
print("\n1. DATASET OVERVIEW")
print("-" * 70)

print(f"Total records: {len(df):,}")
print(f"Total columns: {len(df.columns)}")

print("\nColumn data types:")
print(df.dtypes)

print("\nDate range:")
print(f"Start: {df['InvoiceDate'].min()}")
print(f"End:   {df['InvoiceDate'].max()}")


# 2. MISSING VALUES
print("\n2. MISSING VALUE ANALYSIS")
print("-" * 70)

missing = pd.DataFrame({
    "Missing Values": df.isnull().sum(),
    "Missing Percentage": (
        df.isnull().mean() * 100
    ).round(2)
})

print(missing.to_string())


# 3. REMAINING EXACT DUPLICATES
print("\n3. REMAINING EXACT DUPLICATES")
print("-" * 70)

comparison_columns = [
    column for column in df.columns
    if column != "SourceSheet"
]

duplicate_count = df.duplicated(
    subset=comparison_columns
).sum()

duplicate_group_records = df.duplicated(
    subset=comparison_columns,
    keep=False
).sum()

print(f"Repeated occurrences beyond first copy: {duplicate_count:,}")
print(f"Records belonging to duplicate groups: {duplicate_group_records:,}")


# 4. QUANTITY ANALYSIS
print("\n4. QUANTITY ANALYSIS")
print("-" * 70)

print(f"Positive quantities: {(df['Quantity'] > 0).sum():,}")
print(f"Negative quantities: {(df['Quantity'] < 0).sum():,}")
print(f"Zero quantities: {(df['Quantity'] == 0).sum():,}")

print("\nQuantity statistics:")
print(df["Quantity"].describe().to_string())


# 5. PRICE ANALYSIS
print("\n5. PRICE ANALYSIS")
print("-" * 70)

print(f"Positive prices: {(df['Price'] > 0).sum():,}")
print(f"Negative prices: {(df['Price'] < 0).sum():,}")
print(f"Zero prices: {(df['Price'] == 0).sum():,}")

print("\nPrice statistics:")
print(df["Price"].describe().to_string())


# 6. CANCELLATION ANALYSIS
print("\n6. CANCELLATION ANALYSIS")
print("-" * 70)

df["IsCancellation"] = (
    df["Invoice"].astype(str).str.startswith("C")
)

print(f"Cancellation records: {df['IsCancellation'].sum():,}")
print(f"Non-cancellation records: {(~df['IsCancellation']).sum():,}")

print("\nCancellation and quantity comparison:")
print(
    pd.crosstab(
        df["IsCancellation"],
        df["Quantity"] < 0,
        rownames=["Cancellation"],
        colnames=["Negative Quantity"]
    ).to_string()
)


# 7. TRANSACTION VALUE ANALYSIS
print("\n7. TRANSACTION VALUE ANALYSIS")
print("-" * 70)

df["LineValue"] = df["Quantity"] * df["Price"]

print(f"Positive line values: {(df['LineValue'] > 0).sum():,}")
print(f"Negative line values: {(df['LineValue'] < 0).sum():,}")
print(f"Zero line values: {(df['LineValue'] == 0).sum():,}")

print("\nLine value statistics:")
print(df["LineValue"].describe().to_string())


# 8. CUSTOMER ID ANALYSIS
print("\n8. CUSTOMER ID ANALYSIS")
print("-" * 70)

print(f"Records with Customer ID: {df['Customer ID'].notna().sum():,}")
print(f"Records without Customer ID: {df['Customer ID'].isna().sum():,}")
print(f"Unique identified customers: {df['Customer ID'].nunique():,}")


# 9. SOURCE SHEET VALIDATION
print("\n9. SOURCE SHEET VALIDATION")
print("-" * 70)

print(df["SourceSheet"].value_counts().to_string())


# FINAL STATUS
print("\n" + "=" * 70)
print("CLEANED DATA VALIDATION COMPLETED")
print("=" * 70)
