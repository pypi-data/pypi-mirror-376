"""
metapg - Async PostgreSQL pools and raw SQL migrations for multi-database applications.

A modern, async-first library for managing multiple PostgreSQL databases with
connection pooling and raw SQL migrations.

This is a metapackage that combines:
- metapg.pool - Connection pooling
- metapg.migrations - Schema migrations
- metapg.cli - Command-line interface
"""

# Import independent packages
try:
    from metapg import pool
except ImportError:
    pool = None

try:
    from metapg import migration
except ImportError:
    migration = None

try:
    from metapg import cli
except ImportError:
    cli = None

# Import smart cursor interface if pool is available
if pool:
    from metapg.cursor import (
        close_all_pools,
        close_pool,
        cursor,
        init_pool,
        transaction,
    )
    from metapg.pool import connection, get_pool
else:
    # Fallback implementations if pool not installed
    def cursor(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    def transaction(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    def init_pool(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    async def close_pool(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    async def close_all_pools(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    def connection(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )

    def get_pool(*args, **kwargs):
        raise ImportError(
            "metapg.pool is required. Install with: pip install metapg.pool",
        )


__version__ = "0.0.1"
__all__ = [
    # Namespaced modules (may be None if not installed)
    "cli",
    "pool",
    "migration",
    # Smart cursor interface (requires pool)
    "cursor",
    "transaction",
    "init_pool",
    "close_pool",
    "close_all_pools",
    # Pool API (requires pool)
    "connection",
    "get_pool",
]
