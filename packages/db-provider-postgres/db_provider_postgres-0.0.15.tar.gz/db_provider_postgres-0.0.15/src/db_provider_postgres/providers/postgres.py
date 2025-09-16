import contextlib
from typing import Dict, Any, Optional

import sqlalchemy as sa
from sqlalchemy.engine import URL, Connection
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_db_config
from ..exceptions import ConfigurationError
from .base import BaseDatabaseProvider


class PostgresDatabaseProvider(BaseDatabaseProvider):
    """PostgreSQL database provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, env_prefix: str = '',
    isolation_level: str = "AUTOCOMMIT", pool_size: int = 5,
    max_overflow: int = 10, pool_timeout: int = 30,
    pool_recycle: int = 1800, pool_pre_ping: bool = True):

        """
        Initialize PostgreSQL database provider.

        Args:
            config: Configuration dictionary with host, database, user, password, port
            env_prefix: Prefix for environment variables if config is None
            isolation_level: Transaction isolation level
            pool_size: SQLAlchemy connection pool size
            max_overflow: Maximum number of connections to allow above pool_size
            pool_timeout: Number of seconds to wait before giving up on getting a connection
            pool_recycle: Number of seconds after which a connection is recycled
        """
        self.pool_pre_ping = pool_pre_ping
        self.isolation_level = isolation_level
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle

        super().__init__(config, env_prefix)

    def _setup(self) -> None:
        """Set up the PostgreSQL connection engine."""
        try:
            # Get configuration from either dict or environment variables
            self.db_config = get_db_config(self.config, self.env_prefix)

            # Create SQLAlchemy URL object
            url_object = self._create_url_object()

            # Get connection arguments
            connect_args = self._get_connect_args()


            # Create SQLAlchemy engine with better connection management
            self.engine = sa.create_engine(
                url_object,
                isolation_level=self.isolation_level,
                connect_args=connect_args,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=self.pool_pre_ping,  # Test connections before use
                pool_reset_on_return='commit'  # Reset connections when returned to pool
            )
        except (ValueError, KeyError) as e:
            raise ConfigurationError(f"Database configuration error: {e}")
        except Exception as e:
            raise ConnectionError(f"Failed to create database engine: {e}")

    def _create_url_object(self) -> URL:
        """
        Create SQLAlchemy URL object from configuration.

        Returns:
            SQLAlchemy URL object
        """
        return URL.create(
            "postgresql+psycopg",
            username=self.db_config["user"],
            password=self.db_config["password"],
            host=self.db_config["host"],
            port=self.db_config["port"],
            database=self.db_config["database"],
        )

    def _get_connect_args(self) -> Dict[str, Any]:
        """
        Get connection arguments.

        Returns:
            Dictionary with connection arguments
        """
        connect_args = {
            'connect_timeout': self.db_config.get('timeout', 10),
            'keepalives_idle': 600,  # Send keepalive every 10 minutes
            'keepalives_interval': 30,  # Interval between keepalives
            'keepalives_count': 3,  # Number of failed keepalives before considering connection dead
        }
        return connect_args

    def get_session(self):
        from sqlalchemy.orm import sessionmaker

        def create_session(self):
            """Create a new database session."""
            Session = sessionmaker(bind=self.engine)
            return Session()


    def get_connection(self) -> Connection:
        """Get a new database connection."""
        try:
            conn = self.engine.connect()
            return conn
        except SQLAlchemyError as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    @contextlib.contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        with self.engine.begin() as connection:  # Let SQLAlchemy handle connection lifecycle
            yield connection

    def execute_query_with_result(self, query: str, params: Optional[Dict[str, Any]] = None) -> list:
        """
        Execute a query and return the result as a list of dictionaries.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries with query results
        """
        with self.get_connection() as conn:
            if params:
                result = conn.execute(sa.text(query), params)
            else:
                result = conn.execute(sa.text(query))

            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status for monitoring."""
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }