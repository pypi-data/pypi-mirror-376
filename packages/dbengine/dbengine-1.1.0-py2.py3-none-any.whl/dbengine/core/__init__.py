"""Core database engine functionality."""

from dbengine.core.config import DatabaseConfig, DatabaseType
from dbengine.core.database import Database
from dbengine.core.exceptions import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
    DatabaseReadError,
    DatabaseValidationError,
    DatabaseWriteError,
)
from dbengine.core.filter_operators import FilterCriteriaValidator

__all__ = [
    "Database",
    "DatabaseConfig",
    "DatabaseType",
    # Exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseWriteError",
    "DatabaseReadError",
    "DatabaseQueryError",
    "DatabaseConfigurationError",
    "DatabaseValidationError",
    "FilterCriteriaValidator",
]
