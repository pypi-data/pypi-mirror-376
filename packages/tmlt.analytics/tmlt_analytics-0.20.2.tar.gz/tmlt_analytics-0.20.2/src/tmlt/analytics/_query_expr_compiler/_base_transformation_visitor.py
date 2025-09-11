"""Defines a base class for visitors for transformations."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

import dataclasses
import datetime
import warnings
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Type, Union

from pyspark.sql import DataFrame
from tmlt.core.domains.collections import DictDomain, ListDomain
from tmlt.core.domains.spark_domains import SparkDataFrameDomain, SparkRowDomain
from tmlt.core.measurements.aggregations import NoiseMechanism
from tmlt.core.metrics import (
    AddRemoveKeys,
    DictMetric,
    HammingDistance,
    IfGroupedBy,
    Metric,
    RootSumOfSquared,
    SumOf,
    SymmetricDifference,
)
from tmlt.core.transformations.base import Transformation
from tmlt.core.transformations.converters import HammingDistanceToSymmetricDifference
from tmlt.core.transformations.dictionary import (
    AugmentDictTransformation,
    CreateDictFromValue,
    Subset,
    create_copy_and_transform_value,
)
from tmlt.core.transformations.identity import Identity as IdentityTransformation
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    DropInfsValue as DropInfsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    DropNaNsValue as DropNaNsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    DropNullsValue as DropNullsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    FilterValue as FilterValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    FlatMapByKeyValue as FlatMapByKeyValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    FlatMapValue as FlatMapValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    MapValue as MapValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    PublicJoinValue as PublicJoinValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    RenameValue as RenameValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    ReplaceInfsValue as ReplaceInfsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    ReplaceNaNsValue as ReplaceNaNsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    ReplaceNullsValue as ReplaceNullsValueTransformation,
)
from tmlt.core.transformations.spark_transformations.add_remove_keys import (
    SelectValue as SelectValueTransformation,
)
from tmlt.core.transformations.spark_transformations.filter import (
    Filter as FilterTransformation,
)
from tmlt.core.transformations.spark_transformations.join import (
    PrivateJoin as PrivateJoinTransformation,
)
from tmlt.core.transformations.spark_transformations.join import (
    PrivateJoinOnKey as PrivateJoinOnKeyTransformation,
)
from tmlt.core.transformations.spark_transformations.join import (
    PublicJoin as PublicJoinTransformation,
)
from tmlt.core.transformations.spark_transformations.join import (
    TruncationStrategy as CoreTruncationStrategy,
)
from tmlt.core.transformations.spark_transformations.map import (
    FlatMap as FlatMapTransformation,
)
from tmlt.core.transformations.spark_transformations.map import GroupingFlatMap
from tmlt.core.transformations.spark_transformations.map import Map as MapTransformation
from tmlt.core.transformations.spark_transformations.map import (
    RowsToRowsTransformation,
    RowToRowsTransformation,
    RowToRowTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    DropInfs as DropInfTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    DropNaNs as DropNaNsTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    DropNulls as DropNullsTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    ReplaceInfs as ReplaceInfsTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    ReplaceNaNs as ReplaceNaNsTransformation,
)
from tmlt.core.transformations.spark_transformations.nan import (
    ReplaceNulls as ReplaceNullsTransformation,
)
from tmlt.core.transformations.spark_transformations.rename import (
    Rename as RenameTransformation,
)
from tmlt.core.transformations.spark_transformations.select import (
    Select as SelectTransformation,
)

from tmlt.analytics import AnalyticsInternalError
from tmlt.analytics._catalog import Catalog
from tmlt.analytics._query_expr import AnalyticsDefault
from tmlt.analytics._query_expr import DropInfinity as DropInfExpr
from tmlt.analytics._query_expr import DropNullAndNan, EnforceConstraint
from tmlt.analytics._query_expr import Filter as FilterExpr
from tmlt.analytics._query_expr import FlatMap as FlatMapExpr
from tmlt.analytics._query_expr import FlatMapByID as FlatMapByIDExpr
from tmlt.analytics._query_expr import (
    GetBounds,
    GetGroups,
    GroupByBoundedAverage,
    GroupByBoundedSTDEV,
    GroupByBoundedSum,
    GroupByBoundedVariance,
    GroupByCount,
    GroupByCountDistinct,
    GroupByQuantile,
)
from tmlt.analytics._query_expr import JoinPrivate as JoinPrivateExpr
from tmlt.analytics._query_expr import JoinPublic as JoinPublicExpr
from tmlt.analytics._query_expr import Map as MapExpr
from tmlt.analytics._query_expr import QueryExpr, QueryExprVisitor
from tmlt.analytics._query_expr import Rename as RenameExpr
from tmlt.analytics._query_expr import ReplaceInfinity, ReplaceNullAndNan
from tmlt.analytics._query_expr import Select as SelectExpr
from tmlt.analytics._query_expr import SuppressAggregates
from tmlt.analytics._query_expr_compiler._constraint_propagation import (
    propagate_flat_map,
    propagate_join_private,
    propagate_join_public,
    propagate_map,
    propagate_rename,
    propagate_replace,
    propagate_select,
    propagate_unmodified,
)
from tmlt.analytics._query_expr_compiler._output_schema_visitor import (
    OutputSchemaVisitor,
)
from tmlt.analytics._schema import (
    ColumnDescriptor,
    ColumnType,
    Schema,
    analytics_to_spark_columns_descriptor,
    spark_dataframe_domain_to_analytics_columns,
    spark_schema_to_analytics_columns,
)
from tmlt.analytics._table_identifier import Identifier, TemporaryTable
from tmlt.analytics._table_reference import (
    TableReference,
    find_named_tables,
    find_reference,
    lookup_domain,
    lookup_metric,
)
from tmlt.analytics._transformation_utils import generate_nested_transformation
from tmlt.analytics.constraints import Constraint, simplify_constraints
from tmlt.analytics.truncation_strategy import TruncationStrategy


class BaseTransformationVisitor(QueryExprVisitor):
    """A base visitor to create a transformation from a query expression."""

    class Output(NamedTuple):
        """A container for the outputs of the visitor."""

        transformation: Transformation
        reference: TableReference
        constraints: List[Constraint]

    def __init__(
        self,
        input_domain: DictDomain,
        input_metric: DictMetric,
        mechanism: NoiseMechanism,
        public_sources: Dict[str, DataFrame],
        table_constraints: Dict[Identifier, List[Constraint]],
    ):
        """Constructor for a TransformationVisitor.

        Args:
            input_domain: The input domain that the transformation should have.
            input_metric: The input metric that the transformation should have.
            mechanism: The noise mechanism (only used for FlatMaps).
            public_sources: Public sources to use for JoinPublic queries.
            table_constraints: A mapping of tables to the existing constraints on them.
        """
        self.input_domain = input_domain
        self.input_metric = input_metric
        self.mechanism = mechanism
        self.public_sources = public_sources
        self.table_constraints = table_constraints

    def _new_visitor_after_transformation(self, transformation: Transformation):
        """Return a new visitor that is expecting queries that follow `transformation`.

        The visitor will be initialized with a new domain and metric that match the
        output of the given transformation, but otherwise will be configured the same
        as the original visitor.
        """
        if not isinstance(transformation.output_domain, DictDomain):
            raise AnalyticsInternalError(
                f"Expected DictDomain, got {type(transformation.output_domain)}."
            )
        if not isinstance(transformation.output_metric, DictMetric):
            raise AnalyticsInternalError(
                f"Expected DictMetric, got {type(transformation.output_metric)}."
            )
        return self.__class__(
            transformation.output_domain,
            transformation.output_metric,
            self.mechanism,
            self.public_sources,
            self.table_constraints,
        )

    def validate_transformation(
        self,
        query: QueryExpr,
        transformation: Transformation,
        reference: TableReference,
        catalog: Catalog,
    ):
        """Ensure that a query's transformation is valid on a given catalog."""
        expected_schema = query.accept(OutputSchemaVisitor(catalog))
        expected_output_domain = SparkDataFrameDomain(
            analytics_to_spark_columns_descriptor(expected_schema)
        )

        expected_output_metric: Metric
        if (
            expected_schema.grouping_column is not None
            and expected_schema.id_column is not None
        ):
            raise AnalyticsInternalError(
                "Output schema from a transformation had both an ID column "
                "and a grouping column, which is not allowed."
            )
        if expected_schema.grouping_column is not None:
            expected_output_metric = IfGroupedBy(
                expected_schema.grouping_column, self.inner_metric()
            )
        elif expected_schema.id_column is not None:
            expected_output_metric = IfGroupedBy(
                expected_schema.id_column, SymmetricDifference()
            )
        else:
            expected_output_metric = SymmetricDifference()

        if (
            lookup_domain(transformation.output_domain, reference)
            != expected_output_domain
        ):
            raise AnalyticsInternalError(
                f"Expected output domain {expected_output_domain}, "
                f"but got {lookup_domain(transformation.output_domain, reference)}."
            )
        if (
            lookup_metric(transformation.output_metric, reference)
            != expected_output_metric
        ):
            raise AnalyticsInternalError(
                f"Expected output metric {expected_output_metric}, "
                f"but got {lookup_metric(transformation.output_metric, reference)}."
            )

    def inner_metric(self) -> Union[SumOf, RootSumOfSquared]:
        """Get the inner metric used by this TransformationVisitor."""
        if self.mechanism in (NoiseMechanism.LAPLACE, NoiseMechanism.GEOMETRIC):
            return SumOf(SymmetricDifference())
        elif self.mechanism in (
            NoiseMechanism.DISCRETE_GAUSSIAN,
            NoiseMechanism.GAUSSIAN,
        ):
            return RootSumOfSquared(SymmetricDifference())
        else:
            raise RuntimeError(
                f"Unsupported mechanism {self.mechanism}. "
                "Supported mechanisms are "
                f"{NoiseMechanism.GAUSSIAN},"
                f"{NoiseMechanism.DISCRETE_GAUSSIAN}, "
                f"{NoiseMechanism.LAPLACE}, and"
                f"{NoiseMechanism.GEOMETRIC}."
            )

    def _visit_child(self, child: QueryExpr) -> Output:
        """Visit a child query and raise assertion errors if needed."""
        transformation, reference, constraints = child.accept(self)
        if not isinstance(transformation, Transformation):
            raise AnalyticsInternalError("Child query did not create a transformation.")
        input_domain = lookup_domain(transformation.output_domain, reference)
        input_metric = lookup_metric(transformation.output_metric, reference)
        if not isinstance(input_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                "Child query has an invalid output domain. "
                f"Expected SparkDataFrameDomain, got {type(input_domain)}."
            )
        if not isinstance(
            input_metric, (IfGroupedBy, SymmetricDifference, HammingDistance)
        ):
            raise AnalyticsInternalError(
                "Child query does not have a recognized output metric. "
                f"Expected IfGroupedBy, SymmetricDifference, or HammingDistance, "
                f"but got {type(input_metric)}."
            )
        return self.Output(transformation, reference, constraints)

    @classmethod
    def _ensure_not_hamming(
        cls,
        transformation: Transformation,
        reference: TableReference,
        constraints: List[Constraint],
    ) -> Output:
        """Convert transformation to one with a SymmetricDifference() output metric."""
        input_domain = lookup_domain(transformation.output_domain, reference)
        input_metric = lookup_metric(transformation.output_metric, reference)
        if not isinstance(input_metric, HammingDistance):
            return cls.Output(transformation, reference, constraints)

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    "Cannot convert this transformation to one with a "
                    "SymmetricDifference output metric. "
                    f"Expected SparkDataFrameDomain, got {type(input_domain)}."
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                reference.identifier,
                target,
                HammingDistanceToSymmetricDifference(input_domain),
                lambda *args: None,
            )

        transformation_generator: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric
        }

        return cls.Output(
            *generate_nested_transformation(
                transformation, reference.parent, transformation_generator
            ),
            constraints,
        )

    def visit_private_source(self, expr) -> Output:
        """Create a transformation from a PrivateSource query expression."""
        ref = find_reference(expr.source_id, self.input_domain)
        if ref is None:
            named_tables = find_named_tables(self.input_domain)
            raise ValueError(
                f"Table '{expr.source_id}' does not exist. "
                f"Available tables are: {named_tables}"
            )
        transformation = IdentityTransformation(self.input_metric, self.input_domain)
        try:
            constraints = self.table_constraints[ref.identifier]
        except KeyError as e:
            raise AnalyticsInternalError(
                f"Table {ref.identifier} not present in constraints dictionary."
            ) from e
        return self.Output(transformation, ref, constraints)

    def visit_rename(self, expr: RenameExpr) -> Output:
        """Create a transformation from a Rename query expression."""
        child_transformation, child_ref, child_constraints = expr.child.accept(self)

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            input_domain = lookup_domain(child_transformation.output_domain, child_ref)
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(input_metric, (SymmetricDifference, IfGroupedBy)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            nonexistent_columns = set(expr.column_mapper) - set(input_domain.schema)
            if nonexistent_columns:
                raise ValueError(
                    f"Nonexistent columns in rename query: {nonexistent_columns}"
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                RenameTransformation(
                    input_domain, input_metric, dict(expr.column_mapper)
                ),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return RenameValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                dict(expr.column_mapper),
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_rename(expr, child_constraints)),
        )

    def visit_filter(self, expr: FilterExpr) -> Output:
        """Create a transformation from a FilterExpr query expression."""
        child_transformation, child_ref, child_constraints = expr.child.accept(self)

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            input_domain = lookup_domain(child_transformation.output_domain, child_ref)
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(input_metric, (IfGroupedBy, SymmetricDifference)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                FilterTransformation(input_domain, input_metric, expr.condition),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return FilterValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                expr.condition,
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_unmodified(expr, child_constraints)),
        )

    def visit_select(self, expr: SelectExpr) -> Output:
        """Create a transformation from a Select query expression."""
        child_transformation, child_ref, child_constraints = expr.child.accept(self)

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            input_domain = lookup_domain(child_transformation.output_domain, child_ref)
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)

            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(
                input_metric, (IfGroupedBy, SymmetricDifference, HammingDistance)
            ):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            nonexistent_columns = set(expr.columns) - set(input_domain.schema)
            if nonexistent_columns:
                raise ValueError(
                    f"Nonexistent columns in select query: {nonexistent_columns}"
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                SelectTransformation(input_domain, input_metric, list(expr.columns)),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return SelectValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                list(expr.columns),
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_select(expr, child_constraints)),
        )

    def visit_map(self, expr: MapExpr) -> Output:
        """Create a transformation from a Map query expression."""
        child_transformation, child_ref, child_constraints = expr.child.accept(self)

        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        if not isinstance(input_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(input_domain)}."
            )
        transformer_input_domain = SparkRowDomain(input_domain.schema)
        # Any new column created by Map could contain a null value
        spark_columns_descriptor = {
            # all of the Spark<Type>ColumnDescriptor classes are dataclasses,
            # but the SparkColumnDescriptor base class isn't;
            # hence the "type: ignore" here
            k: dataclasses.replace(v, allow_null=True)  # type: ignore
            for k, v in analytics_to_spark_columns_descriptor(
                expr.schema_new_columns
            ).items()
        }

        if expr.augment:
            output_schema = {
                **transformer_input_domain.schema,
                **spark_columns_descriptor,
            }
        else:
            output_schema = spark_columns_descriptor

        output_domain = SparkRowDomain(output_schema)
        # If you change `getattr(query, "f")` below to `query.f`,
        # mypy will be upset
        transformer = RowToRowTransformation(
            input_domain=transformer_input_domain,
            output_domain=output_domain,
            trusted_f=getattr(expr, "f"),
            augment=expr.augment,
        )

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)
            if not isinstance(
                input_metric, (IfGroupedBy, SymmetricDifference, HammingDistance)
            ):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )

            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                MapTransformation(metric=input_metric, row_transformer=transformer),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            if not expr.augment:
                raise ValueError(
                    "Maps on tables with the AddRowsWithID protected change "
                    "must be augmenting"
                )
            return MapValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                row_transformer=transformer,
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_map(expr, child_constraints)),
        )

    def build_flat_map(
        self,
        input_metric: Union[IfGroupedBy, SymmetricDifference],
        row_transformer: RowToRowsTransformation,
        max_rows: Optional[int],
    ) -> Transformation:
        """Build a Transformation for a FlatMap query expression with grouping=False."""
        transformation = FlatMapTransformation(
            metric=input_metric,
            row_transformer=row_transformer,
            max_num_rows=max_rows,
        )
        return transformation

    def build_grouping_flat_map(
        self,
        inner_metric: Union[SumOf, RootSumOfSquared],
        row_transformer: RowToRowsTransformation,
        max_rows: int,
    ) -> Transformation:
        """Build a Transformation for a FlatMap query expression with grouping=True."""
        transformation = GroupingFlatMap(
            output_metric=inner_metric,
            row_transformer=row_transformer,
            max_num_rows=max_rows,
        )
        return transformation

    def visit_flat_map(
        self,
        expr: FlatMapExpr,
    ) -> Output:
        """Create a transformation from a FlatMap query expression."""
        child_transformation, child_ref, child_constraints = self._ensure_not_hamming(
            *expr.child.accept(self)
        )

        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        if not isinstance(input_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(input_domain)}."
            )
        transformer_input_domain = SparkRowDomain(input_domain.schema)
        # Any new column created by FlatMap could contain a null value
        spark_columns_descriptor = {
            # all of the Spark<Type>ColumnDescriptor classes are dataclasses,
            # but the SparkColumnDescriptor base class isn't;
            # hence the "type: ignore" here
            k: dataclasses.replace(v, allow_null=True)  # type: ignore
            for k, v in analytics_to_spark_columns_descriptor(
                expr.schema_new_columns
            ).items()
        }

        if expr.augment:
            output_schema = {
                **transformer_input_domain.schema,
                **spark_columns_descriptor,
            }
        else:
            output_schema = spark_columns_descriptor

        output_domain = ListDomain(SparkRowDomain(output_schema))

        row_transformer = RowToRowsTransformation(
            input_domain=transformer_input_domain,
            output_domain=output_domain,
            trusted_f=getattr(expr, "f"),
            augment=expr.augment,
        )

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if expr.max_rows is None:
                raise ValueError(
                    "Flat maps on tables without IDs must have a defined max_rows"
                    " parameter."
                )
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)
            if not isinstance(input_metric, (IfGroupedBy, SymmetricDifference)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            transformation: Transformation
            if expr.schema_new_columns.grouping_column is not None:
                transformation = self.build_grouping_flat_map(
                    inner_metric=self.inner_metric(),
                    row_transformer=row_transformer,
                    max_rows=expr.max_rows,
                )
            else:
                transformation = self.build_flat_map(
                    input_metric=input_metric,
                    row_transformer=row_transformer,
                    max_rows=expr.max_rows,
                )

            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                transformation,
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            if not expr.augment:
                raise ValueError(
                    "Flat maps on tables with the AddRowsWithID protected change "
                    "must be augmenting"
                )
            if expr.schema_new_columns.grouping_column is not None:
                raise ValueError(
                    "Flat maps on tables with the AddRowsWithID protected "
                    "change cannot be grouping"
                )
            if expr.max_rows is not None:
                warnings.warn(
                    "When performing a flat map on a table with the AddRowsWithID "
                    "ProtectedChange(), the max_rows parameter "
                    "is not required and will be ignored."
                )
            return FlatMapValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                row_transformer=row_transformer,
                max_num_rows=None,
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_flat_map(expr, child_constraints)),
        )

    def visit_flat_map_by_id(self, expr: FlatMapByIDExpr) -> Output:
        """Create a transformation from a FlatMapByID query expression."""
        child_transformation, child_ref, _child_constraints = self._ensure_not_hamming(
            *expr.child.accept(self)
        )

        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        if not isinstance(input_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(input_domain)}."
            )
        transformer_input_domain = ListDomain(SparkRowDomain(input_domain.schema))

        # Any new column created by FlatMap could contain a null value
        new_columns_descriptor = {
            # all of the Spark<Type>ColumnDescriptor classes are dataclasses,
            # but the SparkColumnDescriptor base class isn't;
            # hence the "type: ignore" here
            k: dataclasses.replace(v, allow_null=True)  # type: ignore
            for k, v in analytics_to_spark_columns_descriptor(
                expr.schema_new_columns
            ).items()
        }

        def gen_transformation_ark(parent_domain, parent_metric, target):
            output_domain = ListDomain(SparkRowDomain(new_columns_descriptor))
            row_transformer = RowsToRowsTransformation(
                input_domain=transformer_input_domain,
                output_domain=output_domain,
                trusted_f=getattr(expr, "f"),
            )
            return FlatMapByKeyValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                row_transformer,
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            AddRemoveKeys: gen_transformation_ark,
        }
        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            # FlatMapByID does not preserve anything except the ID column from the
            # original table, and each ID is not guaranteed to have the same number of
            # records afterwards as it did before, so no constraints can be propagated.
            [],
        )

    def build_private_join_transformation(
        self,
        input_domain: DictDomain,
        left_key: Any,
        right_key: Any,
        left_truncation_strategy: CoreTruncationStrategy,
        right_truncation_strategy: CoreTruncationStrategy,
        left_truncation_threshold: int,
        right_truncation_threshold: int,
        join_cols: Union[List[str], None] = None,
        join_on_nulls: bool = False,
    ) -> Transformation:
        """Build a Transformation for a private join."""
        return PrivateJoinTransformation(
            input_domain=input_domain,
            left_key=left_key,
            right_key=right_key,
            left_truncation_strategy=left_truncation_strategy,
            right_truncation_strategy=right_truncation_strategy,
            left_truncation_threshold=left_truncation_threshold,
            right_truncation_threshold=right_truncation_threshold,
            join_cols=join_cols,
            join_on_nulls=join_on_nulls,
        )

    def visit_join_private(self, expr: JoinPrivateExpr) -> Output:
        """Create a transformation from a JoinPrivate query expression."""
        left_transformation, left_ref, left_constraints = expr.child.accept(self)
        right_visitor = self._new_visitor_after_transformation(left_transformation)
        (
            right_transformation,
            right_ref,
            right_constraints,
        ) = expr.right_operand_expr.accept(right_visitor)

        if left_ref.parent != right_ref.parent:
            raise ValueError(
                "Left and right tables must be initialized with compatible "
                f"ProtectedChange() descriptions, but {left_ref} and {right_ref} "
                "were not."
            )

        child_transformation = left_transformation | right_transformation
        left_domain = lookup_domain(child_transformation.output_domain, left_ref)
        right_domain = lookup_domain(child_transformation.output_domain, right_ref)
        if not isinstance(left_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(left_domain)}."
            )
        if not isinstance(right_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(right_domain)}."
            )

        def get_truncation_params(
            strategy: TruncationStrategy.Type,
        ) -> Tuple[CoreTruncationStrategy, int]:
            if isinstance(strategy, TruncationStrategy.DropExcess):
                return CoreTruncationStrategy.TRUNCATE, strategy.max_rows
            elif isinstance(strategy, TruncationStrategy.DropNonUnique):
                return CoreTruncationStrategy.DROP, 1
            else:
                raise ValueError(
                    f"Truncation strategy type {strategy.__class__.__qualname__} "
                    "is not supported."
                )

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if (
                expr.truncation_strategy_left is None
                or expr.truncation_strategy_right is None
            ):
                raise ValueError(
                    "When joining without IDs, truncation strategies are required."
                )
            l_trunc_strat, l_trunc_threshold = get_truncation_params(
                expr.truncation_strategy_left
            )
            r_trunc_strat, r_trunc_threshold = get_truncation_params(
                expr.truncation_strategy_right
            )
            subset = Subset(
                parent_domain,
                parent_metric,
                [left_ref.identifier, right_ref.identifier],
            )
            if not isinstance(subset.output_domain, DictDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(subset.output_domain)}."
                )
            join = self.build_private_join_transformation(
                input_domain=subset.output_domain,
                left_key=left_ref.identifier,
                right_key=right_ref.identifier,
                left_truncation_strategy=l_trunc_strat,
                right_truncation_strategy=r_trunc_strat,
                left_truncation_threshold=l_trunc_threshold,
                right_truncation_threshold=r_trunc_threshold,
                join_cols=list(expr.join_columns) if expr.join_columns else None,
                join_on_nulls=True,
            )
            create_dict = CreateDictFromValue(
                join.output_domain, join.output_metric, key=target
            )
            return AugmentDictTransformation(subset | join | create_dict)

        def gen_transformation_ark(parent_domain, parent_metric, target):
            if (expr.truncation_strategy_left is not None) or (
                expr.truncation_strategy_right is not None
            ):
                warnings.warn(
                    "When joining with IDs, truncation strategies are not required."
                    " Provided truncation parameters will be ignored."
                )
            return PrivateJoinOnKeyTransformation(
                parent_domain,
                parent_metric,
                left_ref.identifier,
                right_ref.identifier,
                target,
                list(expr.join_columns) if expr.join_columns else None,
                join_on_nulls=True,
            )

        common_cols = set(left_domain.schema) & set(right_domain.schema)
        join_cols = set(expr.join_columns or common_cols)
        overlapping_cols = common_cols - join_cols
        constraints = propagate_join_private(
            join_cols, overlapping_cols, left_constraints, right_constraints
        )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }
        return self.Output(
            *generate_nested_transformation(
                child_transformation,
                # right_ref.parent and left_ref.parent must be the same,
                # so either works here.
                right_ref.parent,
                transformation_generators,
            ),
            simplify_constraints(constraints),
        )

    def visit_join_public(self, expr: JoinPublicExpr) -> Output:
        """Create a transformation from a JoinPublic query expression."""
        child_transformation, child_ref, child_constraints = self._ensure_not_hamming(
            *self._visit_child(expr.child)
        )

        public_df: DataFrame
        if isinstance(expr.public_table, str):
            try:
                public_df = self.public_sources[expr.public_table]
            except KeyError as e:
                raise ValueError(
                    f"There is no public source with the identifier {expr.public_table}"
                ) from e
        else:
            public_df = expr.public_table

        public_df_schema = Schema(spark_schema_to_analytics_columns(public_df.schema))

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            input_domain = lookup_domain(child_transformation.output_domain, child_ref)
            input_metric = lookup_metric(child_transformation.output_metric, child_ref)
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(input_metric, (IfGroupedBy, SymmetricDifference)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )

            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                PublicJoinTransformation(
                    input_domain=SparkDataFrameDomain(input_domain.schema),
                    public_df=public_df,
                    public_df_domain=SparkDataFrameDomain(
                        analytics_to_spark_columns_descriptor(public_df_schema)
                    ),
                    join_cols=list(expr.join_columns) if expr.join_columns else None,
                    metric=input_metric,
                    join_on_nulls=True,
                    how=expr.how,
                ),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return PublicJoinValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                public_df,
                SparkDataFrameDomain(
                    analytics_to_spark_columns_descriptor(public_df_schema)
                ),
                list(expr.join_columns) if expr.join_columns else None,
                join_on_nulls=True,
            )

        child_domain = lookup_domain(child_transformation.output_domain, child_ref)
        if not isinstance(child_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(child_domain)}."
            )

        common_cols = set(child_domain.schema) & set(public_df_schema)
        join_cols = set(expr.join_columns or common_cols)
        overlapping_cols = common_cols - join_cols
        constraints = propagate_join_public(
            join_cols, overlapping_cols, public_df, child_constraints
        )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }
        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(constraints),
        )

    @staticmethod
    def _get_replace_with(
        expr: ReplaceNullAndNan,
        analytics_schema: Dict[str, ColumnDescriptor],
        grouping_column: Optional[str] = None,
    ) -> Dict[str, Any]:
        replace_with: Dict[str, Any] = dict(expr.replace_with).copy()
        if len(replace_with) == 0:
            for col in Schema(analytics_schema).column_descs:
                if col == grouping_column:
                    continue
                if not analytics_schema[col].allow_null and not (
                    analytics_schema[col].allow_nan
                ):
                    continue
                if analytics_schema[col].column_type == ColumnType.INTEGER:
                    replace_with[col] = int(AnalyticsDefault.INTEGER)
                elif analytics_schema[col].column_type == ColumnType.DECIMAL:
                    replace_with[col] = float(AnalyticsDefault.DECIMAL)
                elif analytics_schema[col].column_type == ColumnType.VARCHAR:
                    replace_with[col] = str(AnalyticsDefault.VARCHAR)
                elif analytics_schema[col].column_type == ColumnType.DATE:
                    date: datetime.date = AnalyticsDefault.DATE
                    replace_with[col] = date
                elif analytics_schema[col].column_type == ColumnType.TIMESTAMP:
                    dt: datetime.datetime = AnalyticsDefault.TIMESTAMP
                    replace_with[col] = dt
                else:
                    raise RuntimeError(
                        f"Analytics does not have a default value for column {col} of"
                        f" type {analytics_schema[col].column_type}, and no default"
                        " value was provided"
                    )

        else:
            # Check that all columns exist
            for col in replace_with:
                if not col in analytics_schema:
                    raise ValueError(
                        f"Cannot replace values in column {col}, because it is not in"
                        " the schema"
                    )
            # Make sure all DECIMAL replacement values are floats
            for col in replace_with.keys():
                if analytics_schema[col].column_type == ColumnType.DECIMAL:
                    replace_with[col] = float(replace_with[col])

        return replace_with

    def visit_replace_null_and_nan(self, expr: ReplaceNullAndNan) -> Output:
        """Create a transformation from a ReplaceNullAndNan query expression."""
        child_transformation, child_ref, child_constraints = self._visit_child(
            expr.child
        )
        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        input_metric = lookup_metric(child_transformation.output_metric, child_ref)
        if not isinstance(input_domain, SparkDataFrameDomain):
            raise AnalyticsInternalError(
                f"Unrecognized input domain {type(input_domain)}."
            )
        if not isinstance(
            input_metric, (IfGroupedBy, HammingDistance, SymmetricDifference)
        ):
            raise AnalyticsInternalError(
                f"Unrecognized input metric {type(input_metric)}."
            )
        grouping_column: Optional[str] = None
        if isinstance(input_metric, IfGroupedBy):
            grouping_column = input_metric.column
            if grouping_column in expr.replace_with:
                raise ValueError(
                    "Cannot replace null values in column"
                    f" {input_metric.column}, because it is being used as a"
                    " grouping column"
                )
        analytics_schema = spark_dataframe_domain_to_analytics_columns(input_domain)

        replace_with = self._get_replace_with(expr, analytics_schema, grouping_column)

        replace_null = any(analytics_schema[col].allow_null for col in replace_with)

        replace_nan = any(
            analytics_schema[col].column_type == ColumnType.DECIMAL
            and analytics_schema[col].allow_nan
            for col in replace_with.keys()
        )

        null_replace_map = {
            col: val
            for col, val in replace_with.items()
            if analytics_schema[col].allow_null
        }

        nan_replace_map = {
            col: replace_with[col]
            for col in replace_with.keys()
            if (
                analytics_schema[col].column_type == ColumnType.DECIMAL
                and analytics_schema[col].allow_nan
            )
        }

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            transformation: Transformation = IdentityTransformation(
                input_metric, input_domain
            )
            if replace_null:
                if not isinstance(input_domain, SparkDataFrameDomain):
                    raise AnalyticsInternalError(
                        f"Expected input domain {type(input_domain)}, got"
                        f" {type(input_domain)} instead."
                    )
                if not isinstance(
                    input_metric, (IfGroupedBy, HammingDistance, SymmetricDifference)
                ):
                    raise AnalyticsInternalError(
                        f"Unrecognized input metric {type(input_metric)}."
                    )
                transformation |= ReplaceNullsTransformation(
                    input_domain=input_domain,
                    metric=input_metric,
                    replace_map=null_replace_map,
                )
            if replace_nan:
                if not isinstance(transformation.output_domain, SparkDataFrameDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {SparkDataFrameDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(
                    transformation.output_metric,
                    (IfGroupedBy, HammingDistance, SymmetricDifference),
                ):
                    raise AnalyticsInternalError(
                        f"Expected output metric {IfGroupedBy}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= ReplaceNaNsTransformation(
                    input_domain=transformation.output_domain,
                    metric=transformation.output_metric,
                    replace_map=nan_replace_map,
                )

            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                transformation,
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            transformation: Transformation = IdentityTransformation(
                parent_metric, parent_domain
            )
            temp_table_id = TemporaryTable()

            if replace_null:
                transformation |= ReplaceNullsValueTransformation(
                    parent_domain,
                    parent_metric,
                    child_ref.identifier,
                    temp_table_id if replace_nan else target,
                    replace_map=null_replace_map,
                )

            if replace_nan:
                if not isinstance(transformation.output_domain, DictDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {DictDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(transformation.output_metric, AddRemoveKeys):
                    raise AnalyticsInternalError(
                        f"Expected output metric {AddRemoveKeys}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= ReplaceNaNsValueTransformation(
                    transformation.output_domain,
                    transformation.output_metric,
                    temp_table_id if replace_null else child_ref.identifier,
                    target,
                    nan_replace_map,
                )

            if (not replace_null) and (not replace_nan):
                # Rename that essentially does nothing
                if not isinstance(transformation.output_domain, DictDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {DictDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(transformation.output_metric, AddRemoveKeys):
                    raise AnalyticsInternalError(
                        f"Expected output metric {AddRemoveKeys}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= RenameValueTransformation(
                    transformation.output_domain,
                    transformation.output_metric,
                    child_ref.identifier,
                    target,
                    {},
                )
            return transformation

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_replace(expr, child_constraints)),
        )

    def visit_replace_infinity(self, expr: ReplaceInfinity) -> Output:
        """Create a transformation from a ReplaceInfinity query expression."""
        child_transformation, child_ref, child_constraints = self._visit_child(
            expr.child
        )
        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        input_metric = lookup_metric(child_transformation.output_metric, child_ref)

        analytics_schema = Schema(
            spark_dataframe_domain_to_analytics_columns(input_domain)
        )
        replace_with = dict(expr.replace_with)
        if len(replace_with) == 0:
            replace_with = {
                col: (AnalyticsDefault.DECIMAL, AnalyticsDefault.DECIMAL)
                for col in analytics_schema.column_descs
                if analytics_schema[col].column_type == ColumnType.DECIMAL
            }

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(
                input_metric, (IfGroupedBy, HammingDistance, SymmetricDifference)
            ):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                ReplaceInfsTransformation(
                    input_domain=input_domain,
                    metric=input_metric,
                    replace_map=replace_with,
                ),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return ReplaceInfsValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                replace_map=replace_with,
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_replace(expr, child_constraints)),
        )

    def visit_drop_infinity(self, expr: DropInfExpr) -> Output:
        """Create a transformation from a DropInfinity query expression."""
        child_transformation, child_ref, child_constraints = self._ensure_not_hamming(
            *self._visit_child(expr.child)
        )
        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        input_metric = lookup_metric(child_transformation.output_metric, child_ref)
        analytics_schema = Schema(
            spark_dataframe_domain_to_analytics_columns(input_domain)
        )

        columns = expr.columns
        if len(columns) == 0:
            columns = tuple(
                col
                for col, cd in analytics_schema.column_descs.items()
                if (cd.column_type == ColumnType.DECIMAL and cd.allow_inf)
            )
        else:
            for col in columns:
                if analytics_schema.column_descs[col].column_type != ColumnType.DECIMAL:
                    raise ValueError(
                        f"Cannot drop infinite values from column {col}, because that"
                        " column's type is not DECIMAL"
                    )

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(input_metric, (IfGroupedBy, SymmetricDifference)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                DropInfTransformation(
                    input_domain=input_domain,
                    metric=input_metric,
                    columns=list(columns),
                ),
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            return DropInfsValueTransformation(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                columns=list(columns),
            )

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_unmodified(expr, child_constraints)),
        )

    def visit_drop_null_and_nan(self, expr: DropNullAndNan) -> Output:
        """Create a transformation from a DropNullAndNan query expression."""
        child_transformation, child_ref, child_constraints = self._ensure_not_hamming(
            *self._visit_child(expr.child)
        )
        input_domain = lookup_domain(child_transformation.output_domain, child_ref)
        input_metric = lookup_metric(child_transformation.output_metric, child_ref)
        analytics_schema = Schema(
            spark_dataframe_domain_to_analytics_columns(input_domain)
        )

        # TODO(2702): This should be supported for IDs tables
        grouping_column: Optional[str] = None
        if isinstance(input_metric, IfGroupedBy):
            grouping_column = input_metric.column
            if grouping_column in expr.columns:
                raise ValueError(
                    "Cannot drop null values in column"
                    f" {input_metric.column}, because it is being used as a"
                    " grouping column"
                )

        columns = expr.columns
        if len(columns) == 0:
            columns = tuple(
                col
                for col, cd in analytics_schema.column_descs.items()
                if (cd.allow_null or cd.allow_nan) and not (col == grouping_column)
            )

        null_columns = [col for col in columns if analytics_schema[col].allow_null]

        nan_columns = [col for col in columns if analytics_schema[col].allow_nan]

        def gen_transformation_dictmetric(parent_domain, parent_metric, target):
            if not isinstance(input_domain, SparkDataFrameDomain):
                raise AnalyticsInternalError(
                    f"Unrecognized input domain {type(input_domain)}."
                )
            if not isinstance(input_metric, (IfGroupedBy, SymmetricDifference)):
                raise AnalyticsInternalError(
                    f"Unrecognized input metric {type(input_metric)}."
                )
            transformation: Transformation = IdentityTransformation(
                input_metric, input_domain
            )

            if null_columns:
                transformation |= DropNullsTransformation(
                    input_domain, input_metric, null_columns
                )

            if nan_columns:
                if not isinstance(transformation.output_domain, SparkDataFrameDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {SparkDataFrameDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(
                    transformation.output_metric, (IfGroupedBy, SymmetricDifference)
                ):
                    raise AnalyticsInternalError(
                        f"Expected output metric {IfGroupedBy}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= DropNaNsTransformation(
                    transformation.output_domain,
                    transformation.output_metric,
                    nan_columns,
                )

            return create_copy_and_transform_value(
                parent_domain,
                parent_metric,
                child_ref.identifier,
                target,
                transformation,
                lambda *args: None,
            )

        def gen_transformation_ark(parent_domain, parent_metric, target):
            transformation: Transformation = IdentityTransformation(
                parent_metric, parent_domain
            )
            temp_table_id = TemporaryTable()

            if null_columns:
                transformation |= DropNullsValueTransformation(
                    parent_domain,
                    parent_metric,
                    child_ref.identifier,
                    temp_table_id if nan_columns else target,
                    null_columns,
                )

            if nan_columns:
                if not isinstance(transformation.output_domain, DictDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {DictDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(transformation.output_metric, AddRemoveKeys):
                    raise AnalyticsInternalError(
                        f"Expected output metric {AddRemoveKeys}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= DropNaNsValueTransformation(
                    transformation.output_domain,
                    transformation.output_metric,
                    temp_table_id if null_columns else child_ref.identifier,
                    target,
                    nan_columns,
                )

            if (not null_columns) and (not nan_columns):
                # Rename that essentially does nothing
                if not isinstance(transformation.output_domain, DictDomain):
                    raise AnalyticsInternalError(
                        f"Expected output domain {DictDomain}, got"
                        f" {type(transformation.output_domain)} instead."
                    )
                if not isinstance(transformation.output_metric, AddRemoveKeys):
                    raise AnalyticsInternalError(
                        f"Expected output metric {AddRemoveKeys}, got"
                        f" {type(transformation.output_metric)} instead."
                    )
                transformation |= RenameValueTransformation(
                    transformation.output_domain,
                    transformation.output_metric,
                    child_ref.identifier,
                    target,
                    {},
                )
            return transformation

        transformation_generators: Dict[Type[Metric], Callable] = {
            DictMetric: gen_transformation_dictmetric,
            AddRemoveKeys: gen_transformation_ark,
        }

        return self.Output(
            *generate_nested_transformation(
                child_transformation, child_ref.parent, transformation_generators
            ),
            simplify_constraints(propagate_unmodified(expr, child_constraints)),
        )

    # override in new subclass, if constraints aren't enforced
    def visit_enforce_constraint(self, expr: EnforceConstraint) -> Output:
        """Create a transformation from an EnforceConstraint query expression."""
        # Note: at present, enforcing one constraint can never invalidate
        # another constraint, so just adding the new constraint to the list of
        # constraints is perfectly fine. If a new constraint is added that can
        # invalidate other constraints, this will have to be broken out into
        # per-constraint-type logic.
        child_transformation, child_ref, child_constraints = self._visit_child(
            expr.child
        )
        # pylint: disable=protected-access
        transformation, ref = expr.constraint._enforce(
            child_transformation, child_ref, *expr.options
        )
        # pylint: enable=protected-access
        return self.Output(
            transformation,
            ref,
            simplify_constraints(child_constraints + [expr.constraint]),
        )

    # None of the queries that produce measurements are implemented
    def visit_get_groups(self, expr: GetGroups) -> Any:
        """Visit a GetGroups query expression (raises an error)."""
        raise NotImplementedError

    def visit_get_bounds(self, expr: GetBounds) -> Any:
        """Visit a GetBounds query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_count(self, expr: GroupByCount) -> Any:
        """Visit a GroupByCount query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_count_distinct(self, expr: GroupByCountDistinct) -> Any:
        """Visit a GroupByCountDistinct query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_quantile(self, expr: GroupByQuantile) -> Any:
        """Visit a GroupByQuantile query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_bounded_sum(self, expr: GroupByBoundedSum) -> Any:
        """Visit a GroupByBoundedSum query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_bounded_average(self, expr: GroupByBoundedAverage) -> Any:
        """Visit a GroupByBoundedAverage query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_bounded_variance(self, expr: GroupByBoundedVariance) -> Any:
        """Visit a GroupByBoundedVariance query expression (raises an error)."""
        raise NotImplementedError

    def visit_groupby_bounded_stdev(self, expr: GroupByBoundedSTDEV) -> Any:
        """Visit a GroupByBoundedSTDEV query expression (raises an error)."""
        raise NotImplementedError

    def visit_suppress_aggregates(self, expr: SuppressAggregates) -> Any:
        """Visit a SuppressAggregates query expression (raises an error)."""
        raise NotImplementedError
