"""Async migration runner for metapg."""

import time
from pathlib import Path

from metapg.pool import cursor, transaction

from metapg.migrations.models import Migration, MigrationRecord, MigrationStatus


class MigrationRunner:
    """Handles migration operations for a database."""

    def __init__(self, db_name: str = "default", migrations_dir: Path | None = None):
        self.db_name = db_name
        self.migrations_dir = migrations_dir or Path("migrations") / db_name

    async def ensure_migration_table(self) -> None:
        """Create the migrations table if it doesn't exist."""
        async with cursor(self.db_name) as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS _metapg_migrations (
                    name VARCHAR(255) PRIMARY KEY,
                    version INTEGER NOT NULL,
                    checksum VARCHAR(32) NOT NULL,
                    applied_at TIMESTAMPTZ DEFAULT NOW(),
                    duration_ms NUMERIC(10,2),
                    error TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_metapg_migrations_version
                ON _metapg_migrations(version);

                CREATE INDEX IF NOT EXISTS idx_metapg_migrations_applied_at
                ON _metapg_migrations(applied_at);
            """,
            )

    def discover_migrations(self) -> list[Migration]:
        """Discover all migration files in the migrations directory."""
        if not self.migrations_dir.exists():
            return []

        migration_files = sorted(
            [f for f in self.migrations_dir.glob("*.sql") if f.is_file()],
            key=lambda f: f.name,
        )

        migrations = []
        for file_path in migration_files:
            try:
                migration = Migration.from_file(file_path)
                migrations.append(migration)
            except ValueError as e:
                # Skip invalid migration files but warn
                print(f"Warning: Skipping invalid migration {file_path.name}: {e}")

        return migrations

    async def get_applied_migrations(self) -> list[MigrationRecord]:
        """Get all applied migrations from the database."""
        await self.ensure_migration_table()

        async with cursor(self.db_name) as cur:
            await cur.execute(
                """
                SELECT name, version, checksum, applied_at, duration_ms, error
                FROM _metapg_migrations
                ORDER BY version
            """,
            )
            rows = await cur.fetchall()

        return [MigrationRecord.from_dict(row) for row in rows]

    async def get_status(self) -> MigrationStatus:
        """Get the current migration status."""
        available = self.discover_migrations()
        applied_records = await self.get_applied_migrations()
        applied_names = {record.name for record in applied_records}

        pending = [m for m in available if m.name not in applied_names]
        last_applied = applied_records[-1] if applied_records else None

        return MigrationStatus(
            db_name=self.db_name,
            applied=applied_records,
            pending=pending,
            total_files=len(available),
            last_applied=last_applied,
        )

    async def apply_migration(self, migration: Migration) -> None:
        """Apply a single migration within a transaction."""
        start_time = time.perf_counter()
        error = None

        try:
            async with transaction(self.db_name):
                async with cursor(self.db_name) as cur:
                    # Execute the migration SQL
                    await cur.execute(migration.sql_up)

                    # Record successful migration
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    await cur.execute(
                        """
                        INSERT INTO _metapg_migrations
                        (name, version, checksum, duration_ms)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            migration.name,
                            migration.version,
                            migration.checksum,
                            duration_ms,
                        ),
                    )

        except Exception as e:
            error = str(e)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record failed migration
            async with cursor(self.db_name) as cur:
                await cur.execute(
                    """
                    INSERT INTO _metapg_migrations
                    (name, version, checksum, duration_ms, error)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        migration.name,
                        migration.version,
                        migration.checksum,
                        duration_ms,
                        error,
                    ),
                )
            raise

    async def rollback_migration(self, migration_name: str) -> None:
        """Rollback a single migration."""
        # Find the migration file
        available = self.discover_migrations()
        migration = next((m for m in available if m.name == migration_name), None)

        if not migration:
            msg = f"Migration {migration_name} not found in {self.migrations_dir}"
            raise ValueError(msg)

        if not migration.sql_down:
            msg = f"Migration {migration_name} has no rollback SQL"
            raise ValueError(msg)

        async with transaction(self.db_name), cursor(self.db_name) as cur:
            # Execute rollback SQL
            await cur.execute(migration.sql_down)

            # Remove from migrations table
            await cur.execute(
                "DELETE FROM _metapg_migrations WHERE name = %s",
                (migration_name,),
            )

    async def apply_pending(self, target: str | None = None) -> list[str]:
        """Apply all pending migrations up to an optional target."""
        status = await self.get_status()

        if not status.pending:
            return []

        to_apply = status.pending
        if target:
            # Find target migration
            target_idx = None
            for i, migration in enumerate(to_apply):
                if (
                    migration.name == target
                    or str(migration.version).zfill(3) in target
                ):
                    target_idx = i
                    break

            if target_idx is None:
                msg = f"Target migration '{target}' not found"
                raise ValueError(msg)

            to_apply = to_apply[: target_idx + 1]

        applied = []
        for migration in to_apply:
            await self.apply_migration(migration)
            applied.append(migration.name)

        return applied
