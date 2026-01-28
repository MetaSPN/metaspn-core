"""Repository reader for MetaSPN."""

import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from metaspn.repo.structure import RepoStructure, validate_repo

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
        
        Returns:
            MinimalState object with user info and commit hash
        """
        with open(self.structure.profile_path) as f:
            profile_data = json.load(f)
        
        # Get repo commit (if git repo)
        repo_commit = self._get_repo_commit()
        
        created_at = None
        if profile_data.get("created_at"):
            created_at = datetime.fromisoformat(profile_data["created_at"])
        
        return MinimalState(
            user_id=profile_data["user_id"],
            name=profile_data["name"],
            handle=profile_data.get("handle", f"@{profile_data['user_id']}"),
            avatar_url=profile_data.get("avatar_url"),
            repo_commit=repo_commit,
            created_at=created_at,
        )
    
    def load_activities(self, platform: Optional[str] = None) -> List["Activity"]:
        """Load activities from repository.
        
        Args:
            platform: Optional platform to filter by
        
        Returns:
            List of Activity objects
        """
        from metaspn.core.profile import Activity
        
        activities = []
        
        # Get activity files
        files = self.structure.get_activity_files(platform)
        
        for file_path in files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                # Handle both single activity and list of activities
                if isinstance(data, list):
                    for item in data:
                        activity = Activity.from_dict(item)
                        activities.append(activity)
                else:
                    activity = Activity.from_dict(data)
                    activities.append(activity)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip malformed files
                continue
        
        # Sort by timestamp
        activities.sort(key=lambda a: a.timestamp)
        
        return activities
    
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
        import subprocess
        
        try:
            result = subprocess.run(
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
        from metaspn.core.profile import Activity
        
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
) -> List["Activity"]:
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
    reader = RepoReader(repo_path)
    return reader.load_cached_profile(commit)
