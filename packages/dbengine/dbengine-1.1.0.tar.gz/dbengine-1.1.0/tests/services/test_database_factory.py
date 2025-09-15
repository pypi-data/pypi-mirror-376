"""Test DatabaseFactory and related functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from dbengine.core.config import DatabaseConfig, DatabaseType
from dbengine.core.exceptions import DatabaseConfigurationError
from dbengine.engines.parquet import ParquetDatabase
from dbengine.engines.postgresql import PostgreSQLDatabase
from dbengine.engines.sqlite import SQLiteDatabase
from dbengine.services.database_factory import (
    DatabaseFactory,
    create_database,
    create_database_from_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sqlite_config():
    """Create SQLite configuration."""
    return DatabaseConfig(
        database_config={
            "db_type": "sqlite",
            "params": {"path": "test.db"},
        }
    )


@pytest.fixture
def postgresql_config():
    """Create PostgreSQL configuration."""
    return DatabaseConfig(
        database_config={
            "db_type": "postgresql",
            "params": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
            },
        }
    )


@pytest.fixture
def parquet_config():
    """Create Parquet configuration."""
    return DatabaseConfig(
        database_config={
            "db_type": "parquet",
            "params": {"path": "test_data"},
        }
    )


@pytest.fixture
def sample_config_dict():
    """Create sample configuration dictionary."""
    return {
        "database": {
            "db_type": "sqlite",
            "params": {"path": "sample.db"},
        },
        "logging": {"level": "INFO"},
    }


# DatabaseFactory.create() tests


def test_database_factory_create_sqlite(sqlite_config):
    """Test creating SQLite database instance."""
    with patch.object(SQLiteDatabase, "__init__", return_value=None) as mock_init:
        mock_init.return_value = None

        result = DatabaseFactory.create(sqlite_config)

        assert isinstance(result, SQLiteDatabase)
        mock_init.assert_called_once_with(sqlite_config)


def test_database_factory_create_postgresql(postgresql_config):
    """Test creating PostgreSQL database instance."""
    with patch.object(PostgreSQLDatabase, "__init__", return_value=None) as mock_init:
        mock_init.return_value = None

        result = DatabaseFactory.create(postgresql_config)

        assert isinstance(result, PostgreSQLDatabase)
        mock_init.assert_called_once_with(postgresql_config)


def test_database_factory_create_parquet(parquet_config):
    """Test creating Parquet database instance."""
    with patch.object(ParquetDatabase, "__init__", return_value=None) as mock_init:
        mock_init.return_value = None

        result = DatabaseFactory.create(parquet_config)

        assert isinstance(result, ParquetDatabase)
        mock_init.assert_called_once_with(parquet_config)


# DatabaseFactory.from_config_file() tests


def test_database_factory_from_config_file(temp_dir, sample_config_dict):
    """Test creating database from configuration file."""
    config_path = temp_dir / "test_config.yaml"

    with open(config_path, "w") as f:
        yaml.safe_dump(sample_config_dict, f)

    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = DatabaseFactory.from_config_file(config_path)

        assert isinstance(result, SQLiteDatabase)


def test_database_factory_from_config_file_string_path(temp_dir, sample_config_dict):
    """Test creating database from string config file path."""
    config_path = temp_dir / "test_config.yaml"

    with open(config_path, "w") as f:
        yaml.safe_dump(sample_config_dict, f)

    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = DatabaseFactory.from_config_file(str(config_path))

        assert isinstance(result, SQLiteDatabase)


def test_database_factory_from_config_file_not_found(temp_dir):
    """Test error when configuration file doesn't exist."""
    non_existent_path = temp_dir / "non_existent.yaml"

    with pytest.raises(DatabaseConfigurationError):
        DatabaseFactory.from_config_file(non_existent_path)


# DatabaseFactory.from_config_dict() tests


def test_database_factory_from_config_dict(sample_config_dict):
    """Test creating database from configuration dictionary."""
    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = DatabaseFactory.from_config_dict(sample_config_dict)

        assert isinstance(result, SQLiteDatabase)


def test_database_factory_from_config_dict_postgresql():
    """Test creating PostgreSQL database from config dictionary."""
    config_dict = {
        "database": {
            "db_type": "postgresql",
            "params": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
            },
        }
    }

    with patch.object(PostgreSQLDatabase, "__init__", return_value=None):
        result = DatabaseFactory.from_config_dict(config_dict)

        assert isinstance(result, PostgreSQLDatabase)


def test_database_factory_from_config_dict_invalid():
    """Test error with invalid configuration dictionary."""
    invalid_config = {"invalid": "config"}

    with pytest.raises(DatabaseConfigurationError):
        DatabaseFactory.from_config_dict(invalid_config)


# create_database_from_config() tests


def test_create_database_from_config_with_database_config(sqlite_config):
    """Test creating database from DatabaseConfig instance."""
    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = create_database_from_config(sqlite_config)

        assert isinstance(result, SQLiteDatabase)


def test_create_database_from_config_with_path(temp_dir, sample_config_dict):
    """Test creating database from configuration file path."""
    config_path = temp_dir / "test_config.yaml"

    with open(config_path, "w") as f:
        yaml.safe_dump(sample_config_dict, f)

    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = create_database_from_config(config_path)

        assert isinstance(result, SQLiteDatabase)


