
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd


# ============================================================
# COMMON GROUND | FINAL CLASSIFICATION REFINEMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = OUTPUT_DIR / "classified_transactions_corrected.csv"

OUTPUT_FILE = OUTPUT_DIR / "refined_classified_transactions_corrected.csv"
CATEGORY_FILE = OUTPUT_DIR / "refined_transaction_category_summary.csv"
PREFIX_FILE = OUTPUT_DIR / "refined_transaction_prefix_summary.csv"
FLAG_FILE = OUTPUT_DIR / "refined_transaction_flag_summary.csv"

CHUNK_SIZE = 50000
MINIMUM_FREE_SPACE_GB = 1.0


def stop(message):
    print("\nERROR:", message)
    sys.exit(1)


def main():

    print("=" * 70)
    print("COMMON GROUND | FINAL CLASSIFICATION REFINEMENT")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. CHECK INPUT AND DISK SPACE
    # --------------------------------------------------------

    print("\n1. CHECKING INPUT DATA")
    print("-" * 70)

    if not INPUT_FILE.exists():
        stop(f"Input file not found: {INPUT_FILE}")

    input_size = INPUT_FILE.stat().st_size
    disk = shutil.disk_usage(BASE_DIR)

    print(f"Input file: {INPUT_FILE.name}")
    print(f"Input size: {input_size / (1024 ** 2):,.2f} MB")
    print(f"Available disk space: {disk.free / (1024 ** 3):,.2f} GB")

    estimated_required = (input_size * 2) + (1024 ** 3)

    if disk.free < estimated_required:
        stop("Insufficient disk space. Processing cancelled.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_output = OUTPUT_FILE.with_suffix(".tmp")

    if temporary_output.exists():
        temporary_output.unlink()

    # --------------------------------------------------------
    # 2. INITIALISE SUMMARIES
    # --------------------------------------------------------

    category_parts = []
    prefix_parts = []

    flag_totals = {
        "IsAccountingAdjustment": 0,
        "IsCancellation": 0,
        "IsNegativeQuantity": 0,
        "IsNegativePrice": 0,
        "IsZeroPrice": 0,
        "IsOperationalNonMerchandise": 0
    }

    total_records = 0
    first_chunk = True

    # --------------------------------------------------------
    # 3. PROCESS TRANSACTIONS
    # --------------------------------------------------------

    print("\n2. PROCESSING TRANSACTION DATA")
    print("-" * 70)

    try:

        for chunk_number, chunk in enumerate(
            pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE),
            start=1
        ):

            required_columns = [
                "Invoice",
                "StockCode",
                "Description",
                "Quantity",
                "Price",
                "IsOperationalNonMerchandise"
            ]

            missing_columns = [
                column for column in required_columns
                if column not in chunk.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {missing_columns}"
                )

            # Standardise transaction fields
            chunk["InvoiceNormalized"] = (
                chunk["Invoice"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            chunk["StockCodeNormalized"] = (
                chunk["StockCode"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            chunk["DescriptionNormalized"] = (
                chunk["Description"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            chunk["Quantity"] = pd.to_numeric(
                chunk["Quantity"], errors="coerce"
            )

            chunk["Price"] = pd.to_numeric(
                chunk["Price"], errors="coerce"
            )

            chunk["LineValue"] = (
                chunk["Quantity"] * chunk["Price"]
            )

            chunk["InvoicePrefix"] = (
                chunk["InvoiceNormalized"].str[0].fillna("")
            )

            # Recreate independent flags
            chunk["IsAccountingAdjustment"] = (
                chunk["InvoicePrefix"] == "A"
            )

            chunk["IsCancellation"] = (
                chunk["InvoicePrefix"] == "C"
            )

            chunk["IsNegativeQuantity"] = (
                chunk["Quantity"] < 0
            )

            chunk["IsNegativePrice"] = (
                chunk["Price"] < 0
            )

            chunk["IsZeroPrice"] = (
                chunk["Price"] == 0
            )

            # PRESERVE ORIGINAL OPERATIONAL FLAG
            original_operational_flag = (
                chunk["IsOperationalNonMerchandise"]
            )

            if original_operational_flag.dtype == bool:
                chunk["IsOperationalNonMerchandise"] = (
                    original_operational_flag.fillna(False)
                )
            else:
                chunk["IsOperationalNonMerchandise"] = (
                    original_operational_flag
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .isin(["true", "1", "yes"])
                )

            # ------------------------------------------------
            # 4. REFINE TRANSACTION CLASSIFICATION
            # ------------------------------------------------

            conditions = [
                chunk["IsAccountingAdjustment"],
                chunk["IsOperationalNonMerchandise"],
                chunk["IsCancellation"],
                chunk["IsNegativeQuantity"],
                chunk["IsNegativePrice"],
                chunk["IsZeroPrice"]
            ]

            categories = [
                "Accounting Adjustment",
                "Operational / Non-Merchandise",
                "Cancellation",
                "Negative Quantity Exception",
                "Negative Price Exception",
                "Zero Price Record"
            ]

            chunk["TransactionCategoryRefined"] = np.select(
                conditions,
                categories,
                default="Standard Positive Transaction"
            )

            # ------------------------------------------------
            # 5. UPDATE FLAG TOTALS
            # ------------------------------------------------

            for flag in flag_totals:
                flag_totals[flag] += int(chunk[flag].sum())

            # ------------------------------------------------
            # 6. CATEGORY SUMMARY
            # ------------------------------------------------

            aggregation = {
                "RecordCount": ("Invoice", "size"),
                "TotalQuantity": ("Quantity", "sum"),
                "TotalLineValue": ("LineValue", "sum"),
                "UniqueInvoices": ("InvoiceNormalized", "nunique"),
                "UniqueStockCodes": ("StockCodeNormalized", "nunique")
            }

            if "Customer ID" in chunk.columns:
                aggregation["UniqueCustomers"] = (
                    "Customer ID", "nunique"
                )

            category_summary = (
                chunk.groupby("TransactionCategoryRefined")
                .agg(**aggregation)
                .reset_index()
            )

            category_parts.append(category_summary)

            # ------------------------------------------------
            # 7. INVOICE PREFIX SUMMARY
            # ------------------------------------------------

            prefix_summary = (
                chunk.groupby(
                    ["InvoicePrefix", "TransactionCategoryRefined"]
                )
                .agg(
                    RecordCount=("Invoice", "size"),
                    TotalLineValue=("LineValue", "sum")
                )
                .reset_index()
            )

            prefix_parts.append(prefix_summary)

            # ------------------------------------------------
            # 8. SAVE CHUNK
            # ------------------------------------------------

            chunk.to_csv(
                temporary_output,
                mode="w" if first_chunk else "a",
                header=first_chunk,
                index=False
            )

            first_chunk = False
            total_records += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} records processed | "
                f"Total: {total_records:,}"
            )

            remaining = shutil.disk_usage(BASE_DIR).free

            if remaining < MINIMUM_FREE_SPACE_GB * (1024 ** 3):
                raise OSError(
                    "Available disk space dropped below 1 GB."
                )

        if total_records == 0:
            raise ValueError("No records were processed.")

        # ----------------------------------------------------
        # 9. COMBINE SUMMARIES
        # ----------------------------------------------------

        print("\n3. BUILDING FINAL SUMMARIES")
        print("-" * 70)

        category_final = (
            pd.concat(category_parts, ignore_index=True)
            .groupby("TransactionCategoryRefined")
            .sum(numeric_only=True)
            .reset_index()
        )

        category_final["Percentage"] = (
            category_final["RecordCount"] / total_records * 100
        )

        prefix_final = (
            pd.concat(prefix_parts, ignore_index=True)
            .groupby(
                ["InvoicePrefix", "TransactionCategoryRefined"],
                as_index=False
            )
            .sum(numeric_only=True)
        )

        flag_final = pd.DataFrame({
            "Flag": list(flag_totals.keys()),
            "RecordCount": list(flag_totals.values())
        })

        # ----------------------------------------------------
        # 10. VALIDATE RESULTS
        # ----------------------------------------------------

        print("\n4. VALIDATING RESULTS")
        print("-" * 70)

        category_total = int(
            category_final["RecordCount"].sum()
        )

        operational_category_total = int(
            category_final.loc[
                category_final["TransactionCategoryRefined"]
                == "Operational / Non-Merchandise",
                "RecordCount"
            ].sum()
        )

        operational_flag_total = flag_totals[
            "IsOperationalNonMerchandise"
        ]

        print(f"Records processed: {total_records:,}")
        print(f"Records classified: {category_total:,}")
        print(f"Unclassified records: {total_records - category_total:,}")

        print(
            f"Operational flag total: "
            f"{operational_flag_total:,}"
        )

        print(
            f"Operational category total: "
            f"{operational_category_total:,}"
        )

        if category_total != total_records:
            raise ValueError(
                "Category totals do not match processed records."
            )

        if operational_category_total != operational_flag_total:
            raise ValueError(
                "Operational flag and category totals do not match."
            )

        print("\nVALIDATION PASSED")

        # ----------------------------------------------------
        # 11. SAVE FINAL OUTPUTS
        # ----------------------------------------------------

        print("\n5. SAVING FINAL OUTPUTS")
        print("-" * 70)

        category_final.to_csv(CATEGORY_FILE, index=False)
        prefix_final.to_csv(PREFIX_FILE, index=False)
        flag_final.to_csv(FLAG_FILE, index=False)

        temporary_output.replace(OUTPUT_FILE)

        print(OUTPUT_FILE.name)
        print(CATEGORY_FILE.name)
        print(PREFIX_FILE.name)
        print(FLAG_FILE.name)

        print("\nFINAL CATEGORY OVERVIEW")
        print("-" * 70)

        print(
            category_final.sort_values(
                "RecordCount",
                ascending=False
            ).to_string(index=False)
        )

        print("\nFINAL CLASSIFICATION REFINEMENT COMPLETED")
        print("=" * 70)

    except Exception:
        if temporary_output.exists():
            temporary_output.unlink()
        raise


if __name__ == "__main__":
    main()
