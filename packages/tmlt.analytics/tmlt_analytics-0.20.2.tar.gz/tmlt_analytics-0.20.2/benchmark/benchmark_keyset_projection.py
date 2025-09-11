"""Benchmarking script for taking the cross-product and projection of large keysets."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

import time
from functools import reduce
from typing import List

import pandas as pd
from benchmarking_utils import write_as_html
from pyspark.sql import SparkSession

from tmlt.analytics import KeySet


def evaluate_runtime(
    keysets: List[KeySet],
    columns_to_select: List[str],
) -> tuple[float, int, int]:
    """See how long it takes to select a subset of columns from product keyset."""
    start = time.time()
    product_keyset = reduce(lambda a, b: a * b, keysets)
    projected_keyset = product_keyset[columns_to_select]
    projected_keyset.dataframe().write.format("noop").mode("overwrite").save()
    running_time = time.time() - start

    product_keyset_size = product_keyset.size()
    projected_keyset_size = projected_keyset.size()
    return round(running_time, 3), product_keyset_size, projected_keyset_size


def main() -> None:
    """Evaluate running time for selecting subset of columns from product keysets."""
    print("Benchmark keyset projection")
    spark = (
        SparkSession.builder.config("spark.memory.offHeap.enabled", "true")
        .config("spark.memory.offHeap.size", "4g")
        .getOrCreate()
    )

    benchmark_result = pd.DataFrame(
        [],
        columns=[
            "Keyset Domain Size",
            "Columns",
            "Product Keyset Size",
            "Projected Keyset Size",
            "Running time (s)",
        ],
    )

    keyset_ab = KeySet.from_dataframe(
        spark.createDataFrame(
            pd.DataFrame(
                [
                    ["abc", 123],
                    ["def", 123],
                ],
                columns=["A", "B"],
            ),
        ),
    )

    for size in [100, 400, 10000, 40000, 160000, 640000]:
        keyset_c = KeySet.from_dict({"C": list(range(size))})
        keyset_d = KeySet.from_dict({"D": list(range(0 - size, 0))})
        keyset_e = KeySet.from_dict({"E": [str(n) for n in range(size)]})

        keysets = [keyset_ab, keyset_c, keyset_d, keyset_e]

        # Materialize all dataframes before benchmarking
        for keyset in keysets:
            keyset.dataframe().write.format("noop").mode("overwrite").save()

        column_combinations_to_check = [
            ["A"],
            ["B"],
            ["C"],
            ["D"],
            ["E"],
            ["A", "B"],
            ["A", "C"],
            ["A", "D"],
            ["A", "E"],
        ]
        for columns_to_select in column_combinations_to_check:
            # Make sure everything is "warmed up" for good comparisons.
            evaluate_runtime(keysets, columns_to_select)

            running_time, product_keyset_size, projected_keyset_size = evaluate_runtime(
                keysets, columns_to_select
            )
            row = {
                "Keyset Domain Size": size,
                "Columns": columns_to_select,
                "Product Keyset Size": product_keyset_size,
                "Projected Keyset Size": projected_keyset_size,
                "Running time (s)": running_time,
            }
            print("Benchmark row:", row)
            benchmark_result = pd.concat(
                [benchmark_result, pd.Series(row).to_frame().T], ignore_index=True
            )
    spark.stop()
    write_as_html(benchmark_result, "keyset_projection.html")


if __name__ == "__main__":
    main()
