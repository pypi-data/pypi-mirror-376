from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from dbengine.core.exceptions import DatabaseConfigurationError


class DatabaseType(str, Enum):
    """Supported database types for the dbengine."""

    PARQUET = "parquet"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

    @property
    def required_fields(self) -> list[str]:
        """Get required fields for each database type."""
        field_maps: dict[DatabaseType, list[str]] = {
            DatabaseType.PARQUET: ["path"],
            DatabaseType.SQLITE: ["path"],
            DatabaseType.POSTGRESQL: ["host", "port", "database", "user", "password"],
        }
        return field_maps.get(self, [])

    @staticmethod
    def validate_db_type(db_type: str) -> "DatabaseType":
        """Validate and return the DatabaseType enum."""
        try:
            return DatabaseType(str(db_type).lower())
        except ValueError:
            raise DatabaseConfigurationError(
                f"Unsupported database type: '{db_type}'. "
                f"Supported types are: {[dt.value for dt in DatabaseType]}"
            )


@dataclass
class DatabaseConfig:
    """Configuration manager for database connections and settings."""

    # Core configuration data
    database_config: dict[str, Any] = field(default_factory=dict)
    logging_config: dict[str, Any] = field(default_factory=dict)
    db_type: DatabaseType = field(init=False, repr=False)

    # Optional path to the configuration file
    config_path: Optional[Path] = None

    def __post_init__(self):
        """Validate configuration after initialisation."""
        db_type_str = self.database_config.get("db_type")
        if not db_type_str:
            raise DatabaseConfigurationError(
                "Database type ('db_type') is required in the configuration."
            )
        self.db_type = DatabaseType.validate_db_type(str(db_type_str).lower())

        self._validate_database_config()

    @property
    def connection_params(self) -> dict[str, Any]:
        """Get connection parameters."""
        return self.database_config.get("params", {})

    def _validate_database_config(self):
        """Validate database configuration"""

        # Validate required fields
        missing_fields = [
            field
            for field in self.db_type.required_fields
            if (
                (field not in self.connection_params)
                or (self.connection_params.get(field) is None)
            )
        ]

        if missing_fields:
            raise DatabaseConfigurationError(
                "Missing required configuration fields for "
                f"{self.db_type}: {missing_fields}",
                details=f"Available config: {list(self.connection_params.keys())}",
            )
