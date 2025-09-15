"""Test filter operators and validation system."""

import pytest

from dbengine.core.config import DatabaseType
from dbengine.core.filter_operators import (
    BaseOperators,
    FilterCriteriaValidator,
    FilterValidationError,
    ParquetOperators,
    SQLOperators,
)

# BaseOperators enum tests


def test_base_operators_is_empty():
    """Test that BaseOperators enum has no values."""
    # BaseOperators should be empty as it's just a base class
    assert len(list(BaseOperators)) == 0


# SQLOperators enum tests


def test_sql_operators_values():
    """Test that SQLOperators enum has correct values."""
    assert SQLOperators.EQUAL.value == "="
    assert SQLOperators.NOT_EQUAL.value == "!="
    assert SQLOperators.LESS_THAN.value == "<"
    assert SQLOperators.LESS_THAN_EQUAL.value == "<="
    assert SQLOperators.GREATER_THAN.value == ">"
    assert SQLOperators.GREATER_THAN_EQUAL.value == ">="
    assert SQLOperators.IN.value == "IN"
    assert SQLOperators.LIKE.value == "LIKE"
    assert SQLOperators.NOT_NULL.value == "IS NOT NULL"
    assert SQLOperators.NULL.value == "IS NULL"


def test_sql_operators_count():
    """Test that SQLOperators enum has expected number of operators."""
    expected_count = 10  # Based on the operators defined
    actual_count = len(list(SQLOperators))
    assert actual_count == expected_count


def test_sql_operators_iteration():
    """Test that SQLOperators can be iterated over."""
    operators = {op.value for op in SQLOperators}
    expected_operators = {
        "=",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "IN",
        "LIKE",
        "IS NOT NULL",
        "IS NULL",
    }
    assert operators == expected_operators


def test_sql_operators_membership():
    """Test that operators can be found in SQLOperators._value2member_map_."""
    assert "=" in SQLOperators._value2member_map_
    assert "IN" in SQLOperators._value2member_map_
    assert "LIKE" in SQLOperators._value2member_map_
    assert "IS NULL" in SQLOperators._value2member_map_
    assert "invalid_operator" not in SQLOperators._value2member_map_


# ParquetOperators enum tests


def test_parquet_operators_values():
    """Test that ParquetOperators enum has correct values."""
    assert ParquetOperators.EQUAL.value == "="
    assert ParquetOperators.NOT_EQUAL.value == "!="
    assert ParquetOperators.LESS_THAN.value == "<"
    assert ParquetOperators.LESS_THAN_EQUAL.value == "<="
    assert ParquetOperators.GREATER_THAN.value == ">"
    assert ParquetOperators.GREATER_THAN_EQUAL.value == ">="
    assert ParquetOperators.IN.value == "IN"


def test_parquet_operators_count():
    """Test that ParquetOperators enum has expected number of operators."""
    expected_count = 7  # Based on the operators defined
    actual_count = len(list(ParquetOperators))
    assert actual_count == expected_count


def test_parquet_operators_subset_of_sql():
    """Test that ParquetOperators is a subset of SQLOperators."""
    parquet_ops = {op.value for op in ParquetOperators}
    sql_ops = {op.value for op in SQLOperators}
    assert parquet_ops.issubset(sql_ops)


def test_parquet_operators_missing_sql_specific():
    """Test that ParquetOperators doesn't have SQL-specific operators."""
    parquet_ops = {op.value for op in ParquetOperators}
    assert "LIKE" not in parquet_ops
    assert "IS NULL" not in parquet_ops
    assert "IS NOT NULL" not in parquet_ops


# FilterValidationError tests


def test_filter_validation_error_inheritance():
    """Test that FilterValidationError is a proper exception."""
    error = FilterValidationError("Test error")
    assert isinstance(error, Exception)
    assert str(error) == "Test error"


def test_filter_validation_error_with_message():
    """Test FilterValidationError with custom message."""
    message = "Invalid filter criteria provided"
    error = FilterValidationError(message)
    assert str(error) == message


# FilterCriteriaValidator.validate() tests - Valid cases


def test_validate_sqlite_basic_criteria():
    """Test validation of basic criteria for SQLite."""
    criteria = [("name", "=", "John")]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert where_clause == " WHERE name = :value_0"
    assert params == {"value_0": "John"}


def test_validate_postgresql_basic_criteria():
    """Test validation of basic criteria for PostgreSQL."""
    criteria = [("age", ">", 25)]
    where_clause, params = FilterCriteriaValidator.validate(
        criteria, DatabaseType.POSTGRESQL
    )

    assert where_clause == " WHERE age > :value_0"
    assert params == {"value_0": 25}


