
from pathlib import Path

import pandas as pd


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "online_retail_cleaned.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"


# LOAD DATA
df = pd.read_csv(
    DATA_FILE,
    parse_dates=["InvoiceDate"]
)

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

df["LineValue"] = df["Quantity"] * df["Price"]

print("=" * 70)
print("COMMON GROUND | INVOICE STRUCTURE ANALYSIS")
print("=" * 70)


# 1. INVOICE OVERVIEW
invoice_summary = (
    df.groupby("Invoice")
    .agg(
        TotalLines=("Invoice", "size"),
        UniqueProducts=("StockCode", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        InvoiceValue=("LineValue", "sum")
    )
)

print("\n1. INVOICE OVERVIEW")
print("-" * 70)

print(f"Unique invoices: {df['Invoice'].nunique():,}")
print(f"Average lines per invoice: {invoice_summary['TotalLines'].mean():.2f}")
print(f"Maximum lines in one invoice: {invoice_summary['TotalLines'].max():,}")


# 2. INVOICES WITH REPEATED PRODUCT LINES
line_frequency = (
    df.groupby(comparison_columns, dropna=False)
    .size()
    .reset_index(name="Occurrences")
)

repeated_lines = line_frequency[
    line_frequency["Occurrences"] > 1
].copy()

repeated_invoice_counts = (
    repeated_lines.groupby("Invoice")
    .agg(
        RepeatedProductLines=("Occurrences", "size"),
        RepeatedOccurrences=("Occurrences", lambda x: (x - 1).sum())
    )
    .sort_values("RepeatedOccurrences", ascending=False)
)

print("\n2. INVOICES WITH REPEATED PRODUCT LINES")
print("-" * 70)

print(f"Invoices containing repeated lines: {len(repeated_invoice_counts):,}")
print("\nTop 15 affected invoices:")
print(repeated_invoice_counts.head(15).to_string())


# 3. SELECTED INVOICE INSPECTION
selected_invoices = [
    "555524",
    "530437",
    "547651",
    "525075"
]

print("\n3. SELECTED INVOICE INSPECTION")
print("-" * 70)

for invoice in selected_invoices:

    invoice_data = df[
        df["Invoice"].astype(str) == invoice
    ]

    if invoice_data.empty:
        continue

    print(f"\nInvoice: {invoice}")
    print(f"Total records: {len(invoice_data)}")
    print(f"Unique products: {invoice_data['StockCode'].nunique()}")

    product_lines = (
        invoice_data.groupby(
            ["StockCode", "Description", "Quantity", "Price"],
            dropna=False
        )
        .size()
        .reset_index(name="Occurrences")
        .sort_values("Occurrences", ascending=False)
    )

    print(product_lines.head(15).to_string(index=False))


# 4. DUPLICATION BY SOURCE SHEET
print("\n4. DUPLICATION BY SOURCE SHEET")
print("-" * 70)

source_analysis = (
    df.groupby("SourceSheet")
    .agg(
        TotalRecords=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique")
    )
)

print(source_analysis.to_string())


# 5. DUPLICATION BY CUSTOMER
print("\n5. DUPLICATION BY CUSTOMER")
print("-" * 70)

identified_customers = df[
    df["Customer ID"].notna()
].copy()

identified_customers["IsRepeated"] = (
    identified_customers.duplicated(
        subset=comparison_columns,
        keep="first"
    )
)

customer_duplicates = (
    identified_customers.groupby("Customer ID")["IsRepeated"]
    .sum()
    .sort_values(ascending=False)
)

print("Top 15 customers by repeated transaction occurrences:")
print(customer_duplicates.head(15).to_string())


# 6. SAVE RESULTS
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

invoice_summary.to_csv(
    OUTPUT_DIR / "invoice_summary.csv"
)

repeated_invoice_counts.to_csv(
    OUTPUT_DIR / "repeated_invoice_analysis.csv"
)

repeated_lines.to_csv(
    OUTPUT_DIR / "repeated_transaction_lines.csv",
    index=False
)

customer_duplicates.to_csv(
    OUTPUT_DIR / "customer_duplicate_analysis.csv"
)


# FINAL OUTPUT
print("\n6. OUTPUT FILES")
print("-" * 70)

print("invoice_summary.csv")
print("repeated_invoice_analysis.csv")
print("repeated_transaction_lines.csv")
print("customer_duplicate_analysis.csv")

print("\n" + "=" * 70)
print("INVOICE STRUCTURE ANALYSIS COMPLETED")
print("=" * 70)

