
import pandas as pd
from pathlib import Path

# ============================================================
# COMMON GROUND | ACCOUNTING & FEE ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "classified_transactions.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("COMMON GROUND | ACCOUNTING & FEE ANALYSIS")
print("=" * 70)

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

print("\n1. LOADING TRANSACTION DATA")
print("-" * 70)

required_columns = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
    "TransactionCategory"
]

df = pd.read_csv(
    INPUT_FILE,
    usecols=lambda column: column in required_columns,
    low_memory=False
)

missing_columns = set(required_columns).difference(df.columns)

if missing_columns:
    raise ValueError(f"Missing columns: {sorted(missing_columns)}")

df["Invoice"] = df["Invoice"].astype("string").str.strip()
df["StockCode"] = df["StockCode"].astype("string").str.strip()
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
)
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df["LineValue"] = df["Quantity"] * df["Price"]

df["StockCodeNormalized"] = df["StockCode"].str.upper()
df["InvoicePrefix"] = df["Invoice"].str[0]

target_codes = ["ADJUST", "BANK CHARGES", "AMAZONFEE"]

exceptions = df.loc[
    df["StockCodeNormalized"].isin(target_codes)
].copy()

print(f"Total transaction records: {len(df):,}")
print(f"Accounting and fee records: {len(exceptions):,}")
print(f"Unique invoices: {exceptions['Invoice'].nunique():,}")

# ------------------------------------------------------------
# 2. OVERVIEW
# ------------------------------------------------------------

print("\n2. ACCOUNTING & FEE OVERVIEW")
print("-" * 70)

overview = {
    "Records": len(exceptions),
    "UniqueInvoices": exceptions["Invoice"].nunique(),
    "UniqueCustomers": exceptions["Customer ID"].nunique(),
    "MissingCustomerIDs": exceptions["Customer ID"].isna().sum(),
    "TotalQuantity": exceptions["Quantity"].sum(),
    "TotalLineValue": exceptions["LineValue"].sum(),
    "PositiveLineValues": (exceptions["LineValue"] > 0).sum(),
    "NegativeLineValues": (exceptions["LineValue"] < 0).sum(),
    "ZeroLineValues": (exceptions["LineValue"] == 0).sum(),
    "PositiveQuantities": (exceptions["Quantity"] > 0).sum(),
    "NegativeQuantities": (exceptions["Quantity"] < 0).sum(),
    "ZeroQuantities": (exceptions["Quantity"] == 0).sum(),
    "PositivePrices": (exceptions["Price"] > 0).sum(),
    "NegativePrices": (exceptions["Price"] < 0).sum(),
    "ZeroPrices": (exceptions["Price"] == 0).sum()
}

for metric, value in overview.items():
    print(f"{metric}: {value:,.2f}")

# ------------------------------------------------------------
# 3. STOCK CODE ANALYSIS
# ------------------------------------------------------------

print("\n3. STOCK CODE ANALYSIS")
print("-" * 70)

stock_summary = (
    exceptions.groupby("StockCodeNormalized")
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        UniqueCustomers=("Customer ID", "nunique"),
        MissingCustomerIDs=("Customer ID", lambda x: x.isna().sum()),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean"),
        PositiveValues=("LineValue", lambda x: (x > 0).sum()),
        NegativeValues=("LineValue", lambda x: (x < 0).sum()),
        ZeroValues=("LineValue", lambda x: (x == 0).sum())
    )
    .sort_values("RecordCount", ascending=False)
)

print(stock_summary.to_string())

# ------------------------------------------------------------
# 4. TRANSACTION CATEGORY ANALYSIS
# ------------------------------------------------------------

print("\n4. TRANSACTION CATEGORY ANALYSIS")
print("-" * 70)

category_summary = (
    exceptions.groupby(
        ["StockCodeNormalized", "TransactionCategory"]
    )
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum")
    )
    .sort_values("RecordCount", ascending=False)
)

print(category_summary.to_string())

# ------------------------------------------------------------
# 5. INVOICE PREFIX ANALYSIS
# ------------------------------------------------------------

print("\n5. INVOICE PREFIX ANALYSIS")
print("-" * 70)

prefix_summary = (
    exceptions.groupby(
        ["StockCodeNormalized", "InvoicePrefix"]
    )
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
# 6. DESCRIPTION ANALYSIS
# ------------------------------------------------------------

print("\n6. DESCRIPTION ANALYSIS")
print("-" * 70)

description_summary = (
    exceptions.groupby(
        ["StockCodeNormalized", "Description"],
        dropna=False
    )
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean")
    )
    .sort_values("RecordCount", ascending=False)
)

