"""Core module - data structures and computation logic."""

from metaspn.core.profile import (
    Activity,
    UserProfile,
    PlatformPresence,
    ProfileMetrics,
    compute_profile,
)
from metaspn.core.metrics import (
    GameSignature,
    CreatorMetrics,
    ConsumerMetrics,
    Trajectory,
    DevelopmentMetrics,
)
from metaspn.core.card import CardData, Card, generate_cards
from metaspn.core.state_machine import LifecycleStateMachine, LifecycleState
from metaspn.core.level import LevelCalculator, RarityCalculator, AchievementSystem, Badge

__all__ = [
    # Profile
    "Activity",
    "UserProfile",
    "PlatformPresence",
    "ProfileMetrics",
    "compute_profile",
    # Metrics
    "GameSignature",
    "CreatorMetrics",
    "ConsumerMetrics",
    "Trajectory",
    "DevelopmentMetrics",
    # Cards
    "CardData",
    "Card",
    "generate_cards",
    # State Machine
    "LifecycleStateMachine",
    "LifecycleState",
    # Level/Rarity
    "LevelCalculator",
    "RarityCalculator",
    "AchievementSystem",
    "Badge",
]
