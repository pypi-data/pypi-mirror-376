"""Logic for coercing Spark dataframes into forms usable by Tumult Analytics."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

from typing import Dict, Set

from pyspark.sql import DataFrame
from pyspark.sql.types import (
    DataType,
    DateType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
    TimestampType,
)

SUPPORTED_SPARK_TYPES: Set[DataType] = {
    IntegerType(),
    LongType(),
    FloatType(),
    DoubleType(),
    StringType(),
    DateType(),
    TimestampType(),
}
"""Set of Spark data types supported by Tumult Analytics."""

TYPE_COERCION_MAP: Dict[DataType, DataType] = {
    IntegerType(): LongType(),
    FloatType(): DoubleType(),
}
"""Mapping describing how Spark's data types are coerced by Tumult Analytics."""


def _fail_if_dataframe_contains_unsupported_types(dataframe: DataFrame):
    """Raises an error if DataFrame contains unsupported Spark column types."""
    unsupported_types = [
        (field.name, field.dataType)
        for field in dataframe.schema
        if field.dataType not in SUPPORTED_SPARK_TYPES
    ]

    if unsupported_types:
        raise ValueError(
            "Unsupported Spark data type: Tumult Analytics does not yet support the"
            f" Spark data types for the following columns: {unsupported_types}."
            " Consider casting these columns into one of the supported Spark data"
            f" types: {SUPPORTED_SPARK_TYPES}."
        )


def coerce_spark_schema_or_fail(dataframe: DataFrame) -> DataFrame:
    """Returns a new DataFrame where all column data types are supported.

    In particular, this function raises an error:
        * if ``dataframe`` contains a column type not listed in
            SUPPORTED_SPARK_TYPES
        * if ``dataframe`` contains a column named "" (the empty string)

    This function returns a DataFrame where all column types
        * are coerced according to TYPE_COERCION_MAP if necessary
    """
    if "" in dataframe.columns:
        raise ValueError('This DataFrame contains a column named "" (the empty string)')

    _fail_if_dataframe_contains_unsupported_types(dataframe)

    for field in dataframe.schema:
        if field.dataType in TYPE_COERCION_MAP:
            dataframe = dataframe.withColumn(
                field.name,
                dataframe[field.name].cast(TYPE_COERCION_MAP[field.dataType]),
            )

    return dataframe
