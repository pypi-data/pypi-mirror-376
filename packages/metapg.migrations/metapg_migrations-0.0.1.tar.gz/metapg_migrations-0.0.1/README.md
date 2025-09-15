# metapg.migration

**Raw SQL migrations for PostgreSQL with dependency tracking and rollback support**

`metapg.migration` provides a powerful migration system using plain SQL files with support for dependencies, rollbacks, and multi-database environments.

## Installation

```bash
pip install metapg.migration
```

## Quick Start

```python
import metapg.migration

# Create migration runner
runner = metapg.migration.MigrationRunner(db_name="main")

# Check migration status
status = await runner.get_status()
print(f"Applied: {len(status.applied)}, Pending: {len(status.pending)}")

# Apply pending migrations
applied = await runner.apply_pending()
print(f"Applied migrations: {applied}")

# Rollback if needed
await runner.rollback_migration("002_add_users")
```

## Features

- **📜 Raw SQL** - Write migrations in plain SQL for full database feature access
- **🔄 Rollback Support** - Optional rollback SQL in the same file
- **📊 Dependency Tracking** - Declare migration dependencies
- **✅ Checksums** - Detect migration file changes after application
- **🎛️ Multi-Database** - Support for multiple named databases
- **⚡ Async-First** - Built on async database operations
- **🔒 Transaction Safety** - Each migration runs in its own transaction

## Migration File Format

Create migration files in `migrations/{db_name}/` directory:

```sql
-- migrations/default/001_create_users.sql

-- Create users table
-- Description: Add user authentication system
-- Depends: (none)

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ROLLBACK (optional)
DROP INDEX idx_users_email;
DROP TABLE users;
```

### File Naming Convention

- Format: `{version}_{description}.sql`
- Version: 3-digit zero-padded number (001, 002, 003...)
- Description: Snake_case description

Examples:
- `001_initial_schema.sql`
- `002_add_users_table.sql`
- `003_add_posts_index.sql`

## API Reference

### Migration Runner

```python
import metapg.migration

# Create runner for specific database
runner = metapg.migration.MigrationRunner(
    db_name="default",
    migrations_dir=Path("migrations/default")
)

# Get migration status
status = await runner.get_status()

# Apply specific migration
migration = metapg.migration.Migration.from_file(Path("001_initial.sql"))
await runner.apply_migration(migration)

# Apply all pending migrations
applied = await runner.apply_pending()

# Apply up to specific target
applied = await runner.apply_pending(target="003_add_posts")

# Rollback migration
await runner.rollback_migration("002_add_users")

# Get applied migrations
records = await runner.get_applied_migrations()
```

### Migration Models

```python
# Load migration from file
migration = metapg.migration.Migration.from_file(Path("001_initial.sql"))
print(f"Name: {migration.name}")
print(f"Version: {migration.version}")
print(f"Checksum: {migration.checksum}")
print(f"Dependencies: {migration.dependencies}")

# Migration record from database
record = metapg.migration.MigrationRecord.from_dict({
    "name": "001_initial",
    "version": 1,
    "checksum": "abc123",
    "applied_at": datetime.now(),
    "duration_ms": 150.5
})

# Migration status
status = metapg.migration.MigrationStatus(
    db_name="main",
    applied=[record],
    pending=[migration],
    total_files=2
)
print(f"Up to date: {status.is_up_to_date}")
```

## Directory Structure

```
project/
├── migrations/
│   ├── default/              # Default database
│   │   ├── 001_initial.sql
│   │   ├── 002_add_users.sql
│   │   └── 003_add_posts.sql
│   └── analytics/            # Named database
│       ├── 001_events.sql
│       └── 002_sessions.sql
└── app/
    └── main.py
```

## Advanced Features

### Migration Dependencies

```sql
-- migrations/default/005_add_foreign_keys.sql
-- Depends: 002_add_users, 003_add_posts

ALTER TABLE posts ADD CONSTRAINT fk_posts_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id);
```

### Conditional Rollbacks

```sql
-- Create table with data
CREATE TABLE settings (key VARCHAR(50), value TEXT);
INSERT INTO settings (key, value) VALUES ('version', '1.0');

-- ROLLBACK
-- Only drop if it exists
DROP TABLE IF EXISTS settings;
```

### Multi-Database Migrations

```python
# Set up multiple databases
import os
os.environ["DATABASE_URL"] = "postgresql://localhost/main_db"
os.environ["DATABASE_URL_ANALYTICS"] = "postgresql://localhost/analytics_db"

# Run migrations for each database
main_runner = metapg.migration.MigrationRunner("default")
analytics_runner = metapg.migration.MigrationRunner("analytics")

await main_runner.apply_pending()
await analytics_runner.apply_pending()
```

## Error Handling

```python
try:
    await runner.apply_pending()
except Exception as e:
    print(f"Migration failed: {e}")
    
    # Check which migrations failed
    status = await runner.get_status()
    for record in status.applied:
        if record.error:
            print(f"Failed migration: {record.name} - {record.error}")
```

## Best Practices

### 1. **Atomic Migrations**
Each migration runs in a transaction and should be atomic.

### 2. **Backward Compatible Changes**
When possible, make changes that don't break existing code:
```sql
-- Good: Add optional column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Better: Add with default
ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT '';
```

### 3. **Data Migrations**
Separate schema and data changes:
```sql
-- 001_add_status_column.sql
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- 002_populate_status.sql  
UPDATE users SET status = 'inactive' WHERE last_login < NOW() - INTERVAL '1 year';
```

### 4. **Testing Migrations**
Always test migrations on a copy of production data.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Part of metapg

This package is part of the [metapg](https://github.com/metapg/metapg) metapackage for PostgreSQL operations.