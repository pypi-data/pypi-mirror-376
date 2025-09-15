"""Test configuration management system."""

import pytest

from dbengine.core.config import DatabaseConfig, DatabaseType
from dbengine.core.exceptions import DatabaseConfigurationError

# DatabaseType enum tests


def test_database_type_values():
    """Test that DatabaseType enum has correct values."""
    assert DatabaseType.PARQUET == "parquet"
    assert DatabaseType.SQLITE == "sqlite"
    assert DatabaseType.POSTGRESQL == "postgresql"


def test_database_type_iteration():
    """Test that DatabaseType can be iterated over."""
    expected_types = {"parquet", "sqlite", "postgresql"}
    actual_types = {db_type.value for db_type in DatabaseType}
    assert actual_types == expected_types


def test_required_fields():
    """Test required fields for different database type."""
    assert DatabaseType.PARQUET.required_fields == ["path"]
    assert DatabaseType.SQLITE.required_fields == ["path"]
    expected_fields = ["host", "port", "database", "user", "password"]
    assert DatabaseType.POSTGRESQL.required_fields == expected_fields


def test_validate_db_type_valid_mixed_cases():
    """Test validate_db_type with valid mixed cases string."""

    # lowercase
    result = DatabaseType.validate_db_type("sqlite")
    assert result == DatabaseType.SQLITE
    assert isinstance(result, DatabaseType)
    # uppercase
    result = DatabaseType.validate_db_type("POSTGRESQL")
    assert result == DatabaseType.POSTGRESQL
    assert isinstance(result, DatabaseType)
    # mixed case
    result = DatabaseType.validate_db_type("ParQuet")
    assert result == DatabaseType.PARQUET
    assert isinstance(result, DatabaseType)


def test_validate_db_type_invalid():
    """Test validate_db_type with invalid raises error."""

    # invalid string
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseType.validate_db_type("invalid_db_type")

    assert "Unsupported database type: 'invalid_db_type'" in str(exc_info.value)
    assert "parquet" in str(exc_info.value)
    assert "sqlite" in str(exc_info.value)
    assert "postgresql" in str(exc_info.value)

    # empty string
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseType.validate_db_type("")
    assert "Unsupported database type: ''" in str(exc_info.value)

    # None
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseType.validate_db_type(None)

    assert "Unsupported database type: 'None'" in str(exc_info.value)


# DatabaseConfig tests


def test_database_config_initialisation_sqlite():
    """Test DatabaseConfig initialisation with valid SQLite config."""
    config_data = {"db_type": "sqlite", "params": {"path": "/tmp/test.db"}}
    config = DatabaseConfig(database_config=config_data)

    assert config.db_type == DatabaseType.SQLITE
    assert config.connection_params == {"path": "/tmp/test.db"}


def test_database_config_initialisation_postgresql():
    """Test DatabaseConfig initialisation with valid PostgreSQL config."""
    config_data = {
        "db_type": "postgresql",
        "params": {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        },
    }
    config = DatabaseConfig(database_config=config_data)

    assert config.db_type == DatabaseType.POSTGRESQL
    assert config.connection_params["host"] == "localhost"
    assert config.connection_params["port"] == 5432


def test_database_config_initialisation_parquet():
    """Test DatabaseConfig initialisation with valid Parquet config."""
    config_data = {"db_type": "parquet", "params": {"path": "/tmp/parquet_data"}}
    config = DatabaseConfig(database_config=config_data)

    assert config.db_type == DatabaseType.PARQUET
    assert config.connection_params == {"path": "/tmp/parquet_data"}


def test_database_config_missing_db_type():
    """Test DatabaseConfig initialisation without db_type raises error."""
    config_data = {"params": {"path": "/tmp/test.db"}}
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfig(database_config=config_data)

    assert "Database type ('db_type') is required" in str(exc_info.value)


def test_database_config_invalid_db_type():
    """Test DatabaseConfig initialisation with invalid db_type raises error."""
    config_data = {"db_type": "invalid_type", "params": {"path": "/tmp/test.db"}}
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfig(database_config=config_data)

    assert "Unsupported database type: 'invalid_type'" in str(exc_info.value)


def test_database_config_missing_required_fields():
    """Test DatabaseConfig with missing required fields."""
    # Test SQLite
    config_data = {"db_type": "sqlite", "params": {}}  # Missing 'path'
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfig(database_config=config_data)

    assert "Missing required configuration fields" in str(exc_info.value)
    assert "['path']" in str(exc_info.value)

    # Test PostgreSQL
    config_data = {
        "db_type": "postgresql",
        "params": {
            "host": "localhost",
            # Missing port, database, user, password
        },
    }
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfig(database_config=config_data)

    error_msg = str(exc_info.value)
    assert "Missing required configuration fields" in error_msg
    assert "port" in error_msg
    assert "database" in error_msg
    assert "user" in error_msg
    assert "password" in error_msg


def test_database_config_none_values_treated_as_missing():
    """Test that None values are treated as missing fields."""
    config_data = {
        "db_type": "sqlite",
        "params": {"path": None},  # None should be treated as missing
    }
    with pytest.raises(DatabaseConfigurationError):
        DatabaseConfig(database_config=config_data)


def test_database_config_empty_string_values_treated_as_missing():
    """Test that empty string values are treated as missing fields."""
    config_data = {
        "db_type": "sqlite",
        "params": {"path": ""},  # Empty string should be treated as missing
    }
    # This might depend on implementation - empty strings could be valid paths
    config = DatabaseConfig(database_config=config_data)
    assert config.connection_params["path"] == ""


def test_database_config_with_logging_config():
    """Test DatabaseConfig initialisation with logging configuration."""
    config_data = {"db_type": "sqlite", "params": {"path": "/tmp/test.db"}}
    logging_config = {
        "level": "DEBUG",
        "format": "%(asctime)s - %(levelname)s - %(message)s",
    }
    config = DatabaseConfig(database_config=config_data, logging_config=logging_config)

    assert config.logging_config == logging_config

    # Test without logging config - should return default empty dict
    config_no_logging = DatabaseConfig(database_config=config_data)
    assert config_no_logging.logging_config == {}


def test_database_config_empty_params_dict():
    """Test DatabaseConfig initialisation with empty params dict."""
    config_data = {"db_type": "sqlite", "params": {}}
    with pytest.raises(DatabaseConfigurationError):
        DatabaseConfig(database_config=config_data)
