
import pandas as pd
from pathlib import Path


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "online_retail_cleaned.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# LOAD DATA
df = pd.read_csv(DATA_PATH)

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["Invoice"] = df["Invoice"].astype(str).str.strip()
df["Description"] = df["Description"].fillna("").str.strip()

df["LineValue"] = df["Quantity"] * df["Price"]

print("=" * 70)
print("COMMON GROUND | CORRECTED TRANSACTION CLASSIFICATION")
print("=" * 70)


# 1. INDEPENDENT EXCEPTION FLAGS

print("\n1. CREATING TRANSACTION FLAGS")
print("-" * 70)

invoice = df["Invoice"]
stock_code = df["StockCode"].astype(str).str.strip().str.upper()
description = df["Description"].str.upper()

df["IsAccountingAdjustment"] = invoice.str.startswith("A")
df["IsCancellation"] = invoice.str.startswith("C")

df["IsNegativeQuantity"] = df["Quantity"] < 0
df["IsNegativePrice"] = df["Price"] < 0
df["IsZeroPrice"] = df["Price"] == 0

operational_codes = [
    "POST",
    "DOT",
    "M",
    "AMAZONFEE",
    "BANK CHARGES"
]

operational_keywords = [
    "ADJUSTMENT",
    "DAMAGED",
    "DAMAGE",
    "MISSING",
    "SMASHED",
    "THROWN AWAY",
    "UNSALEABLE",
    "CHECK"
]

is_operational_code = stock_code.isin(operational_codes)

is_operational_description = pd.Series(
    False,
    index=df.index
)

for keyword in operational_keywords:
    is_operational_description |= description.str.contains(
        keyword,
        regex=False,
        na=False
    )

df["IsOperationalNonMerchandise"] = (
    is_operational_code | is_operational_description
)


# 2. PRIMARY TRANSACTION CLASSIFICATION

print("\n2. CLASSIFYING TRANSACTIONS")
print("-" * 70)

df["TransactionCategory"] = "Unclassified"

# Priority:
# 1. Accounting adjustments
# 2. Operational / non-merchandise
# 3. Cancellations
# 4. Negative quantities
# 5. Negative prices
# 6. Zero prices
# 7. Standard positive transactions

remaining = df["TransactionCategory"] == "Unclassified"

conditions = [
    (
        df["IsAccountingAdjustment"],
        "Accounting Adjustment"
    ),
    (
        df["IsOperationalNonMerchandise"],
        "Operational / Non-Merchandise"
    ),
    (
        df["IsCancellation"],
        "Cancellation"
    ),
    (
        df["IsNegativeQuantity"],
        "Negative Quantity Exception"
    ),
    (
        df["IsNegativePrice"],
        "Negative Price Exception"
    ),
    (
        df["IsZeroPrice"],
        "Zero Price Record"
    ),
    (
        (df["Quantity"] > 0) & (df["Price"] > 0),
        "Standard Positive Transaction"
    )
]

for condition, category in conditions:
    assign_mask = remaining & condition
    df.loc[assign_mask, "TransactionCategory"] = category
    remaining = df["TransactionCategory"] == "Unclassified"


# 3. TRANSACTION CATEGORY OVERVIEW

print("\n3. TRANSACTION CATEGORY OVERVIEW")
print("-" * 70)

category_summary = (
    df.groupby("TransactionCategory")
    .agg(
        RecordCount=("Invoice", "size"),
        TotalQuantity=("Quantity", "sum"),
        TotalLineValue=("LineValue", "sum")
    )
    .sort_values("RecordCount", ascending=False)
)

category_summary["Percentage"] = (
    category_summary["RecordCount"] / len(df) * 100
)

print(category_summary.round(2).to_string())


# 4. CATEGORY BY INVOICE PREFIX

print("\n4. CATEGORY BY INVOICE PREFIX")
print("-" * 70)

df["InvoicePrefix"] = invoice.str[0]

prefix_summary = pd.crosstab(
    df["InvoicePrefix"],
    df["TransactionCategory"]
)

print(prefix_summary.to_string())


# 5. CUSTOMER IDENTIFICATION

print("\n5. CUSTOMER IDENTIFICATION")
print("-" * 70)

