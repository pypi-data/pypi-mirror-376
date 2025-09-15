from enum import Enum
from typing import Any

from dbengine.core.config import DatabaseType


class BaseOperators(Enum):
    """Base operators supported by all engines."""


class SQLOperators(BaseOperators):
    """SQL-specific operators."""

    EQUAL = "="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    IN = "IN"
    LIKE = "LIKE"
    NOT_NULL = "IS NOT NULL"
    NULL = "IS NULL"


class ParquetOperators(BaseOperators):
    """Parquet-specific operators (same as base for now)."""

    EQUAL = "="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    IN = "IN"


class FilterValidationError(Exception):
    """Custom exception for filter validation errors."""

    pass


# Validator Class for filter criteria
class FilterCriteriaValidator:
    """Validate filter criteria for different database engines."""

    @staticmethod
    def validate(
        criteria: list[tuple[str, str, Any]], engine: DatabaseType
    ) -> tuple[str, dict[str, Any]]:
        """
        Validate criteria based on the engine type and
        return sql-like where clause and parameters.
        Args:
            criteria: List of tuples (column, operator, value)
            engine: Type of the database engine

        Returns:
            Tuple of (where_clause: str, params: dict)
        Raises:
            FilterValidationError: If criteria is invalid
        """

        # Assert structure of criteria
        if not all(
            isinstance(c, tuple)
            and len(c) == 3
            and isinstance(c[0], str)
            and isinstance(c[1], str)
            for c in criteria
        ):
            raise FilterValidationError(
                "Criteria must be a list of tuples as "
                "(column: str, operator: str, value: Any)"
            )

        match engine:
            case DatabaseType.SQLITE | DatabaseType.POSTGRESQL:
                return FilterCriteriaValidator._validate_criteria(criteria, SQLOperators)
            case DatabaseType.PARQUET:
                return FilterCriteriaValidator._validate_criteria(
                    criteria, ParquetOperators
                )
            case _:
                raise FilterValidationError(f"Unsupported database type: {engine}")

    @staticmethod
    def _validate_criteria(
        criteria: list[tuple[str, str, Any]], valid_operators: type[BaseOperators]
    ):
        """Validate SQL-specific filter criteria."""
        params = {}
        clauses = []
        for idx, (column, operator, value) in enumerate(criteria):
            if operator not in valid_operators._value2member_map_:
                raise FilterValidationError(
                    f"Invalid operator '{operator}' in criteria.\n"
                    f"Must be one of {[op.value for op in valid_operators]}"
                )

            if operator in ["IS NULL", "IS NOT NULL"]:
                clauses.append(f"{column} {operator}")
            elif operator == "IN":
                if not isinstance(value, (list, tuple, set)):
                    raise FilterValidationError(
                        "Value for 'IN' operator must be a list, tuple, or set"
                    )
                placeholders = []
                for i, v in enumerate(value):
                    placeholders.append(f":value_{idx}_{i}")
                    params[f"value_{idx}_{i}"] = v

                clauses.append(f"{column} IN ({', '.join(placeholders)})")
            else:
                clauses.append(f"{column} {operator} :value_{idx}")
                params[f"value_{idx}"] = value

        where_clause = " WHERE " + " AND ".join(clauses)
        return where_clause, params
