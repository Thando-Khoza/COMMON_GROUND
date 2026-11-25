
import pandas as pd
from pathlib import Path


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "operational_exception_records.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"


# LOAD DATA
df = pd.read_csv(DATA_PATH)

df["StockCode"] = (
    df["StockCode"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["Description"] = (
    df["Description"]
    .fillna("")
    .str.strip()
)


print("=" * 70)
print("COMMON GROUND | STOCK CODE EXCEPTION ANALYSIS")
print("=" * 70)


# 1. STOCK CODE OVERVIEW

print("\n1. STOCK CODE OVERVIEW")
print("-" * 70)

print(f"Flagged records: {len(df):,}")
print(f"Unique stock codes: {df['StockCode'].nunique():,}")
print(f"Unique descriptions: {df['Description'].nunique():,}")


# 2. STOCK CODE SUMMARY

print("\n2. STOCK CODE SUMMARY")
print("-" * 70)

stock_summary = (
    df.groupby("StockCode")
    .agg(
        RecordCount=("Invoice", "size"),
        UniqueDescriptions=("Description", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean"),
        PrimaryCategories=("TransactionCategory", "nunique")
    )
    .sort_values("RecordCount", ascending=False)
)

print(stock_summary.head(30).round(2).to_string())


# 3. STOCK CODES WITH MULTIPLE DESCRIPTIONS

print("\n3. STOCK CODES WITH MULTIPLE DESCRIPTIONS")
print("-" * 70)

multiple_descriptions = stock_summary[
    stock_summary["UniqueDescriptions"] > 1
]

print(
    f"Stock codes with multiple descriptions: "
    f"{len(multiple_descriptions):,}"
)

print(
    multiple_descriptions.head(30)
    .round(2)
    .to_string()
)


# 4. DESCRIPTION VARIATIONS

print("\n4. DESCRIPTION VARIATIONS")
print("-" * 70)

description_variations = (
    df.groupby(["StockCode", "Description"])
    .agg(
        RecordCount=("Invoice", "size"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum")
    )
    .reset_index()
    .sort_values(
        ["StockCode", "RecordCount"],
        ascending=[True, False]
    )
)

print(
    description_variations.head(50)
    .round(2)
    .to_string(index=False)
)


# 5. IMPORTANT STOCK CODE INVESTIGATION

print("\n5. IMPORTANT STOCK CODE INVESTIGATION")
print("-" * 70)

important_codes = [
    "POST",
    "DOT",
    "M",
    "BANK CHARGES",
    "AMAZONFEE",
    "ADJUST"
]

important_records = df[
    df["StockCode"].isin(important_codes)
].copy()

important_summary = (
    important_records.groupby("StockCode")
    .agg(
        RecordCount=("Invoice", "size"),
        Descriptions=("Description", "nunique"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum"),
        AveragePrice=("Price", "mean")
    )
    .sort_values("RecordCount", ascending=False)
)

print(important_summary.round(2).to_string())


# 6. TRANSACTION CATEGORY BY STOCK CODE

print("\n6. TRANSACTION CATEGORY BY STOCK CODE")
print("-" * 70)

category_by_stock = pd.crosstab(
    important_records["StockCode"],
    important_records["TransactionCategory"]
)

print(category_by_stock.to_string())


# 7. STOCK CODE VALUE DISTRIBUTION

print("\n7. STOCK CODE VALUE DISTRIBUTION")
print("-" * 70)

value_summary = (
    df.groupby("StockCode")
    .agg(
        PositiveValueRecords=(
            "LineValue",
            lambda x: (x > 0).sum()
        ),
        NegativeValueRecords=(
            "LineValue",
            lambda x: (x < 0).sum()
        ),
        ZeroValueRecords=(
            "LineValue",
            lambda x: (x == 0).sum()
        )
    )
    .sort_values(
        "PositiveValueRecords",
        ascending=False
    )
)

print(value_summary.head(30).to_string())


# 8. REVIEW RECORDS FOR IMPORTANT CODES

print("\n8. IMPORTANT CODE RECORD SAMPLES")
print("-" * 70)

sample_records = important_records[
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
]

print(
    sample_records.head(40)
    .to_string(index=False)
)


# 9. SAVE OUTPUTS

print("\n9. SAVING INVESTIGATION OUTPUTS")
print("-" * 70)

stock_summary.to_csv(
    OUTPUT_DIR / "exception_stock_code_summary.csv"
)

description_variations.to_csv(
    OUTPUT_DIR / "exception_description_variations.csv",
    index=False
)

important_summary.to_csv(
    OUTPUT_DIR / "important_stock_code_summary.csv"
)

category_by_stock.to_csv(
    OUTPUT_DIR / "important_stock_category_summary.csv"
)

value_summary.to_csv(
    OUTPUT_DIR / "exception_stock_value_summary.csv"
)

print("exception_stock_code_summary.csv")
print("exception_description_variations.csv")
print("important_stock_code_summary.csv")
print("important_stock_category_summary.csv")
print("exception_stock_value_summary.csv")


print("\n" + "=" * 70)
print("STOCK CODE EXCEPTION ANALYSIS COMPLETED")
print("=" * 70)
