"""Smart cursor that works with both sync and async contexts."""

import os
import socket
import urllib.parse as urlparse
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import Any

from psycopg import AsyncConnection, Connection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool, ConnectionPool

# Context variables for each database (both sync and async)
_async_connection_stacks: dict[str, ContextVar[AsyncConnection | None]] = {}
_sync_connection_stacks: dict[str, ContextVar[Connection | None]] = {}
_async_cursor_stacks: dict[str, ContextVar[Any | None]] = {}
_sync_cursor_stacks: dict[str, ContextVar[Any | None]] = {}

# Pool registry for multiple databases (both sync and async)
_async_pools: dict[str, AsyncConnectionPool] = {}
_sync_pools: dict[str, ConnectionPool] = {}


def _parse_connection_string(conn_string: str) -> str:
    """Convert postgresql:// URL to psycopg connection string format."""
    if conn_string.startswith("postgresql://"):
        parsed = urlparse.urlparse(conn_string)

        # Build psycopg connection string
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


def _get_application_name(application_name: str | None = None) -> str:
    """Get application name with fallback logic.
    
    Args:
        application_name: Explicit application name
        
    Returns:
        Application name following fallback priority:
        1. Explicit application_name parameter
        2. METAPG_APPLICATION_NAME environment variable
        3. PGAPPNAME environment variable (PostgreSQL standard)
        4. 'metapg@hostname'
    """
    if application_name is not None:
        return application_name
        
    # Check environment variables
    env_name = (
        os.getenv("METAPG_APPLICATION_NAME") or 
        os.getenv("PGAPPNAME")
    )
    
    if env_name is not None:
        return env_name
    
    # Generate default name: metapg@hostname
    hostname = socket.gethostname()
    return f"metapg@{hostname}"


def _get_async_context_vars(db_name: str) -> tuple[ContextVar, ContextVar]:
    """Get or create async context variables for a database."""
    if db_name not in _async_connection_stacks:
        _async_connection_stacks[db_name] = ContextVar(
            f"{db_name}_async_connection",
            default=None,
        )
        _async_cursor_stacks[db_name] = ContextVar(
            f"{db_name}_async_cursor",
            default=None,
        )
    return _async_connection_stacks[db_name], _async_cursor_stacks[db_name]


def _get_sync_context_vars(db_name: str) -> tuple[ContextVar, ContextVar]:
    """Get or create sync context variables for a database."""
    if db_name not in _sync_connection_stacks:
        _sync_connection_stacks[db_name] = ContextVar(
            f"{db_name}_sync_connection",
            default=None,
        )
        _sync_cursor_stacks[db_name] = ContextVar(
            f"{db_name}_sync_cursor",
            default=None,
        )
    return _sync_connection_stacks[db_name], _sync_cursor_stacks[db_name]


def _init_async_pool(
    dsn: str | None = None,
    *,
    db_name: str = "default",
    min_size: int = 1,
    max_size: int = 20,
    application_name: str | None = None,
    **kwargs: Any,
) -> AsyncConnectionPool:
    """Initialize an async connection pool."""
    if dsn is None:
        if db_name == "default":
            dsn = _get_default_dsn()
        else:
            env_key = f"DATABASE_URL_{db_name.upper()}"
            dsn = os.getenv(env_key)
            if dsn is None:
                msg = f"No DSN provided and {env_key} not set"
                raise ValueError(msg)

    parsed_dsn = _parse_connection_string(dsn)
    
    # Get application name and add to connection kwargs
    app_name = _get_application_name(application_name)

    if db_name in _async_pools:
        _async_pools[db_name].close()

    pool = AsyncConnectionPool(
        parsed_dsn,
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row, "application_name": app_name},
        **kwargs,
    )

    _async_pools[db_name] = pool
    return pool


