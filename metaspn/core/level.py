"""Level, rarity, and achievement systems for MetaSPN."""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from metaspn.core.profile import Activity, ProfileMetrics
    from metaspn.core.state_machine import LifecycleState


@dataclass
class Badge:
    """Achievement badge earned by a user."""

    badge_id: str
    name: str
    description: str
    icon: str
    category: str
    earned_at: datetime
    rarity: str = "common"  # common, uncommon, rare, epic, legendary

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "badge_id": self.badge_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "earned_at": self.earned_at.isoformat(),
            "rarity": self.rarity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Badge":
        """Deserialize from dictionary."""
        return cls(
            badge_id=data["badge_id"],
            name=data["name"],
            description=data["description"],
            icon=data.get("icon", "🏆"),
            category=data.get("category", "general"),
            earned_at=(
                datetime.fromisoformat(data["earned_at"])
                if data.get("earned_at")
                else datetime.now()
            ),
            rarity=data.get("rarity", "common"),
        )


@dataclass
class AchievementDefinition:
    """Definition of an achievement that can be earned."""

    badge_id: str
    name: str
    description: str
    icon: str
    category: str
    rarity: str
    check: Callable[["Activity", "ProfileMetrics", Optional["LifecycleState"]], bool]


class LevelCalculator:
    """Calculator for XP and levels.

    XP System:
        - Creation activities: 100 XP base + quality bonus
        - Consumption activities: 25 XP base + engagement bonus
        - Streak bonuses: +10% per consecutive day (max 50%)
        - Quality multiplier: up to 2x for high quality content

    Level Formula:
        XP required = 100 * (level ^ 1.5)
        Level 1: 100 XP
        Level 5: ~1,118 XP
        Level 10: ~3,162 XP
        Level 20: ~8,944 XP
        Level 50: ~35,355 XP
    """

    # Base XP values
    CREATE_BASE_XP = 100
    CONSUME_BASE_XP = 25

    # Level formula exponent
    LEVEL_EXPONENT = 1.5
    LEVEL_BASE = 100

    def compute_xp(self, activities: list["Activity"], metrics: "ProfileMetrics") -> int:
        """Compute total XP from activities and metrics.

        Args:
            activities: List of all activities
            metrics: Computed profile metrics

        Returns:
            Total XP as integer
        """
        if not activities:
            return 0

        total_xp = 0

        # Sort activities by timestamp for streak calculation
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)

        current_streak = 0
        last_date = None

        for activity in sorted_activities:
            # Calculate streak bonus
            activity_date = activity.timestamp.date()
            if last_date is not None:
                days_diff = (activity_date - last_date).days
                if days_diff == 1:
                    current_streak = min(current_streak + 1, 5)  # Max 5 day streak bonus
                elif days_diff > 1:
                    current_streak = 0
            last_date = activity_date

            streak_multiplier = 1.0 + (current_streak * 0.10)  # +10% per streak day

            # Base XP by activity type
            if activity.activity_type == "create":
                base_xp = self.CREATE_BASE_XP

                # Quality bonus for creation
                quality = activity.quality_score or 0.5
                quality_multiplier = 1.0 + quality  # 1.0-2.0x

                xp = base_xp * quality_multiplier * streak_multiplier
            else:
                base_xp = self.CONSUME_BASE_XP

                # Duration bonus for consumption
                duration_hours = (activity.duration_seconds or 0) / 3600.0
                duration_bonus = min(duration_hours * 10, 50)  # Max 50 XP duration bonus

                xp = (base_xp + duration_bonus) * streak_multiplier

            total_xp += int(xp)

        # Achievement bonuses
        if metrics.development:
            total_xp += len(metrics.development.achievements) * 50

        return total_xp

    def compute_level(self, xp: int) -> int:
        """Compute level from XP.

        Args:
            xp: Total XP

        Returns:
            Current level (minimum 1)
        """
        if xp <= 0:
            return 1

        # Inverse of XP formula: level = (xp / base) ^ (1/exponent)
        level = int(math.pow(xp / self.LEVEL_BASE, 1 / self.LEVEL_EXPONENT))
        return max(1, level)

    def xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level.

        Args:
            level: Target level

        Returns:
            XP required to reach that level
        """
        if level <= 1:
            return 0
        return int(self.LEVEL_BASE * math.pow(level, self.LEVEL_EXPONENT))

    def xp_to_next_level(self, current_xp: int) -> int:
        """Calculate XP needed to reach next level.

        Args:
            current_xp: Current XP

        Returns:
            XP needed for next level
        """
        current_level = self.compute_level(current_xp)
        next_level_xp = self.xp_for_level(current_level + 1)
        return max(0, next_level_xp - current_xp)

    def level_progress(self, current_xp: int) -> float:
        """Calculate progress through current level.

        Args:
            current_xp: Current XP

        Returns:
            Progress as 0.0-1.0
        """
        current_level = self.compute_level(current_xp)
        current_level_xp = self.xp_for_level(current_level)
        next_level_xp = self.xp_for_level(current_level + 1)

        level_range = next_level_xp - current_level_xp
        if level_range <= 0:
            return 1.0

        progress_in_level = current_xp - current_level_xp
        return min(1.0, max(0.0, progress_in_level / level_range))


class RarityCalculator:
    """Calculator for rarity tiers.

    Rarity Tiers:
        common: Default, basic activity
        uncommon: Some notable characteristics
        rare: Significant achievement or quality
        epic: Exceptional performance
        legendary: Top-tier, rare accomplishment

    Factors:
        - Quality score (creator)
        - Consistency
        - Lifecycle phase
        - Achievement count
        - Impact factor
    """

    TIERS = ["common", "uncommon", "rare", "epic", "legendary"]

    def compute(self, metrics: "ProfileMetrics", lifecycle: Optional["LifecycleState"]) -> str:
        """Compute rarity tier based on metrics and lifecycle.

        Args:
            metrics: Profile metrics
            lifecycle: Current lifecycle state

        Returns:
            Rarity tier string
        """
        score = 0.0

        # Creator metrics contribution (if present)
        if metrics.creator:
            score += metrics.creator.quality_score * 25
            score += metrics.creator.impact_factor * 20
            score += metrics.creator.consistency_score * 10
            if metrics.creator.game_signature.is_specialist:
                score += 10

        # Consumer metrics contribution (if present)
        if metrics.consumer:
            score += metrics.consumer.execution_rate * 15
            score += metrics.consumer.integration_skill * 10

        # Lifecycle contribution
        if lifecycle:
            phase_scores = {
                "rookie": 0,
                "developing": 5,
                "established": 15,
                "veteran": 25,
                "legend": 40,
            }
            score += phase_scores.get(lifecycle.phase, 0)

        # Achievement contribution
        achievement_count = len(metrics.development.achievements)
        score += min(achievement_count * 2, 20)  # Max 20 points from achievements

        # Determine tier based on score
        if score >= 80:
            return "legendary"
        elif score >= 60:
            return "epic"
        elif score >= 40:
            return "rare"
        elif score >= 20:
            return "uncommon"
        else:
            return "common"

    def tier_index(self, tier: str) -> int:
        """Get numeric index for tier (for comparisons)."""
        try:
            return self.TIERS.index(tier)
        except ValueError:
            return 0

    def is_higher_tier(self, tier1: str, tier2: str) -> bool:
        """Check if tier1 is higher than tier2."""
        return self.tier_index(tier1) > self.tier_index(tier2)


class AchievementSystem:
    """System for tracking and awarding achievements.

    Achievement Categories:
        - activity: Based on activity counts and types
        - streak: Based on consecutive activity
        - quality: Based on quality scores
        - platform: Platform-specific achievements
        - milestone: Major milestones
        - special: Special/rare achievements
    """

    def __init__(self) -> None:
        """Initialize with achievement definitions."""
        self.definitions = self._create_definitions()

    def _create_definitions(self) -> list[AchievementDefinition]:
        """Create all achievement definitions."""
        return [
            # Activity achievements
            AchievementDefinition(
                badge_id="first_activity",
                name="First Steps",
                description="Complete your first activity",
                icon="👣",
                category="activity",
                rarity="common",
                check=lambda acts, metrics, _: len(acts) >= 1,
            ),
            AchievementDefinition(
                badge_id="ten_activities",
                name="Getting Started",
                description="Complete 10 activities",
                icon="🌱",
                category="activity",
                rarity="common",
                check=lambda acts, metrics, _: len(acts) >= 10,
            ),
            AchievementDefinition(
                badge_id="fifty_activities",
                name="Building Momentum",
                description="Complete 50 activities",
                icon="🚀",
                category="activity",
                rarity="uncommon",
                check=lambda acts, metrics, _: len(acts) >= 50,
            ),
            AchievementDefinition(
                badge_id="hundred_activities",
                name="Century",
                description="Complete 100 activities",
                icon="💯",
                category="activity",
                rarity="rare",
                check=lambda acts, metrics, _: len(acts) >= 100,
            ),
            AchievementDefinition(
                badge_id="five_hundred_activities",
                name="Prolific",
                description="Complete 500 activities",
                icon="⭐",
                category="activity",
                rarity="epic",
                check=lambda acts, metrics, _: len(acts) >= 500,
            ),
            # Creator achievements
            AchievementDefinition(
                badge_id="first_creation",
                name="Creator",
                description="Create your first piece of content",
                icon="✍️",
                category="activity",
                rarity="common",
                check=lambda acts, _, __: any(a.activity_type == "create" for a in acts),
            ),
            AchievementDefinition(
                badge_id="quality_creator",
                name="Quality Matters",
                description="Achieve a quality score above 0.80",
                icon="🎯",
                category="quality",
                rarity="rare",
                check=lambda _, metrics, __: metrics.creator is not None
                and metrics.creator.quality_score >= 0.80,
            ),
            AchievementDefinition(
                badge_id="consistent_creator",
                name="Consistency King",
                description="Maintain a consistency score above 0.70",
                icon="📅",
                category="quality",
                rarity="rare",
                check=lambda _, metrics, __: metrics.creator is not None
                and metrics.creator.consistency_score >= 0.70,
            ),
            # Streak achievements
            AchievementDefinition(
                badge_id="week_streak",
                name="Week Warrior",
                description="Maintain a 7-day activity streak",
                icon="🔥",
                category="streak",
                rarity="uncommon",
                check=lambda _, metrics, __: metrics.development.streak_longest >= 7,
            ),
            AchievementDefinition(
                badge_id="month_streak",
                name="Monthly Master",
                description="Maintain a 30-day activity streak",
                icon="🌟",
                category="streak",
                rarity="rare",
                check=lambda _, metrics, __: metrics.development.streak_longest >= 30,
            ),
            # Platform achievements
            AchievementDefinition(
                badge_id="multi_platform",
                name="Cross-Platform",
                description="Be active on 3 or more platforms",
                icon="🌐",
                category="platform",
                rarity="uncommon",
                check=lambda _, metrics, __: metrics.development.platforms_active >= 3,
            ),
            # Lifecycle achievements
            AchievementDefinition(
                badge_id="phase_developing",
                name="Beyond Rookie",
                description="Advance to developing phase",
                icon="📈",
                category="milestone",
                rarity="common",
                check=lambda _, __, lifecycle: lifecycle is not None
                and lifecycle.phase != "rookie",
            ),
            AchievementDefinition(
                badge_id="phase_established",
                name="Established",
                description="Reach established phase",
                icon="🏛️",
                category="milestone",
                rarity="uncommon",
                check=lambda _, __, lifecycle: lifecycle is not None
                and lifecycle.phase in ["established", "veteran", "legend"],
            ),
            AchievementDefinition(
                badge_id="phase_veteran",
                name="Veteran",
                description="Reach veteran phase",
                icon="🎖️",
                category="milestone",
                rarity="rare",
                check=lambda _, __, lifecycle: lifecycle is not None
                and lifecycle.phase in ["veteran", "legend"],
            ),
            AchievementDefinition(
                badge_id="phase_legend",
                name="Legend",
                description="Reach legendary status",
                icon="👑",
                category="milestone",
                rarity="legendary",
                check=lambda _, __, lifecycle: lifecycle is not None
                and lifecycle.phase == "legend",
            ),
            # Game achievements
            AchievementDefinition(
                badge_id="game_specialist",
                name="Specialist",
                description="Achieve specialist status in one game (>0.60)",
                icon="🎯",
                category="special",
                rarity="rare",
                check=lambda _, metrics, __: metrics.creator is not None
                and metrics.creator.game_signature.is_specialist,
            ),
            AchievementDefinition(
                badge_id="game_multi",
                name="Renaissance",
                description="Score >0.30 in 3+ games",
                icon="🎨",
                category="special",
                rarity="rare",
                check=lambda _, metrics, __: metrics.creator is not None
                and metrics.creator.game_signature.is_multi_game,
            ),
        ]

    def compute(
        self,
        activities: list["Activity"],
        metrics: "ProfileMetrics",
        lifecycle: Optional["LifecycleState"],
    ) -> list[Badge]:
        """Compute all earned badges.

        Args:
            activities: All user activities
            metrics: Computed profile metrics
            lifecycle: Current lifecycle state

        Returns:
            List of earned Badge objects
        """
        earned_badges = []

        for definition in self.definitions:
            try:
                if definition.check(activities, metrics, lifecycle):
                    badge = Badge(
                        badge_id=definition.badge_id,
                        name=definition.name,
                        description=definition.description,
                        icon=definition.icon,
                        category=definition.category,
                        earned_at=datetime.now(),  # In real impl, track when actually earned
                        rarity=definition.rarity,
                    )
                    earned_badges.append(badge)
            except Exception:
                # Skip badges that fail to compute
                continue

        return earned_badges

    def get_definition(self, badge_id: str) -> Optional[AchievementDefinition]:
        """Get achievement definition by ID."""
        for definition in self.definitions:
            if definition.badge_id == badge_id:
                return definition
        return None

    def get_by_category(self, category: str) -> list[AchievementDefinition]:
        """Get all achievements in a category."""
        return [d for d in self.definitions if d.category == category]

    def get_by_rarity(self, rarity: str) -> list[AchievementDefinition]:
        """Get all achievements of a specific rarity."""
        return [d for d in self.definitions if d.rarity == rarity]
