"""
DBEngine - A unified interface for database operations across multiple backends.

Supports SQLite, Parquet, and PostgreSQL databases with a consistent pandas-based API.
"""

__version__ = "1.1.0"

from pathlib import Path

from .core import DatabaseConfigurationError  # Exceptions
from .core import (
    Database,
    DatabaseConfig,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
    DatabaseReadError,
    DatabaseType,
    DatabaseValidationError,
    DatabaseWriteError,
    FilterCriteriaValidator,
)
from .engines import ParquetDatabase, PostgreSQLDatabase, SQLiteDatabase
from .services import (
    DatabaseConfigFactory,
    DatabaseFactory,
    create_config_file,
    create_database,
    create_database_from_config,
)
from .utils import PostgreSQLServerManager, create_postgres_server

__root__ = Path(__file__).parent.parent.parent

__all__ = [
    "Database",
    "DatabaseConfig",
    "DatabaseType",
    "FilterCriteriaValidator",
    # Exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseWriteError",
    "DatabaseReadError",
    "DatabaseQueryError",
    "DatabaseConfigurationError",
    "DatabaseValidationError",
    # Engines and their configs
    "SQLiteDatabase",
    "ParquetDatabase",
    "PostgreSQLDatabase",
    # Factory services
    "DatabaseFactory",
    "DatabaseConfigFactory",
    "create_config_file",
    "create_database",
    "create_database_from_config",
    # Server management utilities
    "PostgreSQLServerManager",
    "create_postgres_server",
]
