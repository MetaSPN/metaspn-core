"""Tests for game analyzer."""

import pytest
from datetime import datetime

from metaspn.analyzers.games import GameAnalyzer
from metaspn.core.profile import Activity
from metaspn.core.metrics import GameSignature


class TestGameAnalyzer:
    """Tests for GameAnalyzer class."""
    
    def test_compute_empty(self):
        """Test computing with no activities."""
        analyzer = GameAnalyzer()
        
        signature = analyzer.compute([])
        
        assert isinstance(signature, GameSignature)
        assert signature.G1 == 0.0
    
    def test_compute_single_activity(self, sample_activity):
        """Test computing for single activity."""
        analyzer = GameAnalyzer()
        
        signature = analyzer.compute([sample_activity])
        
        assert isinstance(signature, GameSignature)
        # At least one game should have a score (due to platform weights)
        total = signature.G1 + signature.G2 + signature.G3 + signature.G4 + signature.G5 + signature.G6
        assert total > 0
    
    def test_compute_multiple_activities(self, sample_activities):
        """Test computing for multiple activities."""
        analyzer = GameAnalyzer()
        
        signature = analyzer.compute(sample_activities)
        
        assert isinstance(signature, GameSignature)
    
    def test_keywords_affect_classification(self):
        """Test that keywords affect game classification."""
        analyzer = GameAnalyzer()
        
        # G3 (Models) keywords
        framework_activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title="Building a Framework",
            content="This tutorial explains step by step how to build a system with methodology",
        )
        
        # G6 (Network) keywords
        network_activity = Activity(
            timestamp=datetime.now(),
            platform="podcast",
            activity_type="create",
            title="Interview with Guest",
            content="Today we have a conversation and discussion about community and collaboration",
        )
        
        framework_sig = analyzer.compute_for_activity(framework_activity)
        network_sig = analyzer.compute_for_activity(network_activity)
        
        # Framework content should lean G3
        assert framework_sig.G3 > 0
        # Network content should lean G6
        assert network_sig.G6 > 0
    
    def test_platform_weights(self):
        """Test that platforms have different weight distributions."""
        analyzer = GameAnalyzer()
        
        podcast = Activity(
            timestamp=datetime.now(),
            platform="podcast",
            activity_type="create",
            title="Generic Episode",
        )
        
        youtube = Activity(
            timestamp=datetime.now(),
            platform="youtube",
            activity_type="create",
            title="Generic Video",
        )
        
        podcast_sig = analyzer.compute_for_activity(podcast)
        youtube_sig = analyzer.compute_for_activity(youtube)
        
        # Both should have signatures
        assert podcast_sig.primary_game is not None or sum([podcast_sig.G1, podcast_sig.G2, podcast_sig.G3, podcast_sig.G4, podcast_sig.G5, podcast_sig.G6]) > 0
        assert youtube_sig.primary_game is not None or sum([youtube_sig.G1, youtube_sig.G2, youtube_sig.G3, youtube_sig.G4, youtube_sig.G5, youtube_sig.G6]) > 0
    
    def test_get_primary_game(self, sample_activities):
        """Test getting primary game."""
        analyzer = GameAnalyzer()
        
        primary = analyzer.get_primary_game(sample_activities)
        
        # Should return one of the games or None
        assert primary is None or primary in ["G1", "G2", "G3", "G4", "G5", "G6"]
    
    def test_get_game_breakdown(self, sample_activities):
        """Test getting game breakdown."""
        analyzer = GameAnalyzer()
        
        breakdown = analyzer.get_game_breakdown(sample_activities)
        
        assert "signature" in breakdown
        assert "primary_game" in breakdown
        assert "is_specialist" in breakdown
        assert "is_multi_game" in breakdown
        assert "sample_size" in breakdown
    
    def test_classify_activity_type(self, sample_activity):
        """Test classifying activity type."""
        analyzer = GameAnalyzer()
        
        classification = analyzer.classify_activity_type(sample_activity)
        
        assert classification in [
            "general", "foundational", "exploratory", 
            "instructional", "entertaining", "insightful", "connective"
        ]