def _init_sync_pool(
    dsn: str | None = None,
    *,
    db_name: str = "default",
    min_size: int = 1,
    max_size: int = 20,
    application_name: str | None = None,
    **kwargs: Any,
) -> ConnectionPool:
    """Initialize a sync connection pool."""
    if dsn is None:
        if db_name == "default":
            dsn = _get_default_dsn()
        else:
            env_key = f"DATABASE_URL_{db_name.upper()}"
            dsn = os.getenv(env_key)
            if dsn is None:
                msg = f"No DSN provided and {env_key} not set"
                raise ValueError(msg)

    parsed_dsn = _parse_connection_string(dsn)
    
    # Get application name and add to connection kwargs
    app_name = _get_application_name(application_name)

    if db_name in _sync_pools:
        _sync_pools[db_name].close()

    pool = ConnectionPool(
        parsed_dsn,
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row, "application_name": app_name},
        **kwargs,
    )

    _sync_pools[db_name] = pool
    return pool


def _get_async_pool(db_name: str = "default") -> AsyncConnectionPool:
    """Get an async connection pool."""
    if db_name not in _async_pools:
        if db_name == "default":
            return _init_async_pool(db_name=db_name)
        msg = f"Async pool '{db_name}' not initialized. Call init_pool() first."
        raise ValueError(msg)
    return _async_pools[db_name]


def _get_sync_pool(db_name: str = "default") -> ConnectionPool:
    """Get a sync connection pool."""
    if db_name not in _sync_pools:
        if db_name == "default":
            return _init_sync_pool(db_name=db_name)
        msg = f"Sync pool '{db_name}' not initialized. Call init_pool() first."
        raise ValueError(msg)
    return _sync_pools[db_name]


@asynccontextmanager
async def _async_connection(
    db_name: str = "default",
) -> AsyncGenerator[AsyncConnection, None]:
    """Get an async database connection with automatic cleanup."""
    connection_var, _ = _get_async_context_vars(db_name)

    existing_conn = connection_var.get()
    if existing_conn is not None:
        yield existing_conn
        return

    pool = _get_async_pool(db_name)
    async with pool.connection() as conn:
        token = connection_var.set(conn)
        try:
            yield conn
        finally:
            connection_var.reset(token)


@contextmanager
def _sync_connection(db_name: str = "default") -> Generator[Connection, None, None]:
    """Get a sync database connection with automatic cleanup."""
    connection_var, _ = _get_sync_context_vars(db_name)

    existing_conn = connection_var.get()
    if existing_conn is not None:
        yield existing_conn
        return

    pool = _get_sync_pool(db_name)
    with pool.connection() as conn:
        token = connection_var.set(conn)
        try:
            yield conn
        finally:
            connection_var.reset(token)


@asynccontextmanager
async def _async_cursor(db_name: str = "default") -> AsyncGenerator[Any, None]:
    """Get an async database cursor with automatic cleanup."""
    connection_var, cursor_var = _get_async_context_vars(db_name)

    existing_cursor = cursor_var.get()
    if existing_cursor is not None:
        yield existing_cursor
        return

    async with _async_connection(db_name) as conn, conn.cursor() as cur:
        token = cursor_var.set(cur)
        try:
            yield cur
        finally:
            cursor_var.reset(token)


@contextmanager
def _sync_cursor(db_name: str = "default") -> Generator[Any, None, None]:
    """Get a sync database cursor with automatic cleanup."""
    connection_var, cursor_var = _get_sync_context_vars(db_name)

    existing_cursor = cursor_var.get()
    if existing_cursor is not None:
        yield existing_cursor
        return

    with _sync_connection(db_name) as conn, conn.cursor() as cur:
        token = cursor_var.set(cur)
        try:
            yield cur
        finally:
            cursor_var.reset(token)


@asynccontextmanager
async def _async_transaction(db_name: str = "default") -> AsyncGenerator[None, None]:
    """Execute within an async database transaction."""
    async with _async_connection(db_name) as conn, conn.transaction():
        yield


@contextmanager
def _sync_transaction(db_name: str = "default") -> Generator[None, None, None]:
    """Execute within a sync database transaction."""
    with _sync_connection(db_name) as conn, conn.transaction():
        yield


