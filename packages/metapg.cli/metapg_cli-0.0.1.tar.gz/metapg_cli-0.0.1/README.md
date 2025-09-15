# metapg.cli

**Rich command-line interface for PostgreSQL operations**

`metapg.cli` provides a beautiful terminal interface for managing PostgreSQL databases, migrations, and connection pools with rich formatting and intuitive commands.

## Installation

```bash
pip install metapg.cli
```

This will install the `metapg` command globally.

## Quick Start

```bash
# Migration commands
metapg migration status --db main
metapg migration apply --db main
metapg migration rollback --db main --steps 1
metapg migration create add_users_table --db main

# Pool management commands
metapg pool init mydb --dsn postgresql://localhost/mydb
metapg pool status mydb
metapg pool close mydb

# Backwards compatible (migration commands at root)
metapg status --db main
metapg apply --db main
```

## Features

- **🎨 Rich Interface** - Beautiful tables, colors, and formatting
- **📊 Migration Management** - Status, apply, rollback, and create migrations
- **🔗 Pool Management** - Initialize, monitor, and close connection pools
- **⚡ Fast Operations** - Efficient database operations with progress indicators
- **🛡️ Safe Defaults** - Confirmation prompts for destructive operations
- **🎛️ Multi-Database** - Support for multiple named databases

## Commands

### Migration Commands

```bash
# Show migration status
metapg migration status [--db DATABASE] [--migrations-dir DIR]

# Apply pending migrations
metapg migration apply [--db DATABASE] [--target MIGRATION] [--force]

# Rollback migrations
metapg migration rollback [--db DATABASE] [--steps N]

# Create new migration
metapg migration create MIGRATION_NAME [--db DATABASE]
```

### Pool Commands

```bash
# Initialize connection pool
metapg pool init [DATABASE] [--dsn CONNECTION_STRING] [--min-size N] [--max-size N]

# Show pool status
metapg pool status [DATABASE]

# Close connection pool
metapg pool close [DATABASE] [--force]
```

### Global Options

- `--help` - Show help message
- `--db DATABASE` - Specify database name (default: "default")
- `--force` - Skip confirmation prompts

## Configuration

### Environment Variables

- `DATABASE_URL` - Default database connection string
- `DATABASE_URL_{NAME}` - Connection string for named database

### Migration Directory Structure

```
migrations/
├── default/           # Default database migrations
│   ├── 001_initial.sql
│   └── 002_add_users.sql
└── analytics/         # Named database migrations
    └── 001_events.sql
```

### Migration File Format

```sql
-- Create users table
-- Created: 2024-01-01

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ROLLBACK (optional)
DROP TABLE users;
```

## Examples

### Basic Migration Workflow

```bash
# Check current status
metapg migration status

# Create new migration
metapg migration create add_posts_table

# Edit the generated SQL file, then apply
metapg migration apply

# Check status again
metapg migration status
```

### Multi-Database Setup

```bash
# Set up multiple databases
export DATABASE_URL="postgresql://localhost/main_db"
export DATABASE_URL_ANALYTICS="postgresql://localhost/analytics_db"

# Manage each database separately
metapg migration status --db default
metapg migration status --db analytics

metapg migration apply --db analytics
```

### Pool Management

```bash
# Initialize pools for different databases
metapg pool init main --dsn postgresql://localhost/main_db
metapg pool init analytics --dsn postgresql://localhost/analytics_db

# Monitor pool status
metapg pool status main
metapg pool status analytics

# Close when done
metapg pool close main
```

## Rich Output

The CLI provides beautiful, colored output with:

- **📊 Status Tables** - Clear migration status with timestamps
- **✅ Success Indicators** - Green checkmarks for completed operations
- **⚠️ Warning Messages** - Yellow alerts for pending operations
- **❌ Error Messages** - Red indicators for failed operations
- **📈 Progress Bars** - Visual progress for long operations

## Integration

### Programmatic Usage

```python
import metapg.cli

# Access the CLI app directly
app = metapg.cli.app

# Use in scripts or other applications
if __name__ == "__main__":
    app()
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run migrations
  run: |
    metapg migration apply --force --db production
    metapg migration status --db production
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Part of metapg

This package is part of the [metapg](https://github.com/metapg/metapg) metapackage for PostgreSQL operations.