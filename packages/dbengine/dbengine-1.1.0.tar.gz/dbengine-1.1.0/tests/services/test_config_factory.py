"""Test DatabaseConfigFactory and create_config_file functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from dbengine.core.config import DatabaseConfig
from dbengine.core.exceptions import DatabaseConfigurationError
from dbengine.services.config_factory import DatabaseConfigFactory, create_config_file


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_sqlite_config():
    """Create sample SQLite configuration data."""
    return {
        "database": {
            "db_type": "sqlite",
            "params": {"path": "test.db"},
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def sample_postgresql_config():
    """Create sample PostgreSQL configuration data."""
    return {
        "database": {
            "db_type": "postgresql",
            "params": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
            },
        },
        "logging": {"level": "DEBUG"},
    }


# DatabaseConfigFactory.from_dict tests


def test_from_dict_sqlite_config(sample_sqlite_config):
    """Test creating DatabaseConfig from SQLite dictionary."""
    config = DatabaseConfigFactory.from_dict(sample_sqlite_config)

    assert isinstance(config, DatabaseConfig)
    assert config.db_type.value == "sqlite"
    assert config.connection_params["path"] == "test.db"
    assert config.logging_config["level"] == "INFO"


def test_from_dict_postgresql_config(sample_postgresql_config):
    """Test creating DatabaseConfig from PostgreSQL dictionary."""
    config = DatabaseConfigFactory.from_dict(sample_postgresql_config)

    assert isinstance(config, DatabaseConfig)
    assert config.db_type.value == "postgresql"
    assert config.connection_params["host"] == "localhost"
    assert config.connection_params["port"] == 5432


def test_from_dict_missing_database_config():
    """Test error when database config is missing."""
    invalid_config = {"logging": {"level": "INFO"}}

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfigFactory.from_dict(invalid_config)

    assert "missing database config" in str(exc_info.value).lower()


def test_from_dict_empty_database_config():
    """Test error when database config is empty."""
    invalid_config = {"database": {}}

    with pytest.raises(DatabaseConfigurationError):
        DatabaseConfigFactory.from_dict(invalid_config)


def test_from_dict_default_logging_config():
    """Test default logging configuration is applied."""
    minimal_config = {
        "database": {
            "db_type": "sqlite",
            "params": {"path": "test.db"},
        }
    }

    config = DatabaseConfigFactory.from_dict(minimal_config)

    assert config.logging_config["level"] == "INFO"
    assert config.logging_config["format"] is None


# DatabaseConfigFactory.from_file tests


def test_from_file_valid_config(temp_dir, sample_sqlite_config):
    """Test loading config from valid file."""
    config_path = temp_dir / "test_config.yaml"

    with open(config_path, "w") as f:
        yaml.safe_dump(sample_sqlite_config, f)

    config = DatabaseConfigFactory.from_file(config_path)

    assert isinstance(config, DatabaseConfig)
    assert config.db_type.value == "sqlite"
    assert config.config_path == config_path


def test_from_file_non_existent_file(temp_dir):
    """Test error when config file doesn't exist."""
    non_existent_path = temp_dir / "non_existent.yaml"

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfigFactory.from_file(non_existent_path)

    assert "not found" in str(exc_info.value).lower()


def test_from_file_empty_file(temp_dir):
    """Test error when config file is empty."""
    empty_config_path = temp_dir / "empty_config.yaml"
    empty_config_path.touch()  # Create empty file

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfigFactory.from_file(empty_config_path)

    assert "empty" in str(exc_info.value).lower()


def test_from_file_invalid_yaml(temp_dir):
    """Test error when config file has invalid YAML."""
    invalid_config_path = temp_dir / "invalid.yaml"

    with open(invalid_config_path, "w") as f:
        f.write("invalid: yaml: content: [")

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        DatabaseConfigFactory.from_file(invalid_config_path)

    assert "failed to load" in str(exc_info.value).lower()


# create_config_file tests


def test_create_config_file_sqlite(temp_dir):
    """Test creating SQLite configuration file."""
    config_path = temp_dir / "sqlite_config.yaml"

    create_config_file(config_path, db_type="sqlite")

    assert config_path.exists()

    # Verify content
    with open(config_path, "r") as f:
        content = yaml.safe_load(f)

    assert content["database"]["db_type"] == "sqlite"
    assert "path" in content["database"]["params"]
    assert content["logging"]["level"] == "INFO"


