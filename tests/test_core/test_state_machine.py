"""Tests for state machine module."""

import pytest
from datetime import datetime, timedelta

from metaspn.core.state_machine import LifecycleStateMachine, LifecycleState
from metaspn.core.profile import Activity, PlatformPresence, ProfileMetrics
from metaspn.core.metrics import DevelopmentMetrics


class TestLifecycleState:
    """Tests for LifecycleState class."""
    
    def test_create_lifecycle_state(self):
        """Test creating a lifecycle state."""
        state = LifecycleState(
            phase="developing",
            phase_progress=0.5,
            days_in_phase=30,
            phase_entered=datetime.now() - timedelta(days=30),
        )
        
        assert state.phase == "developing"
        assert state.phase_progress == 0.5
    
    def test_is_rookie(self):
        """Test is_rookie property."""
        rookie = LifecycleState(
            phase="rookie",
            phase_progress=0.3,
            days_in_phase=10,
            phase_entered=datetime.now(),
        )
        
        assert rookie.is_rookie is True
        assert rookie.is_established is False
    
    def test_is_established(self):
        """Test is_established property."""
        established = LifecycleState(
            phase="established",
            phase_progress=0.5,
            days_in_phase=100,
            phase_entered=datetime.now(),
        )
        
        assert established.is_established is True
        assert established.is_rookie is False
    
    def test_is_veteran(self):
        """Test is_veteran property."""
        veteran = LifecycleState(
            phase="veteran",
            phase_progress=0.7,
            days_in_phase=400,
            phase_entered=datetime.now(),
        )
        
        assert veteran.is_veteran is True
        assert veteran.is_established is True
    
    def test_serialization(self, sample_lifecycle_state: LifecycleState):
        """Test serialization."""
        data = sample_lifecycle_state.to_dict()
        restored = LifecycleState.from_dict(data)
        
        assert restored.phase == sample_lifecycle_state.phase
        assert restored.phase_progress == sample_lifecycle_state.phase_progress


class TestLifecycleStateMachine:
    """Tests for LifecycleStateMachine class."""
    
    def test_compute_rookie(self):
        """Test computing rookie state."""
        sm = LifecycleStateMachine()
        
        # Few activities, few days
        activities = [
            Activity(
                timestamp=datetime.now() - timedelta(days=5),
                platform="podcast",
                activity_type="create",
            )
        ]
        
        platforms = [
            PlatformPresence(
                platform="podcast",
                role="creator",
                joined_at=datetime.now() - timedelta(days=5),
                last_active=datetime.now(),
            )
        ]
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(total_activities=1),
        )
        
        state = sm.compute(activities, platforms, metrics)
        
        assert state.phase == "rookie"
    
    def test_compute_developing(self):
        """Test computing developing state."""
        sm = LifecycleStateMachine()
        
        # 15 activities, 40 days
        base_time = datetime.now()
        activities = [
            Activity(
                timestamp=base_time - timedelta(days=40-i*2),
                platform="podcast",
                activity_type="create",
            )
            for i in range(15)
        ]
        
        platforms = [
            PlatformPresence(
                platform="podcast",
                role="creator",
                joined_at=base_time - timedelta(days=40),
                last_active=base_time,
            )
        ]
        
        metrics = ProfileMetrics(
            development=DevelopmentMetrics(total_activities=15),
        )
        
        state = sm.compute(activities, platforms, metrics)
        
        assert state.phase == "developing"
    
    def test_compute_empty_activities(self):
        """Test computing with no activities."""
        sm = LifecycleStateMachine()
        
        state = sm.compute([], [], ProfileMetrics())
        
        assert state.phase == "rookie"
        assert state.phase_progress == 0.0
    
    def test_get_next_phase(self):
        """Test _get_next_phase helper."""
        sm = LifecycleStateMachine()
        
        assert sm._get_next_phase("rookie") == "developing"
        assert sm._get_next_phase("developing") == "established"
        assert sm._get_next_phase("veteran") == "legend"
        assert sm._get_next_phase("legend") is None
    
    def test_can_advance(self):
        """Test can_advance method."""
        sm = LifecycleStateMachine()
        
        can_advance = LifecycleState(
            phase="rookie",
            phase_progress=1.0,
            days_in_phase=30,
            phase_entered=datetime.now(),
            next_phase="developing",
        )
        
        cannot_advance = LifecycleState(
            phase="rookie",
            phase_progress=0.5,
            days_in_phase=15,
            phase_entered=datetime.now(),
            next_phase="developing",
        )
        
        assert sm.can_advance(can_advance) is True
        assert sm.can_advance(cannot_advance) is False
    
    def test_advance(self):
        """Test advance method."""
        sm = LifecycleStateMachine()
        
        state = LifecycleState(
            phase="rookie",
            phase_progress=1.0,
            days_in_phase=30,
            phase_entered=datetime.now(),
            next_phase="developing",
        )
        
        advanced = sm.advance(state)
        
        assert advanced.phase == "developing"
        assert advanced.phase_progress == 0.0
