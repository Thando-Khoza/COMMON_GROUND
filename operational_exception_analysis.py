
import pandas as pd
from pathlib import Path


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "classified_transactions.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"


# LOAD DATA
df = pd.read_csv(DATA_PATH)

df["Description"] = df["Description"].fillna("").str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()

print("=" * 70)
print("COMMON GROUND | OPERATIONAL EXCEPTION ANALYSIS")
print("=" * 70)


# 1. EXCEPTION OVERVIEW

print("\n1. OPERATIONAL EXCEPTION OVERVIEW")
print("-" * 70)

operational = df[df["IsOperationalNonMerchandise"] == True].copy()

print(f"Total flagged records: {len(operational):,}")

print(
    f"Percentage of dataset: "
    f"{len(operational) / len(df) * 100:.2f}%"
)


# 2. PRIMARY CATEGORY DISTRIBUTION

print("\n2. PRIMARY CATEGORY DISTRIBUTION")
print("-" * 70)

category_summary = (
    operational["TransactionCategory"]
    .value_counts()
    .rename_axis("TransactionCategory")
    .reset_index(name="RecordCount")
)

category_summary["Percentage"] = (
    category_summary["RecordCount"]
    / len(operational)
    * 100
)

print(category_summary.round(2).to_string(index=False))


# 3. STOCK CODE ANALYSIS

print("\n3. STOCK CODE ANALYSIS")
print("-" * 70)

stock_summary = (
    operational.groupby("StockCode")
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueDescriptions=("Description", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum")
    )
    .sort_values("RecordCount", ascending=False)
)

print(stock_summary.head(20).round(2).to_string())


# 4. DESCRIPTION ANALYSIS

print("\n4. DESCRIPTION ANALYSIS")
print("-" * 70)

description_summary = (
    operational["Description"]
    .replace("", "Missing Description")
    .value_counts()
    .head(30)
)

print(description_summary.to_string())


# 5. OPERATIONAL KEYWORD ANALYSIS

print("\n5. OPERATIONAL KEYWORD ANALYSIS")
print("-" * 70)

keywords = [
    "ADJUSTMENT",
    "DAMAGED",
    "DAMAGE",
    "MISSING",
    "SMASHED",
    "THROWN AWAY",
    "UNSALEABLE",
    "CHECK"
]

keyword_results = []

for keyword in keywords:

    matches = operational[
        operational["Description"].str.contains(
            keyword,
            case=False,
            regex=False,
            na=False
        )
    ]

    keyword_results.append({
        "Keyword": keyword,
        "RecordCount": len(matches),
        "UniqueStockCodes": matches["StockCode"].nunique(),
        "TotalLineValue": matches["LineValue"].sum()
    })

keyword_summary = pd.DataFrame(keyword_results)

print(keyword_summary.round(2).to_string(index=False))


# 6. CUSTOMER IDENTIFICATION

print("\n6. CUSTOMER IDENTIFICATION")
print("-" * 70)

print(
    f"Identified customer records: "
    f"{operational['Customer ID'].notna().sum():,}"
)

print(
    f"Missing customer records: "
    f"{operational['Customer ID'].isna().sum():,}"
)

print(
    f"Unique identified customers: "
    f"{operational['Customer ID'].nunique():,}"
)


# 7. TRANSACTION VALUE ANALYSIS

print("\n7. TRANSACTION VALUE ANALYSIS")
print("-" * 70)

print(
    f"Total quantity: "
    f"{operational['Quantity'].sum():,}"
)

print(
    f"Total line value: "
    f"{operational['LineValue'].sum():,.2f}"
)

print(
    f"Positive line values: "
    f"{(operational['LineValue'] > 0).sum():,}"
)

print(
    f"Negative line values: "
    f"{(operational['LineValue'] < 0).sum():,}"
)

print(
    f"Zero line values: "
    f"{(operational['LineValue'] == 0).sum():,}"
)


# 8. REVIEW RECORDS

print("\n8. RECORDS REQUIRING REVIEW")
print("-" * 70)

review_records = operational[
    [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "Price",
        "LineValue",
        "TransactionCategory",
        "Customer ID",
        "InvoiceDate",
        "Country"
    ]
].copy()

print(
    review_records.head(25).to_string(index=False)
)


# 9. SAVE INVESTIGATION OUTPUTS

print("\n9. SAVING INVESTIGATION OUTPUTS")
print("-" * 70)

review_records.to_csv(
    OUTPUT_DIR / "operational_exception_records.csv",
    index=False
)

category_summary.to_csv(
    OUTPUT_DIR / "operational_category_summary.csv",
    index=False
)

stock_summary.to_csv(
    OUTPUT_DIR / "operational_stock_summary.csv"
)

keyword_summary.to_csv(
    OUTPUT_DIR / "operational_keyword_summary.csv",
    index=False
)

print("operational_exception_records.csv")
print("operational_category_summary.csv")
print("operational_stock_summary.csv")
print("operational_keyword_summary.csv")


print("\n" + "=" * 70)
print("OPERATIONAL EXCEPTION ANALYSIS COMPLETED")
print("=" * 70)
