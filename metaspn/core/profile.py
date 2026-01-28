"""Profile data structures and computation for MetaSPN."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from metaspn.core.metrics import (
    ConsumerMetrics,
    CreatorMetrics,
    DevelopmentMetrics,
    GameSignature,
)

if TYPE_CHECKING:
    from metaspn.analyzers.games import GameAnalyzer
    from metaspn.analyzers.quality import QualityAnalyzer
    from metaspn.core.card import CardData
    from metaspn.core.state_machine import LifecycleState
    from metaspn.repo.enhancement_store import EnhancedActivity, EnhancementStore


@dataclass
class Activity:
    """Base activity class for all platform events.

    Activities represent any action a user takes on a platform,
    whether creating content or consuming it.
    """

    timestamp: datetime
    platform: str
    activity_type: Literal["create", "consume"]

    # Content metadata
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    duration_seconds: Optional[int] = None

    # Computed fields (cached after first computation)
    quality_score: Optional[float] = None
    game_signature: Optional[dict] = None

    # Raw data (platform-specific)
    raw_data: dict = field(default_factory=dict)

    # Unique identifier
    activity_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Generate activity ID if not provided."""
        if self.activity_id is None:
            # Generate deterministic ID from timestamp and platform
            ts_str = self.timestamp.isoformat()
            self.activity_id = f"{self.platform}_{ts_str}_{hash(self.title or '')}".replace(
                ":", "-"
            )

    @property
    def is_creation(self) -> bool:
        """True if this is a content creation activity."""
        return self.activity_type == "create"

    @property
    def is_consumption(self) -> bool:
        """True if this is a content consumption activity."""
        return self.activity_type == "consume"

    @property
    def duration_minutes(self) -> Optional[float]:
        """Return duration in minutes."""
        if self.duration_seconds is None:
            return None
        return self.duration_seconds / 60.0

    @property
    def duration_hours(self) -> Optional[float]:
        """Return duration in hours."""
        if self.duration_seconds is None:
            return None
        return self.duration_seconds / 3600.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform,
            "activity_type": self.activity_type,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "duration_seconds": self.duration_seconds,
            "quality_score": self.quality_score,
            "game_signature": self.game_signature,
            "raw_data": self.raw_data,
            "activity_id": self.activity_id,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        """Deserialize from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            platform=data["platform"],
            activity_type=data["activity_type"],
            title=data.get("title"),
            content=data.get("content"),
            url=data.get("url"),
            duration_seconds=data.get("duration_seconds"),
            quality_score=data.get("quality_score"),
            game_signature=data.get("game_signature"),
            raw_data=data.get("raw_data", {}),
            activity_id=data.get("activity_id"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Activity":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PlatformPresence:
    """User's presence on a specific platform."""

    platform: str
    role: Literal["creator", "consumer", "hybrid"]
    joined_at: datetime
    last_active: datetime
    activity_count: int = 0
    create_count: int = 0
    consume_count: int = 0

    @property
    def is_rookie(self) -> bool:
        """True if user has been on platform for less than 30 days."""
        now = datetime.now()
        if self.joined_at.tzinfo is not None:
            from datetime import timezone

            now = datetime.now(timezone.utc)
        days_on_platform = (now - self.joined_at).days
        return days_on_platform < 30

    @property
    def is_active(self) -> bool:
        """True if user has been active in the last 30 days."""
        now = datetime.now()
        if self.last_active.tzinfo is not None:
            from datetime import timezone

            now = datetime.now(timezone.utc)
        days_since_active = (now - self.last_active).days
        return days_since_active < 30

    @property
    def is_dormant(self) -> bool:
        """True if user hasn't been active in 90+ days."""
        now = datetime.now()
        if self.last_active.tzinfo is not None:
            from datetime import timezone

            now = datetime.now(timezone.utc)
        days_since_active = (now - self.last_active).days
        return days_since_active >= 90

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "platform": self.platform,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "activity_count": self.activity_count,
            "create_count": self.create_count,
            "consume_count": self.consume_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlatformPresence":
        """Deserialize from dictionary."""
        return cls(
            platform=data["platform"],
            role=data["role"],
            joined_at=datetime.fromisoformat(data["joined_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            activity_count=data.get("activity_count", 0),
            create_count=data.get("create_count", 0),
            consume_count=data.get("consume_count", 0),
        )


@dataclass
class ProfileMetrics:
    """All computed metrics for a user profile."""

    creator: Optional[CreatorMetrics] = None
    consumer: Optional[ConsumerMetrics] = None
    development: DevelopmentMetrics = field(default_factory=DevelopmentMetrics)

    @property
    def is_creator(self) -> bool:
        """True if user has creator metrics."""
        return self.creator is not None and self.creator.total_outputs > 0

    @property
    def is_consumer(self) -> bool:
        """True if user has consumer metrics."""
        return self.consumer is not None and self.consumer.total_consumed > 0

    @property
    def is_hybrid(self) -> bool:
        """True if user is both creator and consumer."""
        return self.is_creator and self.is_consumer

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "creator": self.creator.to_dict() if self.creator else None,
            "consumer": self.consumer.to_dict() if self.consumer else None,
            "development": self.development.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileMetrics":
        """Deserialize from dictionary."""
        return cls(
            creator=CreatorMetrics.from_dict(data["creator"]) if data.get("creator") else None,
            consumer=ConsumerMetrics.from_dict(data["consumer"]) if data.get("consumer") else None,
            development=DevelopmentMetrics.from_dict(data.get("development", {})),
        )


@dataclass
class UserProfile:
    """Complete user profile computed from repository.

    This is the main data structure returned by compute_profile().
    It contains all computed metrics, platform presences, lifecycle state,
    and card data.
    """

    # Identity
    user_id: str
    handle: str
    name: str
    avatar_url: Optional[str] = None

    # State
    repo_commit: str = ""
    last_computed: datetime = field(default_factory=datetime.now)

    # Computed data
    platforms: list[PlatformPresence] = field(default_factory=list)
    lifecycle: Optional["LifecycleState"] = None
    metrics: ProfileMetrics = field(default_factory=ProfileMetrics)
    cards: Optional["CardData"] = None

    @property
    def platform_names(self) -> list[str]:
        """Return list of platform names user is active on."""
        return [p.platform for p in self.platforms]

    @property
    def is_multi_platform(self) -> bool:
        """True if user is active on multiple platforms."""
        return len(self.platforms) > 1

    @property
    def primary_platform(self) -> Optional[str]:
        """Return platform with most activity."""
        if not self.platforms:
            return None
        return max(self.platforms, key=lambda p: p.activity_count).platform

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        # Import here to avoid circular imports

        return {
            "user_id": self.user_id,
            "handle": self.handle,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "repo_commit": self.repo_commit,
            "last_computed": self.last_computed.isoformat(),
            "platforms": [p.to_dict() for p in self.platforms],
            "lifecycle": self.lifecycle.to_dict() if self.lifecycle else None,
            "metrics": self.metrics.to_dict(),
            "cards": self.cards.to_dict() if self.cards else None,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Deserialize from dictionary."""
        from metaspn.core.card import CardData
        from metaspn.core.state_machine import LifecycleState

        return cls(
            user_id=data["user_id"],
            handle=data["handle"],
            name=data["name"],
            avatar_url=data.get("avatar_url"),
            repo_commit=data.get("repo_commit", ""),
            last_computed=(
                datetime.fromisoformat(data["last_computed"])
                if data.get("last_computed")
                else datetime.now()
            ),
            platforms=[PlatformPresence.from_dict(p) for p in data.get("platforms", [])],
            lifecycle=(
                LifecycleState.from_dict(data["lifecycle"]) if data.get("lifecycle") else None
            ),
            metrics=ProfileMetrics.from_dict(data.get("metrics", {})),
            cards=CardData.from_dict(data["cards"]) if data.get("cards") else None,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "UserProfile":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


def compute_profile(
    repo_path: str,
    force_recompute: bool = False,
    cache_results: bool = True,
    use_enhancement_store: bool = True,
    compute_enhancements: bool = True,
) -> UserProfile:
    """Compute complete user profile from repository.

    This is the main entry point for profile computation. It reads all
    activity data from the repository, computes metrics, determines
    lifecycle phase, calculates level and rarity, and generates card data.

    The enhancement layer architecture separates raw source data from
    computed enhancements (quality scores, game signatures). When
    use_enhancement_store=True, enhancements are loaded from/saved to
    artifacts/enhancements/ instead of being embedded in activities.

    Args:
        repo_path: Path to MetaSPN content repository
        force_recompute: If True, ignore cached results and recompute
        cache_results: If True, cache computed results in reports/
        use_enhancement_store: If True, use enhancement layer for scores/signatures
        compute_enhancements: If True and use_enhancement_store is True, compute
            and save missing enhancements

    Returns:
        Complete UserProfile object with all computed metrics

    Raises:
        ValueError: If repo_path is invalid or repo is malformed
        FileNotFoundError: If repo doesn't exist

    Example:
        >>> profile = compute_profile("./my-content")
        >>> print(f"Level: {profile.cards.level}")
        Level: 8
    """
    from metaspn.analyzers.games import GameAnalyzer
    from metaspn.analyzers.impact import ImpactAnalyzer
    from metaspn.analyzers.quality import QualityAnalyzer
    from metaspn.analyzers.trajectory import TrajectoryAnalyzer
    from metaspn.core.card import CardData
    from metaspn.core.level import AchievementSystem, LevelCalculator, RarityCalculator
    from metaspn.core.state_machine import LifecycleStateMachine
    from metaspn.repo.enhancement_store import EnhancementStore
    from metaspn.repo.reader import load_activities, load_minimal_state, try_load_cached_profile
    from metaspn.repo.structure import validate_repo
    from metaspn.repo.writer import cache_profile as write_cache

    # 1. Validate repo structure
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid MetaSPN repository at {repo_path}")

    # 2. Load minimal state
    state = load_minimal_state(repo_path)

    # 3. Check cache
    if not force_recompute:
        cached = try_load_cached_profile(repo_path, state.repo_commit)
        if cached:
            return cached

    # 4. Load all activities
    activities = load_activities(repo_path)

    # 5. Detect platforms and compute platform presences
    platforms = _compute_platform_presences(activities)

    # 6. Initialize analyzers
    quality_analyzer = QualityAnalyzer()
    game_analyzer = GameAnalyzer()
    trajectory_analyzer = TrajectoryAnalyzer()
    impact_analyzer = ImpactAnalyzer()

    # 6a. Handle enhancement store
    enhancement_store = None
    enhanced_activities = None
    if use_enhancement_store:
        enhancement_store = EnhancementStore(repo_path)

        # Compute and store missing enhancements if requested
        if compute_enhancements:
            _compute_and_store_enhancements(
                activities,
                quality_analyzer,
                game_analyzer,
                enhancement_store,
            )

        # Load enhanced activities (activities joined with their enhancements)
        enhanced_activities = enhancement_store.get_all_enhanced(
            activities, load_quality=True, load_games=True, load_embeddings=False
        )

    # Split activities by type
    create_activities = [a for a in activities if a.activity_type == "create"]
    consume_activities = [a for a in activities if a.activity_type == "consume"]

    # For enhanced activities, also split them
    enhanced_create = None
    enhanced_consume = None
    if enhanced_activities:
        enhanced_create = [ea for ea in enhanced_activities if ea.activity_type == "create"]
        enhanced_consume = [ea for ea in enhanced_activities if ea.activity_type == "consume"]

    # Compute creator metrics if there are creation activities
    creator_metrics = None
    if create_activities:
        # Use enhanced activities for aggregate game signature if available
        if enhanced_create:
            quality_score = _compute_avg_quality_from_enhanced(enhanced_create)
            game_signature = _compute_aggregate_game_from_enhanced(enhanced_create)
        else:
            quality_score = quality_analyzer.compute(create_activities)
            game_signature = game_analyzer.compute(create_activities)

        trajectory = trajectory_analyzer.compute(create_activities)
        impact_factor = impact_analyzer.compute(create_activities)

        # For calibration, use enhanced activities if available
        calibration_activities = enhanced_create if enhanced_create else create_activities

        creator_metrics = CreatorMetrics(
            quality_score=quality_score,
            game_alignment=_compute_game_alignment(game_signature),
            impact_factor=impact_factor,
            calibration=_compute_calibration_from_enhanced(calibration_activities),
            game_signature=game_signature,
            trajectory=trajectory,
            total_outputs=len(create_activities),
            consistency_score=_compute_consistency(create_activities),
        )

    # Compute consumer metrics if there are consumption activities
    consumer_metrics = None
    if consume_activities:
        if enhanced_consume:
            consumption_games = _compute_aggregate_game_from_enhanced(enhanced_consume)
        else:
            consumption_games = game_analyzer.compute(consume_activities)
        total_hours = sum((a.duration_seconds or 0) for a in consume_activities) / 3600.0

        # For discernment, use enhanced activities if available
        discernment_activities = enhanced_consume if enhanced_consume else consume_activities

        consumer_metrics = ConsumerMetrics(
            execution_rate=_compute_execution_rate(consume_activities),
            integration_skill=_compute_integration_skill(consume_activities),
            discernment=_compute_discernment_from_enhanced(discernment_activities),
            development=_compute_development_score(consume_activities),
            consumption_games=consumption_games,
            total_consumed=len(consume_activities),
            hours_consumed=total_hours,
        )

    # Compute development metrics
    development_metrics = _compute_development_metrics(activities)

    metrics = ProfileMetrics(
        creator=creator_metrics,
        consumer=consumer_metrics,
        development=development_metrics,
    )

    # 7. Compute lifecycle state
    lifecycle_sm = LifecycleStateMachine()
    lifecycle = lifecycle_sm.compute(activities, platforms, metrics)

    # 8. Compute level/XP
    level_calc = LevelCalculator()
    xp = level_calc.compute_xp(activities, metrics)
    level = level_calc.compute_level(xp)
    xp_to_next = level_calc.xp_for_level(level + 1) - xp

    # 9. Compute rarity
    rarity_calc = RarityCalculator()
    rarity = rarity_calc.compute(metrics, lifecycle)

    # 10. Compute achievements
    achievement_sys = AchievementSystem()
    badges = achievement_sys.compute(activities, metrics, lifecycle)

    # Update development metrics with achievement IDs
    development_metrics.achievements = [b.badge_id for b in badges]

    # 11. Build profile
    profile = UserProfile(
        user_id=state.user_id,
        handle=state.handle,
        name=state.name,
        avatar_url=state.avatar_url,
        repo_commit=state.repo_commit,
        last_computed=datetime.now(),
        platforms=platforms,
        lifecycle=lifecycle,
        metrics=metrics,
        cards=CardData(
            level=level,
            xp=xp,
            xp_to_next=xp_to_next,
            rarity=rarity,
            badges=badges,
            card_number=None,  # Generated on card creation
            edition="genesis",
        ),
    )

    # 12. Cache results
    if cache_results:
        write_cache(repo_path, profile)

    return profile


def _compute_platform_presences(activities: list[Activity]) -> list[PlatformPresence]:
    """Compute platform presences from activities."""
    from collections import defaultdict

    platform_data: dict = defaultdict(
        lambda: {
            "create": [],
            "consume": [],
            "first": None,
            "last": None,
        }
    )

    for activity in activities:
        pdata = platform_data[activity.platform]

        if activity.activity_type == "create":
            pdata["create"].append(activity)
        else:
            pdata["consume"].append(activity)

        if pdata["first"] is None or activity.timestamp < pdata["first"]:
            pdata["first"] = activity.timestamp
        if pdata["last"] is None or activity.timestamp > pdata["last"]:
            pdata["last"] = activity.timestamp

    presences = []
    for platform, data in platform_data.items():
        create_count = len(data["create"])
        consume_count = len(data["consume"])
        total = create_count + consume_count

        # Determine role
        if create_count > 0 and consume_count > 0:
            role = "hybrid"
        elif create_count > 0:
            role = "creator"
        else:
            role = "consumer"

        presences.append(
            PlatformPresence(
                platform=platform,
                role=role,
                joined_at=data["first"],
                last_active=data["last"],
                activity_count=total,
                create_count=create_count,
                consume_count=consume_count,
            )
        )

    return presences


def _compute_game_alignment(signature: GameSignature) -> float:
    """Compute game alignment score based on signature clarity."""
    scores = [signature.G1, signature.G2, signature.G3, signature.G4, signature.G5, signature.G6]
    if not any(scores):
        return 0.0

    max_score = max(scores)
    avg_score = sum(scores) / len(scores)

    # Higher alignment = clearer primary game
    return min(1.0, max_score * 0.5 + (max_score - avg_score) * 0.5)


def _compute_calibration(activities: list[Activity]) -> float:
    """Compute calibration score based on quality consistency."""
    quality_scores = [a.quality_score for a in activities if a.quality_score is not None]
    if not quality_scores:
        return 0.5

    if len(quality_scores) == 1:
        return quality_scores[0]

    # Low variance = high calibration
    mean = sum(quality_scores) / len(quality_scores)
    variance = sum((s - mean) ** 2 for s in quality_scores) / len(quality_scores)

    # Convert variance to calibration score (lower variance = higher calibration)
    return max(0.0, min(1.0, 1.0 - variance * 2))


def _compute_consistency(activities: list[Activity]) -> float:
    """Compute consistency score based on activity regularity."""
    if len(activities) < 2:
        return 0.0

    # Sort by timestamp
    sorted_activities = sorted(activities, key=lambda a: a.timestamp)

    # Calculate gaps between activities
    gaps = []
    for i in range(1, len(sorted_activities)):
        gap = (sorted_activities[i].timestamp - sorted_activities[i - 1].timestamp).days
        gaps.append(gap)

    if not gaps:
        return 0.0

    # Lower average gap and lower variance = higher consistency
    avg_gap = sum(gaps) / len(gaps)

    # Normalize: 1 day gap = 1.0, 30 day gap = 0.0
    return max(0.0, min(1.0, 1.0 - (avg_gap / 30.0)))


def _compute_execution_rate(activities: list[Activity]) -> float:
    """Compute execution rate for consumption activities."""
    # Placeholder: in real implementation, this would analyze
    # whether consumed content was acted upon
    if not activities:
        return 0.0
    return min(1.0, len(activities) / 100.0)


def _compute_integration_skill(activities: list[Activity]) -> float:
    """Compute integration skill based on content variety."""
    if not activities:
        return 0.0

    # More diverse content consumption = higher integration skill
    platforms = set(a.platform for a in activities)
    return min(1.0, len(platforms) / 4.0)


def _compute_discernment(activities: list[Activity]) -> float:
    """Compute discernment based on quality of consumed content."""
    quality_scores = [a.quality_score for a in activities if a.quality_score is not None]
    if not quality_scores:
        return 0.5

    return sum(quality_scores) / len(quality_scores)


def _compute_development_score(activities: list[Activity]) -> float:
    """Compute development score based on consumption growth."""
    if len(activities) < 5:
        return 0.3

    # Simple growth indicator
    return min(1.0, len(activities) / 200.0 + 0.3)


def _compute_development_metrics(activities: list[Activity]) -> DevelopmentMetrics:
    """Compute development metrics from all activities."""
    if not activities:
        return DevelopmentMetrics()

    sorted_activities = sorted(activities, key=lambda a: a.timestamp)

    # Calculate active days
    active_dates = set(a.timestamp.date() for a in activities)

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    if active_dates:
        sorted_dates = sorted(active_dates)
        streak = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1
        longest_streak = max(longest_streak, streak)

        # Check if streak is current
        from datetime import date

        if sorted_dates[-1] == date.today() or (date.today() - sorted_dates[-1]).days == 1:
            current_streak = streak

    # Count platforms
    platforms = set(a.platform for a in activities)

    return DevelopmentMetrics(
        total_activities=len(activities),
        active_days=len(active_dates),
        streak_current=current_streak,
        streak_longest=longest_streak,
        first_activity=sorted_activities[0].timestamp,
        last_activity=sorted_activities[-1].timestamp,
        platforms_active=len(platforms),
        achievements=[],  # Filled in later
    )


# =============================================================================
# Enhancement Layer Helpers
# =============================================================================


def _compute_and_store_enhancements(
    activities: list[Activity],
    quality_analyzer: "QualityAnalyzer",
    game_analyzer: "GameAnalyzer",
    store: "EnhancementStore",
) -> None:
    """Compute and store missing enhancements for activities.

    Only computes enhancements for activities that don't already have
    them stored, allowing for incremental processing.
    """

    # Find activities missing quality scores
    missing_quality = store.get_unprocessed_activities(activities, "quality_scores")
    if missing_quality:
        quality_enhancements = quality_analyzer.compute_enhancements(missing_quality)
        if quality_enhancements:
            store.save_quality_scores(quality_enhancements, append=True)

    # Find activities missing game signatures
    missing_games = store.get_unprocessed_activities(activities, "game_signatures")
    if missing_games:
        game_enhancements = game_analyzer.compute_enhancements(missing_games)
        if game_enhancements:
            store.save_game_signatures(game_enhancements, append=True)


def _compute_avg_quality_from_enhanced(
    enhanced_activities: list["EnhancedActivity"],
) -> float:
    """Compute average quality score from enhanced activities."""
    scores = [ea.quality_score for ea in enhanced_activities if ea.quality_score is not None]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _compute_aggregate_game_from_enhanced(
    enhanced_activities: list["EnhancedActivity"],
) -> GameSignature:
    """Compute aggregate game signature from enhanced activities."""
    signatures = [ea.game_signature for ea in enhanced_activities if ea.game_signature is not None]
    if not signatures:
        return GameSignature()

    # Average the game scores
    totals = {"G1": 0.0, "G2": 0.0, "G3": 0.0, "G4": 0.0, "G5": 0.0, "G6": 0.0}
    for sig in signatures:
        totals["G1"] += sig.G1
        totals["G2"] += sig.G2
        totals["G3"] += sig.G3
        totals["G4"] += sig.G4
        totals["G5"] += sig.G5
        totals["G6"] += sig.G6

    n = len(signatures)
    return GameSignature(
        G1=totals["G1"] / n,
        G2=totals["G2"] / n,
        G3=totals["G3"] / n,
        G4=totals["G4"] / n,
        G5=totals["G5"] / n,
        G6=totals["G6"] / n,
    )


def _compute_calibration_from_enhanced(activities) -> float:
    """Compute calibration score from activities (enhanced or regular).

    Works with both EnhancedActivity and Activity objects.
    """
    quality_scores = []
    for a in activities:
        # Handle both EnhancedActivity and Activity
        score = getattr(a, "quality_score", None)
        if score is not None:
            quality_scores.append(score)

    if not quality_scores:
        return 0.5

    if len(quality_scores) == 1:
        return quality_scores[0]

    # Low variance = high calibration
    mean = sum(quality_scores) / len(quality_scores)
    variance = sum((s - mean) ** 2 for s in quality_scores) / len(quality_scores)

    # Convert variance to calibration score (lower variance = higher calibration)
    return max(0.0, min(1.0, 1.0 - variance * 2))


def _compute_discernment_from_enhanced(activities) -> float:
    """Compute discernment from activities (enhanced or regular).

    Works with both EnhancedActivity and Activity objects.
    """
    quality_scores = []
    for a in activities:
        score = getattr(a, "quality_score", None)
        if score is not None:
            quality_scores.append(score)

    if not quality_scores:
        return 0.5

    return sum(quality_scores) / len(quality_scores)


def compute_and_store_enhancements(
    repo_path: str,
    force_recompute: bool = False,
) -> dict:
    """Compute and store all enhancements for a repository.

    This is a standalone function for computing and storing enhancements
    without computing the full profile. Useful for batch processing or
    pre-computing enhancements.

    Args:
        repo_path: Path to MetaSPN repository
        force_recompute: If True, clear existing enhancements and recompute all

    Returns:
        Dictionary with counts of computed enhancements

    Example:
        >>> result = compute_and_store_enhancements("./my-content")
        >>> print(f"Computed {result['quality_scores']} quality scores")
    """
    from metaspn.analyzers.games import GameAnalyzer
    from metaspn.analyzers.quality import QualityAnalyzer
    from metaspn.repo.enhancement_store import EnhancementStore
    from metaspn.repo.reader import load_activities
    from metaspn.repo.structure import validate_repo

    if not validate_repo(repo_path):
        raise ValueError(f"Invalid MetaSPN repository at {repo_path}")

    activities = load_activities(repo_path)
    store = EnhancementStore(repo_path)

    if force_recompute:
        store.clear_enhancements()

    quality_analyzer = QualityAnalyzer()
    game_analyzer = GameAnalyzer()

    # Compute quality scores
    missing_quality = store.get_unprocessed_activities(activities, "quality_scores")
    quality_count = 0
    if missing_quality:
        quality_enhancements = quality_analyzer.compute_enhancements(missing_quality)
        if quality_enhancements:
            store.save_quality_scores(quality_enhancements, append=not force_recompute)
            quality_count = len(quality_enhancements)

    # Compute game signatures
    missing_games = store.get_unprocessed_activities(activities, "game_signatures")
    game_count = 0
    if missing_games:
        game_enhancements = game_analyzer.compute_enhancements(missing_games)
        if game_enhancements:
            store.save_game_signatures(game_enhancements, append=not force_recompute)
            game_count = len(game_enhancements)

    return {
        "quality_scores": quality_count,
        "game_signatures": game_count,
        "total_activities": len(activities),
    }
