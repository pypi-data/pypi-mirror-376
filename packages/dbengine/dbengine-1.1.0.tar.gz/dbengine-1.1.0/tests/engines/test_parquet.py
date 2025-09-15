"""Test Parquet database implementation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from dbengine.core.config import DatabaseConfig
from dbengine.core.exceptions import (
    DatabaseConnectionError,
    DatabaseValidationError,
    DatabaseWriteError,
)
from dbengine.engines.parquet import ParquetDatabase


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration for ParquetDatabase."""
    return DatabaseConfig(
        database_config={
            "db_type": "parquet",
            "params": {
                "path": str(temp_dir),
                "compression": "snappy",
                "engine": "pyarrow",
            },
        },
        logging_config={"level": "INFO"},
    )


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "active": [True, True, False],
        }
    )


@pytest.fixture
def sample_series():
    """Create sample Series for testing."""
    return pd.Series({"id": 4, "name": "Diana", "age": 28, "active": True})


# Core functionality tests


def test_parquet_database_init(test_config):
    """Test ParquetDatabase initialisation."""
    db = ParquetDatabase(test_config)

    assert db.path == Path(test_config.connection_params.get("path"))
    assert db.compression == "snappy"
    assert db.engine == "pyarrow"
    assert db.path.exists()


def test_parquet_database_init_permission_error(temp_dir):
    """Test ParquetDatabase initialisation with permission error."""
    config = DatabaseConfig(
        database_config={
            "db_type": "parquet",
            "params": {"path": str(temp_dir)},
        }
    )

    # Mock touch to raise PermissionError
    with patch.object(Path, "touch", side_effect=PermissionError("Permission denied")):
        with pytest.raises(DatabaseConnectionError):
            ParquetDatabase(config)


def test_validate_table_name(test_config):
    """Test table name validation."""
    db = ParquetDatabase(test_config)

    # Valid names
    db._validate_table_name("users")
    db._validate_table_name("user_data")
    db._validate_table_name("table-123")

    # Invalid names
    with pytest.raises(DatabaseValidationError):
        db._validate_table_name("invalid table")  # Space

    with pytest.raises(DatabaseValidationError):
        db._validate_table_name("table@name")  # Special character


def test_list_tables(test_config, sample_dataframe):
    """Test listing tables."""
    db = ParquetDatabase(test_config)

    # Initially empty
    assert db.list_tables() == []

    # Add table
    db.write(table_name="users", item=sample_dataframe)
    assert db.list_tables() == ["users"]


def test_write_dataframe(test_config, sample_dataframe):
    """Test writing DataFrame to table."""
    db = ParquetDatabase(test_config)

    db.write(table_name="users", item=sample_dataframe)

    # Verify file was created
    table_path = db._get_table_path("users")
    assert table_path.exists()

    # Verify data integrity
    result = db.query(table_name="users")
    pd.testing.assert_frame_equal(result, sample_dataframe)


def test_write_series(test_config, sample_series: pd.Series):
    """Test writing Series to table."""
    db = ParquetDatabase(test_config)

    db.write(table_name="user", item=sample_series)

    # Verify data was converted to DataFrame
    result = db.query(table_name="user")

    expected = pd.DataFrame([sample_series])
    pd.testing.assert_frame_equal(result, expected)


def test_write_append_data(test_config, sample_dataframe, sample_series):
    """Test appending data to existing table."""
    db = ParquetDatabase(test_config)

    # Write initial data
    db.write(table_name="users", item=sample_dataframe)

    # Append new data
    db.write(table_name="users", item=sample_series)

    # Verify combined data
    result = db.query(table_name="users")
    assert len(result) == 4  # 3 original + 1 new


def test_delete_record(test_config, sample_dataframe):
    """Test deleting record from table."""
    db = ParquetDatabase(test_config)

    # Write data
    db.write(table_name="users", item=sample_dataframe)

    # Delete record
    db.delete(table_name="users", key_column="id", key=2)

    # Verify deletion
    result = db.query(table_name="users")
    assert len(result) == 2
    assert 2 not in result["id"].values


def test_query_table(test_config, sample_dataframe):
    """Test querying table data."""
    db = ParquetDatabase(test_config)
    db.write(table_name="users", item=sample_dataframe)

    # Query all data
    result = db.query(table_name="users")
    pd.testing.assert_frame_equal(result, sample_dataframe)


def test_query_with_criteria(test_config, sample_dataframe):
    """Test querying table with criteria."""
    db = ParquetDatabase(test_config)
    db.write(table_name="users", item=sample_dataframe)

    # Query with filter
    result = db.query(table_name="users", criteria=[("age", ">=", 30)])

    expected = sample_dataframe[sample_dataframe["age"] >= 30]
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True), expected.reset_index(drop=True)
    )


def test_query_all_tables(test_config, sample_dataframe):
    """Test querying all tables."""
    db = ParquetDatabase(test_config)

    # Create multiple tables
    db.write(table_name="users", item=sample_dataframe)
    db.write(table_name="employees", item=sample_dataframe)

    result = db.query(table_name=None)

    # Should contain data from both tables with table column
    assert len(result) == 6  # 3 records * 2 tables
    assert "table" in result.columns
    assert set(result["table"].unique()) == {"users", "employees"}


def test_delete_table_with_confirmation(test_config, sample_dataframe):
    """Test deleting entire table."""
    db = ParquetDatabase(test_config)
    db.write(table_name="users", item=sample_dataframe)

    # Mock user confirmation
    with patch("builtins.input", return_value="y"):
        db.delete_table("users")

    # Verify table is deleted
    assert "users" not in db.list_tables()


def test_delete_table_cancelled(test_config, sample_dataframe):
    """Test cancelling table deletion."""
    db = ParquetDatabase(test_config)
    db.write(table_name="users", item=sample_dataframe)

    # Mock user rejection
    with patch("builtins.input", return_value="n"):
        db.delete_table("users")

    # Verify table still exists
    assert "users" in db.list_tables()


def test_write_error_handling(test_config, sample_dataframe):
    """Test write operation error handling."""
    db = ParquetDatabase(test_config)

    # Mock to_parquet to raise exception
    with patch.object(pd.DataFrame, "to_parquet", side_effect=OSError("Disk full")):
        with pytest.raises(DatabaseWriteError) as exc_info:
            db.write(table_name="users", item=sample_dataframe)

        assert "Failed to write item to table users" in str(exc_info.value)
        assert "users" == exc_info.value.table_name
