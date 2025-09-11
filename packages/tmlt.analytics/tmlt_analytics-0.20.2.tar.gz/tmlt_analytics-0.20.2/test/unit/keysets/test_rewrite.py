"""Tests for KeySetOp tree rewriting operations.

This logic is to some degree tested by the other KeySet tests, but these tests
explicitly cover that rewrite rules don't change the output dataframes, and aim
to hit known-tricky pieces of the rewriting logic.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

from typing import Callable, Optional
from unittest.mock import patch

import pandas as pd
from pyspark.sql import SparkSession
from tmlt.core.utils.testing import Case, assert_dataframe_equal, parametrize

from tmlt.analytics import KeySet


def _from_df(data: dict, spark: SparkSession) -> KeySet:
    return KeySet.from_dataframe(spark.createDataFrame(pd.DataFrame(data)))


# Be careful using anything that boils down to cross-joining FromTuples in these
# tests, as apply_cross_joins_in_memory will hide lots of other optimizations.
@parametrize(
    Case("from_tuples_crossjoin")(
        ks=lambda spark: KeySet.from_tuples([(1, 2), (3, 4)], columns=["A", "B"])
        * KeySet.from_tuples([(5,), (6,), (7,)], columns=["C"])
    ),
    Case("crossjoin_reorder")(
        ks=lambda spark: KeySet.from_dict({"A": [1], "C": [2], "B": [3]})
    ),
    Case("crossjoin_reorder_df")(
        ks=lambda spark: _from_df({"A": [1]}, spark)
        * _from_df({"C": [2]}, spark)
        * _from_df({"B": [3]}, spark)
    ),
    Case("crossjoin_merge")(
        ks=lambda spark: (
            (KeySet.from_dict({"A": [1]}) * KeySet.from_dict({"C": [3]}))
            * (KeySet.from_dict({"D": [4]}) * KeySet.from_dict({"B": [2]}))
        )
    ),
    Case("crossjoin_merge_df")(
        ks=lambda spark: (
            (_from_df({"A": [1]}, spark) * _from_df({"C": [3]}, spark))
            * (_from_df({"D": [4]}, spark) * _from_df({"B": [2]}, spark))
        )
    ),
    Case("crossjoin_merge_mixed")(
        ks=lambda spark: (
            (KeySet.from_dict({"A": [1]}) * _from_df({"C": [3]}, spark))
            * (KeySet.from_dict({"D": [4]}) * _from_df({"B": [2]}, spark))
        )
    ),
    Case("join_reorder")(
        ks=lambda spark: KeySet.from_dict({"B": [2], "C": [3]}).join(
            KeySet.from_dict({"A": [1], "B": [2]})
        )
    ),
    Case("join_linearize")(
        ks=lambda spark: (
            KeySet.from_dict({"B": [2], "C": [3]})
            .join(KeySet.from_dict({"A": [1], "B": [2]}))
            .join(
                KeySet.from_dict({"C": [3], "D": [4]}).join(
                    KeySet.from_dict({"D": [4], "E": [5]})
                )
            )
        )
    ),
    Case("nested_project")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])["A", "B"]["A"]
        )
    ),
    Case("noop_project")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])["A", "B", "C"]
        )
    ),
    Case("crossjoin_project_left")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])
            * KeySet.from_tuples([(4, 5, 6)], columns=["D", "E", "F"])
        )["A", "B"]
    ),
    Case("crossjoin_project_left_df")(
        ks=lambda spark: (
            _from_df({"A": [1], "B": [2], "C": [3]}, spark)
            * _from_df({"D": [4], "E": [5], "F": [6]}, spark)
        )["A", "B"]
    ),
    Case("crossjoin_project_right")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])
            * KeySet.from_tuples([(4, 5, 6)], columns=["D", "E", "F"])
        )["D", "E"]
    ),
    Case("crossjoin_project_right_df")(
        ks=lambda spark: (
            _from_df({"A": [1], "B": [2], "C": [3]}, spark)
            * _from_df({"D": [4], "E": [5], "F": [6]}, spark)
        )["D", "E"]
    ),
    Case("crossjoin_project_both")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])
            * KeySet.from_tuples([(4, 5, 6)], columns=["D", "E", "F"])
        )["C", "D", "E"]
    ),
    Case("crossjoin_project_both_df")(
        ks=lambda spark: (
            _from_df({"A": [1], "B": [2], "C": [3]}, spark)
            * _from_df({"D": [4], "E": [5], "F": [6]}, spark)
        )["C", "D", "E"]
    ),
    Case("crossjoin_project_nested")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2, 3)], columns=["A", "B", "C"])
            * KeySet.from_tuples([(4, 5, 6)], columns=["D", "E", "F"])
            * KeySet.from_tuples([(7, 8, 9)], columns=["G", "H", "I"])
        )["C", "D", "H"]
    ),
    Case("crossjoin_project_nested_df")(
        ks=lambda spark: (
            _from_df({"A": [1], "B": [2], "C": [3]}, spark)
            * _from_df({"D": [4], "E": [5], "F": [6]}, spark)
            * _from_df({"G": [7], "H": [8], "I": [9]}, spark)
        )["C", "D", "H"]
    ),
    Case("subtract_reorder")(
        ks=lambda spark: (
            KeySet.from_dict({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
            - KeySet.from_tuples([(1, 7)], columns=["A", "C"])
            - KeySet.from_tuples([(5, 2), (6, 2)], columns=["B", "A"])
            - KeySet.from_tuples([(4, 7)], columns=["B", "C"])
        )
    ),
    Case("subtract_reorder_nested")(
        ks=lambda spark: (
            KeySet.from_dict({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
            - KeySet.from_tuples([(1, 7)], columns=["A", "C"])
            - (
                KeySet.from_tuples([(5, 2), (6, 2)], columns=["B", "A"])
                - KeySet.from_tuples([(6, 2)], columns=["B", "A"])
            )
            - KeySet.from_tuples([(4, 7)], columns=["B", "C"])
        )
    ),
    Case("extract_crossjoin_from_join_left")(
        ks=lambda spark: (
            KeySet.from_tuples([(2, 8), (4, 10)], columns=["B", "C"])
            * KeySet.from_dict({"D": [1, 2], "E": [3]})
        ).join(KeySet.from_tuples([(1, 2), (3, 4), (5, 6)], columns=["A", "B"]))
    ),
    Case("extract_crossjoin_from_join_right")(
        ks=lambda spark: KeySet.from_tuples(
            [(1, 2), (3, 4), (5, 6)], columns=["A", "B"]
        ).join(
            KeySet.from_tuples([(2, 8), (4, 10)], columns=["B", "C"])
            * KeySet.from_dict({"D": [1, 2], "E": [3]})
        )
    ),
    Case("extract_crossjoin_from_join_both")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2), (3, 4), (5, 6)], columns=["A", "B"])
            * KeySet.from_dict({"D": [1, 2]})
        ).join(
            KeySet.from_tuples([(2, 8), (4, 10)], columns=["B", "C"])
            * KeySet.from_dict({"E": [3]})
        )
    ),
    Case("extract_crossjoin_from_join_neither")(
        ks=lambda spark: (
            KeySet.from_tuples([(1, 2), (3, 4)], columns=["A", "B"])
            * KeySet.from_tuples([(5, 6), (7, 8)], columns=["C", "D"])
        ).join(
            KeySet.from_tuples([(1, 11), (3, 12)], columns=["A", "E"])
            * KeySet.from_tuples([(13, 6), (14, 8)], columns=["F", "D"])
        ),
        allow_unchanged=True,
    ),
    Case("extract_crossjoin_from_subtract")(
        ks=lambda spark: KeySet.from_dict(
            {"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]}
        )
        - KeySet.from_tuples([(5, 7), (6, 8)], columns=["B", "C"])
    ),
)
def test_rewrite_equality(
    ks: Callable[[SparkSession], KeySet], allow_unchanged: Optional[bool], spark
):
    """Rewritten KeySets have the same semantics as the original ones."""
    ks_rewritten = ks(spark)
    with patch("tmlt.analytics.keyset._keyset.rewrite", lambda op: op):
        ks_original = ks(spark)

    if not allow_unchanged:
        # Ensure that rewriting actually happened
        # pylint: disable-next=protected-access
        assert ks_rewritten._op_tree != ks_original._op_tree

    assert ks_rewritten.columns() == ks_original.columns()
    assert ks_rewritten.schema() == ks_original.schema()
    assert_dataframe_equal(ks_rewritten.dataframe(), ks_original.dataframe())
