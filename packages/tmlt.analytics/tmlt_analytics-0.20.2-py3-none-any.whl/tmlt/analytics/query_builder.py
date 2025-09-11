"""An API for building differentially private queries from basic operations."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

from __future__ import annotations

import datetime
import warnings
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

from pyspark.sql import DataFrame
from typeguard import check_type

from tmlt.analytics import AnalyticsInternalError
from tmlt.analytics._query_expr import (
    AnalyticsDefault,
    AverageMechanism,
    CountDistinctMechanism,
    CountMechanism,
    DropInfinity,
    DropNullAndNan,
    EnforceConstraint,
    Filter,
    FlatMap,
    FlatMapByID,
    GetBounds,
    GetGroups,
    GroupByBoundedAverage,
    GroupByBoundedSTDEV,
    GroupByBoundedSum,
    GroupByBoundedVariance,
    GroupByCount,
    GroupByCountDistinct,
    GroupByQuantile,
    JoinPrivate,
    JoinPublic,
    Map,
    PrivateSource,
    QueryExpr,
    Rename,
    ReplaceInfinity,
    ReplaceNullAndNan,
    Select,
    StdevMechanism,
    SumMechanism,
    SuppressAggregates,
    VarianceMechanism,
)
from tmlt.analytics._schema import ColumnDescriptor, ColumnType, FrozenDict, Schema
from tmlt.analytics.binning_spec import BinningSpec, BinT
from tmlt.analytics.config import config
from tmlt.analytics.constraints import Constraint
from tmlt.analytics.keyset import KeySet
from tmlt.analytics.truncation_strategy import TruncationStrategy

# Override exported names to include ColumnType and ColumnDescriptor, as well as
# types from _query_expr.
__all__ = [
    "Row",
    "QueryBuilder",
    "GroupedQueryBuilder",
    "ColumnDescriptor",
    "ColumnType",
    "AnalyticsDefault",
    "AverageMechanism",
    "CountMechanism",
    "CountDistinctMechanism",
    "StdevMechanism",
    "SumMechanism",
    "VarianceMechanism",
    "Query",
    "GroupbyCountQuery",
]

Row = Dict[str, Any]
"""Type alias for a dictionary with string keys."""


def _query_expr_recursive_equivalence(query: QueryExpr, other_query: QueryExpr) -> bool:
    """Checks that each attribute in both queries are equivalent (guaranteed fast)."""
    self_query_attrs = query.__dict__
    other_query_attrs = other_query.__dict__
    if len(self_query_attrs) != len(other_query_attrs):
        return False
    for key, val in self_query_attrs.items():
        if key not in other_query_attrs:
            return False
        if isinstance(val, QueryExpr):
            if not _query_expr_recursive_equivalence(val, other_query_attrs[key]):
                return False
        if isinstance(val, KeySet):
            # Check KeySet fast equality.
            if not val.is_equivalent(other_query_attrs[key]):
                return False
        elif val != other_query_attrs[key]:
            return False
    return True


@dataclass(frozen=True)
class Query:
    """A complete query, ready to be evaluated in a differentially private manner.

    A Query and its subclasses should not be directly constructed, but created
    using a :class:`~tmlt.analytics.QueryBuilder`. A Query can be passed to
    :meth:`~tmlt.analytics.Session.evaluate` in order to evaluate the query and
    obtain differentially private results.
    """

    _query_expr: QueryExpr

    def __hash__(self) -> int:
        """Hashes the query based on the underlying query expression."""
        return hash(self._query_expr)

    def __eq__(self, other: Any):
        """Determines query equitability based on the underlying query expression."""
        if isinstance(other, Query):
            return self._query_expr == other._query_expr
        else:
            return False

    def _is_equivalent(self, other: Any) -> bool:
        """Checks if two Query objects are similar.

        This method returns True in some cases when the objects are equal and False
        whenever they are unequal. A full equality check is runtime expensive so this
        feature is useful for quick equality checks, which are needed for caching. In
        some cases, this method may return False even when the objects are equal.
        """
        if not isinstance(other, Query):
            return False

        query = self._query_expr
        other_query = other._query_expr  # pylint: disable=protected-access
        return _query_expr_recursive_equivalence(query, other_query)


class _QueryProtocol(Protocol):
    @property
    def _query_expr(self) -> QueryExpr:
        ...


class _PostProcessSuppressMixin:
    """Adds a postprocess suppress method to child classes for supported Queries."""

    def suppress(
        self: _QueryProtocol,
        threshold: float,
    ) -> Query:
        """Returns a new query with an added postprocessing thresholding step.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby count query and suppressing results < 1
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1", "2"]}))
            ...     .count()
            ...     .suppress(1)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  count
            0  0      1
            1  1      2

        Args:
            threshold: Threshold value. All results with a lower value in the
                aggregated column will be suppressed.
        """
        if not isinstance(self._query_expr, GroupByCount):
            raise NotImplementedError(
                "Suppressing aggregates under a threshold is currently only "
                f"supported for GroupByCount queries, not {type(self._query_expr)}"
            )
        query_expr = SuppressAggregates(
            child=self._query_expr,
            column=self._query_expr.output_column,
            threshold=threshold,
        )
        return Query(query_expr)


class GroupbyCountQuery(Query, _PostProcessSuppressMixin):
    """Stores the plan for a differentially private groupby count calculation."""


class QueryBuilder:
    """High-level interface for specifying DP queries.

    Each instance corresponds to applying a transformation.
    The full graph of QueryBuilder objects can be traversed from root to a node.

    ..
        >>> # Implicit doctest imports will lead to `isinstance` checks failing
        >>> # (and to typeguard failures)
        >>> # so we explicitly import QueryBuilder in all our doctests here.
        >>> from tmlt.analytics import (
        ...     AddOneRow,
        ...     PureDPBudget,
        ...     QueryBuilder,
        ...     Session,
        ... )
        >>> import pandas as pd
        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> my_private_data = spark.createDataFrame(
        ...     pd.DataFrame(
        ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
        ...     )
        ... )

    Example:
        >>> my_private_data.toPandas()
           A  B  X
        0  0  1  0
        1  1  0  1
        2  1  2  1
        >>> budget = PureDPBudget(float("inf"))
        >>> sess = Session.from_dataframe(
        ...     privacy_budget=budget,
        ...     source_id="my_private_data",
        ...     dataframe=my_private_data,
        ...     protected_change=AddOneRow(),
        ... )
        >>> # Building a query
        >>> query = QueryBuilder("my_private_data").count()
        >>> # Answering the query with infinite privacy budget
        >>> answer = sess.evaluate(
        ...     query,
        ...     PureDPBudget(float("inf"))
        ... )
        >>> answer.toPandas()
           count
        0      3
    """

    def __init__(self, source_id: str):
        """Constructor.

        Args:
            source_id: The source id used in the query_expr.
        """
        self._source_id: str = source_id
        self._query_expr: QueryExpr = PrivateSource(source_id)

    def clone(self) -> QueryBuilder:  # noqa: D102
        # Returns a new QueryBuilder with the same partial query as the current one.
        # No docstring to prevent this from showing in docs.
        builder = QueryBuilder(self._source_id)
        builder._query_expr = self._query_expr  # pylint: disable=protected-access
        return builder

    def join_public(
        self,
        public_table: Union[DataFrame, str],
        join_columns: Optional[Sequence[str]] = None,
        how: str = "inner",
    ) -> "QueryBuilder":
        """Joins the table with a DataFrame or a public source.

        This operation is either an inner or left join.

        This operation performs a natural join between two tables. This means
        that the resulting table will contain all columns unique to each input
        table, along with one copy of each common column. In most cases, the
        columns have the same names they did in the input tables.

        By default, the input tables are joined on all common columns (i.e.,
        columns whose names and data types match). However if ``join_columns``
        is given, the tables will be joined only on the given columns, and the
        remaining common columns will be disambiguated in the resulting table by
        the addition of a ``_left`` or ``_right`` suffix to their names. If
        given, ``join_columns`` must contain a non-empty subset of the tables'
        common columns. For example, two tables with columns ``A,B,C`` and ``A,B,D``
        would by default be joined on columns ``A`` and ``B``, resulting in a
        table with columns ``A,B,C,D``; if ``join_columns=["B"]`` were given
        when performing this join, the resulting table would have columns
        ``A_left,A_right,B,C,D``. The order of columns in the resulting table is
        not guaranteed.

        .. note::
            Columns must share both names and data types for them to be used in
            joining. If this condition is not met, one of the data sources must be
            transformed to be eligible for joining (e.g., by using :func:`rename`
            or :func:`map`).

        Every row within a join group (i.e., every row that shares values in the join
        columns) from the private table will be joined with every row from that same
        group in the public table. For example, if a group has :math:`X` rows in the
        private table and :math:`Y` rows in the public table, then the output table
        will contain :math:`X*Y` rows for this group.

        .. note::
            Tables with a :class:`~tmlt.analytics.ProtectedChange` of
            :class:`~tmlt.analytics.AddRowsWithID` must include the
            *privacy ID* column in the join columns.

        An illustrated example can be found in the
        :ref:`Simple transformations <public-joins>` tutorial.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> public_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 0], ["0", 1], ["1", 1], ["1", 2]], columns=["A", "C"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> public_data.toPandas()
               A  C
            0  0  0
            1  0  1
            2  1  1
            3  1  2
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Create a query joining with public_data as a dataframe:
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .join_public(public_data)
            ...     .groupby(KeySet.from_dict({"C": [0, 1, 2]}))
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("C").toPandas()
               C  count
            0  0      1
            1  1      3
            2  2      2
            >>> # Alternatively, the dataframe can be added to the Session as a public
            >>> # source, and its source ID can be used to perform the join:
            >>> sess.add_public_dataframe(
            ...     source_id="my_public_data", dataframe=public_data
            ... )
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .join_public("my_public_data")
            ...     .groupby(KeySet.from_dict({"C": [0, 1, 2]}))
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("C").toPandas()
               C  count
            0  0      1
            1  1      3
            2  2      2
            >>> # The join can also be a left join. This is helpful to keep
            >>> # records which are not included in the table. One use for this
            >>> # is to find the number of records which are or are not
            >>> # included in a KeySet.
            >>> from pyspark.sql import functions as sf
            >>> my_keyset = KeySet.from_dict({"A": ["0"]})
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .join_public(
            ...         my_keyset.dataframe().withColumn("Indicator", sf.lit(1)),
            ...         how="left",
            ...     )
            ...     .groupby(KeySet.from_dict({"Indicator": [1, None]}))
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()  # pandas converts int to float if there are NaNs
               Indicator  count
            0        NaN      2
            1        1.0      1

        Args:
            public_table: A dataframe or source ID for a public source to natural join
                          with private data.
            join_columns: The columns to join on. If ``join_columns`` is not specified,
                          the tables will be joined on all common columns.
            how: The type of join to perform. Must be one of "inner" or "left".
        """
        self._query_expr = JoinPublic(
            child=self._query_expr,
            public_table=public_table,
            join_columns=tuple(join_columns) if join_columns is not None else None,
            how=how,
        )
        return self

    def join_private(
        self,
        right_operand: Union["QueryBuilder", str],
        truncation_strategy_left: Optional[TruncationStrategy.Type] = None,
        truncation_strategy_right: Optional[TruncationStrategy.Type] = None,
        join_columns: Optional[Sequence[str]] = None,
    ) -> "QueryBuilder":
        # pylint: disable=protected-access
        """Join the table with another :class:`QueryBuilder`.

        The current query can also be joined with a named private table
        (represented as a string).

        This operation is an inner, natural join, with the same behavior and
        requirements as :func:`join_public`.

        Private joins on tables with a
        :class:`~tmlt.analytics.ProtectedChange` that protects
        adding or removing rows (e.g.
        :class:`~tmlt.analytics.AddMaxRows`) require
        truncation, which is specified using the two
        :class:`~tmlt.analytics.TruncationStrategy`
        arguments.

        In contrast, operations on tables with a
        :class:`~tmlt.analytics.AddRowsWithID`
        :class:`~tmlt.analytics.ProtectedChange` do not require a
        :class:`~tmlt.analytics.TruncationStrategy`, as no
        truncation is necessary to perform the join. In this case, the join
        columns must include the privacy ID columns of both tables, and these
        privacy ID columns must have the same name, and be in the same ID space.

        An example of a private join can be found in the
        :ref:`Doing more with privacy IDs <advanced-privacy-ids>` tutorial.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> from tmlt.analytics import TruncationStrategy
            >>> sess.create_view(
            ...     QueryBuilder("my_private_data")
            ...     .select(["A", "X"])
            ...     .rename({"X": "C"}),
            ...     source_id="my_private_view",
            ...     cache=False
            ... )
            >>> # A query where only one row with each join key is kept on the left
            >>> # table, but two are kept on the right table.
            >>> query_drop_excess = (
            ...     QueryBuilder("my_private_data")
            ...     .join_private(
            ...         QueryBuilder("my_private_view"),
            ...         truncation_strategy_left=TruncationStrategy.DropExcess(1),
            ...         truncation_strategy_right=TruncationStrategy.DropExcess(2),
            ...     )
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query_drop_excess,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               count
            0      3
            >>> # A query where all rows that share a join key with another row in
            >>> # their table are dropped, in both the left and right tables.
            >>> query_drop_non_unique = (
            ...     QueryBuilder("my_private_data")
            ...     .join_private(
            ...         QueryBuilder("my_private_view"),
            ...         truncation_strategy_left=TruncationStrategy.DropNonUnique(),
            ...         truncation_strategy_right=TruncationStrategy.DropNonUnique(),
            ...     )
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query_drop_non_unique,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               count
            0      1

        Args:
            right_operand: QueryBuilder object representing the table to be joined with.
                            When calling ``query_a.join_private(query_b, ...)``, we
                            refer to ``query_a`` as the *left table* and ``query_b`` as
                            the *right table*.
                            ``query_a.join_private("table")`` is shorthand for
                            ``query_a.join_private(QueryBuilder("table"))``.
            truncation_strategy_left: Strategy for truncation of the left table.
            truncation_strategy_right: Strategy for truncation of the right table.
            join_columns: The columns to join on. If ``join_columns`` is not specified,
                          the tables will be joined on all common columns.
        """
        if isinstance(right_operand, str):
            right_operand = QueryBuilder(right_operand)
        self._query_expr = JoinPrivate(
            self._query_expr,
            right_operand._query_expr,
            truncation_strategy_left,
            truncation_strategy_right,
            tuple(join_columns) if join_columns is not None else None,
        )
        return self

    def replace_null_and_nan(
        self,
        replace_with: Optional[
            Mapping[str, Union[int, float, str, datetime.date, datetime.datetime]]
        ] = None,
    ) -> "QueryBuilder":
        """Replaces null and NaN values in specified columns.

        .. note::
            Null values *cannot* be replaced in the ID column of a table initialized
            with a :class:`~tmlt.analytics.AddRowsWithID`
            :class:`~tmlt.analytics.ProtectedChange`, nor on a column
            generated by a :meth:`~tmlt.analytics.QueryBuilder.flat_map`
            with the grouping parameter set to True.

        .. warning::
            If null values are replaced in a column, then Analytics will raise
            an error if a KeySet is used with a null value for that column.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [[None, 0, 0.0], ["1", None, 1.1], ["2", 2, None]],
            ...         columns=["A", "B", "X"],
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
                  A    B    X
            0  None  0.0  0.0
            1     1  NaN  1.1
            2     2  2.0  NaN
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a replace_null_and_nan transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .replace_null_and_nan(
            ...         replace_with={
            ...             "A": "new_value",
            ...             "B": 1234,
            ...             "X": 56.78,
            ...         },
            ...     )
            ...     .groupby(KeySet.from_dict({"A": ["new_value", "1", "2"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
                       A  count
            0          1      1
            1          2      1
            2  new_value      1

        Args:
            replace_with: A dictionary mapping column names to values used to
                replace null and NaN values.
                If None (or empty), all columns will have null and NaN
                values replaced with Analytics defaults; see :class:`AnalyticsDefault`.
        """
        if replace_with is None:
            replace_with = {}
        # this assert is for mypy
        if replace_with is None:
            raise AnalyticsInternalError("replace_with parameter is None.")
        self._query_expr = ReplaceNullAndNan(
            child=self._query_expr,
            replace_with=FrozenDict.from_dict(replace_with),
        )
        return self

    def replace_infinity(
        self, replace_with: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> "QueryBuilder":
        """Replaces +inf and -inf values in specified columns.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [
            ...             ["a1", 0, 0.0],
            ...             ["a1", None, float("-inf")],
            ...             ["a2", 2, float("inf")]
            ...         ],
            ...         columns=["A", "B", "X"],
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
                A    B    X
            0  a1  0.0  0.0
            1  a1  NaN -inf
            2  a2  2.0  inf
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a replace_infinity transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .replace_infinity(
            ...         replace_with={
            ...             "X": (-100, 100),
            ...         },
            ...     )
            ...     .groupby(KeySet.from_dict({"A": ["a1", "a2"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
                A  count
            0  a1      2
            1  a2      1

        Args:
            replace_with: A dictionary mapping column names to values used to
                replace -inf and +inf.
                If None (or empty), all columns will have infinite
                values replaced with Analytics defaults; see :class:`AnalyticsDefault`.
        """
        if replace_with is None:
            replace_with = {}
        # this assert is for mypy
        if replace_with is None:
            raise AnalyticsInternalError("replace_with parameter is None.")

        check_type(replace_with, Dict[str, Tuple[float, float]])

        self._query_expr = ReplaceInfinity(
            child=self._query_expr,
            replace_with=FrozenDict.from_dict(replace_with),
        )
        return self

    def drop_null_and_nan(self, columns: Optional[List[str]]) -> "QueryBuilder":
        """Removes rows containing null or NaN values.

        .. note::
            Null values *cannot* be dropped in the ID column of a table
            initialized with a
            :class:`~tmlt.analytics.AddRowsWithID`
            :class:`~tmlt.analytics.ProtectedChange`, nor on a
            column generated by a
            :meth:`~tmlt.analytics.QueryBuilder.flat_map` with the
            grouping parameter set to True.

        .. warning::
            If null and NaN values are dropped from a column, then Analytics will
            raise an error if a :class:`~tmlt.analytics.KeySet` that
            contains a null value is used for that column.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> from pyspark.sql.types import (
            ...     DoubleType,
            ...     LongType,
            ...     StringType,
            ...     StructField,
            ...     StructType,
            ... )
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     [["a1", 2, 0.0], ["a1", None, 1.1], ["a2", 2, None]],
            ...     schema=StructType([
            ...         StructField("A", StringType(), nullable=True),
            ...         StructField("B", LongType(), nullable=True),
            ...         StructField("X", DoubleType(), nullable=True),
            ...     ])
            ... )

        Example:
            >>> my_private_data.toPandas()
                A    B    X
            0  a1  2.0  0.0
            1  a1  NaN  1.1
            2  a2  2.0  NaN
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Count query on the original data
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["a1", "a2"], "B": [None, 2]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A", "B").toPandas()
                A    B  count
            0  a1  NaN      1
            1  a1  2.0      1
            2  a2  NaN      0
            3  a2  2.0      1
            >>> # Building a query with a transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .drop_null_and_nan(columns=["B"])
            ...     .groupby(KeySet.from_dict({"A": ["a1", "a2"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
                A  count
            0  a1      1
            1  a2      1

        Args:
            columns: A list of columns in which to look for null and NaN values.
                If ``None`` or an empty list, then *all* columns will be considered,
                meaning that if *any* column has a null/NaN value then the row it
                is in will be dropped.
        """
        if columns is None:
            columns = []
        if columns is None:
            raise AnalyticsInternalError("columns parameter is None.")
        self._query_expr = DropNullAndNan(
            child=self._query_expr, columns=tuple(columns)
        )
        return self

    def drop_infinity(self, columns: Optional[List[str]]) -> "QueryBuilder":
        """Remove rows containing infinite values.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> from pyspark.sql.types import (
            ...     DoubleType,
            ...     LongType,
            ...     StringType,
            ...     StructField,
            ...     StructType,
            ... )
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     [["a1", 1, 1.1], ["a1", 2, 0.0], ["a2", 2, float("inf")]],
            ...     schema=StructType([
            ...         StructField("A", StringType(), nullable=True),
            ...         StructField("B", LongType(), nullable=True),
            ...         StructField("X", DoubleType(), nullable=True),
            ...     ])
            ... )

        Example:
            >>> my_private_data.toPandas()
                A  B    X
            0  a1  1  1.1
            1  a1  2  0.0
            2  a2  2  inf
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Count query on the original data
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["a1", "a2"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
                A  count
            0  a1      2
            1  a2      1

            >>> # Building a query with a drop_infinity transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .drop_infinity(columns=["X"])
            ...     .groupby(KeySet.from_dict({"A": ["a1", "a2"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
                A  count
            0  a1      2
            1  a2      0

        Args:
            columns: A list of columns in which to look for positive and negative
                infinities. If ``None`` or an empty list, then *all* columns will
                be considered, meaning that if *any* column has an infinite value
                then the row it is in will be dropped.
        """
        if columns is None:
            columns = []
        if columns is None:
            raise AnalyticsInternalError("columns parameter is None.")

        self._query_expr = DropInfinity(child=self._query_expr, columns=tuple(columns))
        return self

    def rename(self, column_mapper: Dict[str, str]) -> "QueryBuilder":
        """Renames one or more columns in the table.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a rename transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .rename({"X": "C"})
            ...     .groupby(KeySet.from_dict({"C": [0, 1]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("C").toPandas()
               C  count
            0  0      1
            1  1      2

        Args:
            column_mapper: A mapping of columns to new column names.
                Columns not specified in the mapper will remain the same.
        """
        self._query_expr = Rename(
            child=self._query_expr,
            column_mapper=FrozenDict.from_dict(column_mapper),
        )
        return self

    def filter(self, condition: str) -> "QueryBuilder":
        """Filter rows matching a condition.

        The ``condition`` parameter accepts the same syntax as in PySpark's
        :meth:`~pyspark.sql.DataFrame.filter` method: valid expressions are
        those that can be used in a `WHERE clause
        <https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-where.html>`__
        in Spark SQL. Examples of valid conditions include:

        * ``age < 42``
        * ``age BETWEEN 17 AND 42``
        * ``age < 42 OR (age < 60 AND gender IS NULL)``
        * ``LENGTH(name) > 17``
        * ``favorite_color IN ('blue', 'red')``
        * ``date = '2022-03-14'``
        * ``time < '2022-01-01T12:45:00'``

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a filter transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .filter("A == '0'")
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               count
            0      1

        Args:
            condition: A string of SQL expressions specifying the filter to apply to the
                data. For example, the string "A > B" matches rows where column A is
                greater than column B.
        """
        self._query_expr = Filter(child=self._query_expr, condition=condition)
        return self

    def select(self, columns: Sequence[str]) -> "QueryBuilder":
        """Selects the specified columns, dropping the others.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> sess.get_column_types("my_private_data")
            {'A': ColumnType.VARCHAR, 'B': ColumnType.INTEGER, 'X': ColumnType.INTEGER}
            >>> # Create a new view using a select query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .select(["A", "B"])
            ... )
            >>> sess.create_view(query, "selected_data", cache=True)
            >>> # Inspect the schema of the resulting view
            >>> sess.get_column_types("selected_data")
            {'A': ColumnType.VARCHAR, 'B': ColumnType.INTEGER}

        Args:
            columns: The columns to select.
        """
        self._query_expr = Select(
            child=self._query_expr,
            columns=tuple(columns) if columns is not None else None,
        )
        return self

    def map(
        self,
        f: Callable[[Row], Row],
        new_column_types: Mapping[str, Union[ColumnDescriptor, ColumnType]],
        augment: bool = False,
    ) -> "QueryBuilder":
        """Applies a mapping function to each row.

        If the new column types are specified using
        :class:`~tmlt.analytics.ColumnType` and not
        :class:`~tmlt.analytics.ColumnDescriptor`, Tumult
        Analytics assumes that all new columns created may contain null values,
        and that DECIMAL columns may contain NaN or infinite values.

        An illustrated example can be found in the
        :ref:`Simple transformations <maps>` tutorial.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a map transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .map(
            ...         lambda row: {"new": row["B"]*2},
            ...         new_column_types={"new": ColumnType.INTEGER},
            ...         augment=True
            ...     )
            ...     .groupby(KeySet.from_dict({"new": [0, 1, 2, 3, 4]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("new").toPandas()
               new  count
            0    0      1
            1    1      0
            2    2      1
            3    3      0
            4    4      1

        Args:
            f: The function to be applied to each row.
                The function's input is a dictionary matching each column name to
                its value for that row.
                This function should return a dictionary, which should always
                have the same keys regardless of input, and the values in that
                dictionary should match the column types specified in
                ``new_column_types``. The function should not have any side effects
                (in particular, f cannot raise exceptions).
            new_column_types: Mapping from column names to types, for new columns
                produced by f. Using
                :class:`~tmlt.analytics.ColumnDescriptor`
                is preferred.
            augment: If True, add new columns to the existing dataframe (so new
                     schema = old schema + schema_new_columns).
                     If False, make the new dataframe with schema = schema_new_columns
        """
        self._query_expr = Map(
            child=self._query_expr,
            f=f,
            schema_new_columns=Schema(
                dict(new_column_types),
                grouping_column=None,
                default_allow_nan=True,
                default_allow_null=True,
                default_allow_inf=True,
            ),
            augment=augment,
        )
        return self

    def flat_map(
        self,
        f: Callable[[Row], List[Row]],
        new_column_types: Mapping[str, Union[str, ColumnDescriptor, ColumnType]],
        augment: bool = False,
        grouping: bool = False,
        max_rows: Optional[int] = None,
        max_num_rows: Optional[int] = None,
    ) -> "QueryBuilder":
        """Applies a mapping function to each row, returning zero or more rows.

        If the new column types are specified using
        :class:`~tmlt.analytics.ColumnType` and not
        :class:`~tmlt.analytics.ColumnDescriptor`, Tumult
        Analytics assumes that all new columns created may contain null values,
        and that DECIMAL columns may contain NaN or infinite values.

        The ``max_rows`` argument is ignored if the table was initialized with
        the :class:`~tmlt.analytics.AddRowsWithID`
        :class:`~tmlt.analytics.ProtectedChange`. Otherwise, it
        is required (and enforced).

        The :ref:`Simple transformations <flat-maps>` and
        :ref:`Doing more with privacy IDs <advanced-privacy-ids>` tutorials
        contain illustrated examples of flat maps.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     KeySet,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1], ["1", 3, 1]],
            ...         columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            3  1  3  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a query with a flat map transformation
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .flat_map(
            ...         lambda row: [{"i_B": i} for i in range(int(row["B"])+1)],
            ...         new_column_types={"i_B": ColumnDescriptor(
            ...             ColumnType.INTEGER, allow_null=False,
            ...         )},
            ...         augment=True,
            ...         grouping=False,
            ...         max_rows=3,
            ...     )
            ...     .groupby(KeySet.from_dict({"B": [0, 1, 2, 3]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("B").toPandas()
               B  count
            0  0      1
            1  1      2
            2  2      3
            3  3      3

        Args:
            f: The function to be applied to each row.
                The function's input is a dictionary matching a column name to
                its value for that row.
                This function should return a list of dictionaries.
                Those dictionaries should always
                have the same keys regardless of input, and the values in those
                dictionaries should match the column types specified in
                ``new_column_types``. The function should not have any side effects
                (in particular, ``f`` must not raise exceptions), and must be
                deterministic (running it multiple times on a fixed input should
                always return the same output).
            new_column_types: Mapping from column names to types, for new columns
                produced by ``f``. Using
                :class:`~tmlt.analytics.ColumnDescriptor`
                is preferred.
            augment: If True, add new columns to the existing dataframe (so new
                     schema = old schema + schema_new_columns).
                     If False, make the new dataframe with schema = schema_new_columns
            grouping: Whether this produces a new column that we want to groupby.
                If True, this requires that any groupby aggregations following this
                query include the new column as a groupby column. Only one new column
                is supported, and the new column must have distinct values for each
                input row.
            max_rows: The enforced limit on the number of rows from each ``f(row)``.
                If ``f`` produces more rows than this, only the first ``max_rows``
                rows will be in the output.
            max_num_rows: Deprecated synonym for ``max_rows``.
        """
        grouping_column: Optional[str]
        if grouping:
            if len(new_column_types) != 1:
                raise ValueError(
                    "new_column_types contains "
                    f"{len(new_column_types)} "
                    "columns, grouping flat map can only result in 1 new column"
                )
            (grouping_column,) = new_column_types
        else:
            grouping_column = None
        if max_num_rows is not None:
            if max_rows is not None:
                raise ValueError(
                    "You must use either max_rows or max_num_rows, not both"
                )
            warnings.warn(
                "max_num_rows is deprecated and will be removed in a future release",
                DeprecationWarning,
            )
            max_rows = max_num_rows
        self._query_expr = FlatMap(
            child=self._query_expr,
            f=f,
            schema_new_columns=Schema(
                dict(new_column_types),
                grouping_column=grouping_column,
                default_allow_null=True,
                default_allow_nan=True,
                default_allow_inf=True,
            ),
            augment=augment,
            max_rows=max_rows,
        )
        return self

    def flat_map_by_id(
        self,
        f: Callable[[List[Row]], List[Row]],
        new_column_types: Mapping[str, Union[str, ColumnDescriptor, ColumnType]],
    ) -> "QueryBuilder":
        """Applies a transformation to each group of records sharing an ID.

        Transforms groups of records that all share a common ID into a new group
        of records with that same ID based on a user-provided function. The
        number of rows produced does not have to match the number of input
        rows. The ID column is automatically added to the output of ``f``, but
        all other input columns are lost unless ``f`` copies them into its
        output.

        Note that this transformation is only valid on tables with the
        :class:`~tmlt.analytics.AddRowsWithID` protected change.

        If you provide only a ColumnType for the new column types, Analytics
        assumes that all new columns created may contain null values (and that
        DECIMAL columns may contain NaN or infinite values).

        ..
            >>> from tmlt.analytics import (
            ...     AddRowsWithID,
            ...     KeySet,
            ...     MaxRowsPerID,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1], ["1", 0], ["1", 1], ["1", 4]],
            ...         columns=["id", "A"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
              id  A
            0  0  1
            1  1  0
            2  1  1
            3  1  4
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddRowsWithID("id"),
            ... )
            >>> # Using flat_map_by_id, each ID's records are pre-summed before
            >>> # computing a total sum, allowing less data loss than truncating
            >>> # and clamping each row individually without having to add
            >>> # more noise.
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .flat_map_by_id(
            ...         lambda rows: [{"per_id_sum": sum(r["A"] for r in rows)}],
            ...         new_column_types={
            ...             "per_id_sum": ColumnDescriptor(
            ...                 ColumnType.INTEGER, allow_null=False,
            ...             )
            ...         },
            ...     )
            ...     .enforce(MaxRowsPerID(1))
            ...     .sum("per_id_sum", low=0, high=5, name="sum")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               sum
            0    6

        Args:
            f: The function to be applied to each group of rows.  The function's
                input is a list of dictionaries, each with one key/value
                pair per column.  This function should return a list of
                dictionaries.  Those dictionaries must each have one key/value
                pair for each column types specified in ``new_column_types``,
                and the values' types must match the column types. The
                function must not have any side effects (in particular, it must
                not raise exceptions), and must be deterministic (running it
                multiple times on a fixed input should always return the same
                output).
            new_column_types: Mapping from column names to types for the new
                columns produced by ``f``. Using
                :class:`~tmlt.analytics.ColumnDescriptor` is
                preferred. Note that while the result of this transformation
                includes the ID column, the ID column must *not* be in
                ``new_column_types``, and must *not* be included in the output
                rows from ``f``.
        """
        self._query_expr = FlatMapByID(
            child=self._query_expr,
            f=f,
            schema_new_columns=Schema(
                dict(new_column_types),
                default_allow_null=True,
                default_allow_nan=True,
                default_allow_inf=True,
            ),
        )
        return self

    def bin_column(
        self, column: str, spec: BinningSpec, name: Optional[str] = None
    ) -> "QueryBuilder":
        """Creates a new column by assigning the values in a given column to bins.

        An illustrated example can be found in the
        :ref:`Simple transformations <binning>` tutorial.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     KeySet,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> from pyspark.sql import SparkSession
            >>> import pandas as pd
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         {
            ...             "age": [11, 17, 30, 18, 59, 48, 76, 91, 48, 53],
            ...             "income": [0, 6, 54, 14, 126, 163, 151, 18, 97, 85],
            ...         }
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               age  income
            0   11       0
            1   17       6
            2   30      54
            3   18      14
            4   59     126
            5   48     163
            6   76     151
            7   91      18
            8   48      97
            9   53      85
            >>> from tmlt.analytics import BinningSpec
            >>> sess = Session.from_dataframe(
            ...     PureDPBudget(float("inf")),
            ...     source_id="private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> age_binspec = BinningSpec(
            ...     [0, 18, 65, 100], include_both_endpoints=False
            ... )
            >>> income_tax_rate_binspec = BinningSpec(
            ...     [0, 10, 40, 86, 165], names=[10, 12, 22, 24]
            ... )
            >>> keys = KeySet.from_dict(
            ...     {
            ...         "age_binned": age_binspec.bins(),
            ...         "marginal_tax_rate": income_tax_rate_binspec.bins()
            ...     }
            ... )
            >>> query = (
            ...     QueryBuilder("private_data")
            ...     .bin_column("age", age_binspec)
            ...     .bin_column(
            ...         "income", income_tax_rate_binspec, name="marginal_tax_rate"
            ...     )
            ...     .groupby(keys).count()
            ... )
            >>> answer = sess.evaluate(query, PureDPBudget(float("inf")))
            >>> answer.sort("age_binned", "marginal_tax_rate").toPandas()
               age_binned  marginal_tax_rate  count
            0     (0, 18]                 10      2
            1     (0, 18]                 12      1
            2     (0, 18]                 22      0
            3     (0, 18]                 24      0
            4    (18, 65]                 10      0
            5    (18, 65]                 12      0
            6    (18, 65]                 22      2
            7    (18, 65]                 24      3
            8   (65, 100]                 10      0
            9   (65, 100]                 12      1
            10  (65, 100]                 22      0
            11  (65, 100]                 24      1

        Args:
            column: Name of the column used to assign bins.
            spec: A :class:`~tmlt.analytics.BinningSpec` that defines the
                binning operation to be performed.
            name: The name of the column that will be created. If None (the default),
                the input column name with ``_binned`` appended to it.
        """
        if name is None:
            name = f"{column}_binned"
        binning_fn = lambda row: {name: spec(row[column])}
        return self.map(
            binning_fn,
            new_column_types={name: spec.column_descriptor},
            augment=True,
        )

    def histogram(
        self,
        column: str,
        bin_edges: Union[Sequence[BinT], BinningSpec],
        name: Optional[str] = None,
    ) -> Query:
        """Returns a count query containing the frequency of values in specified column.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     KeySet,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> from pyspark.sql import SparkSession
            >>> import pandas as pd
            >>> spark = SparkSession.builder.getOrCreate()

        Example:
            >>> from tmlt.analytics import BinningSpec
            >>> private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         {
            ...          "income_thousands": [83, 85, 86, 73, 82, 95,
            ...                               74, 92, 71, 86, 97]
            ...         }
            ...     )
            ... )
            >>> session = Session.from_dataframe(
            ...     privacy_budget=PureDPBudget(epsilon=float('inf')),
            ...     source_id="private_data",
            ...     dataframe=private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> income_binspec = BinningSpec(
            ...     bin_edges=[i for i in range(70,110,10)],
            ...     include_both_endpoints=False
            ... )
            >>> binned_income_count_query = (
            ...     QueryBuilder("private_data")
            ...     .histogram("income_thousands", income_binspec, "income_binned")
            ... )
            >>> binned_income_counts = session.evaluate(
            ...     binned_income_count_query,
            ...     privacy_budget=PureDPBudget(epsilon=10),
            ... )
            >>> print(binned_income_counts.sort("income_binned").toPandas())
              income_binned  count
            0      (70, 80]      3
            1      (80, 90]      5
            2     (90, 100]      3

        Args:
            column: Name of the column used to assign bins.
            bin_edges: The bin edges for the histogram; provided as either a
                :class:`~tmlt.analytics.BinningSpec` or as a list of
                :class:`supported data types <tmlt.analytics.ColumnType>`.
                Values outside the range of the provided bins, ``None`` types,
                and NaN values are all mapped to ``None`` (``null`` in Spark).

            name: The name of the column that will be created. If None (the default),
                the input column name with ``_binned`` appended to it.
        """
        if not isinstance(bin_edges, BinningSpec):
            spec = BinningSpec(bin_edges)
        else:
            spec = bin_edges
        if not name:
            name = column + "_binned"

        keys = KeySet.from_dict({name: spec.bins()})
        return self.bin_column(column, spec, name).groupby(keys).count()

    def enforce(self, constraint: Constraint) -> "QueryBuilder":
        """Enforces a :class:`~tmlt.analytics.Constraint` on the table.

        This method can be used to enforce constraints on the current table. See the
        :ref:`API reference<constraints>` for information about the available
        constraints and what they are used for.

        ..
            >>> from tmlt.analytics import (
            ...     AddRowsWithID,
            ...     MaxRowsPerID,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]],
            ...         columns=["id", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
              id  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> sess = (
            ...     Session.Builder()
            ...     .with_privacy_budget(PureDPBudget(float("inf")))
            ...     .with_id_space("a")
            ...     .with_private_dataframe(
            ...         "my_private_data",
            ...         my_private_data,
            ...         protected_change=AddRowsWithID("id", "a"),
            ...     )
            ...     .build()
            ... )
            >>> # No ID contributes more than 2 rows, so no rows are dropped when
            >>> # enforcing the constraint
            >>> query = QueryBuilder("my_private_data").enforce(MaxRowsPerID(2)).count()
            >>> sess.evaluate(query, sess.remaining_privacy_budget).toPandas()
               count
            0      3
            >>> # ID 1 contributes more than one row, so one of the rows with ID 1 will
            >>> # be dropped when enforcing the constraint
            >>> query = QueryBuilder("my_private_data").enforce(MaxRowsPerID(1)).count()
            >>> sess.evaluate(query, sess.remaining_privacy_budget).toPandas()
               count
            0      2

        Args:
            constraint: The constraint to enforce.
        """
        self._query_expr = EnforceConstraint(
            self._query_expr, constraint, options=FrozenDict.from_dict({})
        )
        return self

    def get_groups(self, columns: Optional[List[str]] = None) -> Query:
        """Returns a query that gets combinations of values in the listed columns.

        .. note::
            Because this uses differential privacy, it won't include all of the values
            in the input dataset columns, and may even return no results at all on
            datasets that have few values for each set of group keys.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     ApproxDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()

        Example:
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0] for _ in range(10000)]
            ...         + [["1", 2, 1] for _ in range(10000)],
            ...         columns=["A", "B", "X"],
            ...     )
            ... )
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=ApproxDPBudget(1, 1e-5),
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a get_groups query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .get_groups()
            ... )
            >>> # Answering the query
            >>> answer = sess.evaluate(
            ...     query,
            ...     sess.remaining_privacy_budget
            ... )
            >>> answer.toPandas()
               A  B  X
            0  0  1  0
            1  1  2  1

        Args:
            columns: Name of the column used to assign bins. If empty or none
                are provided, all of the columns in the table will be used, excluding
                any column marked as a *privacy ID* in a table with a
                :class:`~tmlt.analytics.ProtectedChange` of
                :class:`~tmlt.analytics.AddRowsWithID`.
        """
        cols = tuple(columns) if columns is not None else None
        query_expr = GetGroups(child=self._query_expr, columns=cols)
        return Query(query_expr)

    def get_bounds(
        self,
        column: str,
        lower_bound_column: Optional[str] = None,
        upper_bound_column: Optional[str] = None,
    ) -> Query:
        """Returns a query that gets approximate upper and lower bounds for a column.

        The bounds are selected to give good performance when used as upper and lower
        bounds in other aggregations. They may not be close to the actual maximum and
        minimum values, and are not designed to give a tight representation of the data
        distribution. For any purpose other than providing a lower and upper bound to
        other aggregations we suggest using the quantile aggregation instead.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            The algorithm is approximate, and differentially private, so the bounds
            may not be tight, and not all input values may fall between them.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()

        Example:
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [[i] for i in range(100)],
            ...         columns=["X"],
            ...     )
            ... )
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=PureDPBudget(float('inf')),
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a get_groups query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .get_bounds("X")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     sess.remaining_privacy_budget
            ... )
            >>> answer.toPandas()
               X_upper_bound  X_lower_bound
            0            128           -128

        Args:
            column: Name of the column whose bounds we want to get.
            lower_bound_column: Name of the column to store the lower bound. Defaults to
                ``f"{column}_lower_bound"``.
            upper_bound_column: Name of the column to store the upper bound. Defaults to
                ``f"{column}_upper_bound"``.
        """
        return self.groupby(KeySet.from_dict({})).get_bounds(
            column=column,
            lower_bound_column=lower_bound_column,
            upper_bound_column=upper_bound_column,
        )

    def groupby(self, by: Union[KeySet, List[str], str]) -> "GroupedQueryBuilder":
        """Groups the query by the given set of keys, returning a GroupedQueryBuilder.

        The aggregation will return one row for each key in the KeySet; other
        values present in the data will be discarded.

        More information can be found in the :ref:`Group-by queries<group-by-queries>`
        tutorial.

        .. warning::
            A KeySet containing null values for a column cannot be used on a table where
            that column has had null values dropped or replaced.
        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     ApproxDPBudget,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Examples:
            >>> from tmlt.analytics import KeySet
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )

        Answering a query with the exact groupby domain:
            >>> groupby_keys = KeySet.from_dict({"A": ["0", "1"]})
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(groupby_keys)
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  count
            0  0      1
            1  1      2

        Answering a query with omitted and added domain values:
            >>> groupby_keys = KeySet.from_dict({"A": ["0", "2"]})
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(groupby_keys)
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               A  count
            0  0      1
            1  2      0

        Answering a query with a multi-column domain:
            >>> groupby_keys = KeySet.from_dict(
            ...    {"A": ["0", "1"], "B": [0, 1, 2]}
            ... )
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(groupby_keys)
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A", "B").toPandas()
               A  B  count
            0  0  0      0
            1  0  1      1
            2  0  2      0
            3  1  0      1
            4  1  1      0
            5  1  2      1

        Answering a query with a multi-column domain and structural zeros:
            >>> # Suppose it is known that A and B cannot be equal. This set of
            >>> # groupby keys prevents those impossible values from being computed.
            >>> keys_df = pd.DataFrame({
            ...     "A": ["0", "0", "1", "1"],
            ...     "B": [1, 2, 0, 2],
            ... })
            >>> groupby_keys = KeySet.from_dataframe(spark.createDataFrame(keys_df))
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(groupby_keys)
            ...     .count()
            ... )
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A", "B").toPandas()
               A  B  count
            0  0  1      1
            1  0  2      0
            2  1  0      1
            3  1  2      1

        Args:
            by: A KeySet which defines the columns to group on and the possible values
                for each column.
        """
        if not (isinstance(by, KeySet) or config.features.auto_partition_selection):
            raise ValueError("A groupby must group on a KeySet. Set `by` to a KeySet")

        if isinstance(by, str):
            # If a string was passed we'll treat it similarly to a list of cols.
            grouped_on: Union[KeySet, Tuple[str, ...]] = tuple([by])
        elif isinstance(by, list):
            grouped_on = tuple(by)
        else:
            grouped_on = by

        return GroupedQueryBuilder(
            source_id=self._source_id,
            query_expr=self._query_expr,
            groupby_keys=grouped_on,
        )

    def count(
        self,
        name: Optional[str] = None,
        mechanism: CountMechanism = CountMechanism.DEFAULT,
    ) -> Query:
        """Returns a count query ready to be evaluated.

        .. note::
            Differentially private counts may return values that are not
            possible for a non-DP query - including negative values. You can enforce
            non-negativity once the query returns its results; see the example below.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a count query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               count
            0      3
            >>> # Ensuring all results are non-negative
            >>> import pyspark.sql.functions as sf
            >>> answer = answer.withColumn(
            ...     "count", sf.when(sf.col("count") < 0, 0).otherwise(
            ...             sf.col("count")
            ...     )
            ... )
            >>> answer.toPandas()
               count
            0      3

        Args:
            name: Name for the resulting aggregation column. Defaults to "count".
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        return self.groupby(KeySet.from_dict({})).count(name=name, mechanism=mechanism)

    def count_distinct(
        self,
        columns: Optional[List[str]] = None,
        name: Optional[str] = None,
        mechanism: CountDistinctMechanism = CountDistinctMechanism.DEFAULT,
        cols: Optional[List[str]] = None,
    ) -> Query:
        """Returns a count_distinct query ready to be evaluated.

        .. note::
            Differentially private counts may returns values that are not
            possible for a non-DP query - including negative values. You can enforce
            non-negativity once the query returns its results; see the example below.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["0", 1, 0], ["1", 0, 1], ["1", 2, 1]],
            ...         columns=["A", "B", "X"],
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  0  1  0
            2  1  0  1
            3  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a count_distinct query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .count_distinct()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               count_distinct
            0               3
            >>> # Ensuring all results are non-negative
            >>> import pyspark.sql.functions as sf
            >>> answer = answer.withColumn(
            ...     "count_distinct", sf.when(
            ...         sf.col("count_distinct") < 0, 0
            ...     ).otherwise(
            ...         sf.col("count_distinct")
            ...     )
            ... )
            >>> answer.toPandas()
               count_distinct
            0               3

        Args:
            columns: Columns in which to count distinct values. If none are provided,
                the query will count every distinct row.
            name: Name for the resulting aggregation column. Defaults to
                "count_distinct" if no columns are provided, or
                "count_distinct(A, B, C)" if the provided columns are A, B, and C.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
            cols: Deprecated; use ``columns`` instead.
        """
        return self.groupby(KeySet.from_dict({})).count_distinct(
            columns=columns, name=name, mechanism=mechanism, cols=cols
        )

    def quantile(
        self,
        column: str,
        quantile: float,
        low: float,
        high: float,
        name: Optional[str] = None,
    ) -> Query:
        """Returns a quantile query ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER = '1.331107'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .quantile(column="B", quantile=0.6, low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas() # doctest: +ELLIPSIS
               B_quantile(0.6)
            0         1.331107

        Args:
            column: The column to compute the quantile over.
            quantile: A number between 0 and 1 specifying the quantile to compute.
                For example, 0.5 would compute the median.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low`` is
                less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_quantile({quantile})"``.
        """
        return self.groupby(KeySet.from_dict({})).quantile(
            column=column, quantile=quantile, low=low, high=high, name=name
        )

    def min(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a quantile query requesting a minimum value, ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER = '0.213415'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .min(column="B", low=0, high=5, name="min_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                  min_B
            0  0.213415

        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low`` is
                less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_min"``.
        """
        return self.groupby(KeySet.from_dict({})).min(
            column=column, low=low, high=high, name=name
        )

    def max(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a quantile query requesting a maximum value, ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER='2.331871'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .max(column="B", low=0, high=5, name="max_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                  max_B
            0  2.331871

        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_max"``.
        """
        return self.groupby(KeySet.from_dict({})).max(
            column=column, low=low, high=high, name=name
        )

    def median(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a quantile query requesting a median value, ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER='1.221197'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .median(column="B", low=0, high=5, name="median_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
               median_B
            0  1.221197


        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_median"``.
        """
        return self.groupby(KeySet.from_dict({})).median(
            column=column, low=low, high=high, name=name
        )

    def sum(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: SumMechanism = SumMechanism.DEFAULT,
    ) -> Query:
        """Returns a sum query ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a sum query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .sum(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               B_sum
            0      3

        Args:
            column: The column to compute the sum over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_sum"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        return self.groupby(KeySet.from_dict({})).sum(
            column=column, low=low, high=high, name=name, mechanism=mechanism
        )

    def average(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: AverageMechanism = AverageMechanism.DEFAULT,
    ) -> Query:
        """Returns an average query ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building an average query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .average(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               B_average
            0        1.0

        Args:
            column: The column to compute the average over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_average"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        return self.groupby(KeySet.from_dict({})).average(
            column=column, low=low, high=high, name=name, mechanism=mechanism
        )

    def variance(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: VarianceMechanism = VarianceMechanism.DEFAULT,
    ) -> Query:
        """Returns a variance query ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a variance query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .variance(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               B_variance
            0         1.0

        Args:
            column: The column to compute the variance over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_variance"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        return self.groupby(KeySet.from_dict({})).variance(
            column=column, low=low, high=high, name=name, mechanism=mechanism
        )

    def stdev(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: StdevMechanism = StdevMechanism.DEFAULT,
    ) -> Query:
        """Returns a standard deviation query ready to be evaluated.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~drop_null_and_nan` query will be performed first. If the
            column being measured contains infinite values, a
            :meth:`~drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a standard deviation query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .stdev(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.toPandas()
               B_stdev
            0      1.0

        Args:
            column: The column to compute the stdev over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_stdev"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        return self.groupby(KeySet.from_dict({})).stdev(
            column=column, low=low, high=high, name=name, mechanism=mechanism
        )


class GroupedQueryBuilder:
    """A QueryBuilder that is grouped by a set of columns and can be aggregated."""

    def __init__(self, source_id, query_expr, groupby_keys) -> None:
        """Constructor.

        Do not construct directly; use :func:`~QueryBuilder.groupby`.
        """
        # pylint: disable=pointless-string-statement
        """
        Args:
            source_id: The source id used in the query_expr.
            query_expr: A query expression describing transformations before the
                application of a GroupedQueryBuilder.
            groupby_keys: A KeySet giving the possible combinations of values for
                the groupby columns.
        """
        self._source_id: str = source_id
        self._query_expr: QueryExpr = query_expr
        self._groupby_keys: Union[KeySet, Tuple[str]] = groupby_keys

    def count(
        self,
        name: Optional[str] = None,
        mechanism: CountMechanism = CountMechanism.DEFAULT,
    ) -> GroupbyCountQuery:
        """Returns a GroupedCountQuery with a count query.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby count query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .count()
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  count
            0  0      1
            1  1      2

        Args:
            name: Name for the resulting aggregation column. Defaults to "count".
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        if name is None:
            name = "count"
        query_expr = GroupByCount(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            output_column=name,
            mechanism=mechanism,
        )
        return GroupbyCountQuery(query_expr)

    def count_distinct(
        self,
        columns: Optional[List[str]] = None,
        name: Optional[str] = None,
        mechanism: CountDistinctMechanism = CountDistinctMechanism.DEFAULT,
        cols: Optional[List[str]] = None,
    ) -> Query:
        """Returns a Query with a count_distinct query.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["0", 1, 0], ["1", 0, 1], ["1", 2, 1]],
            ...         columns=["A", "B", "X"],
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  0  1  0
            2  1  0  1
            3  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby count_distinct query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .count_distinct(["B", "X"])
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  count_distinct(B, X)
            0  0                     1
            1  1                     2

        Args:
            columns: Columns in which to count distinct values. If none are provided,
                the query will count every distinct row.
            name: Name for the resulting aggregation column. Defaults to
                "count_distinct" if no columns are provided, or
                "count_distinct(A, B, C)" if the provided columns are A, B, and C.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
            cols: Deprecated; use ``columns`` instead.
        """
        if cols is not None:
            warnings.warn(
                "The `cols` argument is deprecated; use `columns` instead",
                DeprecationWarning,
            )
            if columns is not None:
                raise ValueError(
                    "cannot provide both `cols` and `columns` arguments to"
                    " count_distinct"
                )
            columns = cols
        columns_to_count: Optional[List[str]] = None
        if columns is not None and len(columns) > 0:
            columns_to_count = list(columns)
        if not name:
            if columns_to_count:
                name = f"count_distinct({', '.join(columns_to_count)})"
            else:
                name = "count_distinct"
        query_expr = GroupByCountDistinct(
            child=self._query_expr,
            columns_to_count=tuple(columns_to_count) if columns_to_count else None,
            groupby_keys=self._groupby_keys,
            output_column=name,
            mechanism=mechanism,
        )
        return Query(query_expr)

    def quantile(
        self,
        column: str,
        quantile: float,
        low: float,
        high: float,
        name: Optional[str] = None,
    ) -> Query:
        """Returns a Query with a quantile query.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER = '1.331107'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .quantile(column="B", quantile=0.6, low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas() # doctest: +ELLIPSIS
               A  B_quantile(0.6)
            0  0         1.331107
            1  1         1.331107

        Args:
            column: The column to compute the quantile over.
            quantile: A number between 0 and 1 specifying the quantile to compute.
                For example, 0.5 would compute the median.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_quantile({quantile})"``.
        """
        if name is None:
            name = f"{column}_quantile({quantile})"
        low = low if isinstance(low, float) else float(low)
        high = high if isinstance(high, float) else float(high)
        query_expr = GroupByQuantile(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            quantile=quantile,
            low=low,
            high=high,
            output_column=name,
        )
        return Query(query_expr)

    def min(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a Query with a quantile query requesting a minimum value.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER = '0.213415'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .min(column="B", low=0, high=5, name="min_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
               A     min_B
            0  0  0.213415
            1  1  0.213415

        ..
            >>> # Reset the ellipsis marker
            >>> doctest.ELLIPSIS_MARKER = '...'

        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_min"``.
        """
        if not name:
            name = f"{column}_min"
        return self.quantile(column=column, quantile=0, low=low, high=high, name=name)

    def max(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a Query with a quantile query requesting a maximum value.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER='2.331871'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .max(column="B", low=0, high=5, name="max_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
               A     max_B
            0  0  2.331871
            1  1  2.331871

        ..
            >>> # Reset the ellipsis marker
            >>> doctest.ELLIPSIS_MARKER = '...'

        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_max"``.
        """
        if not name:
            name = f"{column}_max"
        return self.quantile(column=column, quantile=1, low=low, high=high, name=name)

    def median(
        self, column: str, low: float, high: float, name: Optional[str] = None
    ) -> Query:
        """Returns a Query with a quantile query requesting a median value.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )
            >>> import doctest
            >>> doctest.ELLIPSIS_MARKER='1.221197'

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a quantile query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .median(column="B", low=0, high=5, name="median_B")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
               A  median_B
            0  0  1.221197
            1  1  1.221197


        Args:
            column: The column to compute the quantile over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_median"``.
        """
        if not name:
            name = f"{column}_median"
        return self.quantile(column=column, quantile=0.5, low=low, high=high, name=name)

    def sum(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: SumMechanism = SumMechanism.DEFAULT,
    ) -> Query:
        """Returns a Query with a sum query.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby sum query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .sum(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  B_sum
            0  0      1
            1  1      2

        Args:
            column: The column to compute the sum over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_sum"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        if name is None:
            name = f"{column}_sum"
        query_expr = GroupByBoundedSum(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            low=low,
            high=high,
            output_column=name,
            mechanism=mechanism,
        )
        return Query(query_expr)

    def average(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: AverageMechanism = AverageMechanism.DEFAULT,
    ) -> Query:
        """Returns a Query with an average query.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby average query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .average(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  B_average
            0  0        1.0
            1  1        1.0

        Args:
            column: The column to compute the average over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_average"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        if name is None:
            name = f"{column}_average"
        query_expr = GroupByBoundedAverage(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            low=low,
            high=high,
            output_column=name,
            mechanism=mechanism,
        )
        return Query(query_expr)

    def variance(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: VarianceMechanism = VarianceMechanism.DEFAULT,
    ) -> Query:
        """Returns a Query with a variance query.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> import numpy as np
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby variance query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .variance(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  B_variance
            0  0         NaN
            1  1         1.0

        Args:
            column: The column to compute the variance over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_variance"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        if name is None:
            name = f"{column}_variance"
        query_expr = GroupByBoundedVariance(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            low=low,
            high=high,
            output_column=name,
            mechanism=mechanism,
        )
        return Query(query_expr)

    def stdev(
        self,
        column: str,
        low: float,
        high: float,
        name: Optional[str] = None,
        mechanism: StdevMechanism = StdevMechanism.DEFAULT,
    ) -> Query:
        """Returns a Query with a standard deviation query.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            Regarding the clamping bounds:

            #. The values for ``low`` and ``high`` are a choice the caller must make.
            #. All data will be clamped to lie within this range.
            #. The narrower the range, the less noise. Larger bounds mean more data \
                is kept, but more noise needs to be added to the result.
            #. The clamping bounds are assumed to be public information. Avoid using \
                the private data to set these values.

            Consult the :ref:`Numerical aggregations <clamping-bounds>` tutorial
            for more information.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 1], ["1", 2, 1]], columns=["A", "B", "X"]
            ...     )
            ... )

        Example:
            >>> my_private_data.toPandas()
               A  B  X
            0  0  1  0
            1  1  0  1
            2  1  2  1
            >>> budget = PureDPBudget(float("inf"))
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=budget,
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a groupby standard deviation query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .stdev(column="B",low=0, high=2)
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     PureDPBudget(float("inf"))
            ... )
            >>> answer.sort("A").toPandas()
               A  B_stdev
            0  0      NaN
            1  1      1.0

        Args:
            column: The column to compute the stdev over.
            low: The lower bound for clamping.
            high: The upper bound for clamping. Must be such that ``low``
                is less than ``high``.
            name: The name to give the resulting aggregation column. Defaults to
                ``f"{column}_stdev"``.
            mechanism: Choice of noise mechanism. By default, the framework
                automatically selects an appropriate mechanism.
        """
        if name is None:
            name = f"{column}_stdev"
        query_expr = GroupByBoundedSTDEV(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            low=low,
            high=high,
            output_column=name,
            mechanism=mechanism,
        )
        return Query(query_expr)

    def get_bounds(
        self,
        column: str,
        lower_bound_column: Optional[str] = None,
        upper_bound_column: Optional[str] = None,
    ) -> Query:
        """Returns an Query that gets approximate upper and lower bounds for a column.

        The bounds are selected to give good performance when used as upper and lower
        bounds in other aggregations. They may not be close to the actual maximum and
        minimum values, and are not designed to give a tight representation of the data
        distribution. For any purpose other than providing a lower and upper bound to
        other aggregations we suggest using the quantile aggregation instead.

        .. note::
            If the column being measured contains NaN or null values, a
            :meth:`~QueryBuilder.drop_null_and_nan` query will be performed
            first. If the column being measured contains infinite values, a
            :meth:`~QueryBuilder.drop_infinity` query will be performed first.

        .. note::
            The algorithm is approximate, and differentially private, so the bounds
            may not be tight, and not all input values may fall between them.

        ..
            >>> from tmlt.analytics import (
            ...     AddOneRow,
            ...     PureDPBudget,
            ...     QueryBuilder,
            ...     Session,
            ... )
            >>> import pandas as pd
            >>> from pyspark.sql import SparkSession
            >>> spark = SparkSession.builder.getOrCreate()

        Example:
            >>> my_private_data = spark.createDataFrame(
            ...     pd.DataFrame(
            ...         [["0", 1, 0], ["1", 0, 10], ["1", 2, 10], ["2", 2, 1]],
            ...         columns=["A", "B", "X"]
            ...     )
            ... )
            >>> sess = Session.from_dataframe(
            ...     privacy_budget=PureDPBudget(float('inf')),
            ...     source_id="my_private_data",
            ...     dataframe=my_private_data,
            ...     protected_change=AddOneRow(),
            ... )
            >>> # Building a get_groups query
            >>> query = (
            ...     QueryBuilder("my_private_data")
            ...     .groupby(KeySet.from_dict({"A": ["0", "1"]}))
            ...     .get_bounds(column="X")
            ... )
            >>> # Answering the query with infinite privacy budget
            >>> answer = sess.evaluate(
            ...     query,
            ...     sess.remaining_privacy_budget
            ... )
            >>> answer.sort("A").toPandas()
               A  X_upper_bound  X_lower_bound
            0  0              1             -1
            1  1             16            -16

        Args:
            column: Name of the column whose bounds we want to get.
            lower_bound_column: Name of the column to store the lower bound. Defaults to
                ``f"{column}_lower_bound"``.
            upper_bound_column: Name of the column to store the upper bound. Defaults to
                ``f"{column}_upper_bound"``.
        """
        if lower_bound_column is None:
            lower_bound_column = f"{column}_lower_bound"
        if upper_bound_column is None:
            upper_bound_column = f"{column}_upper_bound"
        query_expr = GetBounds(
            child=self._query_expr,
            groupby_keys=self._groupby_keys,
            measure_column=column,
            lower_bound_column=lower_bound_column,
            upper_bound_column=upper_bound_column,
        )
        return Query(query_expr)
