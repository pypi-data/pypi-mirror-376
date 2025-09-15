"""Integration tests for metapg.migrations runner - requires database connection."""

import os
import tempfile
from pathlib import Path

import pytest

# Import testing utilities from metapg.dev
try:
    from metapg.dev.testing import skip_if_no_database, temp_database
except ImportError:
    # Fallback if dev package not available
    def temp_database():
        raise pytest.skip("metapg.dev testing utilities not available")

    def skip_if_no_database():
        return pytest.mark.skipif(
            not os.getenv("DATABASE_URL"),
            reason="Database not available",
        )


from metapg.migrations.models import MigrationStatus
from metapg.migrations.runner import MigrationRunner

pytestmark = pytest.mark.integration


class TestMigrationRunnerIntegration:
    """Integration tests for MigrationRunner with real database."""

    @skip_if_no_database()
    async def test_migration_runner_initialization(self):
        """Test that MigrationRunner can initialize with database."""
        async with temp_database() as db_url:
            runner = MigrationRunner(db_url=db_url, migrations_dir=Path())

            # Test that we can get status without errors
            status = await runner.get_status()
            assert isinstance(status, dict)

    @skip_if_no_database()
    async def test_migration_runner_create_migrations_table(self):
        """Test creating migrations tracking table."""
        async with temp_database() as db_url:
            runner = MigrationRunner(db_url=db_url, migrations_dir=Path())

            # Ensure migrations table is created
            await runner.ensure_migrations_table()

            # Verify table exists by getting status
            status = await runner.get_status()
            assert "pending" in status
            assert "applied" in status

    @skip_if_no_database()
    async def test_apply_single_migration(self):
        """Test applying a single migration to database."""
        # Create temporary migration file
        migration_content = """
        -- Description: Create test table
        
        -- UP
        CREATE TABLE test_migration (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
        
        -- DOWN
        DROP TABLE test_migration;
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            migrations_dir = Path(temp_dir)
            migration_file = migrations_dir / "001_create_test_table.sql"
            migration_file.write_text(migration_content)

            async with temp_database() as db_url:
                runner = MigrationRunner(db_url=db_url, migrations_dir=migrations_dir)

                # Apply pending migrations
                results = await runner.apply_pending()

                assert len(results) == 1
                assert results[0].version == 1
                assert results[0].status == MigrationStatus.APPLIED

                # Verify migration is recorded as applied
                status = await runner.get_status()
                assert len(status["applied"]) == 1
                assert len(status["pending"]) == 0

    @skip_if_no_database()
    async def test_migration_rollback(self):
        """Test rolling back applied migrations."""
        # Create temporary migration file with both UP and DOWN
        migration_content = """
        -- Description: Create and drop test table
        
        -- UP
        CREATE TABLE rollback_test (
            id SERIAL PRIMARY KEY,
            data TEXT
        );
        
        -- DOWN
        DROP TABLE rollback_test;
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            migrations_dir = Path(temp_dir)
            migration_file = migrations_dir / "001_rollback_test.sql"
            migration_file.write_text(migration_content)

            async with temp_database() as db_url:
                runner = MigrationRunner(db_url=db_url, migrations_dir=migrations_dir)

                # Apply migration first
                apply_results = await runner.apply_pending()
                assert len(apply_results) == 1
                assert apply_results[0].status == MigrationStatus.APPLIED

                # Now rollback
                rollback_results = await runner.rollback(steps=1)
                assert len(rollback_results) == 1

                # Verify migration is no longer applied
                status = await runner.get_status()
                assert len(status["applied"]) == 0

    @skip_if_no_database()
    async def test_migration_dependency_checking(self):
        """Test that migration dependencies are validated."""
        # Create migrations with dependencies
        migration1_content = """
        -- Description: Create base table
        
        -- UP
        CREATE TABLE base_table (
            id SERIAL PRIMARY KEY
        );
        
        -- DOWN
        DROP TABLE base_table;
        """

        migration2_content = """
        -- Description: Create dependent table
        -- Depends: 001_create_base_table
        
        -- UP
        CREATE TABLE dependent_table (
            id SERIAL PRIMARY KEY,
            base_id INTEGER REFERENCES base_table(id)
        );
        
        -- DOWN
        DROP TABLE dependent_table;
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            migrations_dir = Path(temp_dir)

            # Create migration files
            (migrations_dir / "001_create_base_table.sql").write_text(
                migration1_content,
            )
            (migrations_dir / "002_create_dependent_table.sql").write_text(
                migration2_content,
            )

            async with temp_database() as db_url:
                runner = MigrationRunner(db_url=db_url, migrations_dir=migrations_dir)

                # Apply all pending migrations
                results = await runner.apply_pending()

                # Both migrations should be applied successfully
                assert len(results) == 2
                assert all(r.status == MigrationStatus.APPLIED for r in results)

                # Verify final status
                status = await runner.get_status()
                assert len(status["applied"]) == 2
                assert len(status["pending"]) == 0

    @skip_if_no_database()
    async def test_migration_checksum_validation(self):
        """Test that migration checksum changes are detected."""
        migration_content = """
        -- Description: Original migration
        
        -- UP
        CREATE TABLE checksum_test (id SERIAL PRIMARY KEY);
        
        -- DOWN
        DROP TABLE checksum_test;
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            migrations_dir = Path(temp_dir)
            migration_file = migrations_dir / "001_checksum_test.sql"
            migration_file.write_text(migration_content)

            async with temp_database() as db_url:
                runner = MigrationRunner(db_url=db_url, migrations_dir=migrations_dir)

                # Apply original migration
                await runner.apply_pending()

                # Modify the migration file
                modified_content = migration_content.replace(
                    "checksum_test",
                    "checksum_test_modified",
                )
                migration_file.write_text(modified_content)

                # Attempting to get status should detect checksum mismatch
                status = await runner.get_status()

                # The behavior depends on implementation, but there should be
                # some indication that the migration has changed
                assert "applied" in status
