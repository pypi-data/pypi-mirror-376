# metapg

**Meta PostgreSQL pools and raw SQL migrations for multi-database applications**

`metapg` is a metapackage that provides a unified interface for PostgreSQL operations through independently installable components.

## Installation

### Install Everything

```bash
pip install metapg[all]
```

### Install Individual Components

```bash
# Connection pooling only
pip install metapg[pool]

# Migrations only  
pip install metapg[migration]

# CLI tools only
pip install metapg[cli]

# Custom combination
pip install metapg[pool,migration]
```

## Quick Start

```python
import metapg

# 🎯 Smart cursor - works with both sync and async!

# Synchronous usage
with metapg.cursor() as cur:
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

# Asynchronous usage (same interface!)
async with metapg.cursor() as cur:
    await cur.execute("SELECT * FROM users")
    users = await cur.fetchall()

# Migrations
runner = metapg.migration.MigrationRunner()
await runner.apply_pending()
```

## Components

### metapg.pool - Connection Pooling

High-performance async and sync PostgreSQL connection pooling.

```python
# Smart interface adapts to context
async with metapg.pool.cursor() as cur:
    await cur.execute("SELECT * FROM users")

with metapg.pool.cursor() as cur:  # Sync version
    cur.execute("SELECT * FROM users")
```

### metapg.migration - Schema Migrations

Raw SQL migrations with dependency tracking and rollback support.

```python
runner = metapg.migration.MigrationRunner()
status = await runner.get_status()
await runner.apply_pending()
```

### metapg.cli - Command Line Interface

Beautiful terminal interface for database operations.

```bash
metapg migration status
metapg migration apply
metapg pool init mydb --dsn postgresql://localhost/mydb
```

## Features

- **🎯 Smart Cursor** - Same interface works with both `with` (sync) and `async with` (async)
- **⚡ Async-first** - Built on psycopg3 with full async/await support
- **🔄 Sync Support** - Full synchronous API when you don't need async
- **🎛️ Multi-database** - Manage multiple PostgreSQL databases with named pools
- **📜 Raw SQL migrations** - Simple, powerful migrations using plain SQL files
- **🧠 Context-aware** - Smart connection reuse with contextvars
- **⚙️ Zero-config** - Works out of the box with sensible defaults
- **🚀 Production-ready** - Proper connection pooling, transactions, and error handling
- **💻 Rich CLI** - Beautiful terminal interface for migration management
- **📦 Modular** - Install only what you need

## Package Architecture

```
metapg/                    # Metapackage (this package)
├── metapg.pool           # Connection pooling
├── metapg.migration      # Schema migrations
└── metapg.cli           # Command-line interface
```

Each component is independently installable and maintained, but they work seamlessly together through the metapackage interface.

## Usage Patterns

### Full Stack (All Components)

```bash
pip install metapg[all]
```

```python
import metapg

# Connection pooling
async with metapg.cursor() as cur:
    await cur.execute("SELECT * FROM users")

# Migrations
runner = metapg.migration.MigrationRunner()
await runner.apply_pending()

# CLI access
metapg.cli.app()  # For programmatic CLI access
```

### Minimal (Pool Only)

```bash
pip install metapg[pool]
```

```python
import metapg

# Only pooling functionality available
async with metapg.cursor() as cur:
    await cur.execute("SELECT * FROM users")

# migration and cli will be None
print(metapg.migration)  # None
print(metapg.cli)        # None
```

### Migration Focus

```bash
pip install metapg[pool,migration]
```

```python
import metapg

# Pooling + migrations available
async with metapg.cursor() as cur:
    await cur.execute("SELECT * FROM users")

runner = metapg.migration.MigrationRunner()
await runner.apply_pending()

# CLI not available
print(metapg.cli)  # None
```

## Environment Variables

- `DATABASE_URL` - Default database connection string
- `DATABASE_URL_{NAME}` - Connection string for named database

## Error Handling

The metapackage provides helpful error messages when components aren't installed:

```python
import metapg

# If metapg.pool not installed
metapg.cursor()  # ImportError: metapg.pool is required. Install with: pip install metapg.pool
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## Individual Package Documentation

- [metapg.pool](https://github.com/metapg/metapg/tree/main/src/pool) - Connection pooling
- [metapg.migration](https://github.com/metapg/metapg/tree/main/src/migration) - Schema migrations
- [metapg.cli](https://github.com/metapg/metapg/tree/main/src/cli) - Command-line interface