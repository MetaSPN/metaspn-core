"""Repository writer for MetaSPN."""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
from datetime import datetime

from metaspn.repo.structure import RepoStructure, validate_repo

if TYPE_CHECKING:
    from metaspn.core.profile import Activity, UserProfile


class RepoWriter:
    """Writer for MetaSPN repository data.
    
    Handles writing activities to sources and caching
    computed profiles.
    """
    
    def __init__(self, repo_path: str) -> None:
        """Initialize writer with repository path.
        
        Args:
            repo_path: Path to MetaSPN repository
        """
        self.structure = RepoStructure(repo_path)
        
        if not self.structure.validate():
            raise ValueError(f"Invalid MetaSPN repository: {repo_path}")
    
    def save_activity(self, activity: "Activity") -> Path:
        """Save an activity to the repository.
        
        Activities are saved to the appropriate platform directory
        in sources/. Each activity is saved as a separate JSON file.
        
        Args:
            activity: Activity to save
        
        Returns:
            Path to saved file
        """
        # Determine platform directory
        platform_dir = self.structure.sources_dir / activity.platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from timestamp and activity ID
        timestamp_str = activity.timestamp.strftime("%Y%m%d_%H%M%S")
        activity_id = activity.activity_id or "unknown"
        filename = f"{timestamp_str}_{activity_id[:8]}.json"
        
        file_path = platform_dir / filename
        
        # Write activity
        with open(file_path, "w") as f:
            json.dump(activity.to_dict(), f, indent=2)
        
        return file_path
    
    def save_activities(self, activities: list["Activity"]) -> list[Path]:
        """Save multiple activities to the repository.
        
        Args:
            activities: List of activities to save
        
        Returns:
            List of paths to saved files
        """
        paths = []
        for activity in activities:
            path = self.save_activity(activity)
            paths.append(path)
        return paths
    
    def append_to_log(
        self, 
        activity: "Activity",
        log_name: str = "activities.json",
    ) -> Path:
        """Append activity to a log file.
        
        Instead of creating individual files, appends to a
        platform-specific log file.
        
        Args:
            activity: Activity to append
            log_name: Name of log file
        
        Returns:
            Path to log file
        """
        platform_dir = self.structure.sources_dir / activity.platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        log_path = platform_dir / log_name
        
        # Load existing activities
        existing = []
        if log_path.exists():
            try:
                with open(log_path) as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
        
        # Append new activity
        existing.append(activity.to_dict())
        
        # Write back
        with open(log_path, "w") as f:
            json.dump(existing, f, indent=2)
        
        return log_path
    
    def cache_profile(self, profile: "UserProfile") -> Path:
        """Cache a computed profile.
        
        Saves the profile to reports/profiles/ for future use.
        
        Args:
            profile: Profile to cache
        
        Returns:
            Path to cached file
        """
        profiles_dir = self.structure.reports_dir / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as latest
        latest_path = profiles_dir / "latest.json"
        with open(latest_path, "w") as f:
            f.write(profile.to_json())
        
        # Also save timestamped version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_path = profiles_dir / f"profile_{timestamp}.json"
        with open(timestamped_path, "w") as f:
            f.write(profile.to_json())
        
        return latest_path
    
    def save_card(self, card: "Card") -> Path:  # type: ignore
        """Save a generated card.
        
        Args:
            card: Card to save
        
        Returns:
            Path to saved file
        """
        from metaspn.core.card import Card
        
        cards_dir = self.structure.reports_dir / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{card.card_type}_{card.card_number}.json"
        file_path = cards_dir / filename
        
        with open(file_path, "w") as f:
            f.write(card.to_json())
        
        return file_path
    
    def update_profile_info(self, updates: dict) -> None:
        """Update profile.json with new information.
        
        Args:
            updates: Dictionary of fields to update
        """
        with open(self.structure.profile_path) as f:
            profile = json.load(f)
        
        profile.update(updates)
        profile["updated_at"] = datetime.now().isoformat()
        
        with open(self.structure.profile_path, "w") as f:
            json.dump(profile, f, indent=2)


def save_activity(repo_path: str, activity: "Activity") -> Path:
    """Save an activity to the repository.
    
    Convenience function for saving a single activity.
    
    Args:
        repo_path: Path to MetaSPN repository
        activity: Activity to save
    
    Returns:
        Path to saved file
    
    Example:
        >>> from metaspn.core.profile import Activity
        >>> activity = Activity(
        ...     timestamp=datetime.now(),
        ...     platform="podcast",
        ...     activity_type="create",
        ...     title="Episode 1"
        ... )
        >>> save_activity("./my-content", activity)
    """
    writer = RepoWriter(repo_path)
    return writer.save_activity(activity)


def add_activity(repo_path: str, activity: "Activity") -> Path:
    """Add an activity to the repository.
    
    Alias for save_activity() with a more intuitive name.
    
    Args:
        repo_path: Path to MetaSPN repository
        activity: Activity to add
    
    Returns:
        Path to saved file
    """
    return save_activity(repo_path, activity)


def cache_profile(repo_path: str, profile: "UserProfile") -> Path:
    """Cache a computed profile.
    
    Convenience function for caching a profile.
    
    Args:
        repo_path: Path to MetaSPN repository
        profile: Profile to cache
    
    Returns:
        Path to cached file
    """
    writer = RepoWriter(repo_path)
    return writer.cache_profile(profile)
