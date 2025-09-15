"""Data models for metapg migrations."""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Migration:
    """Represents a single migration file."""

    name: str
    version: int
    path: Path
    sql_up: str
    sql_down: str | None
    checksum: str
    description: str | None = None
    dependencies: list[str] | None = None

    @classmethod
    def from_file(cls, path: Path) -> "Migration":
        """Parse migration from SQL file with metadata."""
        content = path.read_text(encoding="utf-8")

        # Extract version from filename (001_name.sql -> 1)
        version_match = re.match(r"(\d+)_", path.stem)
        if not version_match:
            msg = f"Migration file {path.name} must start with a number (e.g., 001_)"
            raise ValueError(msg)

        version = int(version_match.group(1))

        # Extract description from filename or file comments
        description = None
        if "_" in path.stem:
            description = path.stem.split("_", 1)[1].replace("_", " ").title()

        # Look for description comment in file
        desc_match = re.search(r"-- Description:\s*(.+)", content)
        if desc_match:
            description = desc_match.group(1).strip()

        # Extract dependencies
        dependencies = []
        dep_matches = re.findall(r"-- Depends:\s*(.+)", content)
        for match in dep_matches:
            dependencies.extend([dep.strip() for dep in match.split(",")])

        # Split on ROLLBACK section if present
        if "-- ROLLBACK" in content:
            up_sql, down_sql = content.split("-- ROLLBACK", 1)
            down_sql = down_sql.strip()
            # Remove comments from rollback section
            down_sql = re.sub(r"^--.*$", "", down_sql, flags=re.MULTILINE).strip()
            if not down_sql:
                down_sql = None
        else:
            up_sql = content
            down_sql = None

        # Clean up SQL (remove comments and normalize)
        up_sql = re.sub(r"^--.*$", "", up_sql, flags=re.MULTILINE)
        up_sql = re.sub(r"\n\s*\n", "\n", up_sql).strip()

        # Calculate checksum
        checksum = hashlib.md5(up_sql.encode("utf-8")).hexdigest()

        return cls(
            name=path.stem,
            version=version,
            path=path,
            sql_up=up_sql,
            sql_down=down_sql,
            checksum=checksum,
            description=description,
            dependencies=dependencies if dependencies else None,
        )


@dataclass
class MigrationRecord:
    """Represents a migration record in the database."""

    name: str
    version: int
    checksum: str
    applied_at: datetime
    duration_ms: float | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MigrationRecord":
        """Create from database row."""
        return cls(
            name=data["name"],
            version=data["version"],
            checksum=data["checksum"],
            applied_at=data["applied_at"],
            duration_ms=data.get("duration_ms"),
            error=data.get("error"),
        )


@dataclass
class MigrationStatus:
    """Status of migrations for a database."""

    db_name: str
    applied: list[MigrationRecord]
    pending: list[Migration]
    total_files: int
    last_applied: MigrationRecord | None = None

    @property
    def is_up_to_date(self) -> bool:
        """Check if all migrations are applied."""
        return len(self.pending) == 0
