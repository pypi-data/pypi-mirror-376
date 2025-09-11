"""Tests for Session with the AddMaxRows ProtectedChange."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import pytest
from pyspark.sql import DataFrame
from tmlt.core.measurements.interactive_measurements import PrivacyAccountantState
from tmlt.core.measures import ApproxDP, PureDP, RhoZCDP
from tmlt.core.utils.exact_number import ExactNumber
from tmlt.core.utils.parameters import calculate_noise_scale
from tmlt.core.utils.testing import Case, parametrize

from tmlt.analytics import (
    AddMaxRowsInMaxGroups,
    AddOneRow,
    AddRowsWithID,
    ApproxDPBudget,
    AverageMechanism,
    ColumnDescriptor,
    ColumnType,
    CountMechanism,
    KeySet,
    PrivacyBudget,
    PureDPBudget,
    Query,
    QueryBuilder,
    RhoZCDPBudget,
    Session,
    StdevMechanism,
    SumMechanism,
    TruncationStrategy,
)
from tmlt.analytics._noise_info import _NoiseMechanism
from tmlt.analytics._query_expr import (
    GroupByBoundedSTDEV,
    GroupByCount,
    PrivateSource,
    QueryExpr,
)
from tmlt.analytics._table_identifier import NamedTable

from ....conftest import assert_frame_equal_with_sort
from .conftest import EVALUATE_TESTS

Row = Dict[str, Any]


@pytest.mark.usefixtures("session_data")
class TestSession:
    """Tests for Valid Sessions."""

    sdf: DataFrame
    join_df: DataFrame
    join_dtypes_df: DataFrame
    groupby_two_columns_df: DataFrame
    groupby_one_column_df: DataFrame
    groupby_with_duplicates_df: DataFrame
    groupby_empty_df: DataFrame

    @pytest.mark.parametrize(
        "query_expr_or_builder,expected_expr,expected_df", EVALUATE_TESTS
    )
    def test_queries_privacy_budget_infinity_puredp(
        self,
        query_expr_or_builder: Query,
        expected_expr: Optional[QueryExpr],
        expected_df: pd.DataFrame,
    ):
        """Session :func:`evaluate` returns the correct results for eps=inf and PureDP.

        Args:
            query_expr_or_builder: The query or builder to evaluate.
            expected_expr: Expected value for query_expr.
            expected_df: The expected answer.
        """
        if expected_expr is not None:
            # pylint: disable=protected-access
            query_expr = query_expr_or_builder._query_expr
            # pylint: enable=protected-access
            assert query_expr == expected_expr
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(float("inf")),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        session.add_public_dataframe(source_id="public", dataframe=self.join_df)
        session.add_public_dataframe(
            source_id="join_dtypes", dataframe=self.join_dtypes_df
        )
        session.add_public_dataframe(
            source_id="groupby_two_columns", dataframe=self.groupby_two_columns_df
        )
        session.add_public_dataframe(
            source_id="groupby_one_column", dataframe=self.groupby_one_column_df
        )
        session.add_public_dataframe(
            source_id="groupby_with_duplicates",
            dataframe=self.groupby_with_duplicates_df,
        )
        session.add_public_dataframe(
            source_id="groupby_empty", dataframe=self.groupby_empty_df
        )
        actual_sdf = session.evaluate(
            query_expr_or_builder, privacy_budget=PureDPBudget(float("inf"))
        )
        assert isinstance(actual_sdf, DataFrame)
        assert_frame_equal_with_sort(actual_sdf.toPandas(), expected_df)

    @pytest.mark.parametrize(
        "query_expr_or_builder,expected_expr,expected_df",
        EVALUATE_TESTS
        + [
            (  # Total with GAUSSIAN
                QueryBuilder("private").count(
                    name="total", mechanism=CountMechanism.GAUSSIAN
                ),
                GroupByCount(
                    child=PrivateSource("private"),
                    groupby_keys=KeySet.from_dict({}),
                    output_column="total",
                    mechanism=CountMechanism.GAUSSIAN,
                ),
                pd.DataFrame({"total": [4]}),
            ),
            (  # BoundedSTDEV on integer valued measure column with GAUSSIAN
                QueryBuilder("private")
                .groupby(KeySet.from_dict({"A": ["0", "1"]}))
                .stdev(column="B", low=0, high=1, mechanism=StdevMechanism.GAUSSIAN),
                GroupByBoundedSTDEV(
                    child=PrivateSource("private"),
                    groupby_keys=KeySet.from_dict({"A": ["0", "1"]}),
                    measure_column="B",
                    low=0,
                    high=1,
                    mechanism=StdevMechanism.GAUSSIAN,
                    output_column="B_stdev",
                ),
                pd.DataFrame({"A": ["0", "1"], "B_stdev": [0.5, np.nan]}),
            ),
        ],
    )
    def test_queries_privacy_budget_infinity_rhozcdp(
        self,
        query_expr_or_builder: Query,
        expected_expr: Optional[QueryExpr],
        expected_df: pd.DataFrame,
    ):
        """Session :func:`evaluate` returns the correct results for eps=inf and RhoZCDP.

        Args:
            query_expr_or_builder: The query or builder to evaluate.
            expected_expr: What to expect query_expr to be.
            expected_df: The expected answer.
        """
        if expected_expr is not None:
            # pylint: disable=protected-access
            query_expr = query_expr_or_builder._query_expr
            # pylint: enable=protected-access
            assert query_expr == expected_expr

        session = Session.from_dataframe(
            privacy_budget=RhoZCDPBudget(float("inf")),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        session.add_public_dataframe(source_id="public", dataframe=self.join_df)
        session.add_public_dataframe(
            source_id="join_dtypes", dataframe=self.join_dtypes_df
        )
        session.add_public_dataframe(
            source_id="groupby_two_columns", dataframe=self.groupby_two_columns_df
        )
        session.add_public_dataframe(
            source_id="groupby_one_column", dataframe=self.groupby_one_column_df
        )
        session.add_public_dataframe(
            source_id="groupby_with_duplicates",
            dataframe=self.groupby_with_duplicates_df,
        )
        session.add_public_dataframe(
            source_id="groupby_empty", dataframe=self.groupby_empty_df
        )
        actual_sdf = session.evaluate(
            query_expr_or_builder, privacy_budget=RhoZCDPBudget(float("inf"))
        )
        assert isinstance(actual_sdf, DataFrame)
        assert_frame_equal_with_sort(actual_sdf.toPandas(), expected_df)

    @pytest.mark.parametrize(
        "query_expr,session_budget,query_budget,expected",
        [
            (
                QueryBuilder("private").count(
                    mechanism=CountMechanism.LAPLACE,
                ),
                PureDPBudget(11),
                PureDPBudget(7),
                [
                    {
                        "noise_mechanism": _NoiseMechanism.GEOMETRIC,
                        "noise_parameter": (1.0 / 7.0),
                    }
                ],
            ),
            (
                QueryBuilder("private").average(
                    "X", -111, 234, mechanism=AverageMechanism.GAUSSIAN
                ),
                RhoZCDPBudget(31),
                RhoZCDPBudget(11),
                [
                    # Noise for the sum query (which uses half the budget)
                    {
                        "noise_mechanism": _NoiseMechanism.DISCRETE_GAUSSIAN,
                        # the upper and lower bounds of the sum aggregation
                        # are -173 and 172;
                        # this is (lower - midpoint) and (upper-midpoint) respectively
                        "noise_parameter": (
                            calculate_noise_scale(
                                173, ExactNumber(11) / ExactNumber(2), RhoZCDP()
                            )
                            ** 2
                        ).to_float(round_up=False),
                    },
                    # Noise for the count query (which uses half the budget)
                    {
                        "noise_mechanism": _NoiseMechanism.DISCRETE_GAUSSIAN,
                        "noise_parameter": (
                            calculate_noise_scale(
                                1, ExactNumber(11) / ExactNumber(2), RhoZCDP()
                            )
                            ** 2
                        ).to_float(round_up=False),
                    },
                ],
            ),
        ],
    )
    def test_noise_info(
        self,
        query_expr: Union[QueryExpr, Query],
        session_budget: PrivacyBudget,
        query_budget: PrivacyBudget,
        expected: List[Dict[str, Any]],
    ):
        """Test _noise_info."""
        session = Session.from_dataframe(
            privacy_budget=session_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        # pylint: disable=protected-access
        info = session._noise_info(query_expr, query_budget)
        # pylint: enable=protected-access
        assert info == expected

    @pytest.mark.parametrize(
        "privacy_budget", [(PureDPBudget(float("inf"))), (RhoZCDPBudget(float("inf")))]
    )
    def test_private_join_privacy_budget_infinity(self, privacy_budget: PrivacyBudget):
        """Session :func:`evaluate` returns correct result for private join, eps=inf."""
        query_builder = (
            QueryBuilder("private")
            .join_private(
                "private_2",
                truncation_strategy_left=TruncationStrategy.DropExcess(3),
                truncation_strategy_right=TruncationStrategy.DropExcess(3),
            )
            .replace_null_and_nan(replace_with={})
            .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            .count()
        )
        expected_df = pd.DataFrame({"A": ["0", "1"], "count": [3, 1]})
        session = Session.from_dataframe(
            privacy_budget=privacy_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        session.create_view(
            query_expr=QueryBuilder("private").flat_map(
                f=lambda row: [{"C": 1 if row["A"] == "0" else 2}],
                new_column_types={"C": "INTEGER"},
                augment=True,
                max_rows=1,
            ),
            source_id="private_2",
            cache=False,
        )
        actual_sdf = session.evaluate(query_builder, privacy_budget=privacy_budget)
        assert isinstance(actual_sdf, DataFrame)
        assert_frame_equal_with_sort(actual_sdf.toPandas(), expected_df)

    @pytest.mark.parametrize(
        "mechanism", [(CountMechanism.DEFAULT), (CountMechanism.LAPLACE)]
    )
    def test_interactivity_puredp(self, mechanism: CountMechanism):
        """Test that interactivity works with PureDP."""
        query_builder = QueryBuilder("private").count(
            name="total",
            mechanism=mechanism,
        )

        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(10),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        session.evaluate(query_builder, privacy_budget=PureDPBudget(5))
        assert session.remaining_privacy_budget == PureDPBudget(5)
        session.evaluate(query_builder, privacy_budget=PureDPBudget(5))
        assert session.remaining_privacy_budget == PureDPBudget(0)

    @pytest.mark.parametrize(
        "mechanism",
        [(CountMechanism.DEFAULT), (CountMechanism.LAPLACE), (CountMechanism.GAUSSIAN)],
    )
    def test_interactivity_zcdp(self, mechanism: CountMechanism):
        """Test that interactivity works with RhoZCDP."""
        query_builder = QueryBuilder("private").count(
            name="total",
            mechanism=mechanism,
        )

        session = Session.from_dataframe(
            privacy_budget=RhoZCDPBudget(10),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        session.evaluate(query_builder, privacy_budget=RhoZCDPBudget(5))
        assert session.remaining_privacy_budget == RhoZCDPBudget(5)
        session.evaluate(query_builder, privacy_budget=RhoZCDPBudget(5))
        assert session.remaining_privacy_budget == RhoZCDPBudget(0)

    @pytest.mark.parametrize("columns", [(["A", "count"])])
    def test_get_groups_invalid_column(self, columns: List[str]):
        """Test that the GetGroups query errors on non-existent column."""
        session = Session.from_dataframe(
            privacy_budget=ApproxDPBudget(1, 1e-5),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        query = QueryBuilder("private").get_groups(columns)
        with pytest.raises(ValueError, match="Nonexistent columns in get_groups query"):
            session.evaluate(query, session.remaining_privacy_budget)

    @pytest.mark.parametrize(
        "session_budget", [(PureDPBudget(float("inf"))), (RhoZCDPBudget(float("inf")))]
    )
    def test_get_groups_errors(
        self, session_budget: Union[PureDPBudget, ApproxDPBudget]
    ):
        """Test that the GetGroups query errors with non ApproxDPBudgets."""
        session = Session.from_dataframe(
            privacy_budget=session_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        query = QueryBuilder("private").get_groups([])
        with pytest.raises(
            ValueError, match="GetGroups is only supported with ApproxDPBudgets."
        ):
            session.evaluate(query, session.remaining_privacy_budget)

    def test_get_groups_with_flat_map(self, spark):
        """Test that the GetGroups works with flat map."""

        def duplicate_rows(_: Row) -> List[Row]:
            """Duplicate each row, with one copy having C=0, and the other C=1."""
            return [{"C": "0"}, {"C": "1"}]

        sdf = spark.createDataFrame(
            pd.DataFrame(
                [[0, 0] for _ in range(10000)]
                + [[0, 1] for _ in range(10000)]
                + [[1, 3]],
                columns=["A", "B"],
            )
        )
        session = Session.from_dataframe(
            privacy_budget=ApproxDPBudget(1, 1e-5),
            source_id="private",
            dataframe=sdf,
            protected_change=AddOneRow(),
        )

        query = (
            QueryBuilder("private")
            .flat_map(
                duplicate_rows,
                new_column_types={"C": "VARCHAR"},
                augment=True,
                max_num_rows=2,
            )
            .get_groups(["A", "B", "C"])
        )

        expected_df = pd.DataFrame(
            {"A": [0, 0, 0, 0], "B": [0, 0, 1, 1], "C": ["0", "1", "0", "1"]}
        )
        actual_sdf = session.evaluate(query, session.remaining_privacy_budget)
        assert isinstance(actual_sdf, DataFrame)
        assert_frame_equal_with_sort(actual_sdf.toPandas(), expected_df)

    @parametrize(
        Case("positive")(
            data=pd.DataFrame(
                [[i] for i in range(100)],
                columns=["X"],
            )
        ),
        Case("negative")(
            data=pd.DataFrame(
                [[i] for i in range(-99, 0)],
                columns=["X"],
            )
        ),
        Case("positive_and_negative")(
            data=pd.DataFrame(
                [[i] for i in range(-99, 100)],
                columns=["X"],
            )
        ),
        Case("floats")(
            data=pd.DataFrame(
                [[float(i) + 0.5] for i in range(-99, 100)],
                columns=["X"],
            )
        ),
    )
    def test_get_bounds_inf_budget(self, spark, data):
        """Test that the get_bounds produces reasonable bounds."""

        sdf = spark.createDataFrame(data)
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(float("inf")),
            source_id="private",
            dataframe=sdf,
            protected_change=AddOneRow(),
        )

        query = QueryBuilder("private").get_bounds("X")

        got_get_bounds = session.evaluate(query, session.remaining_privacy_budget)
        assert got_get_bounds.count() == 1
        upper = got_get_bounds.first()["X_upper_bound"]
        lower = got_get_bounds.first()["X_lower_bound"]
        num_between = sdf.filter((sdf.X < upper) & (sdf.X > lower)).count()
        assert num_between > (0.9 * sdf.count())

        true_max = data["X"].max()
        true_min = data["X"].min()
        assert upper - lower < 4 * max(abs(true_max), abs(true_min))

    @parametrize(
        Case("positive")(
            data=pd.DataFrame(
                [[i] for i in range(100)],
                columns=["X"],
            )
        ),
        Case("negative")(
            data=pd.DataFrame(
                [[i] for i in range(-99, 0)],
                columns=["X"],
            )
        ),
        Case("positive_and_negative")(
            data=pd.DataFrame(
                [[i] for i in range(-99, 100)],
                columns=["X"],
            )
        ),
        Case("floats")(
            data=pd.DataFrame(
                [[float(i) + 0.5] for i in range(-99, 100)],
                columns=["X"],
            )
        ),
    )
    def test_get_bounds_inf_budget_sum(self, spark, data):
        """Test that the bounds from get_bounds produce a reasonable sum."""

        sdf = spark.createDataFrame(data)
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(float("inf")),
            source_id="private",
            dataframe=sdf,
            protected_change=AddOneRow(),
        )

        query = QueryBuilder("private").get_bounds("X")

        got_get_bounds = session.evaluate(query, session.remaining_privacy_budget)
        assert got_get_bounds.count() == 1
        upper = got_get_bounds.first()["X_upper_bound"]
        lower = got_get_bounds.first()["X_lower_bound"]

        sum_query = QueryBuilder("private").sum("X", low=lower, high=upper, name="sum")
        got_sum = session.evaluate(
            sum_query, session.remaining_privacy_budget
        ).collect()[0]["sum"]

        true_sum = data["X"].sum()

        assert (true_sum < 0) == (got_sum < 0)
        assert (0.9 * abs(true_sum) <= abs(got_sum)) and (
            1.1 * abs(true_sum) >= abs(got_sum)
        )

    @parametrize(
        Case("str_column")(
            data=pd.DataFrame(
                [["0"], ["1"], ["1"]],
                columns=["str_column"],
            ),
            column="str_column",
            protected_change=AddOneRow(),
            error_type=ValueError,
            message="Cannot get bounds for column 'str_column',"
            " which is of type VARCHAR",
        ),
        Case("missing_column")(
            data=pd.DataFrame(
                [[1], [0], [2]],
                columns=["int_column"],
            ),
            column="column_does_not_exist",
            protected_change=AddOneRow(),
            error_type=ValueError,
            message="Cannot get bounds for column 'column_does_not_exist',"
            " which does not exist",
        ),
        Case("id_column")(
            data=pd.DataFrame(
                [[0, 10], [1, 20], [2, 30]],
                columns=["id_column", "int_column"],
            ),
            column="id_column",
            protected_change=AddRowsWithID("id_column"),
            error_type=ValueError,
            message="get_bounds cannot be used on the privacy ID column",
        ),
    )
    def test_get_bounds_invalid_columns(
        self, spark, data, column, error_type, message, protected_change
    ):
        """Test that get_bounds throws appropriate errors."""

        sdf = spark.createDataFrame(data)
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(float("inf")),
            source_id="private",
            dataframe=sdf,
            protected_change=protected_change,
        )

        bad_query = QueryBuilder("private").get_bounds(column)

        with pytest.raises(error_type, match=message):
            session.evaluate(bad_query, session.remaining_privacy_budget)

    @pytest.mark.parametrize(
        "budget",
        [
            (PureDPBudget(1)),
            (ApproxDPBudget(0, 0.5)),
            (ApproxDPBudget(1, 0)),
            (RhoZCDPBudget(1)),
        ],
    )
    def test_zero_budget(self, budget: PrivacyBudget):
        """Test that a call to ``evaluate`` raises a ValueError if budget is 0."""
        query_expr = QueryBuilder("private").count(
            name="total", mechanism=CountMechanism.DEFAULT
        )
        session = Session.from_dataframe(
            privacy_budget=budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        zero_budget: PrivacyBudget
        if isinstance(budget, PureDPBudget):
            zero_budget = PureDPBudget(0)
        elif isinstance(budget, ApproxDPBudget):
            zero_budget = ApproxDPBudget(0, 0)
        else:
            zero_budget = RhoZCDPBudget(0)
        with pytest.raises(
            ValueError, match="You need a non-zero privacy budget to evaluate a query."
        ):
            session.evaluate(query_expr, privacy_budget=zero_budget)

    @pytest.mark.parametrize(
        "privacy_budget,expected",
        [
            (  # GEOMETRIC noise since integer measure_column and PureDP
                PureDPBudget(10000),
                pd.DataFrame({"sum": [12]}),
            ),
            (  # GAUSSIAN noise since RhoZCDP
                RhoZCDPBudget(10000),
                pd.DataFrame({"sum": [12]}),
            ),
            (ApproxDPBudget(10000, 1 / 2), pd.DataFrame({"sum": [12]})),
        ],
    )
    def test_create_view_with_stability(
        self, privacy_budget: PrivacyBudget, expected: pd.DataFrame
    ):
        """Smoke test for querying on views with stability changes"""
        session = Session.from_dataframe(
            privacy_budget=privacy_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        transformation_query = QueryBuilder("private").flat_map(
            f=lambda row: [{}, {}],
            new_column_types={},
            augment=True,
            max_rows=1,
        )
        session.create_view(transformation_query, "flatmap_transformation", cache=False)

        sum_query = (
            QueryBuilder("flatmap_transformation")
            .replace_null_and_nan(replace_with={})
            .sum("X", 0, 3, name="sum")
        )
        actual = session.evaluate(sum_query, privacy_budget)
        assert_frame_equal_with_sort(actual.toPandas(), expected, rtol=1)

    @pytest.mark.parametrize(
        "starting_budget,partition_budget",
        [
            (PureDPBudget(20), PureDPBudget(10)),
            (ApproxDPBudget(20, 1 / 2), ApproxDPBudget(10, 1 / 4)),
            (RhoZCDPBudget(20), RhoZCDPBudget(10)),
        ],
    )
    def test_partition_and_create(
        self, starting_budget: PrivacyBudget, partition_budget: PrivacyBudget
    ):
        """Tests using :func:`partition_and_create` to create a new session."""
        session1 = Session.from_dataframe(
            privacy_budget=starting_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        sessions = session1.partition_and_create(
            source_id="private",
            privacy_budget=partition_budget,
            column="A",
            splits={"private0": "0", "private1": "1"},
        )
        session2 = sessions["private0"]
        session3 = sessions["private1"]
        assert session1.remaining_privacy_budget == partition_budget
        assert session2.remaining_privacy_budget == partition_budget
        assert session2.private_sources == ["private0"]
        assert session2.get_schema("private0") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }

        assert session3.remaining_privacy_budget == partition_budget
        assert session3.private_sources == ["private1"]
        assert session3.get_schema("private1") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }

    def test_partition_nonexistent_table(self):
        """Partitioning on a nonexistent table works correctly."""
        sess = Session.from_dataframe(
            PureDPBudget(1), "private", self.sdf, protected_change=AddOneRow()
        )
        sess.add_public_dataframe("public", self.sdf)

        with pytest.raises(KeyError, match="Private table '.*' does not exist"):
            sess.partition_and_create(
                "nonexistent", PureDPBudget(1), "A", {"private0": "0"}
            )
        with pytest.raises(ValueError, match="Table '.*' is a public table"):
            sess.partition_and_create("public", PureDPBudget(1), "A", {"private0": "0"})

    @pytest.mark.parametrize(
        "starting_budget,partition_budget,remaining_budget",
        [
            (PureDPBudget(20), PureDPBudget(12), PureDPBudget(8)),
            (
                ApproxDPBudget(20, 1 / 4),
                ApproxDPBudget(12, 3 / 16),
                ApproxDPBudget(8, 1 / 16),
            ),
            (RhoZCDPBudget(20), RhoZCDPBudget(12), RhoZCDPBudget(8)),
        ],
    )
    def test_partition_and_create_query(
        self,
        starting_budget: PrivacyBudget,
        partition_budget: PrivacyBudget,
        remaining_budget: PrivacyBudget,
    ):
        """Querying on a partitioned session with stability>1 works."""
        session1 = Session.from_dataframe(
            privacy_budget=starting_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        transformation_query = (
            QueryBuilder("private")
            .flat_map(
                f=lambda _: [{}, {}],
                new_column_types={},
                augment=True,
                max_rows=2,
            )
            .replace_null_and_nan(replace_with={})
        )
        session1.create_view(transformation_query, "flatmap", True)

        sessions = session1.partition_and_create(
            "flatmap", partition_budget, "A", splits={"private0": "0", "private1": "1"}
        )
        session2 = sessions["private0"]
        session3 = sessions["private1"]
        assert session1.remaining_privacy_budget == remaining_budget
        assert session2.remaining_privacy_budget == partition_budget
        assert session2.private_sources == ["private0"]
        assert session2.get_schema("private0") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }
        assert session3.remaining_privacy_budget == partition_budget
        assert session3.private_sources == ["private1"]
        assert session3.get_schema("private1") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }
        query = QueryBuilder("private0").count()
        session2.evaluate(query, partition_budget)

    @pytest.mark.parametrize(
        "starting_budget,partition_budget,remaining_budget",
        [(ApproxDPBudget(20, 0.5), PureDPBudget(10), ApproxDPBudget(10, 0.5))],
    )
    def test_partition_and_create_approxDP_session_pureDP_partition(
        self,
        starting_budget: PrivacyBudget,
        partition_budget: PrivacyBudget,
        remaining_budget: PrivacyBudget,
    ):
        """Tests using :func:`partition_and_create` to create a new ApproxDP session
        that supports PureDP partitions."""

        is_approxDP_starting_budget = isinstance(starting_budget, ApproxDPBudget)
        if is_approxDP_starting_budget and isinstance(partition_budget, PureDPBudget):
            partition_budget = ApproxDPBudget(partition_budget.value, 0)

        self.test_partition_and_create_query(
            starting_budget, partition_budget, remaining_budget
        )

    @pytest.mark.parametrize(
        "inf_budget,mechanism",
        [
            (PureDPBudget(float("inf")), CountMechanism.LAPLACE),
            (ApproxDPBudget(float("inf"), 0.5), CountMechanism.LAPLACE),
            (RhoZCDPBudget(float("inf")), CountMechanism.LAPLACE),
            (RhoZCDPBudget(float("inf")), CountMechanism.GAUSSIAN),
        ],
    )
    def test_partition_and_create_correct_answer(
        self, inf_budget: PrivacyBudget, mechanism: CountMechanism
    ):
        """Using :func:`partition_and_create` gives the correct answer if budget=inf."""
        session1 = Session.from_dataframe(
            privacy_budget=inf_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        sessions = session1.partition_and_create(
            "private", inf_budget, "A", splits={"private0": "0", "private1": "1"}
        )
        session2 = sessions["private0"]
        session3 = sessions["private1"]

        answer_session2 = session2.evaluate(
            QueryBuilder("private0").count(
                mechanism=mechanism,
            ),
            inf_budget,
        )
        assert_frame_equal_with_sort(
            answer_session2.toPandas(), pd.DataFrame({"count": [3]})
        )
        answer_session3 = session3.evaluate(
            QueryBuilder("private1").count(),
            inf_budget,
        )
        assert_frame_equal_with_sort(
            answer_session3.toPandas(), pd.DataFrame({"count": [1]})
        )

    @pytest.mark.parametrize("output_measure", [(PureDP()), (ApproxDP()), (RhoZCDP())])
    def test_partitions_composed(
        self, output_measure: Union[PureDP, ApproxDP, RhoZCDP]
    ):
        """Smoke test for composing :func:`partition_and_create`."""
        root_session_budget: PrivacyBudget
        root_session_remaining_budget: PrivacyBudget
        column_A_partition_budget: PrivacyBudget
        column_A_remaining_budget: PrivacyBudget
        column_B_partition_budget: PrivacyBudget

        if output_measure == PureDP():
            root_session_budget = PureDPBudget(20)
            root_session_remaining_budget = PureDPBudget(8)
            column_A_partition_budget = PureDPBudget(12)
            column_A_remaining_budget = PureDPBudget(7)
            column_B_partition_budget = PureDPBudget(5)
        elif output_measure == ApproxDP():
            root_session_budget = ApproxDPBudget(20, 1 / 4)
            root_session_remaining_budget = ApproxDPBudget(8, 3 / 16)
            column_A_partition_budget = ApproxDPBudget(12, 1 / 16)
            column_A_remaining_budget = ApproxDPBudget(7, 3 / 64)
            column_B_partition_budget = ApproxDPBudget(5, 1 / 64)
        elif output_measure == RhoZCDP():
            root_session_budget = RhoZCDPBudget(20)
            root_session_remaining_budget = RhoZCDPBudget(8)
            column_A_partition_budget = RhoZCDPBudget(12)
            column_A_remaining_budget = RhoZCDPBudget(7)
            column_B_partition_budget = RhoZCDPBudget(5)
        else:
            pytest.fail(
                f"must use PureDP, ApproxDP, or RhoZCDP, found {output_measure}"
            )

        root_session = Session.from_dataframe(
            privacy_budget=root_session_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        transformation_query1 = (
            QueryBuilder("private")
            .flat_map(
                f=lambda row: [{}, {}],
                new_column_types={},
                augment=True,
                max_rows=2,
            )
            .replace_null_and_nan(replace_with={})
        )
        root_session.create_view(transformation_query1, "transform1", cache=False)

        first_partition_sessions = root_session.partition_and_create(
            "transform1",
            column_A_partition_budget,
            "A",
            splits={"private0": "0", "private1": "1"},
        )
        sessionA0 = first_partition_sessions["private0"]
        sessionA1 = first_partition_sessions["private1"]
        assert root_session.remaining_privacy_budget == root_session_remaining_budget
        assert sessionA0.remaining_privacy_budget == column_A_partition_budget
        assert sessionA0.private_sources == ["private0"]
        assert sessionA0.get_schema("private0") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }
        assert sessionA1.remaining_privacy_budget == column_A_partition_budget
        assert sessionA1.private_sources == ["private1"]
        assert sessionA1.get_schema("private1") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }

        transformation_query2 = (
            QueryBuilder("private0")
            .flat_map(
                f=lambda row: [{}, {}, {}],
                new_column_types={},
                augment=True,
                max_rows=2,
            )
            .replace_null_and_nan(replace_with={})
        )
        sessionA0.create_view(transformation_query2, "transform2", cache=False)

        second_parition_sessions = sessionA0.partition_and_create(
            "transform2",
            column_B_partition_budget,
            "B",
            splits={"private0": 0, "private1": 1},
        )
        sessionA0B0 = second_parition_sessions["private0"]
        sessionA0B1 = second_parition_sessions["private1"]
        assert sessionA0.remaining_privacy_budget == column_A_remaining_budget
        assert sessionA0B0.remaining_privacy_budget == column_B_partition_budget
        assert sessionA0B0.private_sources == ["private0"]
        assert sessionA0B0.get_schema("private0") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }
        assert sessionA0B1.remaining_privacy_budget == column_B_partition_budget
        assert sessionA0B1.private_sources == ["private1"]
        assert sessionA0B1.get_schema("private1") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }

    @pytest.mark.parametrize(
        "starting_budget,partition_budget",
        [
            (PureDPBudget(20), PureDPBudget(10)),
            (ApproxDPBudget(20, 1 / 2), ApproxDPBudget(10, 1 / 4)),
            (RhoZCDPBudget(20), RhoZCDPBudget(10)),
        ],
    )
    def test_partition_execution_order(
        self, starting_budget: PrivacyBudget, partition_budget: PrivacyBudget
    ):
        """Tests behavior using :func:`partition_and_create` sessions out of order."""
        session1 = Session.from_dataframe(
            privacy_budget=starting_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        sessions = session1.partition_and_create(
            source_id="private",
            privacy_budget=partition_budget,
            column="A",
            splits={"private0": "0", "private1": "1"},
        )
        session2 = sessions["private0"]
        session3 = sessions["private1"]
        assert session1.remaining_privacy_budget == partition_budget
        assert session2.remaining_privacy_budget == partition_budget
        assert session2.private_sources == ["private0"]
        assert session2.get_schema("private0") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }
        assert session3.remaining_privacy_budget == partition_budget
        assert session3.private_sources == ["private1"]
        assert session3.get_schema("private1") == {
            "A": ColumnDescriptor(ColumnType.VARCHAR),
            "B": ColumnDescriptor(ColumnType.INTEGER),
            "X": ColumnDescriptor(ColumnType.INTEGER),
        }

        # pylint: disable=protected-access
        assert session1._accountant.state == PrivacyAccountantState.WAITING_FOR_CHILDREN
        assert session2._accountant.state == PrivacyAccountantState.ACTIVE
        assert session3._accountant.state == PrivacyAccountantState.WAITING_FOR_SIBLING

        # This should work, but it should also retire session2
        select_query3 = QueryBuilder("private1").select(columns=["A"])
        session3.create_view(select_query3, "select_view", cache=False)
        assert session2._accountant.state == PrivacyAccountantState.RETIRED

        # Now trying to do operations on session2 should raise an error
        select_query2 = QueryBuilder("private0").select(columns=["A"])  # type: ignore
        with pytest.raises(
            RuntimeError,
            match=(
                "This session is no longer active, and no new queries can be performed"
            ),
        ):
            session2.create_view(select_query2, "select_view", cache=False)

        # This should work, but it should also retire session3
        select_query1 = QueryBuilder("private").select(columns=["A"])
        session1.create_view(select_query1, "select_view", cache=False)
        assert session3._accountant.state == PrivacyAccountantState.RETIRED

        # Now trying to do operations on session3 should raise an error
        with pytest.raises(
            RuntimeError,
            match=(
                "This session is no longer active, and no new queries can be performed"
            ),
        ):
            session3.create_view(select_query3, "select_view_again", cache=False)

        # pylint: enable=protected-access

    @pytest.mark.parametrize(
        "budget", [(PureDPBudget(20)), (ApproxDPBudget(20, 0.5)), (RhoZCDPBudget(20))]
    )
    def test_partition_on_flatmap_grouping_column(self, budget: PrivacyBudget):
        """Tests that you can partition on columns created by grouping flat maps."""
        session = Session.from_dataframe(
            privacy_budget=budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        grouping_flat_map = QueryBuilder("private").flat_map(
            f=lambda row: [{"new": 1}, {"new": 2}],
            new_column_types={"new": ColumnType.INTEGER},
            augment=True,
            grouping=True,
            max_rows=2,
        )
        session.create_view(grouping_flat_map, "duplicated", cache=False)
        new_sessions = session.partition_and_create(
            source_id="duplicated",
            privacy_budget=budget,
            column="new",
            splits={"new1": 1, "new2": 2},
        )
        new_sessions["new1"].evaluate(QueryBuilder("new1").count(), budget)
        new_sessions["new2"].evaluate(QueryBuilder("new2").count(), budget)

    @pytest.mark.parametrize(
        "budget", [(PureDPBudget(20)), (ApproxDPBudget(20, 0.5)), (RhoZCDPBudget(20))]
    )
    def test_partition_on_nongrouping_column(self, budget: PrivacyBudget):
        """Tests that you can partition on other columns after grouping flat maps."""
        session = Session.from_dataframe(
            privacy_budget=budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        grouping_flat_map = QueryBuilder("private").flat_map(
            f=lambda row: [{"new": 1}, {"new": 2}],
            new_column_types={"new": ColumnType.INTEGER},
            augment=True,
            grouping=True,
            max_rows=2,
        )
        session.create_view(grouping_flat_map, "duplicated", cache=False)
        new_sessions = session.partition_and_create(
            source_id="duplicated",
            privacy_budget=budget,
            column="A",
            splits={"zero": "0", "one": "1"},
        )
        keys = KeySet.from_dict({"new": [1, 2]})
        new_sessions["zero"].evaluate(
            QueryBuilder("zero").groupby(keys).count(), budget
        )
        new_sessions["one"].evaluate(QueryBuilder("one").groupby(keys).count(), budget)

    @pytest.mark.parametrize(
        "budget", [(PureDPBudget(20)), (ApproxDPBudget(20, 0.5)), (RhoZCDPBudget(20))]
    )
    def test_create_view_composed(self, budget: PrivacyBudget):
        """Composing views with :func:`create_view` works."""

        session = Session.from_dataframe(
            privacy_budget=budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        transformation_query1 = QueryBuilder("private").flat_map(
            f=lambda row: [{}, {}],
            new_column_types={},
            augment=True,
            max_rows=2,
        )
        session.create_view(transformation_query1, "flatmap1", cache=False)
        # pylint: disable=protected-access
        assert session._accountant.d_in[NamedTable("flatmap1")] == 2
        # pylint: enable=protected-access

        transformation_query2 = QueryBuilder("flatmap1").flat_map(
            f=lambda row: [{}, {}],
            new_column_types={},
            augment=True,
            max_rows=3,
        )
        session.create_view(transformation_query2, "flatmap2", cache=False)
        # pylint: disable=protected-access
        assert session._accountant.d_in[NamedTable("flatmap2")] == 6
        # pylint: enable=protected-access

    @pytest.mark.parametrize(
        "budget", [(PureDPBudget(10)), (ApproxDPBudget(10, 0.5)), (RhoZCDPBudget(10))]
    )
    def test_create_view_composed_query(self, budget: PrivacyBudget):
        """Smoke test for composing views and querying."""
        session = Session.from_dataframe(
            privacy_budget=budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        transformation_query1 = QueryBuilder("private").flat_map(
            f=lambda row: [{}, {}],
            new_column_types={},
            augment=True,
            max_rows=2,
        )
        session.create_view(transformation_query1, "flatmap1", cache=False)

        transformation_query2 = QueryBuilder("flatmap1").flat_map(
            f=lambda row: [{}, {}],
            new_column_types={},
            augment=True,
            max_rows=3,
        )
        session.create_view(transformation_query2, "flatmap2", cache=False)

        # Check that we can query on the view.
        sum_query = (
            QueryBuilder("flatmap2")
            .replace_null_and_nan(replace_with={})
            .groupby(KeySet.from_dict({}))
            .sum("X", low=0, high=3)
        )
        session.evaluate(query_expr=sum_query, privacy_budget=budget)

    @pytest.mark.parametrize(
        "inf_budget,mechanism",
        [
            (PureDPBudget(float("inf")), SumMechanism.LAPLACE),
            (ApproxDPBudget(float("inf"), 0.5), SumMechanism.LAPLACE),
            (ApproxDPBudget(0.5, 1), SumMechanism.LAPLACE),
            (RhoZCDPBudget(float("inf")), SumMechanism.LAPLACE),
            (RhoZCDPBudget(float("inf")), SumMechanism.GAUSSIAN),
        ],
    )
    def test_create_view_composed_correct_answer(
        self, inf_budget: PrivacyBudget, mechanism: SumMechanism
    ):
        """Composing :func:`create_view` gives the correct answer if budget=inf."""
        session = Session.from_dataframe(
            privacy_budget=inf_budget,
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )

        transformation_query1 = QueryBuilder("private").flat_map(
            f=lambda row: [{"Repeat": 1 if row["A"] == "0" else 2}],
            new_column_types={"Repeat": "INTEGER"},
            augment=True,
            max_rows=1,
        )
        session.create_view(transformation_query1, "flatmap1", cache=False)
        transformation_query2 = QueryBuilder("flatmap1").flat_map(
            f=lambda row: [{"i": row["X"]} for i in range(row["Repeat"])],
            new_column_types={"i": "INTEGER"},
            augment=False,
            max_rows=2,
        )
        session.create_view(transformation_query2, "flatmap2", cache=False)

        # Check that we can query on the view.
        sum_query = (
            QueryBuilder("flatmap2")
            .replace_null_and_nan(replace_with={})
            .groupby(KeySet.from_dict({}))
            .sum("i", low=0, high=3, mechanism=mechanism, name="sum")
        )
        answer = session.evaluate(sum_query, inf_budget).toPandas()
        expected = pd.DataFrame({"sum": [9]})
        assert_frame_equal_with_sort(answer, expected)

    def test_caching(self, spark):
        """Tests that caching works as expected."""
        # pylint: disable=protected-access
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(float("inf")),
            source_id="private",
            dataframe=self.sdf,
            protected_change=AddOneRow(),
        )
        # we need to add this to clear the cache in the spark session, since
        # with the addition of pytest all tests in a module share the same
        # spark context. Since there are views created in the previous test
        # the first assertion here will fail unless we clear the cache
        spark.catalog.clearCache()
        view1_query = QueryBuilder("private").filter("B = 0")
        view2_query = QueryBuilder("private").join_public(self.join_df)
        session.create_view(view1_query, "view1", cache=True)
        session.create_view(view2_query, "view2", cache=True)
        # Views have been created, but are lazy - nothing in cache yet
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 0
        # Evaluate a query on view1
        session.evaluate(QueryBuilder("view1").count(), privacy_budget=PureDPBudget(1))
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 1
        # Evaluate another query on view1
        session.evaluate(QueryBuilder("view1").count(), privacy_budget=PureDPBudget(1))
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 1
        # Evaluate a query on view2
        session.evaluate(QueryBuilder("view2").count(), privacy_budget=PureDPBudget(1))
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 2
        # Delete views
        session.delete_view("view1")
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 1
        session.delete_view("view2")
        assert len(list(spark.sparkContext._jsc.sc().getRDDStorageInfo())) == 0

    # regression test for #2491
    def test_filter_regression(self, spark) -> None:
        """Regression tests for issue 2491.

        This issue caused incorrect results when joining a dataframe with
        another dataframe derived from the first (in this case, a KeySet
        derived from the private data).
        """
        sdf = spark.createDataFrame(
            pd.DataFrame(
                [["0", 1, 100000], ["1", 0, 20000], ["1", 2, 20000]],
                columns=["A", "B", "X"],
            )
        )
        total_budget = 10
        session = Session.from_dataframe(
            privacy_budget=PureDPBudget(total_budget),
            source_id="private",
            dataframe=sdf,
            protected_change=AddOneRow(),
        )

        all_keys = KeySet.from_dataframe(sdf)
        keyset = all_keys["A", "B"]
        budget_per_query = PureDPBudget(total_budget / 3)
        expected_a_b = pd.DataFrame([["0", 1], ["1", 0], ["1", 2]], columns=["A", "B"])

        count_query = QueryBuilder("private").filter("B == 2").groupby(keyset).count()
        count_result = session.evaluate(count_query, budget_per_query)
        count_a_b = count_result.select("A", "B")
        assert_frame_equal_with_sort(count_a_b.toPandas(), expected_a_b)

        median_query = (
            QueryBuilder("private")
            .filter("B == 2")
            .groupby(keyset)
            .median("X", 0, 10**6, "dp_median")
        )
        median_result = session.evaluate(median_query, budget_per_query)
        median_a_b = median_result.select("A", "B")
        assert_frame_equal_with_sort(median_a_b.toPandas(), expected_a_b)

        average_query = (
            QueryBuilder("private")
            .filter("B == 2")
            .groupby(keyset)
            .average("X", 0, 10**6, "dp_average")
        )
        average_result = session.evaluate(average_query, budget_per_query)
        average_a_b = average_result.select("A", "B")
        assert_frame_equal_with_sort(average_a_b.toPandas(), expected_a_b)

    def test_grouping_noninteger_stability(self, spark) -> None:
        """Test that zCDP grouping_column and non-integer stabilities work."""
        grouped_df = spark.createDataFrame(
            pd.DataFrame({"id": [7, 7, 8, 9], "group": [0, 1, 0, 1]})
        )
        ks = KeySet.from_dict({"group": [0, 1]})
        query = QueryBuilder("id").groupby(ks).count()

        session = Session.from_dataframe(
            RhoZCDPBudget(float("inf")),
            "id",
            grouped_df,
            protected_change=AddMaxRowsInMaxGroups(
                grouping_column="group", max_groups=2, max_rows_per_group=1
            ),
        )
        session.evaluate(query, RhoZCDPBudget(1))
