
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

print("=" * 65)
print("COMMON GROUND | SHEET OVERLAP ANALYSIS")
print("=" * 65)

# LOAD SHEETS SEPARATELY
sheets = pd.read_excel(DATA_PATH, sheet_name=None)

first_name = list(sheets.keys())[0]
second_name = list(sheets.keys())[1]

first = sheets[first_name].copy()
second = sheets[second_name].copy()

columns = first.columns.tolist()

# 1. DATE RANGE COMPARISON
print("\n1. REPORTING PERIOD COMPARISON")
print("-" * 65)

for name, data in sheets.items():
    print(f"\n{name}")
    print(f"Rows: {len(data):,}")
    print(f"Start: {data['InvoiceDate'].min()}")
    print(f"End: {data['InvoiceDate'].max()}")

# 2. IDENTIFY EXACT ROW OVERLAP
print("\n2. EXACT ROW OVERLAP BETWEEN SHEETS")
print("-" * 65)

first_hashes = set(
    pd.util.hash_pandas_object(first[columns], index=False)
)

second_hashes = pd.util.hash_pandas_object(
    second[columns],
    index=False
)

cross_sheet_matches = second_hashes.isin(first_hashes)

print(
    f"Rows in second sheet matching first sheet: "
    f"{cross_sheet_matches.sum():,}"
)

print(
    f"Unique matching rows: "
    f"{second.loc[cross_sheet_matches, columns].drop_duplicates().shape[0]:,}"
)

# 3. CHECK OVERLAPPING DATES
print("\n3. OVERLAPPING DATE RECORDS")
print("-" * 65)

first_dates = set(first["InvoiceDate"].dt.date)
second_dates = set(second["InvoiceDate"].dt.date)

overlapping_dates = sorted(first_dates.intersection(second_dates))

print(f"Overlapping calendar dates: {len(overlapping_dates)}")

for date in overlapping_dates:
    print(date)

# 4. INVESTIGATE HIGH DUPLICATE INVOICE COUNTS
print("\n4. HIGH DUPLICATE INVOICE INVESTIGATION")
print("-" * 65)

combined = pd.concat([first, second], ignore_index=True)

for invoice in ["537434", "538071", "537638"]:
    invoice_data = combined[
        combined["Invoice"].astype(str).str.strip() == invoice
    ]

    print(f"\nInvoice: {invoice}")
    print(f"Total rows: {len(invoice_data):,}")
    print(f"Unique exact rows: {len(invoice_data.drop_duplicates()):,}")

    print("\nMost repeated transaction lines:")

    print(
        invoice_data.value_counts(subset=columns)
        .head(5)
        .to_string()
    )

# 5. FINAL SUMMARY
print("\n" + "=" * 65)
print("SHEET OVERLAP ANALYSIS COMPLETED")
print("=" * 65)
