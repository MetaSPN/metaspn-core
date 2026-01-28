"""Tests for level and achievement systems."""

import pytest
from datetime import datetime, timedelta

from metaspn.core.level import (
    LevelCalculator,
    RarityCalculator,
    AchievementSystem,
    Badge,
)
from metaspn.core.profile import Activity, ProfileMetrics
from metaspn.core.metrics import DevelopmentMetrics, CreatorMetrics, GameSignature, Trajectory
from metaspn.core.state_machine import LifecycleState


class TestBadge:
    """Tests for Badge class."""
    
    def test_create_badge(self):
        """Test creating a badge."""
        badge = Badge(
            badge_id="test_badge",
            name="Test Badge",
            description="A test badge",
            icon="🎯",
            category="test",
            earned_at=datetime.now(),
        )
        
        assert badge.badge_id == "test_badge"
        assert badge.name == "Test Badge"
        assert badge.rarity == "common"
    
    def test_serialization(self, sample_badges):
        """Test serialization."""
        badge = sample_badges[0]
        data = badge.to_dict()
        restored = Badge.from_dict(data)
        
        assert restored.badge_id == badge.badge_id
        assert restored.name == badge.name


class TestLevelCalculator:
    """Tests for LevelCalculator class."""
    
    def test_compute_level_from_xp(self):
        """Test computing level from XP."""
        calc = LevelCalculator()
        
        assert calc.compute_level(0) == 1
        assert calc.compute_level(100) == 1
        assert calc.compute_level(500) >= 2
        assert calc.compute_level(5000) >= 5
    
    def test_xp_for_level(self):
        """Test calculating XP required for a level."""
        calc = LevelCalculator()
        
        assert calc.xp_for_level(1) == 0
        assert calc.xp_for_level(2) > 100
        assert calc.xp_for_level(10) > calc.xp_for_level(5)
    
    def test_xp_to_next_level(self):
        """Test calculating XP needed for next level."""
        calc = LevelCalculator()
        
        xp = 500
        level = calc.compute_level(xp)
        xp_needed = calc.xp_to_next_level(xp)
        
        assert xp_needed > 0
        assert calc.compute_level(xp + xp_needed) == level + 1
    
    def test_level_progress(self):
        """Test calculating progress through current level."""
        calc = LevelCalculator()
        
        progress = calc.level_progress(500)
        
        assert 0.0 <= progress <= 1.0
    
    def test_compute_xp_from_activities(self, sample_activities):
        """Test computing XP from activities."""
        calc = LevelCalculator()
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(achievements=["test1", "test2"]),
        )
        
        xp = calc.compute_xp(sample_activities, metrics)
        
        assert xp > 0
        # Create activities should give more XP than consume
        create_count = sum(1 for a in sample_activities if a.activity_type == "create")
        assert xp >= create_count * calc.CREATE_BASE_XP * 0.5  # At least half base XP
    
    def test_compute_xp_empty(self):
        """Test computing XP with no activities."""
        calc = LevelCalculator()
        
        xp = calc.compute_xp([], ProfileMetrics())
        
        assert xp == 0


class TestRarityCalculator:
    """Tests for RarityCalculator class."""
    
    def test_compute_rarity_basic(self):
        """Test computing basic rarity."""
        calc = RarityCalculator()
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(achievements=[]),
        )
        
        rarity = calc.compute(metrics, None)
        
        assert rarity in calc.TIERS
    
    def test_compute_rarity_with_creator(self, sample_creator_metrics):
        """Test rarity with creator metrics."""
        calc = RarityCalculator()
        
        metrics = ProfileMetrics(
            creator=sample_creator_metrics,
            development=DevelopmentMetrics(achievements=["a", "b", "c"]),
        )
        
        lifecycle = LifecycleState(
            phase="established",
            phase_progress=0.5,
            days_in_phase=100,
            phase_entered=datetime.now(),
        )
        
        rarity = calc.compute(metrics, lifecycle)
        
        # Should be at least uncommon with good metrics
        assert calc.tier_index(rarity) >= calc.tier_index("uncommon")
    
    def test_tier_index(self):
        """Test tier_index method."""
        calc = RarityCalculator()
        
        assert calc.tier_index("common") == 0
        assert calc.tier_index("legendary") == 4
        assert calc.tier_index("invalid") == 0
    
    def test_is_higher_tier(self):
        """Test is_higher_tier method."""
        calc = RarityCalculator()
        
        assert calc.is_higher_tier("rare", "common") is True
        assert calc.is_higher_tier("common", "rare") is False
        assert calc.is_higher_tier("legendary", "epic") is True


class TestAchievementSystem:
    """Tests for AchievementSystem class."""
    
    def test_compute_basic_achievements(self, sample_activities):
        """Test computing basic achievements."""
        system = AchievementSystem()
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(
                total_activities=len(sample_activities),
                streak_longest=3,
                platforms_active=3,
            ),
        )
        
        lifecycle = LifecycleState(
            phase="developing",
            phase_progress=0.5,
            days_in_phase=30,
            phase_entered=datetime.now(),
        )
        
        badges = system.compute(sample_activities, metrics, lifecycle)
        
        # Should have at least first_activity badge
        badge_ids = [b.badge_id for b in badges]
        assert "first_activity" in badge_ids
    
    def test_compute_no_activities(self):
        """Test computing with no activities."""
        system = AchievementSystem()
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(),
        )
        
        badges = system.compute([], metrics, None)
        
        # Should have no badges
        assert len(badges) == 0
    
    def test_get_definition(self):
        """Test getting achievement definition."""
        system = AchievementSystem()
        
        definition = system.get_definition("first_activity")
        
        assert definition is not None
        assert definition.name == "First Steps"
    
    def test_get_by_category(self):
        """Test getting achievements by category."""
        system = AchievementSystem()
        
        activity_badges = system.get_by_category("activity")
        
        assert len(activity_badges) > 0
        assert all(d.category == "activity" for d in activity_badges)
    
    def test_get_by_rarity(self):
        """Test getting achievements by rarity."""
        system = AchievementSystem()
        
        common_badges = system.get_by_rarity("common")
        rare_badges = system.get_by_rarity("rare")
        
        assert len(common_badges) > 0
        assert len(rare_badges) > 0
        assert all(d.rarity == "common" for d in common_badges)
