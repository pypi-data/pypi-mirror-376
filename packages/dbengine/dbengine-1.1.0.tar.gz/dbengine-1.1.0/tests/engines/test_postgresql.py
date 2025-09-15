"""Test PostgreSQL database implementation."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from dbengine.core.config import DatabaseConfig
from dbengine.core.exceptions import (
    DatabaseConnectionError,
    DatabaseValidationError,
    DatabaseWriteError,
)
from dbengine.engines.postgresql import PostgreSQLDatabase


@pytest.fixture
def test_config():
    """Create a test configuration for PostgreSQLDatabase."""
    return DatabaseConfig(
        database_config={
            "db_type": "postgresql",
            "params": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "password": "test_password",
                "pool_size": 5,
                "max_overflow": 10,
            },
        },
        logging_config={"level": "INFO"},
    )


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine and connection."""
    mock_engine = Mock()
    mock_connection = Mock()

    # Setup context manager behavior
    mock_connection.__enter__ = Mock(return_value=mock_connection)
    mock_connection.__exit__ = Mock(return_value=None)

    mock_engine.connect.return_value = mock_connection
    return mock_engine, mock_connection


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
    )


@pytest.fixture
def sample_series():
    """Create sample Series for testing."""
    return pd.Series({"id": 4, "name": "Diana", "age": 28})


# Core functionality tests


def test_postgresql_database_init(test_config):
    """Test PostgreSQLDatabase initialisation."""
    with patch("dbengine.engines.postgresql.create_engine") as mock_create_engine:
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)

            assert db.host == "localhost"
            assert db.port == 5432
            assert db.database == "test_db"
            assert db.user == "test_user"
            assert db.password == "test_password"
            assert db.pool_size == 5
            assert db.max_overflow == 10

            mock_create_engine.assert_called_once()


def test_create_engine_connection_string(test_config):
    """Test engine creation with correct connection string."""
    with patch("dbengine.engines.postgresql.create_engine") as mock_create_engine:
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            PostgreSQLDatabase(test_config)

            call_args = mock_create_engine.call_args
            connection_string = call_args[0][0]

            assert "postgresql://" in connection_string
            assert "test_user:test_password" in connection_string
            assert "localhost:5432" in connection_string
            assert "test_db" in connection_string


def test_validate_connection_success(test_config, mock_engine):
    """Test successful connection validation."""
    mock_engine_obj, mock_conn = mock_engine
    mock_result = Mock()
    mock_conn.execute.return_value = mock_result

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        _ = PostgreSQLDatabase(test_config)

        mock_conn.execute.assert_called()
        mock_result.fetchone.assert_called_once()


def test_validate_connection_failure(test_config):
    """Test connection validation failure."""
    with patch("dbengine.engines.postgresql.create_engine") as mock_create_engine:
        mock_engine = Mock()
        mock_engine.connect.side_effect = Exception("Connection failed")
        mock_create_engine.return_value = mock_engine

        with pytest.raises(DatabaseConnectionError):
            PostgreSQLDatabase(test_config)


def test_validate_table_name(test_config, mock_engine):
    """Test table name validation."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)

            # Valid names
            db._validate_table_name("users")
            db._validate_table_name("user_data")
            db._validate_table_name("table-123")

            # Invalid names
            with pytest.raises(DatabaseValidationError):
                db._validate_table_name("invalid table")  # Space

            with pytest.raises(DatabaseValidationError):
                db._validate_table_name("table@name")  # Special character


def test_list_tables(test_config, mock_engine):
    """Test listing tables."""
    mock_engine_obj, mock_conn = mock_engine
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([("users",), ("orders",)]))
    mock_conn.execute.return_value = mock_result

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)

            tables = db.list_tables()

            assert tables == ["users", "orders"]
            mock_conn.execute.assert_called()


def test_write_dataframe(test_config, mock_engine, sample_dataframe):
    """Test writing DataFrame to table."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch("pandas.DataFrame.to_sql") as mock_to_sql:
                db = PostgreSQLDatabase(test_config)
                db.write(table_name="users", item=sample_dataframe)

                mock_to_sql.assert_called_once_with(
                    "users", db.engine, if_exists="append", index=False, method="multi"
                )


