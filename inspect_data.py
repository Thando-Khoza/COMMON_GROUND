
import openpyxl
import pandas as pd
from pathlib import Path
from collections import Counter

DATA_PATH = Path("data/raw/online_retail_II.xlsx")
CHUNK_SIZE = 50000

print("=" * 70)
print("COMMON GROUND | DATA INSPECTION")
print("=" * 70)

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Workbook not found: {DATA_PATH}")

workbook = openpyxl.load_workbook(
    DATA_PATH,
    read_only=True,
    data_only=True
)

print("\nWORKBOOK SHEETS")
print("-" * 70)

for sheet_name in workbook.sheetnames:
    print(sheet_name)

for sheet_name in workbook.sheetnames:

    print("\n" + "=" * 70)
    print(f"DATA INSPECTION: {sheet_name}")
    print("=" * 70)

    worksheet = workbook[sheet_name]
    rows = worksheet.iter_rows(values_only=True)

    headers = next(rows)
    columns = list(headers)

    total_rows = 0
    missing_counts = Counter()
    duplicate_count = 0
    numeric_values = {column: [] for column in columns}

    seen_rows = set()
    first_records = []

    for row in rows:
        if row is None or all(value is None for value in row):
            continue

        total_rows += 1

        if len(first_records) < 5:
            first_records.append(row)

        for index, value in enumerate(row):
            if value is None:
                missing_counts[columns[index]] += 1

        row_key = tuple(row)

        if row_key in seen_rows:
            duplicate_count += 1
        else:
            seen_rows.add(row_key)

        if total_rows % CHUNK_SIZE == 0:
            print(f"Processed {total_rows:,} records...")

    print("\nDATASET DIMENSIONS")
    print("-" * 70)
    print(f"Rows: {total_rows:,}")
    print(f"Columns: {len(columns)}")

    print("\nCOLUMN NAMES")
    print("-" * 70)
    print(columns)

    print("\nMISSING VALUES")
    print("-" * 70)

    for column in columns:
        missing = missing_counts[column]
        percentage = (missing / total_rows * 100) if total_rows else 0
        print(f"{column}: {missing:,} ({percentage:.2f}%)")

    print("\nDUPLICATE RECORDS")
    print("-" * 70)
    print(f"Duplicates: {duplicate_count:,}")

    print("\nFIRST 5 RECORDS")
    print("-" * 70)

    preview = pd.DataFrame(first_records, columns=columns)
    print(preview.to_string(index=False))

    print(f"\nINSPECTION COMPLETED: {sheet_name}")

workbook.close()

print("\n" + "=" * 70)
print("DATA INSPECTION COMPLETED")
print("=" * 70)
