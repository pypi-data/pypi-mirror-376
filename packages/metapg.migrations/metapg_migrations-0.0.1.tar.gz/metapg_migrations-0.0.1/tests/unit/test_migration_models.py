"""Unit tests for metapg.migrations models - no database connection required."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import testing utilities from metapg.dev
try:
    from metapg.dev.testing import MockConnection
except ImportError:
    # Fallback if dev package not available
    MockConnection = Mock

from metapg.migrations.models import Migration, MigrationRecord, MigrationStatus

pytestmark = pytest.mark.unit


class TestMigration:
    """Unit tests for Migration model."""

    def test_migration_from_file_basic(self):
        """Test parsing a basic migration file."""
        migration_content = """
        -- Description: Create users table
        -- Depends: 000_initial_schema
        
        -- UP
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE
        );
        
        -- DOWN
        DROP TABLE users;
        """

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix="_create_users_table.sql",
            delete=False,
        ) as f:
            f.write(migration_content)
            f.flush()

            # Rename to have proper version prefix
            migration_path = Path(f.name).with_name("001_create_users_table.sql")
            Path(f.name).rename(migration_path)

            try:
                migration = Migration.from_file(migration_path)

                assert migration.name == "001_create_users_table.sql"
                assert migration.version == 1
                assert migration.path == migration_path
                assert migration.description == "Create users table"
                assert migration.dependencies == ["000_initial_schema"]
                assert "CREATE TABLE users" in migration.sql_up
                assert "DROP TABLE users" in migration.sql_down
                assert len(migration.checksum) == 64  # SHA256 hash

            finally:
                migration_path.unlink(missing_ok=True)

    def test_migration_from_file_no_version_prefix(self):
        """Test that migration file without version prefix raises error."""
        migration_content = "CREATE TABLE test ();"

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix="_no_version.sql",
            delete=False,
        ) as f:
            f.write(migration_content)
            f.flush()

            try:
                migration_path = Path(f.name)

                with pytest.raises(ValueError, match="must start with a number"):
                    Migration.from_file(migration_path)

            finally:
                Path(f.name).unlink(missing_ok=True)

    def test_migration_from_file_description_from_filename(self):
        """Test extracting description from filename when no comment exists."""
        migration_content = """
        CREATE TABLE products (id SERIAL PRIMARY KEY);
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write(migration_content)
            f.flush()

            # Rename to have proper version and name
            migration_path = Path(f.name).with_name("002_add_products_table.sql")
            Path(f.name).rename(migration_path)

            try:
                migration = Migration.from_file(migration_path)

                assert migration.description == "Add Products Table"

            finally:
                migration_path.unlink(missing_ok=True)

    def test_migration_checksum_consistency(self):
        """Test that migration checksum is consistent for same content."""
        migration_content = "CREATE TABLE test (id SERIAL PRIMARY KEY);"

        # Create two identical files
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f1,
            tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f2,
        ):

            f1.write(migration_content)
            f1.flush()
            f2.write(migration_content)
            f2.flush()

            # Rename both to have proper version prefix
            path1 = Path(f1.name).with_name("003_test1.sql")
            path2 = Path(f2.name).with_name("004_test2.sql")
            Path(f1.name).rename(path1)
            Path(f2.name).rename(path2)

            try:
                migration1 = Migration.from_file(path1)
                migration2 = Migration.from_file(path2)

                # Different files but same content should have same checksum
                assert migration1.checksum == migration2.checksum

            finally:
                path1.unlink(missing_ok=True)
                path2.unlink(missing_ok=True)


class TestMigrationRecord:
    """Unit tests for MigrationRecord model."""

    def test_migration_record_from_dict(self):
        """Test creating MigrationRecord from dictionary."""
        record_data = {
            "name": "001_create_users.sql",
            "version": 1,
            "checksum": "abc123",
            "applied_at": "2023-01-01T12:00:00",
            "status": "applied",
        }

        record = MigrationRecord.from_dict(record_data)

        assert record.name == "001_create_users.sql"
        assert record.version == 1
        assert record.checksum == "abc123"
        assert record.status == MigrationStatus.APPLIED

    def test_migration_record_to_dict(self):
        """Test converting MigrationRecord to dictionary."""
        from datetime import datetime

        record = MigrationRecord(
            name="002_add_products.sql",
            version=2,
            checksum="def456",
            applied_at=datetime(2023, 1, 2, 12, 0, 0),
            status=MigrationStatus.APPLIED,
        )

        record_dict = record.to_dict()

        assert record_dict["name"] == "002_add_products.sql"
        assert record_dict["version"] == 2
        assert record_dict["checksum"] == "def456"
        assert record_dict["status"] == "applied"
        assert isinstance(record_dict["applied_at"], str)


class TestMigrationStatus:
    """Unit tests for MigrationStatus enum."""

    def test_migration_status_values(self):
        """Test MigrationStatus enum values."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.APPLIED.value == "applied"
        assert MigrationStatus.FAILED.value == "failed"

    def test_migration_status_from_string(self):
        """Test creating MigrationStatus from string."""
        assert MigrationStatus("pending") == MigrationStatus.PENDING
        assert MigrationStatus("applied") == MigrationStatus.APPLIED
        assert MigrationStatus("failed") == MigrationStatus.FAILED
