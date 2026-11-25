
import pandas as pd
from pathlib import Path

# ============================================================
# COMMON GROUND | MANUAL TRANSACTION ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "classified_transactions.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("COMMON GROUND | MANUAL TRANSACTION ANALYSIS")
print("=" * 70)

# ------------------------------------------------------------
# 1. LOAD THE REQUIRED DATA
# ------------------------------------------------------------

print("\n1. LOADING TRANSACTION DATA")
print("-" * 70)

required_columns = {
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
    "TransactionCategory"
}

df = pd.read_csv(
    INPUT_FILE,
    usecols=lambda column: column in required_columns,
    low_memory=False
)

missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

df["Invoice"] = df["Invoice"].astype("string").str.strip()
df["StockCode"] = df["StockCode"].astype("string").str.strip()
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
)

df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

df["LineValue"] = df["Quantity"] * df["Price"]

df["IsManual"] = (
    df["StockCode"].str.upper() == "M"
).fillna(False)

manual = df.loc[df["IsManual"]].copy()

print(f"Total transaction records: {len(df):,}")
print(f"Manual transaction records: {len(manual):,}")
print(
    f"Unique invoices containing manual entries: "
    f"{manual['Invoice'].nunique():,}"
)

# ------------------------------------------------------------
# 2. MANUAL TRANSACTION OVERVIEW
# ------------------------------------------------------------

print("\n2. MANUAL TRANSACTION OVERVIEW")
print("-" * 70)

overview = {
    "Records": len(manual),
    "UniqueInvoices": manual["Invoice"].nunique(),
    "UniqueCustomers": manual["Customer ID"].nunique(),
    "MissingCustomerIDs": manual["Customer ID"].isna().sum(),
    "TotalQuantity": manual["Quantity"].sum(),
    "TotalLineValue": manual["LineValue"].sum(),
    "PositiveLineValues": (manual["LineValue"] > 0).sum(),
    "NegativeLineValues": (manual["LineValue"] < 0).sum(),
    "ZeroLineValues": (manual["LineValue"] == 0).sum(),
    "PositivePrices": (manual["Price"] > 0).sum(),
    "NegativePrices": (manual["Price"] < 0).sum(),
    "ZeroPrices": (manual["Price"] == 0).sum()
}

for metric, value in overview.items():
    print(f"{metric}: {value:,.2f}" if isinstance(
        value, (int, float)
    ) else f"{metric}: {value}")

# ------------------------------------------------------------
# 3. TRANSACTION CATEGORY ANALYSIS
# ------------------------------------------------------------

print("\n3. TRANSACTION CATEGORY ANALYSIS")
print("-" * 70)

category_summary = (
    manual.groupby("TransactionCategory", dropna=False)
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean")
    )
    .sort_values("RecordCount", ascending=False)
)

category_summary["Percentage"] = (
    category_summary["RecordCount"] / len(manual) * 100
)

print(category_summary.to_string())

# ------------------------------------------------------------
# 4. INVOICE PREFIX ANALYSIS
# ------------------------------------------------------------

print("\n4. INVOICE PREFIX ANALYSIS")
print("-" * 70)

manual["InvoicePrefix"] = manual["Invoice"].str[0]

prefix_summary = (
    manual.groupby("InvoicePrefix", dropna=False)
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        UniqueCustomers=("Customer ID", "nunique")
    )
    .sort_values("RecordCount", ascending=False)
)

print(prefix_summary.to_string())

# ------------------------------------------------------------
# 5. DESCRIPTION ANALYSIS
# ------------------------------------------------------------

print("\n5. MANUAL DESCRIPTION ANALYSIS")
print("-" * 70)

manual["Description"] = (
    manual["Description"].fillna("Missing Description")
)

description_summary = (
    manual.groupby("Description")
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean")
    )
    .sort_values("RecordCount", ascending=False)
)

print(description_summary.head(20).to_string())

# ------------------------------------------------------------
# 6. MANUAL INVOICE ANALYSIS
# ------------------------------------------------------------

print("\n6. MANUAL INVOICE ANALYSIS")
print("-" * 70)

manual_invoice_summary = (
    manual.groupby("Invoice", dropna=False)
    .agg(
        ManualRecordCount=("StockCode", "size"),
        ManualQuantity=("Quantity", "sum"),
        ManualLineValue=("LineValue", "sum"),
        ManualAveragePrice=("Price", "mean"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
    .sort_values("ManualRecordCount", ascending=False)
)

print("\nInvoices with the most manual entries:")
print(manual_invoice_summary.head(15).to_string())

# ------------------------------------------------------------
# 7. INVOICE CONTEXT ANALYSIS
# ------------------------------------------------------------

print("\n7. INVOICE CONTEXT ANALYSIS")
print("-" * 70)

manual_invoice_ids = manual["Invoice"].dropna().unique()

invoice_context = df.loc[
    df["Invoice"].isin(manual_invoice_ids)
].copy()

invoice_context["ManualLineValue"] = invoice_context[
    "LineValue"
].where(invoice_context["IsManual"], 0)

invoice_context["NonManualLineValue"] = invoice_context[
    "LineValue"
].where(~invoice_context["IsManual"], 0)

invoice_context["ManualRecord"] = invoice_context[
    "IsManual"
].astype(int)

invoice_context["NonManualRecord"] = (
    ~invoice_context["IsManual"]
).astype(int)

context_summary = (
    invoice_context.groupby("Invoice", dropna=False)
    .agg(
        TotalInvoiceRecords=("StockCode", "size"),
        ManualRecords=("ManualRecord", "sum"),
        NonManualRecords=("NonManualRecord", "sum"),
        ManualLineValue=("ManualLineValue", "sum"),
        NonManualLineValue=("NonManualLineValue", "sum"),
        TotalInvoiceLineValue=("LineValue", "sum"),
        UniqueStockCodes=("StockCode", "nunique"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
)

context_summary["InvoiceType"] = "Manual Only"

context_summary.loc[
    context_summary["NonManualRecords"] > 0,
    "InvoiceType"
] = "Manual and Other Items"

print("\nInvoice composition:")
print(context_summary["InvoiceType"].value_counts().to_string())

print("\nInvoices containing manual entries and other items:")
print(
    context_summary[
        context_summary["InvoiceType"] == "Manual and Other Items"
    ]
    .sort_values("TotalInvoiceRecords", ascending=False)
    .head(15)
    .to_string()
)

# ------------------------------------------------------------
# 8. SAVE ANALYSIS OUTPUTS
# ------------------------------------------------------------

print("\n8. SAVING ANALYSIS OUTPUTS")
print("-" * 70)

manual.to_csv(
    OUTPUT_DIR / "manual_transaction_records.csv",
    index=False
)

category_summary.to_csv(
    OUTPUT_DIR / "manual_transaction_category_summary.csv"
)

manual_invoice_summary.to_csv(
    OUTPUT_DIR / "manual_transaction_invoice_summary.csv"
)

description_summary.to_csv(
    OUTPUT_DIR / "manual_transaction_description_summary.csv"
)

context_summary.to_csv(
    OUTPUT_DIR / "manual_transaction_invoice_context.csv"
)

print("Saved manual_transaction_records.csv")
print("Saved manual_transaction_category_summary.csv")
print("Saved manual_transaction_invoice_summary.csv")
print("Saved manual_transaction_description_summary.csv")
print("Saved manual_transaction_invoice_context.csv")

print("\n" + "=" * 70)
print("MANUAL TRANSACTION ANALYSIS COMPLETED")
print("=" * 70)
