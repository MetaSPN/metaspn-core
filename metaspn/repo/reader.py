"""Repository reader for MetaSPN."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from metaspn.repo.structure import RepoStructure

if TYPE_CHECKING:
    from metaspn.core.profile import Activity, UserProfile


@dataclass
class MinimalState:
    """Minimal state loaded from repository.

    Contains just enough information to check cache validity
    and identify the user.
    """

    user_id: str
    name: str
    handle: str
    avatar_url: Optional[str]
    repo_commit: str
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "handle": self.handle,
            "avatar_url": self.avatar_url,
            "repo_commit": self.repo_commit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RepoReader:
    """Reader for MetaSPN repository data.

    Handles reading activities from sources and artifacts,
    as well as loading cached profile data.
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize reader with repository path.

        Args:
            repo_path: Path to MetaSPN repository
        """
        self.structure = RepoStructure(repo_path)

        if not self.structure.validate():
            raise ValueError(f"Invalid MetaSPN repository: {repo_path}")

    def load_minimal_state(self) -> MinimalState:
        """Load minimal state from repository.

        Supports both standard (.metaspn/profile.json) and legacy (meta.json) formats.

        Returns:
            MinimalState object with user info and commit hash
        """
        with open(self.structure.profile_path) as f:
            profile_data = json.load(f)

        # Get repo commit (if git repo)
        repo_commit = self._get_repo_commit()

        created_at = None
        # Legacy format uses last_sync, standard uses created_at
        date_field = profile_data.get("created_at") or profile_data.get("last_sync")
        if date_field:
            try:
                created_at = datetime.fromisoformat(date_field.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Handle legacy format which only has user_id
        user_id = profile_data.get("user_id", "unknown")
        name = profile_data.get("name", user_id)
        handle = profile_data.get("handle", f"@{user_id}")

        return MinimalState(
            user_id=user_id,
            name=name,
            handle=handle,
            avatar_url=profile_data.get("avatar_url"),
            repo_commit=repo_commit,
            created_at=created_at,
        )

    def load_activities(self, platform: Optional[str] = None) -> list["Activity"]:
        """Load activities from repository.

        Supports both JSON and JSONL files, and both standard and legacy formats.

        Args:
            platform: Optional platform to filter by

        Returns:
            List of Activity objects
        """

        activities = []

        # Get activity files
        files = self.structure.get_activity_files(platform)

        for file_path in files:
            try:
                if file_path.suffix == ".jsonl":
                    # JSONL format - one JSON object per line
                    with open(file_path) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                activity = self._parse_activity(data, file_path)
                                if activity:
                                    activities.append(activity)
                            except (json.JSONDecodeError, KeyError, ValueError):
                                continue
                else:
                    # Standard JSON format
                    with open(file_path) as f:
                        data = json.load(f)

                    # Handle both single activity and list of activities
                    if isinstance(data, list):
                        for item in data:
                            activity = self._parse_activity(item, file_path)
                            if activity:
                                activities.append(activity)
                    else:
                        activity = self._parse_activity(data, file_path)
                        if activity:
                            activities.append(activity)
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                # Skip malformed files
                continue

        # Sort by timestamp
        activities.sort(key=lambda a: a.timestamp)

        return activities

    def _parse_activity(self, data: dict, file_path: Path) -> Optional["Activity"]:
        """Parse activity from data, handling both standard and legacy formats."""
        from metaspn.core.profile import Activity

        # Determine if this is legacy format by checking for nested structures
        if "episode" in data and "listening" not in data:
            # Legacy created podcast episode
            return self._parse_legacy_podcast_episode(data)
        elif "listening" in data:
            # Legacy podcast listening event
            return self._parse_legacy_listening_event(data)
        elif "post" in data:
            # Legacy blog post
            return self._parse_legacy_blog_post(data)
        elif "reading" in data or "source_type" in data and data.get("source_type") == "blog":
            # Legacy blog reading event
            return self._parse_legacy_reading_event(data)
        else:
            # Standard format
            try:
                return Activity.from_dict(data)
            except (KeyError, ValueError):
                return None

    def _parse_legacy_podcast_episode(self, data: dict) -> Optional["Activity"]:
        """Parse legacy podcast episode format."""
        from metaspn.core.profile import Activity

        episode = data.get("episode", {})
        timestamp_str = data.get("timestamp") or episode.get("publish_date")

        if not timestamp_str:
            return None

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

        return Activity(
            timestamp=timestamp,
            platform="podcast",
            activity_type="create",
            title=episode.get("title"),
            content=episode.get("description"),
            url=episode.get("episode_url"),
            duration_seconds=episode.get("duration_seconds"),
            raw_data={
                "episode_id": episode.get("episode_id"),
                "guid": episode.get("guid"),
                "id": data.get("id"),
            },
        )

    def _parse_legacy_listening_event(self, data: dict) -> Optional["Activity"]:
        """Parse legacy podcast listening event format."""
        from metaspn.core.profile import Activity

        episode = data.get("episode", {})
        listening = data.get("listening", {})
        podcast = data.get("podcast", {})
        timestamp_str = data.get("timestamp") or listening.get("end_time")

        if not timestamp_str:
            return None

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

        return Activity(
            timestamp=timestamp,
            platform="podcast",
            activity_type="consume",
            title=episode.get("title"),
            content=None,
            url=episode.get("episode_url"),
            duration_seconds=listening.get("duration_seconds") or episode.get("duration_seconds"),
            raw_data={
                "podcast_title": podcast.get("title"),
                "show_id": podcast.get("show_id"),
                "episode_id": episode.get("episode_id"),
                "completion_percentage": listening.get("completion_percentage"),
                "playback_speed": listening.get("playback_speed"),
                "id": data.get("id"),
            },
        )

    def _parse_legacy_blog_post(self, data: dict) -> Optional["Activity"]:
        """Parse legacy blog post format."""
        from metaspn.core.profile import Activity

        post = data.get("post", {})
        content_data = data.get("content", {})
        timestamp_str = data.get("timestamp") or post.get("publish_date")

        if not timestamp_str:
            return None

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

        # Get content from nested content object
        content = content_data.get("plain_text") or content_data.get("excerpt")

        return Activity(
            timestamp=timestamp,
            platform="blog",
            activity_type="create",
            title=post.get("title"),
            content=content,
            url=post.get("url"),
            duration_seconds=None,
            raw_data={
                "slug": post.get("slug"),
                "word_count": post.get("word_count"),
                "categories": post.get("categories", []),
                "id": data.get("id"),
            },
        )

    def _parse_legacy_reading_event(self, data: dict) -> Optional["Activity"]:
        """Parse legacy blog reading event format."""
        from metaspn.core.profile import Activity

        reading = data.get("reading", {})
        post = data.get("post", {})
        timestamp_str = data.get("timestamp") or reading.get("end_time")

        if not timestamp_str:
            return None

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

        return Activity(
            timestamp=timestamp,
            platform="blog",
            activity_type="consume",
            title=post.get("title"),
            content=None,
            url=post.get("url"),
            duration_seconds=reading.get("duration_seconds"),
            raw_data={
                "completion_percentage": reading.get("completion_percentage"),
                "id": data.get("id"),
            },
        )

    def load_cached_profile(self, commit: Optional[str] = None) -> Optional["UserProfile"]:
        """Load cached profile if available and valid.

        Args:
            commit: Expected repo commit (for cache validation)

        Returns:
            UserProfile if cache is valid, None otherwise
        """
        from metaspn.core.profile import UserProfile

        cache_path = self.structure.reports_dir / "profiles" / "latest.json"

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)

            # Check if cache is valid
            if commit and data.get("repo_commit") != commit:
                return None

            return UserProfile.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def _get_repo_commit(self) -> str:
        """Get current git commit hash if available."""
        import subprocess  # nosec B404

        try:
            result = subprocess.run(  # nosec B603, B607
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.structure.repo_path),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fallback: hash of profile.json modification time
        stat = self.structure.profile_path.stat()
        return f"mtime_{int(stat.st_mtime)}"

    def get_platform_stats(self) -> dict:
        """Get statistics about activities by platform.

        Returns:
            Dictionary with platform names and activity counts
        """

        stats = {}

        for platform in ["podcast", "youtube", "twitter", "blog"]:
            files = self.structure.get_activity_files(platform)
            count = 0

            for file_path in files:
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        count += len(data)
                    else:
                        count += 1
                except (json.JSONDecodeError, KeyError):
                    continue

            if count > 0:
                stats[platform] = count

        return stats


def load_minimal_state(repo_path: str) -> MinimalState:
    """Load minimal state from repository.

    Convenience function for loading just the essential state
    needed for cache checking and user identification.

    Args:
        repo_path: Path to MetaSPN repository

    Returns:
        MinimalState object

    Example:
        >>> state = load_minimal_state("./my-content")
        >>> print(f"User: {state.name}")
    """
    reader = RepoReader(repo_path)
    return reader.load_minimal_state()


def load_activities(
    repo_path: str,
    platform: Optional[str] = None,
) -> list["Activity"]:
    """Load activities from repository.

    Loads all activities from sources/ and artifacts/ directories,
    optionally filtered by platform.

    Args:
        repo_path: Path to MetaSPN repository
        platform: Optional platform to filter by

    Returns:
        List of Activity objects sorted by timestamp

    Example:
        >>> activities = load_activities("./my-content")
        >>> print(f"Total activities: {len(activities)}")

        >>> podcast_activities = load_activities("./my-content", "podcast")
    """
    reader = RepoReader(repo_path)
    return reader.load_activities(platform)


def try_load_cached_profile(
    repo_path: str,
    commit: Optional[str] = None,
) -> Optional["UserProfile"]:
    """Try to load a cached profile.

    Returns None if cache doesn't exist or is invalid.

    Args:
        repo_path: Path to MetaSPN repository
        commit: Expected repo commit for validation

    Returns:
        UserProfile if cache is valid, None otherwise
    """
    try:
        reader = RepoReader(repo_path)
        return reader.load_cached_profile(commit)
    except Exception:
        return None
