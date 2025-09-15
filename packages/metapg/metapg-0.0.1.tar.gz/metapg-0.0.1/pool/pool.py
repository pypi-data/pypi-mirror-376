"""Async database connection pool with multi-database support."""

import os
import urllib.parse as urlparse
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

# Context variables for each database
_connection_stacks: dict[str, ContextVar[AsyncConnection | None]] = {}
_cursor_stacks: dict[str, ContextVar[Any | None]] = {}

# Pool registry for multiple databases
_pools: dict[str, AsyncConnectionPool] = {}


def _get_context_vars(db_name: str) -> tuple[ContextVar, ContextVar]:
    """Get or create context variables for a database."""
    if db_name not in _connection_stacks:
        _connection_stacks[db_name] = ContextVar(f"{db_name}_connection", default=None)
        _cursor_stacks[db_name] = ContextVar(f"{db_name}_cursor", default=None)
    return _connection_stacks[db_name], _cursor_stacks[db_name]


def _parse_connection_string(conn_string: str) -> str:
    """Convert postgresql:// URL to psycopg3 connection string format."""
    if conn_string.startswith("postgresql://"):
        parsed = urlparse.urlparse(conn_string)

        # Build psycopg3 connection string
        parts = []
        if parsed.hostname:
            parts.append(f"host={parsed.hostname}")
        if parsed.port:
            parts.append(f"port={parsed.port}")
        if parsed.path and len(parsed.path) > 1:
            parts.append(f"dbname={parsed.path[1:]}")
        if parsed.username:
            parts.append(f"user={parsed.username}")
        if parsed.password:
            parts.append(f"password={parsed.password}")

        return " ".join(parts)
    return conn_string


def _get_default_dsn() -> str:
    """Get default DSN from environment or use localhost."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/postgres",
    )


def init_pool(
    dsn: str | None = None,
    *,
    db_name: str = "default",
    min_size: int = 1,
    max_size: int = 20,
    **kwargs: Any,
) -> AsyncConnectionPool:
    """Initialize a connection pool for a database.

    Args:
        dsn: Database connection string. If None, uses DATABASE_URL env var
        db_name: Name for this database pool
        min_size: Minimum connections in pool
        max_size: Maximum connections in pool
        **kwargs: Additional psycopg pool arguments

    Returns:
        The initialized connection pool

    Example:
        >>> init_pool("postgresql://user:pass@localhost/mydb", db_name="mydb")
        >>> init_pool(db_name="analytics", max_size=50)
    """
    if dsn is None:
        if db_name == "default":
            dsn = _get_default_dsn()
        else:
            env_key = f"DATABASE_URL_{db_name.upper()}"
            dsn = os.getenv(env_key)
            if dsn is None:
                msg = f"No DSN provided and {env_key} not set"
                raise ValueError(msg)

    # Parse connection string
    parsed_dsn = _parse_connection_string(dsn)

    # Close existing pool if any
    if db_name in _pools:
        _pools[db_name].close()

    # Create new pool
    pool = AsyncConnectionPool(
        parsed_dsn,
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row},
        **kwargs,
    )

    _pools[db_name] = pool
    return pool


def get_pool(db_name: str = "default") -> AsyncConnectionPool:
    """Get an existing connection pool.

    Args:
        db_name: Name of the database pool

    Returns:
        The connection pool for the database

    Raises:
        ValueError: If pool doesn't exist
    """
    if db_name not in _pools:
        # Try to auto-initialize default pool
        if db_name == "default":
            return init_pool(db_name=db_name)
        msg = f"Pool '{db_name}' not initialized. Call init_pool() first."
        raise ValueError(msg)

    return _pools[db_name]


async def close_pool(db_name: str = "default") -> None:
    """Close a specific database pool.

    Args:
        db_name: Name of the database pool to close
    """
    if db_name in _pools:
        await _pools[db_name].close()
        del _pools[db_name]


async def close_all_pools() -> None:
    """Close all database pools."""
    for pool in _pools.values():
        await pool.close()
    _pools.clear()


@asynccontextmanager
async def connection(db_name: str = "default") -> AsyncGenerator[AsyncConnection, None]:
    """Get a database connection with automatic cleanup.

    Args:
        db_name: Name of the database to connect to

    Yields:
        Database connection

    Example:
        >>> async with connection() as conn:
        ...     async with conn.cursor() as cur:
        ...         await cur.execute("SELECT 1")
    """
    connection_var, _ = _get_context_vars(db_name)

    # Check if we already have a connection in this context
    existing_conn = connection_var.get()
    if existing_conn is not None:
        yield existing_conn
        return

    # Get new connection from pool
    pool = get_pool(db_name)
    async with pool.connection() as conn:
        token = connection_var.set(conn)
        try:
            yield conn
        finally:
            connection_var.reset(token)


@asynccontextmanager
async def cursor(db_name: str = "default") -> AsyncGenerator[Any, None]:
    """Get a database cursor with automatic cleanup.

    Args:
        db_name: Name of the database to connect to

    Yields:
        Database cursor

    Example:
        >>> async with cursor() as cur:
        ...     await cur.execute("SELECT * FROM users")
        ...     users = await cur.fetchall()
    """
    connection_var, cursor_var = _get_context_vars(db_name)

    # Check if we already have a cursor in this context
    existing_cursor = cursor_var.get()
    if existing_cursor is not None:
        yield existing_cursor
        return

    # Get connection and create cursor
    async with connection(db_name) as conn, conn.cursor() as cur:
        token = cursor_var.set(cur)
        try:
            yield cur
        finally:
            cursor_var.reset(token)


@asynccontextmanager
async def transaction(db_name: str = "default") -> AsyncGenerator[None, None]:
    """Execute within a database transaction.

    Args:
        db_name: Name of the database to use

    Example:
        >>> async with transaction():
        ...     async with cursor() as cur:
        ...         await cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
        ...         await cur.execute("INSERT INTO posts (title) VALUES (%s)", ("Hello",))
    """
    async with connection(db_name) as conn, conn.transaction():
        yield
