"""Tests for smart cursor functionality (sync and async)."""

import os

import pytest

# Import from metapg metapackage (which uses the smart cursor)
import metapg


@pytest.fixture(autouse=True)
async def cleanup_pools():
    """Clean up pools after each test."""
    yield
    await metapg.close_all_pools()


def test_sync_cursor():
    """Test synchronous cursor functionality."""
    with metapg.cursor() as cur:
        cur.execute("SELECT 1 as test_value")
        result = cur.fetchone()
        assert result["test_value"] == 1


@pytest.mark.asyncio
async def test_async_cursor():
    """Test asynchronous cursor functionality."""
    async with metapg.cursor() as cur:
        await cur.execute("SELECT 1 as test_value")
        result = await cur.fetchone()
        assert result["test_value"] == 1


def test_sync_transaction():
    """Test synchronous transaction functionality."""
    # Create a test table
    with metapg.cursor() as cur:
        cur.execute(
            """
            CREATE TEMP TABLE test_sync_tx (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """,
        )

    # Test successful transaction
    with metapg.transaction(), metapg.cursor() as cur:
        cur.execute("INSERT INTO test_sync_tx (value) VALUES (%s)", ("test",))

    # Verify data was committed
    with metapg.cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM test_sync_tx")
        result = cur.fetchone()
        assert result["count"] == 1

    # Test rollback on exception
    with pytest.raises(Exception), metapg.transaction(), metapg.cursor() as cur:
        cur.execute(
            "INSERT INTO test_sync_tx (value) VALUES (%s)",
            ("rollback",),
        )
        raise Exception("Test rollback")

    # Verify data was rolled back
    with metapg.cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM test_sync_tx")
        result = cur.fetchone()
        assert result["count"] == 1  # Still only 1 record


@pytest.mark.asyncio
async def test_async_transaction():
    """Test asynchronous transaction functionality."""
    # Create a test table
    async with metapg.cursor() as cur:
        await cur.execute(
            """
            CREATE TEMP TABLE test_async_tx (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """,
        )

    # Test successful transaction
    async with metapg.transaction(), metapg.cursor() as cur:
        await cur.execute(
            "INSERT INTO test_async_tx (value) VALUES (%s)",
            ("test",),
        )

    # Verify data was committed
    async with metapg.cursor() as cur:
        await cur.execute("SELECT COUNT(*) as count FROM test_async_tx")
        result = await cur.fetchone()
        assert result["count"] == 1

    # Test rollback on exception
    with pytest.raises(Exception):
        async with metapg.transaction():
            async with metapg.cursor() as cur:
                await cur.execute(
                    "INSERT INTO test_async_tx (value) VALUES (%s)",
                    ("rollback",),
                )
                raise Exception("Test rollback")

    # Verify data was rolled back
    async with metapg.cursor() as cur:
        await cur.execute("SELECT COUNT(*) as count FROM test_async_tx")
        result = await cur.fetchone()
        assert result["count"] == 1  # Still only 1 record


def test_sync_named_database():
    """Test synchronous cursor with named database."""
    # Set up test environment
    os.environ["DATABASE_URL_SYNC_TEST"] = os.getenv("DATABASE_URL")

    with metapg.cursor("sync_test") as cur:
        cur.execute("SELECT 'sync_test_db' as db_name")
        result = cur.fetchone()
        assert result["db_name"] == "sync_test_db"


@pytest.mark.asyncio
async def test_async_named_database():
    """Test asynchronous cursor with named database."""
    # Set up test environment
    os.environ["DATABASE_URL_ASYNC_TEST"] = os.getenv("DATABASE_URL")

    async with metapg.cursor("async_test") as cur:
        await cur.execute("SELECT 'async_test_db' as db_name")
        result = await cur.fetchone()
        assert result["db_name"] == "async_test_db"


def test_sync_nested_cursors():
    """Test nested synchronous cursor usage with connection reuse."""
    with metapg.cursor() as cur1:
        cur1.execute("SELECT 1 as outer_value")
        outer_result = cur1.fetchone()

        # Nested cursor should reuse the same connection
        with metapg.cursor() as cur2:
            cur2.execute("SELECT 2 as inner_value")
            inner_result = cur2.fetchone()

            assert outer_result["outer_value"] == 1
            assert inner_result["inner_value"] == 2


@pytest.mark.asyncio
async def test_async_nested_cursors():
    """Test nested asynchronous cursor usage with connection reuse."""
    async with metapg.cursor() as cur1:
        await cur1.execute("SELECT 1 as outer_value")
        outer_result = await cur1.fetchone()

        # Nested cursor should reuse the same connection
        async with metapg.cursor() as cur2:
            await cur2.execute("SELECT 2 as inner_value")
            inner_result = await cur2.fetchone()

            assert outer_result["outer_value"] == 1
            assert inner_result["inner_value"] == 2


def test_pool_initialization():
    """Test pool initialization returns both sync and async pools."""
    async_pool, sync_pool = metapg.init_pool(
        dsn=os.getenv("DATABASE_URL"),
        db_name="test_smart",
        min_size=1,
        max_size=5,
    )

    assert async_pool is not None
    assert sync_pool is not None

    # Test using both pools
    with metapg.cursor("test_smart") as cur:
        cur.execute("SELECT 'sync_pool' as pool_type")
        result = cur.fetchone()
        assert result["pool_type"] == "sync_pool"


@pytest.mark.asyncio
async def test_pool_initialization_async():
    """Test using async pool after initialization."""
    metapg.init_pool(
        dsn=os.getenv("DATABASE_URL"),
        db_name="test_smart_async",
        min_size=1,
        max_size=5,
    )

    async with metapg.cursor("test_smart_async") as cur:
        await cur.execute("SELECT 'async_pool' as pool_type")
        result = await cur.fetchone()
        assert result["pool_type"] == "async_pool"
