
import pandas as pd
from pathlib import Path

# ============================================================
# COMMON GROUND | POSTAGE TRANSACTION ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "classified_transactions.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("COMMON GROUND | POSTAGE TRANSACTION ANALYSIS")
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

postage = df.loc[
    df["StockCodeNormalized"].isin(["POST", "DOT"])
].copy()

postage["PostageType"] = postage["StockCodeNormalized"].map({
    "POST": "Postage",
    "DOT": "Dotcom Postage"
})

postage["InvoicePrefix"] = postage["Invoice"].str[0]

print(f"Total transaction records: {len(df):,}")
print(f"Postage records: {len(postage):,}")
print(f"Unique postage invoices: {postage['Invoice'].nunique():,}")

# ------------------------------------------------------------
# 2. POSTAGE OVERVIEW
# ------------------------------------------------------------

print("\n2. POSTAGE OVERVIEW")
print("-" * 70)

overview = {
    "Records": len(postage),
    "UniqueInvoices": postage["Invoice"].nunique(),
    "UniqueCustomers": postage["Customer ID"].nunique(),
    "MissingCustomerIDs": postage["Customer ID"].isna().sum(),
    "TotalQuantity": postage["Quantity"].sum(),
    "TotalLineValue": postage["LineValue"].sum(),
    "PositiveLineValues": (postage["LineValue"] > 0).sum(),
    "NegativeLineValues": (postage["LineValue"] < 0).sum(),
    "ZeroLineValues": (postage["LineValue"] == 0).sum(),
    "PositiveQuantities": (postage["Quantity"] > 0).sum(),
    "NegativeQuantities": (postage["Quantity"] < 0).sum(),
    "ZeroQuantities": (postage["Quantity"] == 0).sum()
}

for metric, value in overview.items():
    print(f"{metric}: {value:,.2f}")

# ------------------------------------------------------------
# 3. POSTAGE TYPE COMPARISON
# ------------------------------------------------------------

print("\n3. POSTAGE TYPE COMPARISON")
print("-" * 70)

type_summary = (
    postage.groupby("PostageType")
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
)

print(type_summary.to_string())

# ------------------------------------------------------------
# 4. TRANSACTION CATEGORY ANALYSIS
# ------------------------------------------------------------

print("\n4. TRANSACTION CATEGORY ANALYSIS")
print("-" * 70)

category_summary = (
    postage.groupby(["StockCodeNormalized", "TransactionCategory"])
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
    postage.groupby(["StockCodeNormalized", "InvoicePrefix"])
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
    postage.groupby(["StockCodeNormalized", "Description"], dropna=False)
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
    postage.groupby(["StockCodeNormalized", "Country"], dropna=False)
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
# 8. POSTAGE INVOICE ANALYSIS
# ------------------------------------------------------------

print("\n8. POSTAGE INVOICE ANALYSIS")
print("-" * 70)

invoice_summary = (
    postage.groupby("Invoice", dropna=False)
    .agg(
        PostageRecords=("StockCode", "size"),
        PostageQuantity=("Quantity", "sum"),
        PostageLineValue=("LineValue", "sum"),
        PostageAveragePrice=("Price", "mean"),
        PostageTypes=("PostageType", "nunique"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
    .sort_values("PostageLineValue", ascending=False)
)

print("\nHighest postage invoice values:")
print(invoice_summary.head(15).to_string())

print("\nLowest postage invoice values:")
print(invoice_summary.tail(15).to_string())

# ------------------------------------------------------------
# 9. INVOICE CONTEXT ANALYSIS
# ------------------------------------------------------------

print("\n9. INVOICE CONTEXT ANALYSIS")
print("-" * 70)

postage_invoice_ids = postage["Invoice"].dropna().unique()

invoice_context = df.loc[
    df["Invoice"].isin(postage_invoice_ids)
].copy()

invoice_context["IsPostage"] = (
    invoice_context["StockCodeNormalized"].isin(["POST", "DOT"])
)

invoice_context["PostageLineValue"] = invoice_context[
    "LineValue"
].where(invoice_context["IsPostage"], 0)

invoice_context["OtherLineValue"] = invoice_context[
    "LineValue"
].where(~invoice_context["IsPostage"], 0)

invoice_context["PostageRecord"] = (
    invoice_context["IsPostage"].astype(int)
)

invoice_context["OtherRecord"] = (
    (~invoice_context["IsPostage"]).astype(int)
)

context_summary = (
    invoice_context.groupby("Invoice", dropna=False)
    .agg(
        TotalInvoiceRecords=("StockCode", "size"),
        PostageRecords=("PostageRecord", "sum"),
        OtherRecords=("OtherRecord", "sum"),
        PostageValue=("PostageLineValue", "sum"),
        OtherItemValue=("OtherLineValue", "sum"),
        TotalInvoiceValue=("LineValue", "sum"),
        CustomerID=("Customer ID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min")
    )
)

context_summary["InvoiceType"] = "Postage Only"

context_summary.loc[
    context_summary["OtherRecords"] > 0,
    "InvoiceType"
] = "Postage and Other Items"

print("\nInvoice composition:")
print(context_summary["InvoiceType"].value_counts().to_string())

print("\nInvoices containing postage and other items:")
print(
    context_summary[
        context_summary["InvoiceType"] == "Postage and Other Items"
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

postage.to_csv(
    OUTPUT_DIR / "postage_transaction_records.csv",
    index=False
)

type_summary.to_csv(
    OUTPUT_DIR / "postage_type_summary.csv"
)

category_summary.to_csv(
    OUTPUT_DIR / "postage_category_summary.csv"
)

prefix_summary.to_csv(
    OUTPUT_DIR / "postage_prefix_summary.csv"
)

description_summary.to_csv(
    OUTPUT_DIR / "postage_description_summary.csv"
)

country_summary.to_csv(
    OUTPUT_DIR / "postage_country_summary.csv"
)

invoice_summary.to_csv(
    OUTPUT_DIR / "postage_invoice_summary.csv"
)

context_summary.to_csv(
    OUTPUT_DIR / "postage_invoice_context.csv"
)

print("Saved postage_transaction_records.csv")
print("Saved postage_type_summary.csv")
print("Saved postage_category_summary.csv")
print("Saved postage_prefix_summary.csv")
print("Saved postage_description_summary.csv")
print("Saved postage_country_summary.csv")
print("Saved postage_invoice_summary.csv")
print("Saved postage_invoice_context.csv")

print("\n" + "=" * 70)
print("POSTAGE TRANSACTION ANALYSIS COMPLETED")
print("=" * 70)
