"""Enhancement store for managing computed enhancement layers.

The EnhancementStore provides a unified interface for reading, writing,
and joining enhancement layers with source activities. It maintains
the separation between raw source data and computed enhancements.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from metaspn.core.enhancements import (
    EmbeddingEnhancement,
    GameSignatureEnhancement,
    QualityScoreEnhancement,
)
from metaspn.repo.structure import RepoStructure
from metaspn.repo.writer import RepoWriter

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class EnhancementStore:
    """Store for managing enhancement layers.

    Handles reading, writing, and joining enhancement data with
    source activities. Enhancements are stored in JSONL files
    in artifacts/enhancements/ and reference activities by activity_id.

    Example:
        >>> store = EnhancementStore("./my-content")
        >>>
        >>> # Save quality scores
        >>> scores = [QualityScoreEnhancement(activity_id="x", quality_score=0.85)]
        >>> store.save_quality_scores(scores)
        >>>
        >>> # Load and join with activities
        >>> activities = reader.load_activities()
        >>> enhanced = store.get_all_enhanced(activities)
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize enhancement store.

        Args:
            repo_path: Path to MetaSPN repository
        """
        self.structure = RepoStructure(repo_path)
        self.writer = RepoWriter(repo_path)

    # =========================================================================
    # Writing Methods
    # =========================================================================

    def save_quality_scores(
        self,
        scores: list[QualityScoreEnhancement],
        append: bool = False,
    ) -> Path:
        """Save quality score enhancements.

        Args:
            scores: List of quality score enhancements
            append: If True, append to existing file; otherwise overwrite

        Returns:
            Path to the quality scores file
        """
        if append:
            for score in scores:
                self.writer.append_jsonl(self.structure.quality_scores_path, score)
            return self.structure.quality_scores_path
        return self.writer.write_jsonl(self.structure.quality_scores_path, scores)

    def save_game_signatures(
        self,
        signatures: list[GameSignatureEnhancement],
        append: bool = False,
    ) -> Path:
        """Save game signature enhancements.

        Args:
            signatures: List of game signature enhancements
            append: If True, append to existing file; otherwise overwrite

        Returns:
            Path to the game signatures file
        """
        if append:
            for sig in signatures:
                self.writer.append_jsonl(self.structure.game_signatures_path, sig)
            return self.structure.game_signatures_path
        return self.writer.write_jsonl(self.structure.game_signatures_path, signatures)

    def save_embeddings(
        self,
        embeddings: list[EmbeddingEnhancement],
        append: bool = False,
    ) -> Path:
        """Save embedding enhancements.

        Args:
            embeddings: List of embedding enhancements
            append: If True, append to existing file; otherwise overwrite

        Returns:
            Path to the embeddings file
        """
        if append:
            for emb in embeddings:
                self.writer.append_jsonl(self.structure.embeddings_path, emb)
            return self.structure.embeddings_path
        return self.writer.write_jsonl(self.structure.embeddings_path, embeddings)

    # =========================================================================
    # Reading Methods
    # =========================================================================

    def load_quality_scores(self) -> dict[str, QualityScoreEnhancement]:
        """Load all quality score enhancements.

        Returns:
            Dictionary mapping activity_id to QualityScoreEnhancement
        """
        return self._load_enhancements(
            self.structure.quality_scores_path,
            QualityScoreEnhancement,
        )

    def load_game_signatures(self) -> dict[str, GameSignatureEnhancement]:
        """Load all game signature enhancements.

        Returns:
            Dictionary mapping activity_id to GameSignatureEnhancement
        """
        return self._load_enhancements(
            self.structure.game_signatures_path,
            GameSignatureEnhancement,
        )

    def load_embeddings(self) -> dict[str, EmbeddingEnhancement]:
        """Load all embedding enhancements.

        Returns:
            Dictionary mapping activity_id to EmbeddingEnhancement
        """
        return self._load_enhancements(
            self.structure.embeddings_path,
            EmbeddingEnhancement,
        )

    def _load_enhancements(self, path: Path, cls: type) -> dict:
        """Load enhancements from a JSONL file.

        Args:
            path: Path to JSONL file
            cls: Enhancement class with from_dict method

        Returns:
            Dictionary mapping activity_id to enhancement
        """
        result = {}

        if not path.exists():
            return result

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    enhancement = cls.from_dict(data)
                    result[enhancement.activity_id] = enhancement
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Skip malformed records
                    continue

        return result

    # =========================================================================
    # Joining Methods
    # =========================================================================

    def get_enhanced_activity(
        self,
        activity: "Activity",
        quality_map: Optional[dict[str, QualityScoreEnhancement]] = None,
        game_map: Optional[dict[str, GameSignatureEnhancement]] = None,
        embedding_map: Optional[dict[str, EmbeddingEnhancement]] = None,
    ) -> "EnhancedActivity":
        """Get an activity with its enhancements joined.

        Args:
            activity: Source activity to enhance
            quality_map: Pre-loaded quality scores (loads if None)
            game_map: Pre-loaded game signatures (loads if None)
            embedding_map: Pre-loaded embeddings (loads if None)

        Returns:
            EnhancedActivity with joined enhancements
        """
        # Lazy load maps if not provided
        if quality_map is None:
            quality_map = self.load_quality_scores()
        if game_map is None:
            game_map = self.load_game_signatures()
        if embedding_map is None:
            embedding_map = self.load_embeddings()

        return EnhancedActivity(
            activity=activity,
            quality_enhancement=quality_map.get(activity.activity_id),
            game_enhancement=game_map.get(activity.activity_id),
            embedding_enhancement=embedding_map.get(activity.activity_id),
        )

    def get_all_enhanced(
        self,
        activities: list["Activity"],
        load_quality: bool = True,
        load_games: bool = True,
        load_embeddings: bool = False,
    ) -> list["EnhancedActivity"]:
        """Get all activities with their enhancements joined.

        Efficiently loads enhancement maps once and joins all activities.

        Args:
            activities: List of source activities
            load_quality: Whether to load quality scores
            load_games: Whether to load game signatures
            load_embeddings: Whether to load embeddings

        Returns:
            List of EnhancedActivity with joined enhancements
        """
        # Load maps once
        quality_map = self.load_quality_scores() if load_quality else {}
        game_map = self.load_game_signatures() if load_games else {}
        embedding_map = self.load_embeddings() if load_embeddings else {}

        # Join all activities
        return [
            self.get_enhanced_activity(
                activity,
                quality_map=quality_map,
                game_map=game_map,
                embedding_map=embedding_map,
            )
            for activity in activities
        ]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def has_quality_scores(self) -> bool:
        """Check if quality scores file exists."""
        return self.structure.quality_scores_path.exists()

    def has_game_signatures(self) -> bool:
        """Check if game signatures file exists."""
        return self.structure.game_signatures_path.exists()

    def has_embeddings(self) -> bool:
        """Check if embeddings file exists."""
        return self.structure.embeddings_path.exists()

    def get_unprocessed_activities(
        self,
        activities: list["Activity"],
        enhancement_type: str,
    ) -> list["Activity"]:
        """Get activities that don't have a specific enhancement.

        Useful for incremental processing - only compute enhancements
        for activities that haven't been processed yet.

        Args:
            activities: List of all activities
            enhancement_type: Type of enhancement (quality_scores, game_signatures, embeddings)

        Returns:
            List of activities without the specified enhancement
        """
        existing_ids: set[str] = set()

        if enhancement_type == "quality_scores":
            existing_ids = set(self.load_quality_scores().keys())
        elif enhancement_type == "game_signatures":
            existing_ids = set(self.load_game_signatures().keys())
        elif enhancement_type == "embeddings":
            existing_ids = set(self.load_embeddings().keys())
        else:
            raise ValueError(f"Unknown enhancement type: {enhancement_type}")

        return [a for a in activities if a.activity_id not in existing_ids]

    def clear_enhancements(self, enhancement_type: Optional[str] = None) -> None:
        """Clear enhancement files for recomputation.

        Args:
            enhancement_type: Specific type to clear, or None to clear all
        """
        paths = {
            "quality_scores": self.structure.quality_scores_path,
            "game_signatures": self.structure.game_signatures_path,
            "embeddings": self.structure.embeddings_path,
        }

        if enhancement_type:
            if enhancement_type not in paths:
                raise ValueError(f"Unknown enhancement type: {enhancement_type}")
            path = paths[enhancement_type]
            if path.exists():
                path.unlink()
        else:
            # Clear all
            for path in paths.values():
                if path.exists():
                    path.unlink()


class EnhancedActivity:
    """Activity with its computed enhancements joined.

    Read-only view that wraps an Activity and provides convenient
    access to its enhancement data without modifying the underlying
    Activity object.
    """

    def __init__(
        self,
        activity: "Activity",
        quality_enhancement: Optional[QualityScoreEnhancement] = None,
        game_enhancement: Optional[GameSignatureEnhancement] = None,
        embedding_enhancement: Optional[EmbeddingEnhancement] = None,
    ) -> None:
        """Initialize enhanced activity.

        Args:
            activity: The source activity
            quality_enhancement: Quality score enhancement if available
            game_enhancement: Game signature enhancement if available
            embedding_enhancement: Embedding enhancement if available
        """
        self._activity = activity
        self._quality = quality_enhancement
        self._game = game_enhancement
        self._embedding = embedding_enhancement

    @property
    def activity(self) -> "Activity":
        """The underlying source activity."""
        return self._activity

    # Forward common activity properties
    @property
    def activity_id(self) -> str:
        """Activity ID."""
        return self._activity.activity_id

    @property
    def timestamp(self):
        """Activity timestamp."""
        return self._activity.timestamp

    @property
    def platform(self) -> str:
        """Activity platform."""
        return self._activity.platform

    @property
    def activity_type(self) -> str:
        """Activity type (create/consume)."""
        return self._activity.activity_type

    @property
    def title(self) -> Optional[str]:
        """Activity title."""
        return self._activity.title

    @property
    def content(self) -> Optional[str]:
        """Activity content."""
        return self._activity.content

    @property
    def url(self) -> Optional[str]:
        """Activity URL."""
        return self._activity.url

    @property
    def duration_seconds(self) -> Optional[int]:
        """Activity duration in seconds."""
        return self._activity.duration_seconds

    # Enhancement accessors
    @property
    def quality_enhancement(self) -> Optional[QualityScoreEnhancement]:
        """Quality score enhancement if available."""
        return self._quality

    @property
    def game_enhancement(self) -> Optional[GameSignatureEnhancement]:
        """Game signature enhancement if available."""
        return self._game

    @property
    def embedding_enhancement(self) -> Optional[EmbeddingEnhancement]:
        """Embedding enhancement if available."""
        return self._embedding

    # Convenience accessors for common values
    @property
    def quality_score(self) -> Optional[float]:
        """Quality score from enhancement, or None if not computed."""
        if self._quality:
            return self._quality.quality_score
        # Fall back to embedded score for backward compatibility
        return self._activity.quality_score

    @property
    def game_signature(self):
        """Game signature from enhancement, or None if not computed."""
        if self._game:
            return self._game.game_signature
        # Fall back to embedded signature for backward compatibility
        return self._activity.game_signature

    @property
    def embedding(self) -> Optional[list[float]]:
        """Embedding vector from enhancement, or None if not computed."""
        if self._embedding:
            return self._embedding.embedding
        return None

    @property
    def has_quality_score(self) -> bool:
        """True if quality score enhancement is available."""
        return self._quality is not None

    @property
    def has_game_signature(self) -> bool:
        """True if game signature enhancement is available."""
        return self._game is not None

    @property
    def has_embedding(self) -> bool:
        """True if embedding enhancement is available."""
        return self._embedding is not None

    def __repr__(self) -> str:
        """String representation."""
        enhancements = []
        if self._quality:
            enhancements.append(f"quality={self._quality.quality_score:.2f}")
        if self._game:
            enhancements.append(f"game={self._game.primary_game}")
        if self._embedding:
            enhancements.append(f"embedding={self._embedding.dimensions}d")

        enh_str = ", ".join(enhancements) if enhancements else "none"
        return f"EnhancedActivity({self._activity.activity_id}, enhancements=[{enh_str}])"
