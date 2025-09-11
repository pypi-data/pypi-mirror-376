"""Unit tests for schema."""

# SPDX-License-Identifier: Apache-2.0
# Copyright Tumult Labs 2025

import random
import re

import pytest

from tmlt.analytics._schema import ColumnDescriptor, ColumnType, FrozenDict, Schema


def test_invalid_column_type() -> None:
    """Schema raises an exception when an invalid column type is used."""
    with pytest.raises(
        ValueError,
        match=r"Column types \{'BADTYPE'\} not supported; "
        r"use supported types \['[A-Z', ]+'\].",
    ):
        columns = {"Col1": "VARCHAR", "Col2": "BADTYPE", "Col3": "INTEGER"}
        Schema(columns)


def test_invalid_column_name() -> None:
    """Schema raises an exception if a column is named "" (empty string)."""
    with pytest.raises(
        ValueError,
        match=re.escape('"" (the empty string) is not a supported column name'),
    ):
        Schema({"col1": "VARCHAR", "": "VARCHAR"})


def test_valid_column_types() -> None:
    """Schema construction and py type translation succeeds with valid columns."""
    columns = {
        "1": "INTEGER",
        "2": "DECIMAL",
        "3": "VARCHAR",
        "4": "DATE",
        "5": "TIMESTAMP",
    }
    schema = Schema(columns)
    expected = {
        "1": ColumnDescriptor(ColumnType.INTEGER, allow_null=False),
        "2": ColumnDescriptor(ColumnType.DECIMAL, allow_null=False),
        "3": ColumnDescriptor(ColumnType.VARCHAR, allow_null=False),
        "4": ColumnDescriptor(ColumnType.DATE, allow_null=False),
        "5": ColumnDescriptor(ColumnType.TIMESTAMP, allow_null=False),
    }
    assert expected == schema.column_descs


def test_schema_equality() -> None:
    """Make sure schema equality check works properly."""
    columns_1 = {"a": "VARCHAR", "b": "INTEGER"}
    columns_2 = {"a": "VARCHAR", "b": "INTEGER"}
    columns_3 = {"y": "VARCHAR", "z": "INTEGER"}
    columns_4 = {"a": "INTEGER", "b": "VARCHAR"}
    schema_1 = Schema(columns_1)
    schema_2 = Schema(columns_2)
    schema_3 = Schema(columns_3)
    schema_4 = Schema(columns_4)
    assert schema_1 == schema_2
    assert schema_1 != schema_3
    assert schema_1 != schema_4


def test_schema_hash() -> None:
    """Makes sure that schema hash is consistent."""

    columns_1 = {"a": "VARCHAR", "b": "INTEGER"}
    columns_2 = {"a": "VARCHAR", "b": "INTEGER"}
    columns_3 = {"y": "VARCHAR", "z": "INTEGER"}
    columns_4 = {"a": "INTEGER", "b": "VARCHAR"}
    columns_5 = {"z": "VARCHAR", "b": "INTEGER"}
    schema_1 = Schema(columns_1)
    schema_2 = Schema(columns_2)
    schema_3 = Schema(columns_3)
    schema_4 = Schema(columns_4)
    schema_5 = Schema(columns_5)
    assert hash(schema_1) == hash(schema_2)
    assert hash(schema_1) != hash(schema_3)
    assert hash(schema_1) != hash(schema_4)
    assert hash(schema_1) != hash(schema_5)


def test_frozen_dict():
    """FrozenDict works like an immutable dict."""

    a = FrozenDict.from_dict({"a": 1, "b": 2})
    assert a["a"] == 1
    assert a["b"] == 2

    with pytest.raises(KeyError):
        _ = a["c"]

    with pytest.raises(TypeError):
        a["a"] = 3  # type: ignore

    b = FrozenDict.from_dict({"x": 1, "y": 2})
    assert a != b
    assert hash(a) != hash(b)

    a_2 = FrozenDict.from_dict({"a": 1, "b": 2})
    assert a == a_2
    assert hash(a) == hash(a_2)

    assert isinstance(dict(a), dict)
    assert dict(a)["a"] == 1

    assert set(a) == set(["a", "b"])

    assert [("a", 1), ("b", 2)] == list(a.items())
    assert ["a", "b"] == list(a.keys())
    assert [1, 2] == list(a.values())

    assert a.get("a") == 1
    assert a.get("c", 10) == 10

    assert dict(a | b) == dict(a) | dict(b)
    assert list((a | b).keys()) == ["a", "b", "x", "y"]


def test_frozen_dict_order():
    """FrozenDict preserves element order when converting to/from a dict."""
    keys = list(range(1000))
    random.shuffle(keys)

    def f(n: int) -> int:
        return (127 * n) % 8191

    pre_d = {k: f(k) for k in keys}
    fd = FrozenDict.from_dict(pre_d)
    post_d = dict(fd)

    assert list(fd.keys()) == keys
    assert list(fd.values()) == [f(k) for k in keys]
    assert list(fd.items()) == [(k, f(k)) for k in keys]

    assert post_d == pre_d
    assert list(post_d.keys()) == keys
    assert list(post_d.values()) == [f(k) for k in keys]
    assert list(post_d.items()) == [(k, f(k)) for k in keys]


def test_frozen_dict_order_comparison():
    """FrozenDict considers order when comparing for equality."""
    fd1 = FrozenDict.from_dict({1: 2, 3: 4})
    fd2 = FrozenDict.from_dict({1: 2, 3: 4})
    fd3 = FrozenDict.from_dict({3: 4, 1: 2})
    fd4 = FrozenDict.from_dict({1: 2, 3: 5})

    assert fd1 == fd1  # pylint: disable=comparison-with-itself
    assert fd1 == fd2
    assert fd1 != fd3
    assert fd1 != fd4
