"""Repository structure management for MetaSPN.

Data Lake Architecture:
    .metaspn/
        profile.json          # User identity
        config.json           # Repository configuration

    sources/                  # EXTERNAL INPUTS (what you consumed)
        podcasts/
            listening-events.jsonl
        books/
            reading-events.jsonl
        blogs/
            reading-events.jsonl
        twitter/
            engagement-events.jsonl

    artifacts/                # YOUR OUTPUTS (what you created)
        twitter/
            tweets.jsonl
        podcast/
            episodes.jsonl
        blog/
            posts.jsonl
        youtube/
            videos.jsonl

        enhancements/         # Computed layers with history
            quality_scores/
                latest.jsonl
                history/
            game_signatures/
                latest.jsonl
                history/
            embeddings/
                latest.jsonl
                history/

        indexes/              # Fast lookup indexes
            manifest.json
            by_date/
            by_platform/

    reports/                  # Computed outputs
        profiles/
        cards/

Key principles:
    - Sources = external inputs (consumed content)
    - Artifacts = your outputs (created content)
    - Each activity exists in exactly ONE location
    - Enhancements are separate computed layers with full history
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional


class RepoStructure:
    """Manager for MetaSPN repository structure."""

    # Required directories for data lake layout
    REQUIRED_DIRS = [
        ".metaspn",
        # Sources - external inputs (consumed)
        "sources/podcasts",
        "sources/books",
        "sources/blogs",
        "sources/twitter",
        # Artifacts - your outputs (created)
        "artifacts/twitter",
        "artifacts/podcast",
        "artifacts/blog",
        "artifacts/youtube",
        # Enhancements with history
        "artifacts/enhancements/quality_scores",
        "artifacts/enhancements/quality_scores/history",
        "artifacts/enhancements/game_signatures",
        "artifacts/enhancements/game_signatures/history",
        "artifacts/enhancements/embeddings",
        "artifacts/enhancements/embeddings/history",
        # Indexes
        "artifacts/indexes",
        "artifacts/indexes/by_date",
        "artifacts/indexes/by_platform",
        # Reports
        "reports/profiles",
        "reports/cards",
    ]

    # Required files (relative to repo root)
    REQUIRED_FILES = [
        ".metaspn/profile.json",
    ]

    # Platform configurations
    SOURCE_PLATFORMS = ["podcasts", "books", "blogs", "twitter"]
    ARTIFACT_PLATFORMS = ["twitter", "podcast", "blog", "youtube"]

    # Legacy layout detection (for backward compatibility during transition)
    LEGACY_PROFILE = "meta.json"

    def __init__(self, repo_path: str) -> None:
        """Initialize with repository path.

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()

    @property
    def is_legacy_layout(self) -> bool:
        """Check if this is a legacy layout (meta.json style)."""
        return (self.repo_path / self.LEGACY_PROFILE).exists()

    # =========================================================================
    # Core Directories
    # =========================================================================

    @property
    def metaspn_dir(self) -> Path:
        """Path to .metaspn directory."""
        return self.repo_path / ".metaspn"

    @property
    def profile_path(self) -> Path:
        """Path to profile.json (or meta.json for legacy)."""
        if self.is_legacy_layout:
            return self.repo_path / self.LEGACY_PROFILE
        return self.metaspn_dir / "profile.json"

    @property
    def config_path(self) -> Path:
        """Path to config.json."""
        return self.metaspn_dir / "config.json"

    @property
    def sources_dir(self) -> Path:
        """Path to sources directory (external inputs/consumed content)."""
        return self.repo_path / "sources"

    @property
    def artifacts_dir(self) -> Path:
        """Path to artifacts directory (your outputs/created content)."""
        return self.repo_path / "artifacts"

    @property
    def reports_dir(self) -> Path:
        """Path to reports directory."""
        return self.repo_path / "reports"

    # =========================================================================
    # Source Paths (External Inputs)
    # =========================================================================

    def get_source_dir(self, platform: str) -> Path:
        """Get source directory for a platform (consumed content).

        Args:
            platform: Platform name (podcasts, books, blogs, twitter)
        """
        return self.sources_dir / platform

    def get_source_file(self, platform: str, filename: str = None) -> Path:
        """Get path to a source file.

        Args:
            platform: Platform name
            filename: File name (defaults to standard event file)
        """
        if filename is None:
            # Default event file names
            default_files = {
                "podcasts": "listening-events.jsonl",
                "books": "reading-events.jsonl",
                "blogs": "reading-events.jsonl",
                "twitter": "engagement-events.jsonl",
            }
            filename = default_files.get(platform, f"{platform}-events.jsonl")
        return self.get_source_dir(platform) / filename

    # =========================================================================
    # Artifact Paths (Your Outputs)
    # =========================================================================

    def get_artifact_dir(self, platform: str) -> Path:
        """Get artifact directory for a platform (created content).

        Args:
            platform: Platform name (twitter, podcast, blog, youtube)
        """
        return self.artifacts_dir / platform

    def get_artifact_file(self, platform: str, filename: str = None) -> Path:
        """Get path to an artifact file.

        Args:
            platform: Platform name
            filename: File name (defaults to standard content file)
        """
        if filename is None:
            # Default content file names
            default_files = {
                "twitter": "tweets.jsonl",
                "podcast": "episodes.jsonl",
                "blog": "posts.jsonl",
                "youtube": "videos.jsonl",
            }
            filename = default_files.get(platform, f"{platform}.jsonl")
        return self.get_artifact_dir(platform) / filename

    # =========================================================================
    # Enhancement Paths (Computed Layers)
    # =========================================================================

    @property
    def enhancements_dir(self) -> Path:
        """Path to enhancements directory."""
        return self.artifacts_dir / "enhancements"

    def get_enhancement_dir(self, enhancement_type: str) -> Path:
        """Get directory for an enhancement type.

        Args:
            enhancement_type: Type (quality_scores, game_signatures, embeddings)
        """
        return self.enhancements_dir / enhancement_type

    def get_enhancement_latest_path(self, enhancement_type: str) -> Path:
        """Get path to latest enhancement file.

        Args:
            enhancement_type: Type (quality_scores, game_signatures, embeddings)
        """
        return self.get_enhancement_dir(enhancement_type) / "latest.jsonl"

    def get_enhancement_history_dir(self, enhancement_type: str) -> Path:
        """Get path to enhancement history directory.

        Args:
            enhancement_type: Type (quality_scores, game_signatures, embeddings)
        """
        return self.get_enhancement_dir(enhancement_type) / "history"

    # Convenience properties for common enhancement paths
    @property
    def quality_scores_path(self) -> Path:
        """Path to latest quality scores file."""
        return self.get_enhancement_latest_path("quality_scores")

    @property
    def game_signatures_path(self) -> Path:
        """Path to latest game signatures file."""
        return self.get_enhancement_latest_path("game_signatures")

    @property
    def embeddings_path(self) -> Path:
        """Path to latest embeddings file."""
        return self.get_enhancement_latest_path("embeddings")

    # =========================================================================
    # Index Paths
    # =========================================================================

    @property
    def indexes_dir(self) -> Path:
        """Path to indexes directory."""
        return self.artifacts_dir / "indexes"

    @property
    def manifest_path(self) -> Path:
        """Path to manifest.json (master activity index)."""
        return self.indexes_dir / "manifest.json"

    @property
    def date_index_dir(self) -> Path:
        """Path to date-based index directory."""
        return self.indexes_dir / "by_date"

    @property
    def platform_index_dir(self) -> Path:
        """Path to platform-based index directory."""
        return self.indexes_dir / "by_platform"

    # =========================================================================
    # Structure Management
    # =========================================================================

    def create_structure(self) -> None:
        """Create the repository directory structure."""
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.repo_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate that repository structure exists.

        Supports both standard and legacy layouts.

        Returns:
            True if repo structure is valid
        """
        # Check for legacy layout first
        if self.is_legacy_layout:
            return self._validate_legacy()

        # Check that at least the core structure exists
        if not self.metaspn_dir.is_dir():
            return False

        # Check required files
        for file_path in self.REQUIRED_FILES:
            full_path = self.repo_path / file_path
            if not full_path.is_file():
                return False

        # Check that sources or artifacts exist
        has_sources = self.sources_dir.is_dir()
        has_artifacts = self.artifacts_dir.is_dir()

        return has_sources or has_artifacts

    def _validate_legacy(self) -> bool:
        """Validate legacy layout (meta.json style)."""
        if not (self.repo_path / self.LEGACY_PROFILE).is_file():
            return False
        has_sources = self.sources_dir.is_dir()
        has_artifacts = self.artifacts_dir.is_dir()
        return has_sources or has_artifacts

    # =========================================================================
    # Activity File Discovery
    # =========================================================================

    def get_activity_files(
        self,
        platform: Optional[str] = None,
        activity_type: Optional[Literal["create", "consume"]] = None,
    ) -> list[Path]:
        """Get all activity files, optionally filtered.

        Args:
            platform: Optional platform to filter by
            activity_type: Optional activity type ("create" for artifacts, "consume" for sources)

        Returns:
            List of activity file paths
        """
        files = []

        if self.is_legacy_layout:
            return self._get_legacy_activity_files(platform)

        # Determine which directories to search
        search_sources = activity_type is None or activity_type == "consume"
        search_artifacts = activity_type is None or activity_type == "create"

        # Search sources (consumed content)
        if search_sources:
            if platform:
                # Map artifact platform names to source platform names
                source_platform = self._artifact_to_source_platform(platform)
                if source_platform:
                    source_dir = self.get_source_dir(source_platform)
                    if source_dir.is_dir():
                        files.extend(source_dir.glob("*.jsonl"))
                        files.extend(source_dir.glob("*.json"))
            else:
                for source_platform in self.SOURCE_PLATFORMS:
                    source_dir = self.get_source_dir(source_platform)
                    if source_dir.is_dir():
                        files.extend(source_dir.glob("*.jsonl"))
                        files.extend(source_dir.glob("*.json"))

        # Search artifacts (created content)
        if search_artifacts:
            if platform:
                artifact_dir = self.get_artifact_dir(platform)
                if artifact_dir.is_dir():
                    files.extend(artifact_dir.glob("*.jsonl"))
                    files.extend(artifact_dir.glob("*.json"))
            else:
                for artifact_platform in self.ARTIFACT_PLATFORMS:
                    artifact_dir = self.get_artifact_dir(artifact_platform)
                    if artifact_dir.is_dir():
                        files.extend(artifact_dir.glob("*.jsonl"))
                        files.extend(artifact_dir.glob("*.json"))

        return sorted(files)

    def _artifact_to_source_platform(self, artifact_platform: str) -> Optional[str]:
        """Map artifact platform name to source platform name."""
        mapping = {
            "twitter": "twitter",
            "podcast": "podcasts",
            "blog": "blogs",
            "youtube": None,  # No consumption tracking for youtube yet
        }
        return mapping.get(artifact_platform)

    def _get_legacy_activity_files(self, platform: Optional[str] = None) -> list[Path]:
        """Get activity files from legacy layout."""
        files = []

        platform_mapping = {
            "podcast": [
                self.repo_path / "artifacts" / "podcast",
                self.repo_path / "sources" / "podcasts",
            ],
            "blog": [
                self.repo_path / "artifacts" / "blog",
                self.repo_path / "sources" / "blogs",
            ],
            "twitter": [
                self.repo_path / "artifacts" / "twitter",
                self.repo_path / "sources" / "twitter",
            ],
            "youtube": [
                self.repo_path / "artifacts" / "youtube",
                self.repo_path / "sources" / "youtube",
            ],
        }

        if platform:
            dirs = platform_mapping.get(platform, [])
            for d in dirs:
                if d.is_dir():
                    files.extend(d.glob("*.jsonl"))
                    files.extend(d.glob("*.json"))
        else:
            for platform_dirs in platform_mapping.values():
                for d in platform_dirs:
                    if d.is_dir():
                        files.extend(d.glob("*.jsonl"))
                        files.extend(d.glob("*.json"))

        return sorted(files)


def init_repo(path: str, user_info: dict) -> None:
    """Initialize a new MetaSPN repository with data lake structure.

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
        "source_platforms": ["podcasts", "books", "blogs", "twitter"],
        "artifact_platforms": ["twitter", "podcast", "blog", "youtube"],
        "created_at": datetime.now().isoformat(),
    }

    with open(structure.config_path, "w") as f:
        json.dump(config_data, f, indent=2)

    # Create .gitkeep files in empty directories
    # Sources (consumed content)
    for platform in structure.SOURCE_PLATFORMS:
        (structure.get_source_dir(platform) / ".gitkeep").touch()

    # Artifacts (created content)
    for platform in structure.ARTIFACT_PLATFORMS:
        (structure.get_artifact_dir(platform) / ".gitkeep").touch()

    # Enhancements with history
    for enhancement_type in ["quality_scores", "game_signatures", "embeddings"]:
        (structure.get_enhancement_dir(enhancement_type) / ".gitkeep").touch()
        (structure.get_enhancement_history_dir(enhancement_type) / ".gitkeep").touch()

    # Indexes
    (structure.indexes_dir / ".gitkeep").touch()
    (structure.date_index_dir / ".gitkeep").touch()
    (structure.platform_index_dir / ".gitkeep").touch()

    # Reports
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
    if not structure.is_legacy_layout and structure.config_path.exists():
        with open(structure.config_path) as f:
            config = json.load(f)

    # Count activities
    activity_files = structure.get_activity_files()

    # Handle legacy format
    user_id = profile.get("user_id", "unknown")
    name = profile.get("name", user_id)
    handle = profile.get("handle", f"@{user_id}")
    created_at = profile.get("created_at") or profile.get("last_sync")

    return {
        "path": str(structure.repo_path),
        "user_id": user_id,
        "name": name,
        "handle": handle,
        "created_at": created_at,
        "version": profile.get("version") or profile.get("schema_version"),
        "platforms": config.get("platforms", []),
        "activity_files": len(activity_files),
        "is_legacy": structure.is_legacy_layout,
    }
