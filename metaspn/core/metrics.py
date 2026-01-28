"""Metrics data structures for MetaSPN."""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime


@dataclass
class GameSignature:
    """Distribution across six games representing different types of value creation.
    
    Each game score is a float from 0.00 to 1.00.
    
    Games:
        G1: Identity/Canon - Foundational content that defines who you are
        G2: Idea Mining - Exploration and discovery of new concepts
        G3: Models - Framework and system building
        G4: Performance - Entertainment and engagement
        G5: Meaning - Deep insight and wisdom sharing
        G6: Network - Connection and community building
    """
    
    G1: float = 0.0  # Identity/Canon
    G2: float = 0.0  # Idea Mining
    G3: float = 0.0  # Models
    G4: float = 0.0  # Performance
    G5: float = 0.0  # Meaning
    G6: float = 0.0  # Network
    
    def __post_init__(self) -> None:
        """Validate game scores are in valid range."""
        for game in ["G1", "G2", "G3", "G4", "G5", "G6"]:
            value = getattr(self, game)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{game} must be between 0.0 and 1.0, got {value}")
    
    @property
    def primary_game(self) -> Optional[str]:
        """Return the game with the highest score, or None if all are zero."""
        games = {"G1": self.G1, "G2": self.G2, "G3": self.G3, 
                 "G4": self.G4, "G5": self.G5, "G6": self.G6}
        max_score = max(games.values())
        if max_score == 0:
            return None
        return max(games, key=games.get)  # type: ignore
    
    @property
    def is_specialist(self) -> bool:
        """True if any game score exceeds 0.60."""
        return any(score > 0.60 for score in [self.G1, self.G2, self.G3, 
                                               self.G4, self.G5, self.G6])
    
    @property
    def is_multi_game(self) -> bool:
        """True if 3 or more games exceed 0.30."""
        count = sum(1 for score in [self.G1, self.G2, self.G3, 
                                     self.G4, self.G5, self.G6] if score > 0.30)
        return count >= 3
    
    @property
    def is_balanced(self) -> bool:
        """True if no single game dominates (all within 0.20 of each other)."""
        scores = [self.G1, self.G2, self.G3, self.G4, self.G5, self.G6]
        if not any(scores):
            return True
        return max(scores) - min(scores) <= 0.20
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "G1": self.G1,
            "G2": self.G2,
            "G3": self.G3,
            "G4": self.G4,
            "G5": self.G5,
            "G6": self.G6,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameSignature":
        """Deserialize from dictionary."""
        return cls(
            G1=data.get("G1", 0.0),
            G2=data.get("G2", 0.0),
            G3=data.get("G3", 0.0),
            G4=data.get("G4", 0.0),
            G5=data.get("G5", 0.0),
            G6=data.get("G6", 0.0),
        )


@dataclass
class Trajectory:
    """Trajectory data representing trends over a time window."""
    
    direction: Literal["ascending", "stable", "descending"]
    slope: float  # Rate of change
    window_days: int = 30
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data_points: int = 0
    
    @property
    def is_positive(self) -> bool:
        """True if trajectory is ascending."""
        return self.direction == "ascending"
    
    @property
    def is_stable(self) -> bool:
        """True if trajectory is stable."""
        return self.direction == "stable"
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "direction": self.direction,
            "slope": self.slope,
            "window_days": self.window_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "data_points": self.data_points,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Trajectory":
        """Deserialize from dictionary."""
        return cls(
            direction=data.get("direction", "stable"),
            slope=data.get("slope", 0.0),
            window_days=data.get("window_days", 30),
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            data_points=data.get("data_points", 0),
        )