print(description_summary.to_string())

# ------------------------------------------------------------
# 7. COUNTRY ANALYSIS
# ------------------------------------------------------------

print("\n7. COUNTRY ANALYSIS")
print("-" * 70)

country_summary = (
    exceptions.groupby(
        ["StockCodeNormalized", "Country"],
        dropna=False
    )
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueInvoices=("Invoice", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        UniqueCustomers=("Customer ID", "nunique")
    )
    .sort_values("RecordCount", ascending=False)
)

print(country_summary.head(30).to_string())

# ------------------------------------------------------------
# 8. INVOICE ANALYSIS
# ------------------------------------------------------------

print("\n8. INVOICE ANALYSIS")
print("-" * 70)

invoice_summary = (
    exceptions.groupby("Invoice", dropna=False)
    .agg(
        ExceptionRecords=("StockCode", "size"),
        ExceptionQuantity=("Quantity", "sum"),
        ExceptionLineValue=("LineValue", "sum"),
        UniqueExceptionCodes=("StockCodeNormalized", "nunique"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
    .sort_values("ExceptionLineValue", ascending=False)
)

print("\nHighest exception invoice values:")
print(invoice_summary.head(15).to_string())

print("\nLowest exception invoice values:")
print(invoice_summary.tail(15).to_string())

# ------------------------------------------------------------
# 9. INVOICE CONTEXT ANALYSIS
# ------------------------------------------------------------

print("\n9. INVOICE CONTEXT ANALYSIS")
print("-" * 70)

exception_invoice_ids = exceptions["Invoice"].dropna().unique()

invoice_context = df.loc[
    df["Invoice"].isin(exception_invoice_ids)
].copy()

invoice_context["IsAccountingFeeRecord"] = (
    invoice_context["StockCodeNormalized"].isin(target_codes)
)

invoice_context["ExceptionLineValue"] = invoice_context[
    "LineValue"
].where(invoice_context["IsAccountingFeeRecord"], 0)

invoice_context["OtherLineValue"] = invoice_context[
    "LineValue"
].where(~invoice_context["IsAccountingFeeRecord"], 0)

invoice_context["ExceptionRecord"] = (
    invoice_context["IsAccountingFeeRecord"].astype(int)
)

invoice_context["OtherRecord"] = (
    (~invoice_context["IsAccountingFeeRecord"]).astype(int)
)

context_summary = (
    invoice_context.groupby("Invoice", dropna=False)
    .agg(
        TotalInvoiceRecords=("StockCode", "size"),
        ExceptionRecords=("ExceptionRecord", "sum"),
        OtherRecords=("OtherRecord", "sum"),
        ExceptionValue=("ExceptionLineValue", "sum"),
        OtherItemValue=("OtherLineValue", "sum"),
        TotalInvoiceValue=("LineValue", "sum"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
)

context_summary["InvoiceType"] = "Exception Only"

context_summary.loc[
    context_summary["OtherRecords"] > 0,
    "InvoiceType"
] = "Exception and Other Items"

print("\nInvoice composition:")
print(context_summary["InvoiceType"].value_counts().to_string())

print("\nInvoices containing exceptions and other items:")
print(
    context_summary[
        context_summary["InvoiceType"] == "Exception and Other Items"
    ]
    .sort_values("TotalInvoiceRecords", ascending=False)
    .head(15)
    .to_string()
)

# ------------------------------------------------------------
# 10. SAVE OUTPUTS
# ------------------------------------------------------------

print("\n10. SAVING ANALYSIS OUTPUTS")
print("-" * 70)

exceptions.to_csv(
    OUTPUT_DIR / "accounting_fee_records.csv",
    index=False
)

stock_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_stock_summary.csv"
)

category_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_category_summary.csv"
)

prefix_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_prefix_summary.csv"
)

description_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_description_summary.csv"
)

country_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_country_summary.csv"
)

invoice_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_invoice_summary.csv"
)

context_summary.to_csv(
    OUTPUT_DIR / "accounting_fee_invoice_context.csv"
)

print("Saved accounting_fee_records.csv")
print("Saved accounting_fee_stock_summary.csv")
print("Saved accounting_fee_category_summary.csv")
print("Saved accounting_fee_prefix_summary.csv")
print("Saved accounting_fee_description_summary.csv")
print("Saved accounting_fee_country_summary.csv")
print("Saved accounting_fee_invoice_summary.csv")
print("Saved accounting_fee_invoice_context.csv")

print("\n" + "=" * 70)
print("ACCOUNTING & FEE ANALYSIS COMPLETED")
print("=" * 70)