customer_summary = (
    df.groupby("TransactionCategory")
    .agg(
        TotalRecords=("Invoice", "size"),
        IdentifiedCustomerRecords=("Customer ID", "count"),
        UniqueCustomers=("Customer ID", "nunique")
    )
)

customer_summary["MissingCustomerRecords"] = (
    customer_summary["TotalRecords"]
    - customer_summary["IdentifiedCustomerRecords"]
)

print(customer_summary.to_string())


# 6. INDEPENDENT EXCEPTION FLAG SUMMARY

print("\n6. INDEPENDENT EXCEPTION FLAG SUMMARY")
print("-" * 70)

flag_columns = [
    "IsAccountingAdjustment",
    "IsCancellation",
    "IsNegativeQuantity",
    "IsNegativePrice",
    "IsZeroPrice",
    "IsOperationalNonMerchandise"
]

flag_summary = pd.DataFrame({
    "Flag": flag_columns,
    "RecordCount": [
        int(df[column].sum())
        for column in flag_columns
    ]
})

flag_summary["Percentage"] = (
    flag_summary["RecordCount"] / len(df) * 100
)

print(flag_summary.round(2).to_string(index=False))


# 7. ZERO PRICE INVESTIGATION

print("\n7. ZERO PRICE INVESTIGATION")
print("-" * 70)

zero_price = df[df["IsZeroPrice"]]

print(f"Total zero-price records: {len(zero_price):,}")

print(
    f"Zero-price records with negative quantities: "
    f"{zero_price['IsNegativeQuantity'].sum():,}"
)

print(
    f"Zero-price records with positive quantities: "
    f"{(zero_price['Quantity'] > 0).sum():,}"
)

print(
    f"Unique stock codes: "
    f"{zero_price['StockCode'].nunique():,}"
)

print("\nMost frequent descriptions:")

print(
    zero_price["Description"]
    .replace("", "Missing Description")
    .value_counts()
    .head(15)
    .to_string()
)


# 8. UNCLASSIFIED RECORDS

print("\n8. UNCLASSIFIED RECORDS")
print("-" * 70)

unclassified = df[
    df["TransactionCategory"] == "Unclassified"
]

print(f"Unclassified records: {len(unclassified):,}")


# 9. CLASSIFICATION VALIDATION

print("\n9. CLASSIFICATION VALIDATION")
print("-" * 70)

original_records = len(df)
classified_records = df["TransactionCategory"].notna().sum()
category_total = category_summary["RecordCount"].sum()

print(f"Original records: {original_records:,}")
print(f"Classified records: {classified_records:,}")
print(f"Unclassified records: {len(unclassified):,}")
print(f"Category total: {category_total:,}")

print(
    "\nOperational flag total: "
    f"{df['IsOperationalNonMerchandise'].sum():,}"
)

print(
    "Operational category total: "
    f"{(df['TransactionCategory'] == 'Operational / Non-Merchandise').sum():,}"
)

print("\nOPERATIONAL FLAG CROSS-CHECK")

print(
    pd.crosstab(
        df["IsOperationalNonMerchandise"],
        df["TransactionCategory"]
    ).to_string()
)

if original_records != category_total:
    raise ValueError("Classification validation failed: category totals do not match.")

if len(unclassified) > 0:
    raise ValueError("Classification validation failed: unclassified records remain.")


# 10. SAVE CORRECTED OUTPUTS

print("\n10. SAVING CORRECTED CLASSIFICATION OUTPUTS")
print("-" * 70)

df.to_csv(
    OUTPUT_DIR / "classified_transactions_corrected.csv",
    index=False
)

category_summary.to_csv(
    OUTPUT_DIR / "transaction_category_summary_corrected.csv"
)

prefix_summary.to_csv(
    OUTPUT_DIR / "transaction_prefix_summary_corrected.csv"
)

customer_summary.to_csv(
    OUTPUT_DIR / "transaction_customer_summary_corrected.csv"
)

flag_summary.to_csv(
    OUTPUT_DIR / "transaction_flag_summary_corrected.csv",
    index=False
)

print("classified_transactions_corrected.csv")
print("transaction_category_summary_corrected.csv")
print("transaction_prefix_summary_corrected.csv")
print("transaction_customer_summary_corrected.csv")
print("transaction_flag_summary_corrected.csv")

print("\n" + "=" * 70)
print("CORRECTED TRANSACTION CLASSIFICATION COMPLETED")
print("=" * 70)
