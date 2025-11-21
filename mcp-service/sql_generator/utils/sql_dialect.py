from typing import Any, Dict, List, Optional, Union


class SQLDialect:
    """Utility class for handling SQL dialect differences between PostgreSQL and MySQL."""

    @staticmethod
    def get_limit_offset(
        dialect: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> str:
        """
        Generate LIMIT/OFFSET clause based on the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')
            limit: Maximum number of rows to return
            offset: Number of rows to skip

        Returns:
            SQL LIMIT/OFFSET clause
        """
        if limit is None and offset is None:
            return ""

        if dialect == "postgresql":
            parts = []
            if limit is not None:
                parts.append(f"LIMIT {limit}")
            if offset is not None:
                parts.append(f"OFFSET {offset}")
            return " ".join(parts)
        else:  # MySQL
            if offset is None:
                return f"LIMIT {limit}" if limit is not None else ""
            else:
                return f"LIMIT {offset}, {limit if limit is not None else 18446744073709551615}"

    @staticmethod
    def get_returning(dialect: str, returning_cols: Optional[List[str]] = None) -> str:
        """
        Generate RETURNING clause based on the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')
            returning_cols: List of column names to return

        Returns:
            SQL RETURNING clause
        """
        if not returning_cols:
            return ""

        if dialect == "postgresql":
            return f"RETURNING {', '.join(returning_cols)}"
        else:  # MySQL doesn't support RETURNING
            return ""

    @staticmethod
    def get_upsert(
        dialect: str, table: str, unique_cols: List[str], update_cols: List[str]
    ) -> str:
        """
        Generate upsert (insert on duplicate key update) clause based on the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')
            table: Table name
            unique_cols: List of columns that form the unique constraint
            update_cols: List of columns to update on conflict

        Returns:
            SQL upsert clause
        """
        if dialect == "postgresql":
            update_clause = ", ".join(
                [f"{col} = EXCLUDED.{col}" for col in update_cols]
            )
            return (
                f"ON CONFLICT ({', '.join(unique_cols)}) DO UPDATE SET {update_clause}"
            )
        else:  # MySQL
            update_clause = ", ".join([f"{col} = VALUES({col})" for col in update_cols])
            return f"ON DUPLICATE KEY UPDATE {update_clause}"

    @staticmethod
    def get_true_false(dialect: str) -> Dict[str, str]:
        """
        Get the true/false literals for the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')

        Returns:
            Dictionary with 'true' and 'false' keys
        """
        if dialect == "postgresql":
            return {"true": "TRUE", "false": "FALSE"}
        else:  # MySQL
            return {"true": "1", "false": "0"}

    @staticmethod
    def get_now_function(dialect: str) -> str:
        """
        Get the function to get current timestamp for the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')

        Returns:
            SQL function for current timestamp
        """
        if dialect == "postgresql":
            return "NOW()"
        else:  # MySQL
            return "NOW()"

    @staticmethod
    def get_random_function(dialect: str) -> str:
        """
        Get the function to generate random values for the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')

        Returns:
            SQL function for random values
        """
        if dialect == "postgresql":
            return "RANDOM()"
        else:  # MySQL
            return "RAND()"

    @staticmethod
    def get_regex_operator(dialect: str, case_sensitive: bool = True) -> str:
        """
        Get the regex operator for the dialect.

        Args:
            dialect: SQL dialect ('postgresql' or 'mysql')
            case_sensitive: Whether the regex should be case sensitive

        Returns:
            SQL regex operator
        """
        if dialect == "postgresql":
            return "~" if case_sensitive else "~*"
        else:  # MySQL
            return "REGEXP"  # MySQL REGEXP is case-insensitive by default
