import os
import logging
from typing import Optional
import oracledb

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    A class to manage opening and closing Oracle database connections.

    Supports credentials from environment variables or direct parameters.
    Environment variables checked:
    - ORACLE_USER or ORACLE_USERNAME
    - ORACLE_PASSWORD
    - ORACLE_DSN or TNS_ADMIN
    """

    def __init__(self, user: Optional[str] = None, password: Optional[str] = None, dsn: Optional[str] = None):
        """
        Initializes the connection manager with credentials.

        Credentials can be provided directly or via environment variables.
        Direct parameters take precedence over environment variables.

        Args:
            user (str, optional): The Oracle database username.
                                 Falls back to ORACLE_USER or ORACLE_USERNAME env vars.
            password (str, optional): The password for the user.
                                     Falls back to ORACLE_PASSWORD env var.
            dsn (str, optional): The Data Source Name (TNS name or Easy Connect string).
                                Falls back to ORACLE_DSN env var.

        Raises:
            ValueError: If required credentials cannot be determined from parameters or environment.
        """
        self._user = user or os.getenv('ORACLE_USER') or os.getenv('ORACLE_USERNAME')
        self._password = password or os.getenv('ORACLE_PASSWORD')
        self._dsn = dsn or os.getenv('ORACLE_DSN')
        self._connection = None

        # Handle TNS_ADMIN for Oracle Wallet connections
        tns_admin = os.getenv('TNS_ADMIN')
        if tns_admin:
            os.environ['TNS_ADMIN'] = tns_admin
            logger.info(f"Set TNS_ADMIN to: {tns_admin}")

        if not all([self._user, self._password, self._dsn]):
            missing = []
            if not self._user:
                missing.append("user (parameter or ORACLE_USER/ORACLE_USERNAME env var)")
            if not self._password:
                missing.append("password (parameter or ORACLE_PASSWORD env var)")
            if not self._dsn:
                missing.append("dsn (parameter or ORACLE_DSN env var)")

            raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    def open_connection(self) -> Optional[oracledb.Connection]:
        """
        Establishes a connection to the Oracle database.

        Returns:
            oracledb.Connection: The database connection object if successful, None otherwise.

        Raises:
            oracledb.Error: If connection fails due to database-related issues.
        """
        if self._connection is None:
            try:
                self._connection = oracledb.connect(
                    user=self._user, password=self._password, dsn=self._dsn
                )
                logger.info("Connection to Oracle database established successfully.")
            except oracledb.Error as e:
                logger.error(f"Error connecting to Oracle database: {e}")
                raise
        return self._connection

    def close_connection(self) -> None:
        """
        Closes the established connection.
        """
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Connection to Oracle database closed.")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
                raise

    def __enter__(self):
        """Context manager entry."""
        return self.open_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()

    @property
    def is_connected(self) -> bool:
        """
        Check if the connection is active.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connection is not None


def open_connection(user: Optional[str] = None, password: Optional[str] = None, dsn: Optional[str] = None) -> oracledb.Connection:
    """
    Convenience function to open an Oracle database connection.

    Args:
        user (str, optional): Oracle username or uses environment variable
        password (str, optional): Oracle password or uses environment variable
        dsn (str, optional): Oracle DSN or uses environment variable

    Returns:
        oracledb.Connection: Active database connection

    Raises:
        ValueError: If credentials are missing
        oracledb.Error: If connection fails
    """
    manager = ConnectionManager(user, password, dsn)
    return manager.open_connection()


def close_connection(connection: oracledb.Connection) -> None:
    """
    Convenience function to close an Oracle database connection.

    Args:
        connection: The connection object to close
    """
    if connection:
        try:
            connection.close()
            logger.info("Connection closed.")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
            raise