def test_create_config_file_postgresql(temp_dir):
    """Test creating PostgreSQL configuration file."""
    config_path = temp_dir / "postgres_config.yaml"

    create_config_file(config_path, db_type="postgresql")

    assert config_path.exists()

    # Verify content
    with open(config_path, "r") as f:
        content = yaml.safe_load(f)

    assert content["database"]["db_type"] == "postgresql"
    assert "host" in content["database"]["params"]
    assert "port" in content["database"]["params"]


def test_create_config_file_parquet(temp_dir):
    """Test creating Parquet configuration file."""
    config_path = temp_dir / "parquet_config.yaml"

    create_config_file(config_path, db_type="parquet")

    assert config_path.exists()

    # Verify content
    with open(config_path, "r") as f:
        content = yaml.safe_load(f)

    assert content["database"]["db_type"] == "parquet"
    assert "path" in content["database"]["params"]


def test_create_config_file_unsupported_type(temp_dir):
    """Test error with unsupported database type."""
    config_path = temp_dir / "unsupported_config.yaml"

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        create_config_file(config_path, db_type="unsupported_db")

    assert "unsupported database type" in str(exc_info.value).lower()
    assert "unsupported_db" in str(exc_info.value)


def test_create_config_file_existing_file_no_overwrite(temp_dir):
    """Test error when file exists and overwrite is False."""
    config_path = temp_dir / "existing_config.yaml"

    # Create initial file
    create_config_file(config_path, db_type="sqlite")

    # Try to create again without overwrite
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        create_config_file(config_path, db_type="postgresql", overwrite=False)

    assert "already exists" in str(exc_info.value).lower()


def test_create_config_file_existing_file_with_overwrite(temp_dir):
    """Test overwriting existing file when overwrite is True."""
    config_path = temp_dir / "overwrite_config.yaml"

    # Create initial SQLite config
    create_config_file(config_path, db_type="sqlite")

    # Overwrite with PostgreSQL config
    create_config_file(config_path, db_type="postgresql", overwrite=True)

    # Verify it was overwritten
    with open(config_path, "r") as f:
        content = yaml.safe_load(f)

    assert content["database"]["db_type"] == "postgresql"


def test_create_config_file_load_config_true(temp_dir):
    """Test creating file and loading config."""
    config_path = temp_dir / "load_config.yaml"

    result = create_config_file(config_path, db_type="sqlite", load_config=True)

    assert isinstance(result, DatabaseConfig)
    assert result.db_type.value == "sqlite"
    assert config_path.exists()


def test_create_config_file_load_config_false(temp_dir):
    """Test creating file without loading config."""
    config_path = temp_dir / "no_load_config.yaml"

    result = create_config_file(config_path, db_type="sqlite", load_config=False)

    assert result is None
    assert config_path.exists()


def test_create_config_file_load_existing_config(temp_dir):
    """Test loading existing config when load_config is True."""
    config_path = temp_dir / "existing_load_config.yaml"

    # Create initial file
    create_config_file(config_path, db_type="sqlite")

    # Load existing file
    result = create_config_file(
        config_path, db_type="postgresql", load_config=True, overwrite=False
    )

    assert isinstance(result, DatabaseConfig)
    assert result.db_type.value == "sqlite"  # Should load existing, not create new


def test_create_config_file_creates_directory(temp_dir):
    """Test that parent directories are created."""
    nested_path = temp_dir / "configs" / "database" / "test_config.yaml"

    create_config_file(nested_path, db_type="sqlite")

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_create_config_file_write_error_handling(temp_dir):
    """Test handling of write errors."""
    # Try to create config in a read-only directory (if possible)
    config_path = temp_dir / "readonly" / "config.yaml"
    config_path.parent.mkdir()
    config_path.parent.chmod(0o444)  # Read-only

    with pytest.raises(DatabaseConfigurationError) as exc_info:
        create_config_file(config_path, db_type="sqlite")

    assert "permission denied" in str(exc_info.value.details).lower()

    # Restore permissions for cleanup
    try:
        config_path.parent.chmod(0o755)
    except Exception:
        pass


# Integration tests


def test_config_factory_round_trip(temp_dir):
    """Test creating config file and loading it back."""
    config_path = temp_dir / "round_trip_config.yaml"

    # Create and load config
    original_config = create_config_file(config_path, db_type="sqlite", load_config=True)

    # Load again from file
    loaded_config = DatabaseConfigFactory.from_file(config_path)

    assert original_config.db_type == loaded_config.db_type
    assert original_config.connection_params == loaded_config.connection_params
