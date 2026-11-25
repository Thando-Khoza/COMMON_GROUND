
import pandas as pd
from collections import Counter

FILE_PATH = "data/raw/online_retail_II.xlsx"

print("=" * 65)
print("COMMON GROUND | CROSS-SHEET DUPLICATE VERIFICATION")
print("=" * 65)

# LOAD THE ORIGINAL WORKSHEETS
sheet_1 = pd.read_excel(FILE_PATH, sheet_name="Year 2009-2010")
sheet_2 = pd.read_excel(FILE_PATH, sheet_name="Year 2010-2011")

columns = list(sheet_1.columns)

# CREATE CONSISTENT ROW IDENTIFIERS
hashes_1 = pd.util.hash_pandas_object(
    sheet_1[columns], index=False
)

hashes_2 = pd.util.hash_pandas_object(
    sheet_2[columns], index=False
)

# COUNT HOW MANY TIMES EACH EXACT ROW APPEARS
counts_1 = Counter(hashes_1)
counts_2 = Counter(hashes_2)

# CALCULATE THE ACTUAL CROSS-SHEET OVERLAP
shared_hashes = set(counts_1) & set(counts_2)

duplicate_occurrences = sum(
    min(counts_1[row], counts_2[row])
    for row in shared_hashes
)

print("\n1. CROSS-SHEET OVERLAP")
print("-" * 65)

print(f"Unique matching transaction rows: {len(shared_hashes):,}")
print(f"Duplicated occurrences across sheets: {duplicate_occurrences:,}")

# INVESTIGATE HIGH-DUPLICATE INVOICES
print("\n2. HIGH-DUPLICATE INVOICE VERIFICATION")
print("-" * 65)

target_invoices = ["537434", "538071", "537638"]

for invoice in target_invoices:

    first = sheet_1[
        sheet_1["Invoice"].astype(str) == invoice
    ]

    second = sheet_2[
        sheet_2["Invoice"].astype(str) == invoice
    ]

    first_hashes = Counter(
        pd.util.hash_pandas_object(first[columns], index=False)
    )

    second_hashes = Counter(
        pd.util.hash_pandas_object(second[columns], index=False)
    )

    shared = set(first_hashes) & set(second_hashes)

    shared_count = sum(
        min(first_hashes[row], second_hashes[row])
        for row in shared
    )

    print(f"\nInvoice: {invoice}")
    print(f"Rows in first sheet: {len(first):,}")
    print(f"Rows in second sheet: {len(second):,}")
    print(f"Unique matching lines: {len(shared):,}")
    print(f"Matching occurrences: {shared_count:,}")

print("\n" + "=" * 65)
print("VERIFICATION COMPLETED")
print("=" * 65)