class SmartCursor:
    """A cursor that works with both sync and async contexts.

    Usage:
        # Async usage
        async with metapg.cursor() as cur:
            await cur.execute("SELECT 1")

        # Sync usage
        with metapg.cursor() as cur:
            cur.execute("SELECT 1")
    """

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name

    # Async context manager
    async def __aenter__(self):
        self._async_cursor_cm = _async_cursor(self.db_name)
        self._cursor = await self._async_cursor_cm.__aenter__()
        return self._cursor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._async_cursor_cm.__aexit__(exc_type, exc_val, exc_tb)

    # Sync context manager
    def __enter__(self):
        self._sync_cursor_cm = _sync_cursor(self.db_name)
        self._cursor = self._sync_cursor_cm.__enter__()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._sync_cursor_cm.__exit__(exc_type, exc_val, exc_tb)


class SmartTransaction:
    """A transaction that works with both sync and async contexts."""

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name

    # Async context manager
    async def __aenter__(self):
        self._async_tx_cm = _async_transaction(self.db_name)
        return await self._async_tx_cm.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._async_tx_cm.__aexit__(exc_type, exc_val, exc_tb)

    # Sync context manager
    def __enter__(self):
        self._sync_tx_cm = _sync_transaction(self.db_name)
        return self._sync_tx_cm.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._sync_tx_cm.__exit__(exc_type, exc_val, exc_tb)


def cursor(db_name: str = "default") -> SmartCursor:
    """Get a smart cursor that works with both sync and async contexts.

    Args:
        db_name: Name of the database to connect to

    Returns:
        A smart cursor that adapts to sync or async usage

    Examples:
        # Async usage
        async with metapg.cursor() as cur:
            await cur.execute("SELECT * FROM users")
            users = await cur.fetchall()

        # Sync usage
        with metapg.cursor() as cur:
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
    """
    return SmartCursor(db_name)


def transaction(db_name: str = "default") -> SmartTransaction:
    """Get a smart transaction that works with both sync and async contexts.

    Args:
        db_name: Name of the database to use

    Returns:
        A smart transaction that adapts to sync or async usage

    Examples:
        # Async usage
        async with metapg.transaction():
            async with metapg.cursor() as cur:
                await cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))

        # Sync usage
        with metapg.transaction():
            with metapg.cursor() as cur:
                cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
    """
    return SmartTransaction(db_name)


# Pool management functions
def init_pool(
    dsn: str | None = None,
    *,
    db_name: str = "default",
    min_size: int = 1,
    max_size: int = 20,
    application_name: str | None = None,
    **kwargs: Any,
) -> tuple[AsyncConnectionPool, ConnectionPool]:
    """Initialize both async and sync connection pools.

    Args:
        dsn: Database connection string
        db_name: Name for this database pool
        min_size: Minimum connections in pool  
        max_size: Maximum connections in pool
        application_name: Application name for connection identification.
            Falls back to METAPG_APPLICATION_NAME, PGAPPNAME env vars,
            or 'metapg@hostname'
        **kwargs: Additional psycopg pool arguments

    Returns:
        Tuple of (async_pool, sync_pool)
    """
    async_pool = _init_async_pool(
        dsn,
        db_name=db_name,
        min_size=min_size,
        max_size=max_size,
        application_name=application_name,
        **kwargs,
    )
    sync_pool = _init_sync_pool(
        dsn,
        db_name=db_name,
        min_size=min_size,
        max_size=max_size,
        application_name=application_name,
        **kwargs,
    )
    return async_pool, sync_pool


async def close_pool(db_name: str = "default") -> None:
    """Close both async and sync pools for a database."""
    if db_name in _async_pools:
        await _async_pools[db_name].close()
        del _async_pools[db_name]

    if db_name in _sync_pools:
        _sync_pools[db_name].close()
        del _sync_pools[db_name]


async def close_all_pools() -> None:
    """Close all async and sync pools."""
    for pool in _async_pools.values():
        await pool.close()
    _async_pools.clear()

    for pool in _sync_pools.values():
        pool.close()
    _sync_pools.clear()
