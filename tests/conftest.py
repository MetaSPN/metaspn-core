"""Pytest configuration and fixtures for MetaSPN tests."""

import json
import shutil
import tempfile
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from metaspn.core.card import CardData
from metaspn.core.level import Badge
from metaspn.core.metrics import (
    ConsumerMetrics,
    CreatorMetrics,
    DevelopmentMetrics,
    GameSignature,
    Trajectory,
)
from metaspn.core.profile import Activity, PlatformPresence, ProfileMetrics, UserProfile
from metaspn.core.state_machine import LifecycleState
from metaspn.repo import init_repo


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_repo(temp_dir: Path) -> Path:
    """Create a sample MetaSPN repository with test data."""
    repo_path = temp_dir / "test_repo"

    # Initialize repo
    init_repo(
        str(repo_path),
        {
            "user_id": "test_user",
            "name": "Test User",
            "handle": "@test_user",
        },
    )

    # Add sample activities
    activities = [
        {
            "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
            "platform": "podcast",
            "activity_type": "create",
            "title": "Episode 1: Getting Started",
            "content": "Introduction to the show " * 100,
            "duration_seconds": 3600,
        },
        {
            "timestamp": (datetime.now() - timedelta(days=20)).isoformat(),
            "platform": "podcast",
            "activity_type": "create",
            "title": "Episode 2: Deep Dive",
            "content": "A deep exploration " * 150,
            "duration_seconds": 5400,
        },
        {
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
            "platform": "blog",
            "activity_type": "create",
            "title": "How I Built My Framework",
            "content": "In this post I'll explain the framework " * 200,
        },
        {
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
            "platform": "twitter",
            "activity_type": "create",
            "title": None,
            "content": "Just shipped a new feature! Check it out at example.com",
        },
        {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "platform": "youtube",
            "activity_type": "consume",
            "title": "Learning React",
            "duration_seconds": 1800,
        },
    ]

    for i, activity_data in enumerate(activities):
        platform = activity_data["platform"]
        platform_dir = repo_path / "sources" / platform
        platform_dir.mkdir(parents=True, exist_ok=True)

        filename = f"activity_{i:03d}.json"
        with open(platform_dir / filename, "w") as f:
            json.dump(activity_data, f)

    return repo_path


@pytest.fixture
def empty_repo(temp_dir: Path) -> Path:
    """Create an empty MetaSPN repository."""
    repo_path = temp_dir / "empty_repo"

    init_repo(
        str(repo_path),
        {
            "user_id": "empty_user",
            "name": "Empty User",
            "handle": "@empty_user",
        },
    )

    return repo_path


@pytest.fixture
def sample_activity() -> Activity:
    """Create a sample Activity object."""
    return Activity(
        timestamp=datetime.now(),
        platform="podcast",
        activity_type="create",
        title="Sample Episode",
        content="This is a sample podcast episode " * 50,
        duration_seconds=3600,
    )


@pytest.fixture
def sample_activities() -> list[Activity]:
    """Create a list of sample Activity objects."""
    base_time = datetime.now()
    return [
        Activity(
            timestamp=base_time - timedelta(days=30),
            platform="podcast",
            activity_type="create",
            title="Episode 1",
            content="Content " * 100,
            duration_seconds=3600,
        ),
        Activity(
            timestamp=base_time - timedelta(days=25),
            platform="podcast",
            activity_type="create",
            title="Episode 2",
            content="More content " * 120,
            duration_seconds=4200,
        ),
        Activity(
            timestamp=base_time - timedelta(days=20),
            platform="blog",
            activity_type="create",
            title="Blog Post 1",
            content="Blog content " * 200,
        ),
        Activity(
            timestamp=base_time - timedelta(days=15),
            platform="twitter",
            activity_type="create",
            title="Tweet",
            content="A thought on something interesting",
        ),
        Activity(
            timestamp=base_time - timedelta(days=10),
            platform="youtube",
            activity_type="consume",
            title="Tutorial Video",
            duration_seconds=1800,
        ),
    ]


@pytest.fixture
def sample_game_signature() -> GameSignature:
    """Create a sample GameSignature."""
    return GameSignature(
        G1=0.2,
        G2=0.4,
        G3=0.6,
        G4=0.3,
        G5=0.5,
        G6=0.1,
    )