@dataclass
class CreatorMetrics:
    """Metrics for content creators."""
    
    quality_score: float = 0.0       # 0.00-1.00
    game_alignment: float = 0.0      # 0.00-1.00
    impact_factor: float = 0.0       # 0.00-1.00
    calibration: float = 0.0         # 0.00-1.00
    
    game_signature: GameSignature = field(default_factory=GameSignature)
    trajectory: Trajectory = field(default_factory=lambda: Trajectory(direction="stable", slope=0.0))
    
    total_outputs: int = 0
    consistency_score: float = 0.0   # 0.00-1.00
    
    def __post_init__(self) -> None:
        """Validate score ranges."""
        for field_name in ["quality_score", "game_alignment", "impact_factor", 
                          "calibration", "consistency_score"]:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")
    
    @property
    def overall_score(self) -> float:
        """Compute weighted overall score."""
        return (
            self.quality_score * 0.35 +
            self.game_alignment * 0.25 +
            self.impact_factor * 0.25 +
            self.calibration * 0.15
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "quality_score": self.quality_score,
            "game_alignment": self.game_alignment,
            "impact_factor": self.impact_factor,
            "calibration": self.calibration,
            "game_signature": self.game_signature.to_dict(),
            "trajectory": self.trajectory.to_dict(),
            "total_outputs": self.total_outputs,
            "consistency_score": self.consistency_score,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CreatorMetrics":
        """Deserialize from dictionary."""
        return cls(
            quality_score=data.get("quality_score", 0.0),
            game_alignment=data.get("game_alignment", 0.0),
            impact_factor=data.get("impact_factor", 0.0),
            calibration=data.get("calibration", 0.0),
            game_signature=GameSignature.from_dict(data.get("game_signature", {})),
            trajectory=Trajectory.from_dict(data.get("trajectory", {"direction": "stable", "slope": 0.0})),
            total_outputs=data.get("total_outputs", 0),
            consistency_score=data.get("consistency_score", 0.0),
        )


@dataclass
class ConsumerMetrics:
    """Metrics for content consumers."""
    
    execution_rate: float = 0.0      # 0.00-1.00
    integration_skill: float = 0.0   # 0.00-1.00
    discernment: float = 0.0         # 0.00-1.00
    development: float = 0.0         # 0.00-1.00
    
    consumption_games: GameSignature = field(default_factory=GameSignature)
    
    total_consumed: int = 0
    hours_consumed: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate score ranges."""
        for field_name in ["execution_rate", "integration_skill", 
                          "discernment", "development"]:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")
    
    @property
    def overall_score(self) -> float:
        """Compute weighted overall score."""
        return (
            self.execution_rate * 0.30 +
            self.integration_skill * 0.30 +
            self.discernment * 0.20 +
            self.development * 0.20
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "execution_rate": self.execution_rate,
            "integration_skill": self.integration_skill,
            "discernment": self.discernment,
            "development": self.development,
            "consumption_games": self.consumption_games.to_dict(),
            "total_consumed": self.total_consumed,
            "hours_consumed": self.hours_consumed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConsumerMetrics":
        """Deserialize from dictionary."""
        return cls(
            execution_rate=data.get("execution_rate", 0.0),
            integration_skill=data.get("integration_skill", 0.0),
            discernment=data.get("discernment", 0.0),
            development=data.get("development", 0.0),
            consumption_games=GameSignature.from_dict(data.get("consumption_games", {})),
            total_consumed=data.get("total_consumed", 0),
            hours_consumed=data.get("hours_consumed", 0.0),
        )


@dataclass
class DevelopmentMetrics:
    """Metrics tracking overall development and achievements."""
    
    total_activities: int = 0
    active_days: int = 0
    streak_current: int = 0
    streak_longest: int = 0
    first_activity: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    platforms_active: int = 0
    achievements: List[str] = field(default_factory=list)  # List of badge IDs
    
    @property
    def days_active(self) -> int:
        """Calculate days since first activity."""
        if not self.first_activity:
            return 0
        return (datetime.now() - self.first_activity).days
    
    @property
    def activity_rate(self) -> float:
        """Calculate activities per active day."""
        if self.active_days == 0:
            return 0.0
        return self.total_activities / self.active_days
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "total_activities": self.total_activities,
            "active_days": self.active_days,
            "streak_current": self.streak_current,
            "streak_longest": self.streak_longest,
            "first_activity": self.first_activity.isoformat() if self.first_activity else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "platforms_active": self.platforms_active,
            "achievements": self.achievements,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DevelopmentMetrics":
        """Deserialize from dictionary."""
        return cls(
            total_activities=data.get("total_activities", 0),
            active_days=data.get("active_days", 0),
            streak_current=data.get("streak_current", 0),
            streak_longest=data.get("streak_longest", 0),
            first_activity=datetime.fromisoformat(data["first_activity"]) if data.get("first_activity") else None,
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            platforms_active=data.get("platforms_active", 0),
            achievements=data.get("achievements", []),
        )
