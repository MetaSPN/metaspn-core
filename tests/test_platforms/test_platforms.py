"""Tests for platform integrations."""

import pytest
from datetime import datetime

from metaspn.platforms.base import BasePlatform, PlatformRegistry
from metaspn.platforms.podcast import PodcastPlatform
from metaspn.platforms.youtube import YouTubePlatform
from metaspn.platforms.twitter import TwitterPlatform
from metaspn.platforms.blog import BlogPlatform


class TestPodcastPlatform:
    """Tests for PodcastPlatform."""
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = PodcastPlatform()
        assert platform.get_platform_name() == "podcast"
    
    def test_ingest_basic(self):
        """Test basic ingestion."""
        platform = PodcastPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "Episode 1",
            "description": "A great episode",
            "duration_seconds": 3600,
        }
        
        activity = platform.ingest(data)
        
        assert activity.platform == "podcast"
        assert activity.title == "Episode 1"
        assert activity.duration_seconds == 3600
    
    def test_ingest_with_guests(self):
        """Test ingestion with guest data."""
        platform = PodcastPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "Interview Episode",
            "guests": ["Alice", "Bob"],
            "duration_seconds": 5400,
        }
        
        activity = platform.ingest(data)
        
        assert activity.raw_data.get("guests") == ["Alice", "Bob"]
    
    def test_compute_metrics(self, sample_activities):
        """Test computing podcast metrics."""
        platform = PodcastPlatform()
        
        # Filter to podcast activities
        podcast_activities = [a for a in sample_activities if a.platform == "podcast"]
        
        metrics = platform.compute_metrics(podcast_activities)
        
        assert "total_episodes" in metrics
        assert "total_duration_hours" in metrics
        assert "episode_types" in metrics
    
    def test_estimate_quality(self):
        """Test quality estimation."""
        platform = PodcastPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "Long Episode",
            "description": "Detailed description " * 50,
            "duration_seconds": 5400,
            "guests": ["Expert"],
        }
        
        activity = platform.ingest(data)
        quality = platform.estimate_quality(activity)
        
        assert 0.0 <= quality <= 1.0


class TestYouTubePlatform:
    """Tests for YouTubePlatform."""
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = YouTubePlatform()
        assert platform.get_platform_name() == "youtube"
    
    def test_ingest_basic(self):
        """Test basic ingestion."""
        platform = YouTubePlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "Tutorial Video",
            "video_id": "abc123",
            "duration_seconds": 600,
            "views": 1000,
        }
        
        activity = platform.ingest(data)
        
        assert activity.platform == "youtube"
        assert activity.title == "Tutorial Video"
        assert activity.url == "https://www.youtube.com/watch?v=abc123"
        assert activity.raw_data.get("views") == 1000
    
    def test_compute_metrics_empty(self):
        """Test computing metrics with no activities."""
        platform = YouTubePlatform()
        
        metrics = platform.compute_metrics([])
        
        assert metrics["total_videos"] == 0


class TestTwitterPlatform:
    """Tests for TwitterPlatform."""
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = TwitterPlatform()
        assert platform.get_platform_name() == "twitter"
    
    def test_ingest_tweet(self):
        """Test ingesting a tweet."""
        platform = TwitterPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "text": "Hello world! #testing",
            "tweet_id": "12345",
            "username": "testuser",
            "likes": 50,
        }
        
        activity = platform.ingest(data)
        
        assert activity.platform == "twitter"
        assert activity.content == "Hello world! #testing"
        assert activity.raw_data.get("likes") == 50
    
    def test_ingest_retweet(self):
        """Test that retweets are marked as consume."""
        platform = TwitterPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "text": "RT: Original tweet",
            "is_retweet": True,
        }
        
        activity = platform.ingest(data)
        
        assert activity.activity_type == "consume"


class TestBlogPlatform:
    """Tests for BlogPlatform."""
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = BlogPlatform()
        assert platform.get_platform_name() == "blog"
    
    def test_ingest_basic(self):
        """Test basic ingestion."""
        platform = BlogPlatform()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "My Blog Post",
            "content": "This is the content " * 100,
        }
        
        activity = platform.ingest(data)
        
        assert activity.platform == "blog"
        assert activity.title == "My Blog Post"
        assert activity.raw_data.get("word_count") is not None
    
    def test_reading_time_calculation(self):
        """Test reading time calculation."""
        platform = BlogPlatform()
        
        # 400 words = 2 minutes at 200 wpm
        content = "word " * 400
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "Test Post",
            "content": content,
        }
        
        activity = platform.ingest(data)
        
        # Should be approximately 2 minutes = 120 seconds
        assert activity.duration_seconds is not None
        assert 100 <= activity.duration_seconds <= 140


class TestPlatformRegistry:
    """Tests for PlatformRegistry."""
    
    def test_register_and_get(self):
        """Test registering and retrieving platforms."""
        registry = PlatformRegistry()
        
        podcast = PodcastPlatform()
        registry.register(podcast)
        
        retrieved = registry.get("podcast")
        
        assert retrieved is not None
        assert retrieved.get_platform_name() == "podcast"
    
    def test_get_nonexistent(self):
        """Test getting nonexistent platform."""
        registry = PlatformRegistry()
        
        result = registry.get("nonexistent")
        
        assert result is None
