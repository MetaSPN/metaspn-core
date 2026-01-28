"""Activity loader with selective loading capabilities.

The ActivityLoader provides efficient loading of activities with filtering,
using the manifest index when available for fast lookups.

This allows working with subsets of a large dataset without loading
everything into memory.
"""

import json
from collections.abc import Iterator
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from metaspn.repo.manifest import ManifestManager
from metaspn.repo.structure import RepoStructure

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class ActivityLoader:
    """Load activities with filtering, without loading entire dataset.

    Uses the manifest index when available for efficient filtering.
    Falls back to full scan when manifest is not available.

    Example:
        >>> loader = ActivityLoader("./my-content")
        >>>
        >>> # Query specific activities
        >>> tweets = list(loader.query(platform="twitter", limit=100))
        >>>
        >>> # Stream activities without loading all into memory
        >>> for activity in loader.stream(platform="podcast"):
        ...     process(activity)
        >>>
        >>> # Load specific activities by ID
        >>> activities = loader.load_by_ids(["twitter_123", "podcast_456"])
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize activity loader.

        Args:
            repo_path: Path to MetaSPN repository
        """
        self.structure = RepoStructure(repo_path)
        self.manifest_manager = ManifestManager(repo_path)

        if not self.structure.validate():
            raise ValueError(f"Invalid MetaSPN repository: {repo_path}")

    def query(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[Literal["create", "consume"]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Iterator["Activity"]:
        """Query activities with filters.

        Uses manifest for efficiency when available. Yields activities
        one at a time to support large datasets.

        Args:
            platform: Filter by platform
            activity_type: Filter by "create" or "consume"
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            limit: Maximum number of activities to return

        Yields:
            Activity objects matching the filters
        """
        # Try to use manifest for efficient filtering
        if self.manifest_manager.exists():
            yield from self._query_with_manifest(
                platform=platform,
                activity_type=activity_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        else:
            # Fall back to full scan
            yield from self._query_full_scan(
                platform=platform,
                activity_type=activity_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

    def _query_with_manifest(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Iterator["Activity"]:
        """Query using manifest index."""
        # Get matching activity IDs from manifest
        activity_ids = self.manifest_manager.query(
            platform=platform,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date,
        )

        # Load activities by ID
        count = 0
        for activity in self._load_activities_by_ids(activity_ids):
            yield activity
            count += 1
            if limit and count >= limit:
                break

    def _query_full_scan(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Iterator["Activity"]:
        """Query by scanning all files."""
        from metaspn.repo.reader import RepoReader

        reader = RepoReader(str(self.structure.repo_path))
        count = 0

        for activity in self._stream_all_activities(reader):
            # Apply filters
            if platform and activity.platform != platform:
                continue
            if activity_type and activity.activity_type != activity_type:
                continue
            if start_date and activity.timestamp < start_date:
                continue
            if end_date and activity.timestamp > end_date:
                continue

            yield activity
            count += 1
            if limit and count >= limit:
                break

    def _stream_all_activities(self, reader) -> Iterator["Activity"]:
        """Stream all activities from all files."""
        files = self.structure.get_activity_files()

        for file_path in files:
            try:
                activities = reader._load_file(file_path)
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                continue
            yield from activities

    def load_by_ids(self, activity_ids: list[str]) -> list["Activity"]:
        """Load specific activities by their IDs.

        Uses manifest to find file locations when available.

        Args:
            activity_ids: List of activity IDs to load

        Returns:
            List of Activity objects (order may not match input)
        """
        return list(self._load_activities_by_ids(activity_ids))

    def _load_activities_by_ids(
        self,
        activity_ids: list[str],
    ) -> Iterator["Activity"]:
        """Load activities by ID using manifest for location hints."""
        from metaspn.repo.reader import RepoReader

        reader = RepoReader(str(self.structure.repo_path))
        id_set = set(activity_ids)

        if self.manifest_manager.exists():
            # Group by file for efficient loading
            files_to_check: dict[str, set[str]] = {}

            for activity_id in activity_ids:
                index = self.manifest_manager.get_activity_index(activity_id)
                if index and index.file_path:
                    if index.file_path not in files_to_check:
                        files_to_check[index.file_path] = set()
                    files_to_check[index.file_path].add(activity_id)

            # Load from known files
            for file_path, ids in files_to_check.items():
                full_path = self.structure.repo_path / file_path
                if not full_path.exists():
                    continue

                try:
                    activities = reader._load_file(full_path)
                    for activity in activities:
                        if activity.activity_id in ids:
                            yield activity
                            id_set.discard(activity.activity_id)
                except (json.JSONDecodeError, KeyError, ValueError, OSError):
                    continue

        # For any remaining IDs, do a full scan
        if id_set:
            for activity in self._stream_all_activities(reader):
                if activity.activity_id in id_set:
                    yield activity
                    id_set.discard(activity.activity_id)
                    if not id_set:
                        break

    def stream(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[Literal["create", "consume"]] = None,
    ) -> Iterator["Activity"]:
        """Stream activities without loading all into memory.

        More memory-efficient than query() for processing large datasets.

        Args:
            platform: Optional platform filter
            activity_type: Optional activity type filter

        Yields:
            Activity objects
        """
        yield from self.query(
            platform=platform,
            activity_type=activity_type,
        )

    def count(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[Literal["create", "consume"]] = None,
    ) -> int:
        """Count activities matching filters.

        Uses manifest stats when available for fast counting.

        Args:
            platform: Optional platform filter
            activity_type: Optional activity type filter

        Returns:
            Count of matching activities
        """
        if self.manifest_manager.exists():
            # Use manifest for fast counting
            if platform and activity_type:
                return len(
                    self.manifest_manager.query(platform=platform, activity_type=activity_type)
                )
            elif platform:
                return len(self.manifest_manager.get_activities_by_platform(platform))
            elif activity_type:
                return len(self.manifest_manager.get_activities_by_type(activity_type))
            else:
                return self.manifest_manager.manifest.total_activities

        # Fall back to counting via stream
        return sum(1 for _ in self.stream(platform=platform, activity_type=activity_type))

    def get_platforms(self) -> list[str]:
        """Get list of platforms with activities.

        Returns:
            List of platform names
        """
        if self.manifest_manager.exists():
            return list(self.manifest_manager.manifest.stats.get("by_platform", {}).keys())

        # Fall back to checking structure
        platforms = []
        for platform in self.structure.ARTIFACT_PLATFORMS:
            files = self.structure.get_activity_files(platform)
            if files:
                platforms.append(platform)
        return platforms

    def get_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of all activities.

        Returns:
            Tuple of (earliest_date, latest_date), or (None, None) if empty
        """
        earliest: Optional[datetime] = None
        latest: Optional[datetime] = None

        if self.manifest_manager.exists():
            for index in self.manifest_manager.manifest.activities.values():
                ts = datetime.fromisoformat(index.timestamp.replace("Z", "+00:00"))
                if earliest is None or ts < earliest:
                    earliest = ts
                if latest is None or ts > latest:
                    latest = ts
        else:
            from metaspn.repo.reader import RepoReader

            reader = RepoReader(str(self.structure.repo_path))
            for activity in self._stream_all_activities(reader):
                if earliest is None or activity.timestamp < earliest:
                    earliest = activity.timestamp
                if latest is None or activity.timestamp > latest:
                    latest = activity.timestamp

        return earliest, latest

    def get_stats(self) -> dict:
        """Get statistics about the activities.

        Returns:
            Dictionary with counts and metadata
        """
        if self.manifest_manager.exists():
            return self.manifest_manager.get_stats()

        # Build stats manually
        by_platform: dict[str, int] = {}
        by_type: dict[str, int] = {}
        total = 0

        from metaspn.repo.reader import RepoReader

        reader = RepoReader(str(self.structure.repo_path))

        for activity in self._stream_all_activities(reader):
            total += 1
            by_platform[activity.platform] = by_platform.get(activity.platform, 0) + 1
            by_type[activity.activity_type] = by_type.get(activity.activity_type, 0) + 1

        return {
            "total": total,
            "by_platform": by_platform,
            "by_type": by_type,
        }


# Convenience functions


def query_activities(
    repo_path: str,
    platform: Optional[str] = None,
    activity_type: Optional[Literal["create", "consume"]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> list["Activity"]:
    """Query activities from a repository.

    Convenience function that creates a loader and queries.

    Args:
        repo_path: Path to MetaSPN repository
        platform: Filter by platform
        activity_type: Filter by "create" or "consume"
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum results

    Returns:
        List of matching activities
    """
    loader = ActivityLoader(repo_path)
    return list(
        loader.query(
            platform=platform,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    )


def stream_activities(
    repo_path: str,
    platform: Optional[str] = None,
    activity_type: Optional[Literal["create", "consume"]] = None,
) -> Iterator["Activity"]:
    """Stream activities from a repository.

    Memory-efficient iteration over activities.

    Args:
        repo_path: Path to MetaSPN repository
        platform: Filter by platform
        activity_type: Filter by "create" or "consume"

    Yields:
        Activity objects
    """
    loader = ActivityLoader(repo_path)
    yield from loader.stream(platform=platform, activity_type=activity_type)
