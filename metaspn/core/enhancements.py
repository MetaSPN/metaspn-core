"""Enhancement layer data structures for MetaSPN.

Enhancement layers store computed data separately from raw source data,
allowing source files to remain append-only while enhancements can be
recomputed without modifying the original records.

Each enhancement references its source activity by activity_id and includes
metadata about when and how it was computed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from metaspn.core.metrics import GameSignature

# Current algorithm versions - bump when computation logic changes
QUALITY_ALGORITHM_VERSION = "1.0"
GAME_SIGNATURE_ALGORITHM_VERSION = "1.0"
EMBEDDING_ALGORITHM_VERSION = "1.0"


@dataclass
class EnhancementRecord:
    """Base class for all enhancement records.

    Every enhancement must reference its source activity and track
    computation metadata for recomputation support.
    """

    activity_id: str
    computed_at: datetime = field(default_factory=datetime.now)
    algorithm_version: str = "1.0"

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSONL storage."""
        return {
            "activity_id": self.activity_id,
            "computed_at": self.computed_at.isoformat(),
            "algorithm_version": self.algorithm_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnhancementRecord":
        """Deserialize from dictionary."""
        return cls(
            activity_id=data["activity_id"],
            computed_at=datetime.fromisoformat(data["computed_at"]),
            algorithm_version=data.get("algorithm_version", "1.0"),
        )


@dataclass
class QualityScoreEnhancement(EnhancementRecord):
    """Enhancement layer for quality scores.

    Stores the computed quality score for an individual activity,
    along with component scores for debugging/analysis.
    """

    quality_score: float = 0.0
    content_score: float = 0.0
    consistency_score: float = 0.0
    depth_score: float = 0.0
    algorithm_version: str = QUALITY_ALGORITHM_VERSION

    def __post_init__(self) -> None:
        """Validate score ranges."""
        for field_name in ["quality_score", "content_score", "consistency_score", "depth_score"]:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSONL storage."""
        base = super().to_dict()
        base.update(
            {
                "quality_score": self.quality_score,
                "content_score": self.content_score,
                "consistency_score": self.consistency_score,
                "depth_score": self.depth_score,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "QualityScoreEnhancement":
        """Deserialize from dictionary."""
        return cls(
            activity_id=data["activity_id"],
            computed_at=datetime.fromisoformat(data["computed_at"]),
            algorithm_version=data.get("algorithm_version", QUALITY_ALGORITHM_VERSION),
            quality_score=data.get("quality_score", 0.0),
            content_score=data.get("content_score", 0.0),
            consistency_score=data.get("consistency_score", 0.0),
            depth_score=data.get("depth_score", 0.0),
        )


@dataclass
class GameSignatureEnhancement(EnhancementRecord):
    """Enhancement layer for game signature classification.

    Stores the computed game signature distribution for an individual activity.
    """

    game_signature: GameSignature = field(default_factory=GameSignature)
    confidence: float = 0.0  # Model confidence in classification
    algorithm_version: str = GAME_SIGNATURE_ALGORITHM_VERSION

    def __post_init__(self) -> None:
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def primary_game(self) -> Optional[str]:
        """Return the game with the highest score."""
        return self.game_signature.primary_game

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSONL storage."""
        base = super().to_dict()
        base.update(
            {
                "game_signature": self.game_signature.to_dict(),
                "confidence": self.confidence,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "GameSignatureEnhancement":
        """Deserialize from dictionary."""
        return cls(
            activity_id=data["activity_id"],
            computed_at=datetime.fromisoformat(data["computed_at"]),
            algorithm_version=data.get("algorithm_version", GAME_SIGNATURE_ALGORITHM_VERSION),
            game_signature=GameSignature.from_dict(data.get("game_signature", {})),
            confidence=data.get("confidence", 0.0),
        )


@dataclass
class EmbeddingEnhancement(EnhancementRecord):
    """Enhancement layer for vector embeddings.

    Stores the computed embedding vector for an individual activity.
    Useful for semantic search and similarity computations.
    """

    embedding: list[float] = field(default_factory=list)
    model_name: str = ""
    dimensions: int = 0
    algorithm_version: str = EMBEDDING_ALGORITHM_VERSION

    def __post_init__(self) -> None:
        """Set dimensions from embedding length."""
        if self.embedding and self.dimensions == 0:
            self.dimensions = len(self.embedding)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSONL storage."""
        base = super().to_dict()
        base.update(
            {
                "embedding": self.embedding,
                "model_name": self.model_name,
                "dimensions": self.dimensions,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingEnhancement":
        """Deserialize from dictionary."""
        return cls(
            activity_id=data["activity_id"],
            computed_at=datetime.fromisoformat(data["computed_at"]),
            algorithm_version=data.get("algorithm_version", EMBEDDING_ALGORITHM_VERSION),
            embedding=data.get("embedding", []),
            model_name=data.get("model_name", ""),
            dimensions=data.get("dimensions", 0),
        )