def test_write_series(test_config, mock_engine, sample_series):
    """Test writing Series to table."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch("pandas.DataFrame.to_sql") as mock_to_sql:
                db = PostgreSQLDatabase(test_config)
                db.write(table_name="profiles", item=sample_series)

                # Series should be converted to DataFrame
                mock_to_sql.assert_called_once_with(
                    "profiles", db.engine, if_exists="append", index=False, method="multi"
                )


def test_delete_record(test_config, mock_engine):
    """Test deleting record from table."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)
            db.delete(table_name="users", key=123, key_column="id")

            # Verify SQL execution
            mock_conn.execute.assert_called()
            call_args = mock_conn.execute.call_args
            sql_query = str(call_args[0][0])
            params = call_args[0][1]

            assert "DELETE FROM users WHERE id = :key" in sql_query
            assert params == {"key": 123}
            mock_conn.commit.assert_called_once()


def test_query_table(test_config, mock_engine, sample_dataframe):
    """Test querying table data."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch.object(PostgreSQLDatabase, "list_tables", return_value=["users"]):
                with patch(
                    "pandas.read_sql", return_value=sample_dataframe
                ) as mock_read_sql:
                    db = PostgreSQLDatabase(test_config)
                    result = db.query(table_name="users")

                    assert len(result) == 3
                    mock_read_sql.assert_called_once()


def test_query_with_criteria(test_config, mock_engine, sample_dataframe):
    """Test querying table with criteria."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch.object(PostgreSQLDatabase, "list_tables", return_value=["users"]):
                with patch(
                    "pandas.read_sql", return_value=sample_dataframe
                ) as mock_read_sql:
                    with patch(
                        "dbengine.core.filter_operators.FilterCriteriaValidator.validate",
                        return_value=(" WHERE age >= :value_0", {"value_0": 30}),
                    ):
                        db = PostgreSQLDatabase(test_config)
                        db.query(table_name="users", criteria=[("age", ">=", 30)])

                        mock_read_sql.assert_called()


def test_query_all_tables(test_config, mock_engine, sample_dataframe):
    """Test querying all tables."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch.object(
                PostgreSQLDatabase, "list_tables", return_value=["users", "orders"]
            ):
                with patch(
                    "pandas.read_sql", return_value=sample_dataframe
                ) as mock_read_sql:
                    db = PostgreSQLDatabase(test_config)
                    result = db.query(table_name=None)

                    # Should query each table (users and orders)
                    assert mock_read_sql.call_count == 2
                    # Result should contain data from both tables
                    assert len(result) == 6  # 3 records * 2 tables


def test_delete_table(test_config, mock_engine):
    """Test deleting entire table."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)
            db.delete_table("test_table")

            # Verify SQL execution
            mock_conn.execute.assert_called()
            call_args = mock_conn.execute.call_args
            sql_query = str(call_args[0][0])

            assert "DROP TABLE IF EXISTS test_table CASCADE" in sql_query
            mock_conn.commit.assert_called_once()


def test_write_error_handling(test_config, mock_engine, sample_dataframe):
    """Test write operation error handling."""
    mock_engine_obj, mock_conn = mock_engine

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            with patch("pandas.DataFrame.to_sql", side_effect=Exception("Write failed")):
                db = PostgreSQLDatabase(test_config)

                with pytest.raises(DatabaseWriteError) as exc_info:
                    db.write(table_name="users", item=sample_dataframe)

                assert "Failed to write item to table" in str(exc_info.value)
                assert "users" == exc_info.value.table_name


def test_delete_error_handling(test_config, mock_engine):
    """Test delete operation error handling."""
    mock_engine_obj, mock_conn = mock_engine
    mock_conn.execute.side_effect = Exception("Delete failed")

    with patch("dbengine.engines.postgresql.create_engine", return_value=mock_engine_obj):
        with patch.object(PostgreSQLDatabase, "_validate_connection"):
            db = PostgreSQLDatabase(test_config)

            with pytest.raises(DatabaseWriteError) as exc_info:
                db.delete(table_name="users", key=123, key_column="id")

            assert "Failed to delete item from table" in str(exc_info.value)
