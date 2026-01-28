"""Manifest system for fast activity indexing and lookup.

The manifest provides a master index of all activities in the repository,
enabling fast filtered loading without scanning all files.

Manifest Structure:
    artifacts/indexes/
    ├── manifest.json         # Master catalog with stats
    ├── by_date/
    │   ├── 2024-01.json      # Activity IDs by month
    │   └── 2024-02.json
    └── by_platform/
        ├── twitter.json      # Activity IDs by platform
        └── podcast.json
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from metaspn.repo.structure import RepoStructure

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


@dataclass
class ActivityIndex:
    """Index entry for a single activity."""

    activity_id: str
    source_type: str  # "source" or "artifact"
    platform: str
    activity_type: str  # "create" or "consume"
    timestamp: str
    file_path: str
    line_number: int

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "activity_id": self.activity_id,
            "source_type": self.source_type,
            "platform": self.platform,
            "activity_type": self.activity_type,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActivityIndex":
        """Deserialize from dictionary."""
        return cls(
            activity_id=data["activity_id"],
            source_type=data["source_type"],
            platform=data["platform"],
            activity_type=data["activity_type"],
            timestamp=data["timestamp"],
            file_path=data["file_path"],
            line_number=data["line_number"],
        )


@dataclass
class Manifest:
    """Master index of all activities for fast filtered loading."""

    version: str = "2.0"
    last_updated: Optional[str] = None
    total_activities: int = 0
    activities: dict[str, ActivityIndex] = field(default_factory=dict)
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "total_activities": self.total_activities,
            "activities": {k: v.to_dict() for k, v in self.activities.items()},
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        """Deserialize from dictionary."""
        activities = {k: ActivityIndex.from_dict(v) for k, v in data.get("activities", {}).items()}
        return cls(
            version=data.get("version", "2.0"),
            last_updated=data.get("last_updated"),
            total_activities=data.get("total_activities", 0),
            activities=activities,
            stats=data.get("stats", {}),
        )


class ManifestManager:
    """Manager for building and querying the activity manifest."""

    def __init__(self, repo_path: str) -> None:
        """Initialize manifest manager.

        Args:
            repo_path: Path to MetaSPN repository
        """
        self.structure = RepoStructure(repo_path)
        self._manifest: Optional[Manifest] = None

    @property
    def manifest(self) -> Manifest:
        """Get the current manifest, loading from disk if needed."""
        if self._manifest is None:
            self._manifest = self.load()
        return self._manifest

    # =========================================================================
    # Building
    # =========================================================================

    def build(self, force: bool = False) -> Manifest:
        """Build or rebuild the manifest by scanning all activity files.

        Args:
            force: If True, rebuild even if manifest exists

        Returns:
            The built manifest
        """
        from metaspn.repo.reader import RepoReader

        if not force and self.structure.manifest_path.exists():
            return self.load()

        reader = RepoReader(str(self.structure.repo_path))
        manifest = Manifest(last_updated=datetime.now().isoformat())

        # Track stats
        by_platform: dict[str, int] = defaultdict(int)
        by_year: dict[str, int] = defaultdict(int)
        by_month: dict[str, list[str]] = defaultdict(list)
        by_type: dict[str, int] = defaultdict(int)

        # Scan all activity files
        files = self.structure.get_activity_files()

        for file_path in files:
            source_type = self._determine_source_type(file_path)
            platform = self._determine_platform(file_path)

            activities = reader._load_file(file_path)

            for line_num, activity in enumerate(activities, 1):
                if not activity.activity_id:
                    continue

                index = ActivityIndex(
                    activity_id=activity.activity_id,
                    source_type=source_type,
                    platform=platform,
                    activity_type=activity.activity_type,
                    timestamp=activity.timestamp.isoformat(),
                    file_path=str(file_path.relative_to(self.structure.repo_path)),
                    line_number=line_num,
                )

                manifest.activities[activity.activity_id] = index

                # Update stats
                by_platform[platform] += 1
                year = activity.timestamp.strftime("%Y")
                month = activity.timestamp.strftime("%Y-%m")
                by_year[year] += 1
                by_month[month].append(activity.activity_id)
                by_type[activity.activity_type] += 1

        manifest.total_activities = len(manifest.activities)
        manifest.stats = {
            "by_platform": dict(by_platform),
            "by_year": dict(by_year),
            "by_type": dict(by_type),
        }

        # Save manifest and indexes
        self._save_manifest(manifest)
        self._save_date_indexes(by_month)
        self._save_platform_indexes(manifest)

        self._manifest = manifest
        return manifest

    def _determine_source_type(self, file_path: Path) -> str:
        """Determine if file is in sources or artifacts."""
        path_str = str(file_path)
        if "/sources/" in path_str or "\\sources\\" in path_str:
            return "source"
        return "artifact"

    def _determine_platform(self, file_path: Path) -> str:
        """Determine platform from file path."""
        # Get the first directory after sources/ or artifacts/
        parts = file_path.parts
        for i, part in enumerate(parts):
            if part in ("sources", "artifacts") and i + 1 < len(parts):
                return parts[i + 1]
        return "unknown"

    def _save_manifest(self, manifest: Manifest) -> None:
        """Save manifest to disk."""
        self.structure.indexes_dir.mkdir(parents=True, exist_ok=True)
        with open(self.structure.manifest_path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)

    def _save_date_indexes(self, by_month: dict[str, list[str]]) -> None:
        """Save date-based indexes."""
        self.structure.date_index_dir.mkdir(parents=True, exist_ok=True)
        for month, activity_ids in by_month.items():
            index_path = self.structure.date_index_dir / f"{month}.json"
            with open(index_path, "w") as f:
                json.dump({"month": month, "activity_ids": activity_ids}, f)

    def _save_platform_indexes(self, manifest: Manifest) -> None:
        """Save platform-based indexes."""
        self.structure.platform_index_dir.mkdir(parents=True, exist_ok=True)

        # Group by platform
        by_platform: dict[str, list[str]] = defaultdict(list)
        for activity_id, index in manifest.activities.items():
            by_platform[index.platform].append(activity_id)

        for platform, activity_ids in by_platform.items():
            index_path = self.structure.platform_index_dir / f"{platform}.json"
            with open(index_path, "w") as f:
                json.dump({"platform": platform, "activity_ids": activity_ids}, f)

    # =========================================================================
    # Loading
    # =========================================================================

    def load(self) -> Manifest:
        """Load manifest from disk.

        Returns:
            Manifest object, or empty manifest if not found
        """
        if not self.structure.manifest_path.exists():
            return Manifest()

        with open(self.structure.manifest_path) as f:
            data = json.load(f)

        return Manifest.from_dict(data)

    def exists(self) -> bool:
        """Check if manifest exists."""
        return self.structure.manifest_path.exists()

    # =========================================================================
    # Querying
    # =========================================================================

    def get_activities_by_date(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[str]:
        """Get activity IDs within a date range.

        Args:
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)

        Returns:
            List of activity IDs
        """
        result = []

        for activity_id, index in self.manifest.activities.items():
            ts = datetime.fromisoformat(index.timestamp.replace("Z", "+00:00"))

            # Remove timezone for comparison if needed
            if ts.tzinfo is not None and start_date and start_date.tzinfo is None:
                ts = ts.replace(tzinfo=None)

            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue

            result.append(activity_id)

        return result

    def get_activities_by_platform(self, platform: str) -> list[str]:
        """Get activity IDs for a specific platform.

        Args:
            platform: Platform name

        Returns:
            List of activity IDs
        """
        # Try to load from platform index first
        index_path = self.structure.platform_index_dir / f"{platform}.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)
                return data.get("activity_ids", [])

        # Fall back to manifest
        return [aid for aid, idx in self.manifest.activities.items() if idx.platform == platform]

    def get_activities_by_type(self, activity_type: str) -> list[str]:
        """Get activity IDs by activity type.

        Args:
            activity_type: "create" or "consume"

        Returns:
            List of activity IDs
        """
        return [
            aid
            for aid, idx in self.manifest.activities.items()
            if idx.activity_type == activity_type
        ]

    def get_activity_index(self, activity_id: str) -> Optional[ActivityIndex]:
        """Get index entry for a specific activity.

        Args:
            activity_id: The activity ID to look up

        Returns:
            ActivityIndex if found, None otherwise
        """
        return self.manifest.activities.get(activity_id)

    def query(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[str]:
        """Query activity IDs with multiple filters.

        Args:
            platform: Optional platform filter
            activity_type: Optional activity type filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of activity IDs matching all filters
        """
        # Start with all activities
        candidates = set(self.manifest.activities.keys())

        # Apply filters
        if platform:
            platform_ids = set(self.get_activities_by_platform(platform))
            candidates &= platform_ids

        if activity_type:
            type_ids = set(self.get_activities_by_type(activity_type))
            candidates &= type_ids

        if start_date or end_date:
            date_ids = set(self.get_activities_by_date(start_date, end_date))
            candidates &= date_ids

        return list(candidates)

    # =========================================================================
    # Incremental Updates
    # =========================================================================

    def update_incremental(self, new_activities: list["Activity"]) -> int:
        """Add new activities to the index without full rebuild.

        Args:
            new_activities: List of new activities to index

        Returns:
            Number of activities added
        """
        added = 0

        for activity in new_activities:
            if not activity.activity_id:
                continue
            if activity.activity_id in self.manifest.activities:
                continue

            # Determine source type and platform from activity
            source_type = "artifact" if activity.activity_type == "create" else "source"

            index = ActivityIndex(
                activity_id=activity.activity_id,
                source_type=source_type,
                platform=activity.platform,
                activity_type=activity.activity_type,
                timestamp=activity.timestamp.isoformat(),
                file_path="",  # Unknown for incremental
                line_number=0,
            )

            self.manifest.activities[activity.activity_id] = index
            added += 1

        if added > 0:
            self.manifest.total_activities = len(self.manifest.activities)
            self.manifest.last_updated = datetime.now().isoformat()
            self._save_manifest(self.manifest)

        return added

    def get_stats(self) -> dict:
        """Get manifest statistics.

        Returns:
            Dictionary with counts by platform, year, type
        """
        return {
            "total": self.manifest.total_activities,
            "last_updated": self.manifest.last_updated,
            **self.manifest.stats,
        }


# Convenience functions


def build_manifest(repo_path: str, force: bool = False) -> Manifest:
    """Build or rebuild the manifest for a repository.

    Args:
        repo_path: Path to MetaSPN repository
        force: If True, rebuild even if manifest exists

    Returns:
        The built manifest
    """
    manager = ManifestManager(repo_path)
    return manager.build(force=force)


def load_manifest(repo_path: str) -> Manifest:
    """Load the manifest for a repository.

    Args:
        repo_path: Path to MetaSPN repository

    Returns:
        Manifest object
    """
    manager = ManifestManager(repo_path)
    return manager.load()