def test_validate_parquet_basic_criteria():
    """Test validation of basic criteria for Parquet."""
    criteria = [("price", "<=", 100.0)]
    where_clause, params = FilterCriteriaValidator.validate(
        criteria, DatabaseType.PARQUET
    )

    assert where_clause == " WHERE price <= :value_0"
    assert params == {"value_0": 100.0}


def test_validate_multiple_criteria():
    """Test validation of multiple criteria."""
    criteria = [("name", "=", "John"), ("age", ">", 25), ("active", "=", True)]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert (
        where_clause == " WHERE name = :value_0 AND age > :value_1 AND active = :value_2"
    )
    assert params == {"value_0": "John", "value_1": 25, "value_2": True}


def test_validate_in_operator_with_list():
    """Test validation of IN operator with list values."""
    criteria = [("status", "IN", ["active", "pending", "completed"])]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    expected_clause = " WHERE status IN (:value_0_0, :value_0_1, :value_0_2)"
    expected_params = {
        "value_0_0": "active",
        "value_0_1": "pending",
        "value_0_2": "completed",
    }

    assert where_clause == expected_clause
    assert params == expected_params


def test_validate_in_operator_with_tuple():
    """Test validation of IN operator with tuple values."""
    criteria = [("id", "IN", (1, 2, 3, 4))]
    where_clause, params = FilterCriteriaValidator.validate(
        criteria, DatabaseType.POSTGRESQL
    )

    expected_clause = " WHERE id IN (:value_0_0, :value_0_1, :value_0_2, :value_0_3)"
    expected_params = {"value_0_0": 1, "value_0_1": 2, "value_0_2": 3, "value_0_3": 4}

    assert where_clause == expected_clause
    assert params == expected_params


def test_validate_in_operator_with_set():
    """Test validation of IN operator with set values."""
    criteria = [("category", "IN", {"tech", "finance"})]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    # Sets are unordered, so we need to check both possible orders
    assert " WHERE category IN (" in where_clause
    assert "value_0_0" in where_clause and "value_0_1" in where_clause
    assert set(params.values()) == {"tech", "finance"}


def test_validate_null_operators():
    """Test validation of NULL operators for SQL databases."""
    criteria = [("deleted_at", "IS NULL", None), ("created_at", "IS NOT NULL", None)]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    expected_clause = " WHERE deleted_at IS NULL AND created_at IS NOT NULL"
    assert where_clause == expected_clause
    assert params == {}  # NULL operators don't use parameters


def test_validate_like_operator():
    """Test validation of LIKE operator for SQL databases."""
    criteria = [("name", "LIKE", "%John%")]
    where_clause, params = FilterCriteriaValidator.validate(
        criteria, DatabaseType.POSTGRESQL
    )

    assert where_clause == " WHERE name LIKE :value_0"
    assert params == {"value_0": "%John%"}


def test_validate_mixed_operators():
    """Test validation with mixed operator types."""
    criteria = [
        ("name", "LIKE", "%John%"),
        ("age", ">=", 18),
        ("status", "IN", ["active", "pending"]),
        ("deleted_at", "IS NULL", None),
    ]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    expected_clause = (
        " WHERE name LIKE :value_0 AND age >= :value_1 AND "
        "status IN (:value_2_0, :value_2_1) AND deleted_at IS NULL"
    )
    expected_params = {
        "value_0": "%John%",
        "value_1": 18,
        "value_2_0": "active",
        "value_2_1": "pending",
    }

    assert where_clause == expected_clause
    assert params == expected_params


# FilterCriteriaValidator.validate() tests - Error cases


def test_validate_unsupported_database_type():
    """Test validation with unsupported database type."""
    criteria = [("name", "=", "John")]

    # Create a mock unsupported database type
    class UnsupportedType:
        pass

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(criteria, UnsupportedType())

    assert "Unsupported database type" in str(exc_info.value)


def test_validate_invalid_criteria_structure_not_tuple():
    """Test validation with invalid criteria structure - not tuple."""
    invalid_criteria = [["name", "=", "John"]]  # List instead of tuple

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(invalid_criteria, DatabaseType.SQLITE)

    assert "Criteria must be a list of tuples" in str(exc_info.value)


def test_validate_invalid_criteria_structure_wrong_length():
    """Test validation with invalid criteria structure - wrong tuple length."""
    invalid_criteria = [("name", "=")]  # Missing value

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(invalid_criteria, DatabaseType.SQLITE)

    assert "Criteria must be a list of tuples" in str(exc_info.value)


def test_validate_invalid_criteria_structure_non_string_column():
    """Test validation with non-string column name."""
    invalid_criteria = [(123, "=", "John")]  # Integer column name

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(invalid_criteria, DatabaseType.SQLITE)

    assert "Criteria must be a list of tuples" in str(exc_info.value)


