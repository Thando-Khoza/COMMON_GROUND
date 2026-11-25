
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

# LOAD DATA
sheets = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)

print("=" * 65)
print("COMMON GROUND | DUPLICATE ANALYSIS")
print("=" * 65)

# 1. EXACT DUPLICATE COUNTS
print("\n1. EXACT DUPLICATE RECORDS")
print("-" * 65)

duplicate_mask = df.duplicated(keep=False)
excess_duplicates = df.duplicated(keep="first")

print(f"Records in duplicate groups: {duplicate_mask.sum():,}")
print(f"Repeated records beyond first occurrence: {excess_duplicates.sum():,}")

# 2. DUPLICATE RECORDS BY INVOICE
print("\n2. INVOICES WITH EXACT DUPLICATES")
print("-" * 65)

duplicate_rows = df[duplicate_mask].copy()

invoice_duplicates = (
    duplicate_rows.groupby("Invoice")
    .size()
    .sort_values(ascending=False)
)

print(invoice_duplicates.head(15).to_string())

# 3. REPEATED PRODUCTS WITHIN INVOICES
print("\n3. REPEATED PRODUCTS WITHIN INVOICES")
print("-" * 65)

invoice_product_counts = (
    df.groupby(["Invoice", "StockCode"], dropna=False)
    .size()
    .reset_index(name="LineCount")
)

repeated_products = invoice_product_counts[
    invoice_product_counts["LineCount"] > 1
]

print(f"Invoice/product combinations: {len(invoice_product_counts):,}")
print(f"Repeated combinations: {len(repeated_products):,}")

print("\nExamples:")
print(repeated_products.head(20).to_string(index=False))

# 4. EXACT DUPLICATE VALUE IMPACT
print("\n4. POTENTIAL DUPLICATE VALUE IMPACT")
print("-" * 65)

df["LineValue"] = df["Quantity"] * df["Price"]

duplicate_excess = df[excess_duplicates]

print(f"Repeated records: {len(duplicate_excess):,}")
print(f"Quantity in repeated records: {duplicate_excess['Quantity'].sum():,}")
print(f"Line value in repeated records: {duplicate_excess['LineValue'].sum():,.2f}")

# 5. DUPLICATES BY REPORTING YEAR
print("\n5. DUPLICATES BY YEAR")
print("-" * 65)

df["Year"] = df["InvoiceDate"].dt.year

year_duplicates = (
    df.groupby("Year")
    .apply(lambda group: group.duplicated().sum())
)

print(year_duplicates.to_string())

print("\n" + "=" * 65)
print("DUPLICATE ANALYSIS COMPLETED")
print("=" * 65)