@pytest.fixture
def sample_creator_metrics(sample_game_signature: GameSignature) -> CreatorMetrics:
    """Create sample CreatorMetrics."""
    return CreatorMetrics(
        quality_score=0.75,
        game_alignment=0.65,
        impact_factor=0.55,
        calibration=0.70,
        game_signature=sample_game_signature,
        trajectory=Trajectory(direction="ascending", slope=0.1),
        total_outputs=50,
        consistency_score=0.80,
    )


@pytest.fixture
def sample_consumer_metrics() -> ConsumerMetrics:
    """Create sample ConsumerMetrics."""
    return ConsumerMetrics(
        execution_rate=0.6,
        integration_skill=0.5,
        discernment=0.7,
        development=0.55,
        consumption_games=GameSignature(G1=0.1, G2=0.3, G3=0.4, G4=0.1, G5=0.05, G6=0.05),
        total_consumed=100,
        hours_consumed=150.0,
    )


@pytest.fixture
def sample_profile_metrics(
    sample_creator_metrics: CreatorMetrics,
    sample_consumer_metrics: ConsumerMetrics,
) -> ProfileMetrics:
    """Create sample ProfileMetrics."""
    return ProfileMetrics(
        creator=sample_creator_metrics,
        consumer=sample_consumer_metrics,
        development=DevelopmentMetrics(
            total_activities=150,
            active_days=60,
            streak_current=5,
            streak_longest=14,
            first_activity=datetime.now() - timedelta(days=90),
            last_activity=datetime.now(),
            platforms_active=3,
            achievements=["first_activity", "ten_activities"],
        ),
    )


@pytest.fixture
def sample_lifecycle_state() -> LifecycleState:
    """Create a sample LifecycleState."""
    return LifecycleState(
        phase="developing",
        phase_progress=0.6,
        days_in_phase=45,
        phase_entered=datetime.now() - timedelta(days=45),
        activities_in_phase=25,
        next_phase="established",
        activities_to_next=25,
    )


@pytest.fixture
def sample_badges() -> list[Badge]:
    """Create sample badges."""
    return [
        Badge(
            badge_id="first_activity",
            name="First Steps",
            description="Complete your first activity",
            icon="👣",
            category="activity",
            earned_at=datetime.now() - timedelta(days=30),
            rarity="common",
        ),
        Badge(
            badge_id="ten_activities",
            name="Getting Started",
            description="Complete 10 activities",
            icon="🌱",
            category="activity",
            earned_at=datetime.now() - timedelta(days=20),
            rarity="common",
        ),
    ]


@pytest.fixture
def sample_card_data(sample_badges: list[Badge]) -> CardData:
    """Create sample CardData."""
    return CardData(
        level=5,
        xp=1200,
        xp_to_next=300,
        rarity="uncommon",
        badges=sample_badges,
        card_number="CR-12345",
        edition="genesis",
    )


@pytest.fixture
def sample_platform_presences() -> list[PlatformPresence]:
    """Create sample PlatformPresences."""
    return [
        PlatformPresence(
            platform="podcast",
            role="creator",
            joined_at=datetime.now() - timedelta(days=90),
            last_active=datetime.now() - timedelta(days=5),
            activity_count=20,
            create_count=20,
            consume_count=0,
        ),
        PlatformPresence(
            platform="blog",
            role="creator",
            joined_at=datetime.now() - timedelta(days=60),
            last_active=datetime.now() - timedelta(days=10),
            activity_count=10,
            create_count=10,
            consume_count=0,
        ),
        PlatformPresence(
            platform="youtube",
            role="consumer",
            joined_at=datetime.now() - timedelta(days=30),
            last_active=datetime.now() - timedelta(days=2),
            activity_count=15,
            create_count=0,
            consume_count=15,
        ),
    ]


@pytest.fixture
def sample_user_profile(
    sample_platform_presences: list[PlatformPresence],
    sample_lifecycle_state: LifecycleState,
    sample_profile_metrics: ProfileMetrics,
    sample_card_data: CardData,
) -> UserProfile:
    """Create a complete sample UserProfile."""
    return UserProfile(
        user_id="test_user",
        handle="@test_user",
        name="Test User",
        avatar_url="https://example.com/avatar.png",
        repo_commit="abc123",
        last_computed=datetime.now(),
        platforms=sample_platform_presences,
        lifecycle=sample_lifecycle_state,
        metrics=sample_profile_metrics,
        cards=sample_card_data,
    )
