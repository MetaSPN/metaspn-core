"""Tests for core metrics module."""

import pytest
from datetime import datetime

from metaspn.core.metrics import (
    GameSignature,
    Trajectory,
    CreatorMetrics,
    ConsumerMetrics,
    DevelopmentMetrics,
)


class TestGameSignature:
    """Tests for GameSignature class."""
    
    def test_create_game_signature(self):
        """Test creating a game signature."""
        sig = GameSignature(G1=0.5, G2=0.3, G3=0.7, G4=0.2, G5=0.4, G6=0.1)
        
        assert sig.G1 == 0.5
        assert sig.G3 == 0.7
    
    def test_validation_range(self):
        """Test validation of score ranges."""
        with pytest.raises(ValueError):
            GameSignature(G1=1.5)  # > 1.0
        
        with pytest.raises(ValueError):
            GameSignature(G2=-0.1)  # < 0.0
    
    def test_primary_game(self, sample_game_signature: GameSignature):
        """Test primary_game property."""
        assert sample_game_signature.primary_game == "G3"  # 0.6 is highest
    
    def test_primary_game_none(self):
        """Test primary_game when all zeros."""
        sig = GameSignature()
        assert sig.primary_game is None
    
    def test_is_specialist(self, sample_game_signature: GameSignature):
        """Test is_specialist property."""
        assert sample_game_signature.is_specialist is False  # No game > 0.60
        
        specialist = GameSignature(G1=0.8)
        assert specialist.is_specialist is True
    
    def test_is_multi_game(self, sample_game_signature: GameSignature):
        """Test is_multi_game property."""
        # G2=0.4, G3=0.6, G5=0.5 - 3 games > 0.30
        assert sample_game_signature.is_multi_game is True
        
        single_game = GameSignature(G1=0.8, G2=0.1)
        assert single_game.is_multi_game is False
    
    def test_is_balanced(self):
        """Test is_balanced property."""
        balanced = GameSignature(G1=0.4, G2=0.45, G3=0.5, G4=0.42, G5=0.48, G6=0.4)
        assert balanced.is_balanced is True
        
        unbalanced = GameSignature(G1=0.9, G2=0.1)
        assert unbalanced.is_balanced is False
    
    def test_serialization(self, sample_game_signature: GameSignature):
        """Test serialization."""
        data = sample_game_signature.to_dict()
        restored = GameSignature.from_dict(data)
        
        assert restored.G1 == sample_game_signature.G1
        assert restored.G3 == sample_game_signature.G3


class TestTrajectory:
    """Tests for Trajectory class."""
    
    def test_create_trajectory(self):
        """Test creating a trajectory."""
        traj = Trajectory(direction="ascending", slope=0.15, window_days=30)
        
        assert traj.direction == "ascending"
        assert traj.slope == 0.15
    
    def test_is_positive(self):
        """Test is_positive property."""
        ascending = Trajectory(direction="ascending", slope=0.1)
        assert ascending.is_positive is True
        
        descending = Trajectory(direction="descending", slope=-0.1)
        assert descending.is_positive is False
    
    def test_is_stable(self):
        """Test is_stable property."""
        stable = Trajectory(direction="stable", slope=0.02)
        assert stable.is_stable is True
    
    def test_serialization(self):
        """Test serialization."""
        traj = Trajectory(
            direction="ascending",
            slope=0.1,
            window_days=30,
            start_date=datetime.now(),
        )
        
        data = traj.to_dict()
        restored = Trajectory.from_dict(data)
        
        assert restored.direction == traj.direction
        assert restored.slope == traj.slope


class TestCreatorMetrics:
    """Tests for CreatorMetrics class."""
    
    def test_create_creator_metrics(self, sample_game_signature: GameSignature):
        """Test creating creator metrics."""
        metrics = CreatorMetrics(
            quality_score=0.8,
            game_alignment=0.7,
            impact_factor=0.6,
            calibration=0.75,
            game_signature=sample_game_signature,
            total_outputs=100,
        )
        
        assert metrics.quality_score == 0.8
        assert metrics.total_outputs == 100
    
    def test_validation_range(self):
        """Test validation of score ranges."""
        with pytest.raises(ValueError):
            CreatorMetrics(quality_score=1.5)
    
    def test_overall_score(self, sample_creator_metrics: CreatorMetrics):
        """Test overall_score calculation."""
        score = sample_creator_metrics.overall_score
        
        # Verify weighted average
        expected = (
            0.75 * 0.35 +  # quality
            0.65 * 0.25 +  # alignment
            0.55 * 0.25 +  # impact
            0.70 * 0.15    # calibration
        )
        
        assert abs(score - expected) < 0.01
    
    def test_serialization(self, sample_creator_metrics: CreatorMetrics):
        """Test serialization."""
        data = sample_creator_metrics.to_dict()
        restored = CreatorMetrics.from_dict(data)
        
        assert restored.quality_score == sample_creator_metrics.quality_score
        assert restored.total_outputs == sample_creator_metrics.total_outputs


class TestConsumerMetrics:
    """Tests for ConsumerMetrics class."""
    
    def test_create_consumer_metrics(self):
        """Test creating consumer metrics."""
        metrics = ConsumerMetrics(
            execution_rate=0.7,
            integration_skill=0.6,
            discernment=0.8,
            development=0.5,
            total_consumed=50,
            hours_consumed=75.5,
        )
        
        assert metrics.execution_rate == 0.7
        assert metrics.total_consumed == 50
        assert metrics.hours_consumed == 75.5
    
    def test_overall_score(self, sample_consumer_metrics: ConsumerMetrics):
        """Test overall_score calculation."""
        score = sample_consumer_metrics.overall_score
        
        # Verify weighted average
        expected = (
            0.6 * 0.30 +   # execution
            0.5 * 0.30 +   # integration
            0.7 * 0.20 +   # discernment
            0.55 * 0.20    # development
        )
        
        assert abs(score - expected) < 0.01


class TestDevelopmentMetrics:
    """Tests for DevelopmentMetrics class."""
    
    def test_create_development_metrics(self):
        """Test creating development metrics."""
        metrics = DevelopmentMetrics(
            total_activities=100,
            active_days=45,
            streak_current=7,
            streak_longest=14,
        )
        
        assert metrics.total_activities == 100
        assert metrics.active_days == 45
    
    def test_activity_rate(self):
        """Test activity_rate calculation."""
        metrics = DevelopmentMetrics(
            total_activities=100,
            active_days=50,
        )
        
        assert metrics.activity_rate == 2.0
    
    def test_activity_rate_zero_days(self):
        """Test activity_rate with zero active days."""
        metrics = DevelopmentMetrics(
            total_activities=0,
            active_days=0,
        )
        
        assert metrics.activity_rate == 0.0
