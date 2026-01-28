"""Tests for core profile module."""

from datetime import datetime, timedelta

import pytest

from metaspn.core.profile import (
    Activity,
    PlatformPresence,
    ProfileMetrics,
    UserProfile,
    compute_profile,
)


class TestActivity:
    """Tests for Activity class."""

    def test_create_activity(self):
        """Test creating a basic activity."""
        activity = Activity(
            timestamp=datetime.now(),
            platform="podcast",
            activity_type="create",
            title="Test Episode",
        )

        assert activity.platform == "podcast"
        assert activity.activity_type == "create"
        assert activity.title == "Test Episode"
        assert activity.activity_id is not None

    def test_activity_is_creation(self, sample_activity: Activity):
        """Test is_creation property."""
        assert sample_activity.is_creation is True
        assert sample_activity.is_consumption is False

    def test_activity_duration_conversions(self, sample_activity: Activity):
        """Test duration conversion properties."""
        assert sample_activity.duration_minutes == 60.0
        assert sample_activity.duration_hours == 1.0

    def test_activity_serialization(self, sample_activity: Activity):
        """Test to_dict and from_dict."""
        data = sample_activity.to_dict()
        restored = Activity.from_dict(data)

        assert restored.platform == sample_activity.platform
        assert restored.activity_type == sample_activity.activity_type
        assert restored.title == sample_activity.title
        assert restored.duration_seconds == sample_activity.duration_seconds

    def test_activity_json_serialization(self, sample_activity: Activity):
        """Test JSON serialization."""
        json_str = sample_activity.to_json()
        restored = Activity.from_json(json_str)

        assert restored.platform == sample_activity.platform
        assert restored.title == sample_activity.title


class TestPlatformPresence:
    """Tests for PlatformPresence class."""

    def test_create_platform_presence(self):
        """Test creating a platform presence."""
        presence = PlatformPresence(
            platform="podcast",
            role="creator",
            joined_at=datetime.now() - timedelta(days=60),
            last_active=datetime.now(),
            activity_count=10,
        )

        assert presence.platform == "podcast"
        assert presence.role == "creator"
        assert presence.is_rookie is False  # 60 days > 30 days

    def test_is_rookie(self):
        """Test is_rookie property."""
        new_presence = PlatformPresence(
            platform="twitter",
            role="creator",
            joined_at=datetime.now() - timedelta(days=15),
            last_active=datetime.now(),
        )

        assert new_presence.is_rookie is True

    def test_is_active(self):
        """Test is_active property."""
        active = PlatformPresence(
            platform="blog",
            role="creator",
            joined_at=datetime.now() - timedelta(days=90),
            last_active=datetime.now() - timedelta(days=5),
        )

        inactive = PlatformPresence(
            platform="blog",
            role="creator",
            joined_at=datetime.now() - timedelta(days=90),
            last_active=datetime.now() - timedelta(days=60),
        )

        assert active.is_active is True
        assert inactive.is_active is False

    def test_is_dormant(self):
        """Test is_dormant property."""
        dormant = PlatformPresence(
            platform="youtube",
            role="consumer",
            joined_at=datetime.now() - timedelta(days=180),
            last_active=datetime.now() - timedelta(days=100),
        )

        assert dormant.is_dormant is True

    def test_serialization(self, sample_platform_presences):
        """Test serialization."""
        presence = sample_platform_presences[0]
        data = presence.to_dict()
        restored = PlatformPresence.from_dict(data)

        assert restored.platform == presence.platform
        assert restored.role == presence.role


class TestProfileMetrics:
    """Tests for ProfileMetrics class."""

    def test_is_creator(self, sample_profile_metrics: ProfileMetrics):
        """Test is_creator property."""
        assert sample_profile_metrics.is_creator is True

    def test_is_consumer(self, sample_profile_metrics: ProfileMetrics):
        """Test is_consumer property."""
        assert sample_profile_metrics.is_consumer is True

    def test_is_hybrid(self, sample_profile_metrics: ProfileMetrics):
        """Test is_hybrid property."""
        assert sample_profile_metrics.is_hybrid is True

    def test_serialization(self, sample_profile_metrics: ProfileMetrics):
        """Test serialization."""
        data = sample_profile_metrics.to_dict()
        restored = ProfileMetrics.from_dict(data)

        assert restored.creator.quality_score == sample_profile_metrics.creator.quality_score
        assert restored.consumer.total_consumed == sample_profile_metrics.consumer.total_consumed


class TestUserProfile:
    """Tests for UserProfile class."""

    def test_platform_names(self, sample_user_profile: UserProfile):
        """Test platform_names property."""
        names = sample_user_profile.platform_names
        assert "podcast" in names
        assert "blog" in names
        assert "youtube" in names

    def test_is_multi_platform(self, sample_user_profile: UserProfile):
        """Test is_multi_platform property."""
        assert sample_user_profile.is_multi_platform is True

    def test_primary_platform(self, sample_user_profile: UserProfile):
        """Test primary_platform property."""
        # Podcast has most activities (20)
        assert sample_user_profile.primary_platform == "podcast"

    def test_serialization(self, sample_user_profile: UserProfile):
        """Test full serialization cycle."""
        data = sample_user_profile.to_dict()
        restored = UserProfile.from_dict(data)

        assert restored.user_id == sample_user_profile.user_id
        assert restored.name == sample_user_profile.name
        assert restored.handle == sample_user_profile.handle
        assert len(restored.platforms) == len(sample_user_profile.platforms)

    def test_json_serialization(self, sample_user_profile: UserProfile):
        """Test JSON serialization."""
        json_str = sample_user_profile.to_json()
        restored = UserProfile.from_json(json_str)

        assert restored.user_id == sample_user_profile.user_id


class TestComputeProfile:
    """Tests for compute_profile function."""

    def test_compute_profile_sample_repo(self, sample_repo):
        """Test computing profile from sample repo."""
        profile = compute_profile(str(sample_repo))

        assert profile.user_id == "test_user"
        assert profile.name == "Test User"
        assert len(profile.platforms) > 0
        assert profile.cards is not None
        assert profile.cards.level >= 1

    def test_compute_profile_empty_repo(self, empty_repo):
        """Test computing profile from empty repo."""
        profile = compute_profile(str(empty_repo))

        assert profile.user_id == "empty_user"
        assert len(profile.platforms) == 0
        assert profile.cards.level == 1

    def test_compute_profile_force_recompute(self, sample_repo):
        """Test force recompute ignores cache."""
        # First computation
        profile1 = compute_profile(str(sample_repo))

        # Second computation with force
        profile2 = compute_profile(str(sample_repo), force_recompute=True)

        # Should have same data (deterministic)
        assert profile1.user_id == profile2.user_id
        assert profile1.cards.level == profile2.cards.level

    def test_compute_profile_invalid_repo(self, temp_dir):
        """Test error on invalid repo."""
        with pytest.raises(ValueError):
            compute_profile(str(temp_dir / "nonexistent"))
