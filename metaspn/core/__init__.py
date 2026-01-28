"""Core module - data structures and computation logic."""

from metaspn.core.card import Card, CardData, generate_cards
from metaspn.core.level import AchievementSystem, Badge, LevelCalculator, RarityCalculator
from metaspn.core.metrics import (
    ConsumerMetrics,
    CreatorMetrics,
    DevelopmentMetrics,
    GameSignature,
    Trajectory,
)
from metaspn.core.profile import (
    Activity,
    PlatformPresence,
    ProfileMetrics,
    UserProfile,
    compute_profile,
)
from metaspn.core.state_machine import LifecycleState, LifecycleStateMachine

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
