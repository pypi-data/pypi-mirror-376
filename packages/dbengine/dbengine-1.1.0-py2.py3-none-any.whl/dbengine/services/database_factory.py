"""Database factory for creating database instances based on configuration."""

from pathlib import Path
from typing import Optional, Union

import yaml

from dbengine.core.config import DatabaseConfig, DatabaseType
from dbengine.core.database import Database
from dbengine.core.exceptions import DatabaseConfigurationError
from dbengine.engines.parquet import ParquetDatabase
from dbengine.engines.postgresql import PostgreSQLDatabase
from dbengine.engines.sqlite import SQLiteDatabase
from dbengine.services.config_factory import DatabaseConfigFactory


class DatabaseFactory:
    """Factory for creating database instances based on configuration protocols."""

    @staticmethod
    def create(
        config: DatabaseConfig,
    ) -> Database | ParquetDatabase | SQLiteDatabase | PostgreSQLDatabase:
        """
        Create database instance based on configuration type.

        Args:
            config: DatabaseConfig instance

        Returns:
            Database: The appropriate database instance (SQLite, PostgreSQL, or Parquet)

        Raises:
            DatabaseConfigurationError: If database type is unsupported
        """
        match config.db_type:
            case DatabaseType.SQLITE:
                return SQLiteDatabase(config)
            case DatabaseType.POSTGRESQL:
                return PostgreSQLDatabase(config)
            case DatabaseType.PARQUET:
                return ParquetDatabase(config)

    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> Database:
        """
        Create database instance directly from configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Database: The appropriate database instance
        """
        config = DatabaseConfigFactory.from_file(config_path)
        return cls.create(config)

    @classmethod
    def from_config_dict(cls, config_dict: dict) -> Database:
        """
        Create database instance directly from configuration dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Database: The appropriate database instance
        """
        config = DatabaseConfigFactory.from_dict(config_dict)
        return cls.create(config)


def create_database_from_config(config: Union[DatabaseConfig, Path]) -> Database:
    """
    Create a database instance from the given configuration.

    Args:
        config (Union[DatabaseConfig, Path]): The database configuration.

    Raises:
        DatabaseConfigurationError: If the config type is unsupported.

    Returns:
        Database: The created database instance.
    """
    if isinstance(config, Path):
        return DatabaseFactory.from_config_file(config)
    elif isinstance(config, DatabaseConfig):
        return DatabaseFactory.create(config)
    raise DatabaseConfigurationError(
        f"Unsupported config type: {type(config).__name__}",
        details="Supported types: DatabaseConfig, Path",
    )


def create_database(
    db_type: DatabaseType,
    database: str,
    host: Optional[str] = "localhost",
    user: Optional[str] = "dbengine",
    password: Optional[str] = None,
) -> Database:
    """
    Create a database instance based on the provided parameters.
    If db_type is "sqlite" or "parquet", a local file-based database is created.
    If db_type is "postgresql", a PostgreSQL database connection is established.

    Args:
        db_type (str): The type of database (e.g., "sqlite", "postgresql", "parquet").
        database (str): The name of the database.
        host (Optional[str], optional): The database host. Defaults to "localhost".
        user (Optional[str], optional): The database user. Defaults to "dbengine".
        password (Optional[str], optional): The database password. Defaults to None.

    Raises:
        NotImplementedError: If the database type is unknown.
        DatabaseConfigurationError: If the database configuration is invalid.

    Returns:
        Database: The created database instance.
    """
    # Validate inputs
    assert database is not None
    if db_type.lower() not in ["parquet", "sqlite", "postgresql"]:
        raise NotImplementedError(f"Unknown database type {db_type}")

    if db_type.lower() == "postgresql":
        assert host is not None
        assert user is not None
        assert password is not None

    config_path = f"./config_{database}.yaml"

    match db_type.lower():
        case "sqlite":
            db_config = {
                "db_type": "sqlite",
                "params": {"path": f"data_{database}.db"},
            }

        case "parquet":
            db_config = {
                "db_type": "parquet",
                "params": {"path": f"data_{database}/parquet"},
            }
        case "postgresql":
            db_config = {
                "db_type": "postgresql",
                "params": {
                    "host": host or "localhost",
                    "port": 5432,
                    "database": database or "dbengine",
                    "user": user or "dbengine",
                    "password": password or "password",
                },
            }
        case _:
            raise DatabaseConfigurationError(
                f"Unsupported database type: {db_type}",
                config_path=str(config_path),
            )
    config = {
        "database": db_config,
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": None,
        },
    }

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, indent=2)

    return DatabaseFactory.from_config_file(config_path)