def test_validate_invalid_criteria_structure_non_string_operator():
    """Test validation with non-string operator."""
    invalid_criteria = [("name", 123, "John")]  # Integer operator

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(invalid_criteria, DatabaseType.SQLITE)

    assert "Criteria must be a list of tuples" in str(exc_info.value)


def test_validate_invalid_operator_for_sql():
    """Test validation with invalid operator for SQL databases."""
    criteria = [("name", "INVALID_OP", "John")]

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert "Invalid operator 'INVALID_OP' in criteria" in str(exc_info.value)
    assert "Must be one of" in str(exc_info.value)


def test_validate_invalid_operator_for_parquet():
    """Test validation with SQL-specific operator for Parquet."""
    criteria = [("name", "LIKE", "%John%")]  # LIKE not supported in Parquet

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(criteria, DatabaseType.PARQUET)

    assert "Invalid operator 'LIKE' in criteria" in str(exc_info.value)


def test_validate_invalid_value_for_in_operator():
    """Test validation with invalid value type for IN operator."""
    criteria = [("status", "IN", "not_a_list")]  # String instead of list/tuple/set

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert "Value for 'IN' operator must be a list, tuple, or set" in str(exc_info.value)


def test_validate_invalid_value_for_in_operator_integer():
    """Test validation with integer value for IN operator."""
    criteria = [("id", "IN", 123)]  # Integer instead of collection

    with pytest.raises(FilterValidationError) as exc_info:
        FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert "Value for 'IN' operator must be a list, tuple, or set" in str(exc_info.value)


def test_validate_empty_criteria_list():
    """Test validation with empty criteria list."""
    criteria = []
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    # Should probably handle empty criteria gracefully
    # Depending on implementation, this might return empty where clause or raise error


def test_validate_empty_in_list():
    """Test validation with empty list for IN operator."""
    criteria = [("status", "IN", [])]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    # Should handle empty IN list - resulting in "WHERE status IN ()"
    assert " WHERE status IN ()" in where_clause
    assert params == {}


def test_validate_none_values_in_criteria():
    """Test validation with None values in various positions."""
    criteria = [("column", "=", None)]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert where_clause == " WHERE column = :value_0"
    assert params == {"value_0": None}


def test_validate_unicode_values():
    """Test validation with unicode values."""
    criteria = [("name", "=", "Jöhn Döe 🚀")]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert where_clause == " WHERE name = :value_0"
    assert params == {"value_0": "Jöhn Döe 🚀"}


def test_validate_very_long_column_names():
    """Test validation with very long column names."""
    long_column = "very_" * 50 + "long_column_name"
    criteria = [(long_column, "=", "value")]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert f" WHERE {long_column} = :value_0" == where_clause
    assert params == {"value_0": "value"}


def test_validate_complex_nested_values():
    """Test validation with complex nested values."""
    complex_value = {"nested": {"data": [1, 2, 3]}}
    criteria = [("data", "=", complex_value)]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    assert where_clause == " WHERE data = :value_0"
    assert params == {"value_0": complex_value}


def test_validate_boolean_values():
    """Test validation with boolean values."""
    criteria = [("active", "=", True), ("deleted", "=", False)]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    expected_clause = " WHERE active = :value_0 AND deleted = :value_1"
    expected_params = {"value_0": True, "value_1": False}

    assert where_clause == expected_clause
    assert params == expected_params


def test_validate_numeric_edge_cases():
    """Test validation with numeric edge cases."""
    criteria = [
        ("zero", "=", 0),
        ("negative", "<", -999),
        ("float", ">=", 3.14159),
        ("large", "<=", 1e10),
    ]
    where_clause, params = FilterCriteriaValidator.validate(criteria, DatabaseType.SQLITE)

    expected_clause = (
        " WHERE zero = :value_0 AND negative < :value_1 AND "
        "float >= :value_2 AND large <= :value_3"
    )
    expected_params = {"value_0": 0, "value_1": -999, "value_2": 3.14159, "value_3": 1e10}

    assert where_clause == expected_clause
    assert params == expected_params


# Private method tests


def test_private_validate_criteria_with_invalid_operators():
    """Test _validate_criteria private method with invalid operators."""
    criteria = [("name", "INVALID", "John")]

    with pytest.raises(FilterValidationError):
        FilterCriteriaValidator._validate_criteria(criteria, SQLOperators)


def test_private_validate_criteria_with_valid_operators():
    """Test _validate_criteria private method with valid operators."""
    criteria = [("name", "=", "John")]
    where_clause, params = FilterCriteriaValidator._validate_criteria(
        criteria, SQLOperators
    )

    assert where_clause == " WHERE name = :value_0"
    assert params == {"value_0": "John"}