def test_create_database_from_config_unsupported_type():
    """Test error with unsupported configuration type."""
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        create_database_from_config("invalid_string_config")

    assert "unsupported config type" in str(exc_info.value).lower()
    assert "str" in str(exc_info.value)


# create_database() tests


def test_create_database_sqlite():
    """Test creating SQLite database with create_database function."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ) as mock_open, patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        result = create_database(db_type=DatabaseType.SQLITE, database="test_db")

        assert result == mock_db
        mock_dump.assert_called_once()
        mock_open.assert_called_once()


def test_create_database_postgresql():
    """Test creating PostgreSQL database with create_database function."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ) as mock_open, patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        result = create_database(
            db_type=DatabaseType.POSTGRESQL,
            database="test_db",
            host="localhost",
            user="testuser",
            password="testpass",
        )

        assert result == mock_db
        mock_dump.assert_called_once()
        mock_open.assert_called_once()


def test_create_database_parquet():
    """Test creating Parquet database with create_database function."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ) as mock_open, patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        result = create_database(db_type=DatabaseType.PARQUET, database="test_data")

        assert result == mock_db
        mock_dump.assert_called_once()
        mock_open.assert_called_once()


def test_create_database_invalid_type():
    """Test error with invalid database type."""
    with pytest.raises(NotImplementedError) as exc_info:
        create_database(db_type="invalid_type", database="test_db")

    assert "unknown database type" in str(exc_info.value).lower()


def test_create_database_sqlite_with_string():
    """Test creating SQLite database with string db_type."""
    with patch("yaml.safe_dump"), patch("builtins.open", create=True), patch.object(
        DatabaseFactory, "from_config_file"
    ) as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        result = create_database(db_type="sqlite", database="test_db")

        assert result == mock_db


def test_create_database_postgresql_missing_credentials():
    """Test PostgreSQL creation with missing required credentials."""
    with pytest.raises(AssertionError):
        create_database(
            db_type="postgresql",
            database="test_db",
            host="localhost",
            user="testuser",
            password=None,  # Missing password
        )


def test_create_database_postgresql_missing_host():
    """Test PostgreSQL creation with missing host."""
    with pytest.raises(AssertionError):
        create_database(
            db_type="postgresql",
            database="test_db",
            host=None,
            user="testuser",
            password="testpass",
        )


def test_create_database_missing_database_name():
    """Test error when database name is None."""
    with pytest.raises(AssertionError):
        create_database(db_type="sqlite", database=None)


def test_create_database_config_file_creation():
    """Test that configuration file is created with correct content."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ), patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        create_database(db_type="sqlite", database="test_db")

        # Verify config structure passed to yaml.safe_dump
        call_args = mock_dump.call_args[0][0]  # First argument to safe_dump

        assert "database" in call_args
        assert "logging" in call_args
        assert call_args["database"]["db_type"] == "sqlite"
        assert "params" in call_args["database"]


def test_create_database_postgresql_config_structure():
    """Test PostgreSQL configuration structure."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ), patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        create_database(
            db_type="postgresql",
            database="test_db",
            host="custom_host",
            user="custom_user",
            password="custom_pass",
        )

        # Verify PostgreSQL config structure
        call_args = mock_dump.call_args[0][0]
        db_config = call_args["database"]

        assert db_config["db_type"] == "postgresql"
        assert db_config["params"]["host"] == "custom_host"
        assert db_config["params"]["user"] == "custom_user"
        assert db_config["params"]["password"] == "custom_pass"
        assert db_config["params"]["database"] == "test_db"
        assert db_config["params"]["port"] == 5432


def test_create_database_parquet_config_structure():
    """Test Parquet configuration structure."""
    with patch("yaml.safe_dump") as mock_dump, patch(
        "builtins.open", create=True
    ), patch.object(DatabaseFactory, "from_config_file") as mock_from_file:

        mock_db = MagicMock()
        mock_from_file.return_value = mock_db

        create_database(db_type="parquet", database="test_data")

        # Verify Parquet config structure
        call_args = mock_dump.call_args[0][0]
        db_config = call_args["database"]

        assert db_config["db_type"] == "parquet"
        assert db_config["params"]["path"] == "data_test_data/parquet"


# Integration tests


def test_factory_integration_sqlite(temp_dir):
    """Test complete SQLite database creation flow."""
    config_dict = {
        "database": {
            "db_type": "sqlite",
            "params": {"path": str(temp_dir / "integration_test.db")},
        }
    }

    # This would create a real SQLite database, but we'll mock it
    with patch.object(SQLiteDatabase, "__init__", return_value=None):
        result = DatabaseFactory.from_config_dict(config_dict)
        assert isinstance(result, SQLiteDatabase)


def test_factory_type_consistency():
    """Test that factory creates consistent types."""
    config_dict = {
        "database": {
            "db_type": "postgresql",
            "params": {
                "host": "localhost",
                "port": 5432,
                "database": "test",
                "user": "test",
                "password": "test",
            },
        }
    }

    with patch.object(PostgreSQLDatabase, "__init__", return_value=None):
        # Create through different factory methods
        result1 = DatabaseFactory.from_config_dict(config_dict)

        config = DatabaseConfig(database_config=config_dict["database"])
        result2 = DatabaseFactory.create(config)

        assert type(result1) is type(result2)
        assert isinstance(result1, PostgreSQLDatabase)
        assert isinstance(result2, PostgreSQLDatabase)
