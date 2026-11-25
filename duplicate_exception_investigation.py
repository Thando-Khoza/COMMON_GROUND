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


print("=" * 70)
print("COMMON GROUND | DUPLICATE EXCEPTION INVESTIGATION")
print("=" * 70)


# IDENTIFY INVOICES WITH REPEATED LINES ACROSS TIMESTAMPS
repeated_groups = (
    df.groupby(
        [
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "Price",
            "Customer ID",
            "Country"
        ],
        dropna=False
    )
    .agg(
        Occurrences=("InvoiceDate", "size"),
        UniqueTimestamps=("InvoiceDate", "nunique")
    )
    .reset_index()
)

exceptions = repeated_groups[
    (repeated_groups["Occurrences"] > 1)
    & (repeated_groups["UniqueTimestamps"] > 1)
]

exception_invoices = exceptions["Invoice"].unique()


# 1. EXCEPTION OVERVIEW
print("\n1. EXCEPTION OVERVIEW")
print("-" * 70)

print(f"Unusual repeated product groups: {len(exceptions):,}")
print(f"Affected invoices: {len(exception_invoices):,}")

print("\nAffected invoice numbers:")
for invoice in exception_invoices:
    print(invoice)


# 2. INVOICE TIMELINES
print("\n2. INVOICE TIMELINES")
print("-" * 70)

timeline_results = []

for invoice in exception_invoices:

    invoice_data = df[df["Invoice"] == invoice].copy()

    print(f"\nINVOICE: {invoice}")
    print("-" * 50)

    print(f"Total records: {len(invoice_data):,}")
    print(
        f"Unique timestamps: "
        f"{invoice_data['InvoiceDate'].nunique():,}"
    )

    print("\nTransaction timeline:")

    timeline = (
        invoice_data.groupby("InvoiceDate")
        .agg(
            TransactionLines=("Invoice", "size"),
            UniqueProducts=("StockCode", "nunique")
        )
        .reset_index()
        .sort_values("InvoiceDate")
    )

    print(timeline.to_string(index=False))

    timeline["Invoice"] = invoice

    timeline_results.append(timeline)


# 3. REPEATED PRODUCT DETAILS
print("\n3. REPEATED PRODUCT DETAILS")
print("-" * 70)

exception_details = []

for invoice in exception_invoices:

    print(f"\nINVOICE: {invoice}")
    print("-" * 50)

    invoice_exceptions = exceptions[
        exceptions["Invoice"] == invoice
    ].copy()

    invoice_exceptions = invoice_exceptions.sort_values(
        "Occurrences",
        ascending=False
    )

    print(
        invoice_exceptions.to_string(index=False)
    )

    exception_details.append(invoice_exceptions)


# 4. TIMESTAMP DIFFERENCES
print("\n4. TIMESTAMP DIFFERENCES")
print("-" * 70)

timestamp_differences = []

for _, group in exceptions.iterrows():

    matching_rows = df[
        (df["Invoice"] == group["Invoice"])
        & (df["StockCode"] == group["StockCode"])
        & (df["Description"] == group["Description"])
        & (df["Quantity"] == group["Quantity"])
        & (df["Price"] == group["Price"])
        & (df["InvoiceDate"].notna())
    ].copy()

    timestamps = sorted(
        matching_rows["InvoiceDate"].unique()
    )

    if len(timestamps) > 1:

        for previous, current in zip(
            timestamps,
            timestamps[1:]
        ):

            difference = (
                pd.Timestamp(current)
                - pd.Timestamp(previous)
            )

            timestamp_differences.append({
                "Invoice": group["Invoice"],
                "StockCode": group["StockCode"],
                "Description": group["Description"],
                "PreviousTimestamp": previous,
                "CurrentTimestamp": current,
                "TimeDifferenceMinutes": (
                    difference.total_seconds() / 60
                )
            })


if timestamp_differences:

    differences_df = pd.DataFrame(timestamp_differences)

    print(
        differences_df.to_string(index=False)
    )

else:

    differences_df = pd.DataFrame()

    print("No timestamp differences identified.")


# 5. SAVE INVESTIGATION RESULTS
print("\n5. SAVING INVESTIGATION RESULTS")
print("-" * 70)

if timeline_results:

    timeline_df = pd.concat(
        timeline_results,
        ignore_index=True
    )

    timeline_df.to_csv(
        OUTPUT_DIR / "duplicate_exception_timelines.csv",
        index=False
    )

if exception_details:

    details_df = pd.concat(
        exception_details,
        ignore_index=True
    )

    details_df.to_csv(
        OUTPUT_DIR / "duplicate_exception_details.csv",
        index=False
    )

differences_df.to_csv(
    OUTPUT_DIR / "duplicate_exception_time_differences.csv",
    index=False
)

print("duplicate_exception_timelines.csv")
print("duplicate_exception_details.csv")
print("duplicate_exception_time_differences.csv")


print("\n" + "=" * 70)
print("DUPLICATE EXCEPTION INVESTIGATION COMPLETED")
print("=" * 70)