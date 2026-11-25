import pandas as pd
from pathlib import Path


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "online_retail_cleaned.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# LOAD DATA
df = pd.read_csv(DATA_PATH)

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["Customer ID"] = pd.to_numeric(
    df["Customer ID"], errors="coerce"
)

print("=" * 70)
print("COMMON GROUND | DUPLICATE PATTERN ANALYSIS")
print("=" * 70)


# TRANSACTION COMPARISON
comparison_columns = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country"
]

df["IsRepeated"] = df.duplicated(
    subset=comparison_columns,
    keep="first"
)


# 1. TIMESTAMP ANALYSIS
print("\n1. REPEATED TRANSACTIONS BY TIMESTAMP")
print("-" * 70)

repeated = df[df["IsRepeated"]].copy()

print(f"Repeated occurrences: {len(repeated):,}")

repeated_timestamp_summary = (
    repeated.groupby("Invoice")
    .agg(
        RepeatedOccurrences=("Invoice", "size"),
        UniqueTimestamps=("InvoiceDate", "nunique")
    )
)

repeated_timestamp_summary["TimestampPattern"] = (
    repeated_timestamp_summary["UniqueTimestamps"]
    .map(lambda x: "Single timestamp" if x == 1 else "Multiple timestamps")
)

print("\nRepeated invoice timestamp patterns:")
print(
    repeated_timestamp_summary["TimestampPattern"]
    .value_counts()
)

repeated_timestamp_summary.to_csv(
    OUTPUT_DIR / "repeated_timestamp_analysis.csv"
)


# 2. REPEATED LINES ACROSS DIFFERENT TIMESTAMPS
print("\n2. REPEATED PRODUCTS ACROSS DIFFERENT TIMESTAMPS")
print("-" * 70)

invoice_product_columns = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "Price",
    "Customer ID",
    "Country"
]

product_timestamp_analysis = (
    df.groupby(invoice_product_columns, dropna=False)
    .agg(
        Occurrences=("InvoiceDate", "size"),
        UniqueTimestamps=("InvoiceDate", "nunique")
    )
    .reset_index()
)

product_timestamp_analysis = product_timestamp_analysis[
    product_timestamp_analysis["Occurrences"] > 1
]

same_timestamp = product_timestamp_analysis[
    product_timestamp_analysis["UniqueTimestamps"] == 1
]

multiple_timestamps = product_timestamp_analysis[
    product_timestamp_analysis["UniqueTimestamps"] > 1
]

print(f"Repeated product groups: {len(product_timestamp_analysis):,}")
print(f"Groups at one timestamp: {len(same_timestamp):,}")
print(f"Groups across multiple timestamps: {len(multiple_timestamps):,}")

product_timestamp_analysis.to_csv(
    OUTPUT_DIR / "product_timestamp_patterns.csv",
    index=False
)


# 3. DUPLICATE DISTRIBUTION BY INVOICE
print("\n3. DUPLICATE DISTRIBUTION BY INVOICE")
print("-" * 70)

invoice_distribution = (
    repeated.groupby("Invoice")
    .size()
    .sort_values(ascending=False)
)

print(f"Invoices with repeated occurrences: {len(invoice_distribution):,}")
print(f"Maximum repeated occurrences: {invoice_distribution.max():,}")
print("\nTop 15 invoices:")
print(invoice_distribution.head(15))

invoice_distribution.rename(
    "RepeatedOccurrences"
).to_csv(
    OUTPUT_DIR / "duplicate_invoice_distribution.csv"
)


# 4. CUSTOMER TRANSACTION VOLUME COMPARISON
print("\n4. CUSTOMER DUPLICATION VS TRANSACTION VOLUME")
print("-" * 70)

identified = df[df["Customer ID"].notna()].copy()

customer_analysis = (
    identified.groupby("Customer ID")
    .agg(
        TotalTransactionLines=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        RepeatedOccurrences=("IsRepeated", "sum")
    )
)

customer_analysis["RepeatedOccurrenceRate"] = (
    customer_analysis["RepeatedOccurrences"]
    / customer_analysis["TotalTransactionLines"]
    * 100
)

customer_analysis = customer_analysis.sort_values(
    "RepeatedOccurrences",
    ascending=False
)

print("\nTop 15 customers by repeated occurrences:")
print(customer_analysis.head(15).round(2))

customer_analysis.to_csv(
    OUTPUT_DIR / "customer_duplicate_patterns.csv"
)


# 5. DUPLICATION BY SOURCE SHEET
print("\n5. DUPLICATION BY SOURCE SHEET")
print("-" * 70)

source_analysis = (
    df.groupby("SourceSheet")
    .agg(
        TotalRecords=("Invoice", "size"),
        RepeatedOccurrences=("IsRepeated", "sum"),
        UniqueInvoices=("Invoice", "nunique")
    )
)

source_analysis["RepeatedOccurrenceRate"] = (
    source_analysis["RepeatedOccurrences"]
    / source_analysis["TotalRecords"]
    * 100
)

print(source_analysis.round(2))

source_analysis.to_csv(
    OUTPUT_DIR / "source_sheet_duplicate_patterns.csv"
)


# 6. FINAL SUMMARY
print("\n6. ANALYSIS SUMMARY")
print("-" * 70)

print(f"Total records analysed: {len(df):,}")
print(f"Repeated occurrences: {df['IsRepeated'].sum():,}")
print(
    f"Repeated occurrence rate: "
    f"{df['IsRepeated'].mean() * 100:.2f}%"
)

print("\nOUTPUT FILES")
print("-" * 70)

output_files = [
    "repeated_timestamp_analysis.csv",
    "product_timestamp_patterns.csv",
    "duplicate_invoice_distribution.csv",
    "customer_duplicate_patterns.csv",
    "source_sheet_duplicate_patterns.csv"
]

for file in output_files:
    print(file)

print("\n" + "=" * 70)
print("DUPLICATE PATTERN ANALYSIS COMPLETED")
print("=" * 70)
