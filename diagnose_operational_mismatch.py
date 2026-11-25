
from pathlib import Path
import pandas as pd
import re

INPUT = Path("data/processed/classified_transactions_corrected.csv")
CHUNK_SIZE = 50000

operational_codes = {
    "POST",
    "DOT",
    "M",
    "AMAZONFEE",
    "BANK CHARGES"
}

operational_keywords = [
    "ADJUSTMENT",
    "DAMAGED",
    "DAMAGE",
    "MISSING",
    "SMASHED",
    "THROWN AWAY",
    "UNSALEABLE",
    "DESTROYED",
    "BAD DEBT"
]

pattern = "|".join(re.escape(x) for x in operational_keywords)

original_flag_total = 0
recalculated_flag_total = 0
category_total = 0
overlap_difference = 0

print("=" * 70)
print("COMMON GROUND | OPERATIONAL CLASSIFICATION DIAGNOSTIC")
print("=" * 70)

for chunk in pd.read_csv(INPUT, chunksize=CHUNK_SIZE):

    original_flag = chunk["IsOperationalNonMerchandise"].fillna(False).astype(bool)

    stock_codes = (
        chunk["StockCode"].fillna("").astype(str).str.strip().str.upper()
    )

    descriptions = (
        chunk["Description"].fillna("").astype(str).str.strip().str.upper()
    )

    recalculated_flag = (
        stock_codes.isin(operational_codes)
        | descriptions.str.contains(pattern, regex=True, na=False)
    )

    original_flag_total += int(original_flag.sum())
    recalculated_flag_total += int(recalculated_flag.sum())

    category_total += int(
        (chunk["TransactionCategory"] == "Operational / Non-Merchandise").sum()
    )

    overlap_difference += int((original_flag != recalculated_flag).sum())

print("\nORIGINAL OPERATIONAL FLAG:", f"{original_flag_total:,}")
print("RECALCULATED OPERATIONAL FLAG:", f"{recalculated_flag_total:,}")
print("OPERATIONAL CATEGORY:", f"{category_total:,}")
print("RECORDS WITH DIFFERENT FLAGS:", f"{overlap_difference:,}")

print("\nDIAGNOSTIC COMPLETED")
print("=" * 70)
