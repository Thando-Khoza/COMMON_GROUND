
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

# LOAD DATA
sheets = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)

df["Invoice"] = df["Invoice"].astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip()
df["LineValue"] = df["Quantity"] * df["Price"]

print("=" * 65)
print("COMMON GROUND | EXCEPTION ANALYSIS")
print("=" * 65)

# 1. CANCELLATION EXCEPTION
print("\n1. CANCELLATION WITHOUT NEGATIVE QUANTITY")
print("-" * 65)

cancellation_exception = df[
    df["Invoice"].str.startswith("C")
    & (df["Quantity"] >= 0)
]

print(cancellation_exception.to_string(index=False))

# 2. NEGATIVE QUANTITY WITHOUT CANCELLATION PREFIX
print("\n2. NEGATIVE QUANTITY WITHOUT C PREFIX")
print("-" * 65)

other_returns = df[
    ~df["Invoice"].str.startswith("C")
    & (df["Quantity"] < 0)
]

print(f"Records: {len(other_returns):,}")
print(f"Total value: {other_returns['LineValue'].sum():,.2f}")

print("\nMost frequent descriptions:")
print(other_returns["Description"].value_counts().head(15).to_string())

# 3. ACCOUNTING ADJUSTMENTS
print("\n3. ACCOUNTING ADJUSTMENTS")
print("-" * 65)

adjustments = df[df["Invoice"].str.startswith("A")]

print(adjustments.to_string(index=False))

# 4. ZERO PRICE EXCEPTIONS
print("\n4. ZERO PRICE EXCEPTIONS")
print("-" * 65)

zero_price = df[df["Price"] == 0]

print(
    zero_price.groupby("Description", dropna=False)
    .agg(
        Records=("Invoice", "size"),
        UniqueProducts=("StockCode", "nunique"),
        TotalQuantity=("Quantity", "sum")
    )
    .sort_values("Records", ascending=False)
    .head(20)
    .to_string()
)

# 5. NEGATIVE PRICE EXCEPTIONS
print("\n5. NEGATIVE PRICE EXCEPTIONS")
print("-" * 65)

negative_price = df[df["Price"] < 0]

print(negative_price.to_string(index=False))

# 6. TRANSACTION VALUE OUTLIERS
print("\n6. EXTREME POSITIVE LINE VALUES")
print("-" * 65)

positive_values = df[df["LineValue"] > 0]

print(
    positive_values.nlargest(15, "LineValue")[
        ["Invoice", "StockCode", "Description",
         "Quantity", "Price", "LineValue"]
    ].to_string(index=False)
)

print("\n" + "=" * 65)
print("EXCEPTION ANALYSIS COMPLETED")
print("=" * 65)
