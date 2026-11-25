
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

# LOAD DATA
sheets = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)

df["Invoice"] = df["Invoice"].astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip()
df["LineValue"] = df["Quantity"] * df["Price"]

# CLASSIFY TRANSACTION CHARACTERISTICS
df["IsCancellation"] = df["Invoice"].str.startswith("C")
df["IsNegativeQuantity"] = df["Quantity"] < 0
df["IsZeroPrice"] = df["Price"] == 0
df["IsNegativePrice"] = df["Price"] < 0
df["HasCustomerID"] = df["Customer ID"].notna()

print("=" * 65)
print("COMMON GROUND | TRANSACTION ANALYSIS")
print("=" * 65)

# 1. INVOICE PREFIXES
print("\n1. INVOICE PREFIX ANALYSIS")
print("-" * 65)

df["InvoicePrefix"] = df["Invoice"].str[0]

print(
    df.groupby("InvoicePrefix")
    .agg(
        Records=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalValue=("LineValue", "sum")
    )
    .sort_values("Records", ascending=False)
    .to_string()
)

# 2. CANCELLATION AND NEGATIVE QUANTITY OVERLAP
print("\n2. CANCELLATION / NEGATIVE QUANTITY OVERLAP")
print("-" * 65)

overlap = pd.crosstab(
    df["IsCancellation"],
    df["IsNegativeQuantity"],
    rownames=["Cancellation Invoice"],
    colnames=["Negative Quantity"]
)

print(overlap)

# 3. ZERO-PRICE PRODUCT INVESTIGATION
print("\n3. ZERO-PRICE TRANSACTIONS")
print("-" * 65)

zero_price = df[df["IsZeroPrice"]]

print(f"Zero-price records: {len(zero_price):,}")
print(f"Unique zero-price products: {zero_price['StockCode'].nunique():,}")

print("\nMost frequent zero-price descriptions:")

print(
    zero_price["Description"]
    .value_counts(dropna=False)
    .head(15)
    .to_string()
)

# 4. NON-STANDARD STOCK CODES
print("\n4. NON-STANDARD STOCK CODES")
print("-" * 65)

print(
    df.groupby("StockCode")
    .agg(
        Records=("StockCode", "size"),
        Description=("Description", "first"),
        AveragePrice=("Price", "mean")
    )
    .sort_values("Records", ascending=False)
    .head(25)
    .to_string()
)

# 5. CUSTOMER IDENTIFICATION BY TRANSACTION TYPE
print("\n5. CUSTOMER IDENTIFICATION")
print("-" * 65)

customer_analysis = df.groupby("IsCancellation").agg(
    TotalRecords=("Invoice", "size"),
    MissingCustomerIDs=("Customer ID", lambda x: x.isna().sum()),
    UniqueCustomers=("Customer ID", "nunique")
)

customer_analysis["MissingCustomerPercentage"] = (
    customer_analysis["MissingCustomerIDs"]
    / customer_analysis["TotalRecords"]
    * 100
)

print(customer_analysis.to_string())

# 6. SUMMARY
print("\n6. TRANSACTION ANALYSIS SUMMARY")
print("-" * 65)

print(f"Total records: {len(df):,}")
print(f"Cancellation records: {df['IsCancellation'].sum():,}")
print(f"Negative quantity records: {df['IsNegativeQuantity'].sum():,}")
print(f"Zero-price records: {df['IsZeroPrice'].sum():,}")
print(f"Negative-price records: {df['IsNegativePrice'].sum():,}")

print("\nTRANSACTION ANALYSIS COMPLETED")
