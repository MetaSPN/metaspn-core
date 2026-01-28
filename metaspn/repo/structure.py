"""Repository structure management for MetaSPN."""

import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class RepoStructure:
    """Manager for MetaSPN repository structure.
    
    Repository Layout:
        .metaspn/
            profile.json      # User identity and minimal state
            config.json       # Repository configuration
            cache/            # Cached computations
        sources/
            podcast/          # Platform-specific source data
            youtube/
            twitter/
            blog/
        artifacts/
            computed/         # Computed activity data with scores
        reports/
            profiles/         # Cached profile computations
            cards/            # Generated card data
    """
    
    # Required directories
    REQUIRED_DIRS = [
        ".metaspn",
        ".metaspn/cache",
        "sources",
        "sources/podcast",
        "sources/youtube",
        "sources/twitter",
        "sources/blog",
        "artifacts",
        "artifacts/computed",
        "reports",
        "reports/profiles",
        "reports/cards",
    ]
    
    # Required files (relative to repo root)
    REQUIRED_FILES = [
        ".metaspn/profile.json",
    ]
    
    def __init__(self, repo_path: str) -> None:
        """Initialize with repository path.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
    
    @property
    def metaspn_dir(self) -> Path:
        """Path to .metaspn directory."""
        return self.repo_path / ".metaspn"
    
    @property
    def profile_path(self) -> Path:
        """Path to profile.json."""
        return self.metaspn_dir / "profile.json"
    
    @property
    def config_path(self) -> Path:
        """Path to config.json."""
        return self.metaspn_dir / "config.json"
    
    @property
    def cache_dir(self) -> Path:
        """Path to cache directory."""
        return self.metaspn_dir / "cache"
    
    @property
    def sources_dir(self) -> Path:
        """Path to sources directory."""
        return self.repo_path / "sources"
    
    @property
    def artifacts_dir(self) -> Path:
        """Path to artifacts directory."""
        return self.repo_path / "artifacts"
    
    @property
    def reports_dir(self) -> Path:
        """Path to reports directory."""
        return self.repo_path / "reports"
    
    def create_structure(self) -> None:
        """Create the repository directory structure."""
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.repo_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate that repository structure exists.
        
        Returns:
            True if all required directories and files exist
        """
        # Check directories
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.repo_path / dir_path
            if not full_path.is_dir():
                return False
        
        # Check files
        for file_path in self.REQUIRED_FILES:
            full_path = self.repo_path / file_path
            if not full_path.is_file():
                return False
        
        return True
    
    def get_platform_dir(self, platform: str) -> Path:
        """Get the source directory for a platform.
        
        Args:
            platform: Platform name
        
        Returns:
            Path to platform source directory
        """
        return self.sources_dir / platform
    
    def get_activity_files(self, platform: Optional[str] = None) -> list[Path]:
        """Get all activity files, optionally filtered by platform.
        
        Args:
            platform: Optional platform to filter by
        
        Returns:
            List of activity file paths
        """
        files = []
        
        if platform:
            platform_dir = self.get_platform_dir(platform)
            if platform_dir.is_dir():
                files.extend(platform_dir.glob("*.json"))
        else:
            # Get from all platforms
            for platform_name in ["podcast", "youtube", "twitter", "blog"]:
                platform_dir = self.get_platform_dir(platform_name)
                if platform_dir.is_dir():
                    files.extend(platform_dir.glob("*.json"))
            
            # Also check artifacts
            computed_dir = self.artifacts_dir / "computed"
            if computed_dir.is_dir():
                files.extend(computed_dir.glob("*.json"))
        
        return sorted(files)


def init_repo(path: str, user_info: dict) -> None:
    """Initialize a new MetaSPN repository.
    
    Creates the directory structure and initial profile.json file.
    
    Args:
        path: Path where to create the repository
        user_info: Dictionary containing user information:
            - user_id (required): Unique user identifier
            - name (required): Display name
            - handle (optional): User handle (e.g., @username)
            - avatar_url (optional): URL to avatar image
    
    Raises:
        ValueError: If required user_info fields are missing
        FileExistsError: If repo already exists at path
    
    Example:
        >>> init_repo("./my-content", {
        ...     "user_id": "leo_guinan",
        ...     "name": "Leo Guinan",
        ...     "handle": "@leo_guinan"
        ... })
    """
    # Validate required fields
    if "user_id" not in user_info:
        raise ValueError("user_info must contain 'user_id'")
    if "name" not in user_info:
        raise ValueError("user_info must contain 'name'")
    
    repo_path = Path(path).resolve()
    
    # Check if already initialized
    metaspn_dir = repo_path / ".metaspn"
    if metaspn_dir.exists():
        raise FileExistsError(f"MetaSPN repository already exists at {path}")
    
    # Create structure
    structure = RepoStructure(path)
    structure.create_structure()
    
    # Create profile.json
    profile_data = {
        "user_id": user_info["user_id"],
        "name": user_info["name"],
        "handle": user_info.get("handle", f"@{user_info['user_id']}"),
        "avatar_url": user_info.get("avatar_url"),
        "created_at": datetime.now().isoformat(),
        "version": "0.1.0",
    }
    
    with open(structure.profile_path, "w") as f:
        json.dump(profile_data, f, indent=2)
    
    # Create config.json
    config_data = {
        "version": "0.1.0",
        "platforms": ["podcast", "youtube", "twitter", "blog"],
        "cache_enabled": True,
        "created_at": datetime.now().isoformat(),
    }
    
    with open(structure.config_path, "w") as f:
        json.dump(config_data, f, indent=2)
    
    # Create .gitkeep files in empty directories
    for platform in ["podcast", "youtube", "twitter", "blog"]:
        gitkeep = structure.sources_dir / platform / ".gitkeep"
        gitkeep.touch()
    
    (structure.artifacts_dir / "computed" / ".gitkeep").touch()
    (structure.reports_dir / "profiles" / ".gitkeep").touch()
    (structure.reports_dir / "cards" / ".gitkeep").touch()


def validate_repo(path: str) -> bool:
    """Validate that a path contains a valid MetaSPN repository.
    
    Args:
        path: Path to check
    
    Returns:
        True if path contains a valid MetaSPN repository
    
    Example:
        >>> if validate_repo("./my-content"):
        ...     print("Valid repo!")
    """
    repo_path = Path(path).resolve()
    
    if not repo_path.exists():
        return False
    
    structure = RepoStructure(path)
    return structure.validate()


def get_repo_info(path: str) -> dict:
    """Get basic information about a repository.
    
    Args:
        path: Path to repository
    
    Returns:
        Dictionary with repo information
    
    Raises:
        ValueError: If not a valid repository
    """
    if not validate_repo(path):
        raise ValueError(f"Not a valid MetaSPN repository: {path}")
    
    structure = RepoStructure(path)
    
    with open(structure.profile_path) as f:
        profile = json.load(f)
    
    config = {}
    if structure.config_path.exists():
        with open(structure.config_path) as f:
            config = json.load(f)
    
    # Count activities
    activity_files = structure.get_activity_files()
    
    return {
        "path": str(structure.repo_path),
        "user_id": profile.get("user_id"),
        "name": profile.get("name"),
        "handle": profile.get("handle"),
        "created_at": profile.get("created_at"),
        "version": profile.get("version"),
        "platforms": config.get("platforms", []),
        "activity_files": len(activity_files),
    }
