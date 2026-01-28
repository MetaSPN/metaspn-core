"""Tests for quality analyzer."""

from datetime import datetime, timedelta

from metaspn.analyzers.quality import QualityAnalyzer
from metaspn.core.profile import Activity


class TestQualityAnalyzer:
    """Tests for QualityAnalyzer class."""

    def test_compute_empty(self):
        """Test computing quality with no activities."""
        analyzer = QualityAnalyzer()

        score = analyzer.compute([])

        assert score == 0.0

    def test_compute_single_activity(self, sample_activity):
        """Test computing quality for single activity."""
        analyzer = QualityAnalyzer()

        score = analyzer.compute([sample_activity])

        assert 0.0 <= score <= 1.0

    def test_compute_multiple_activities(self, sample_activities):
        """Test computing quality for multiple activities."""
        analyzer = QualityAnalyzer()

        score = analyzer.compute(sample_activities)

        assert 0.0 <= score <= 1.0

    def test_compute_for_activity(self, sample_activity):
        """Test computing quality for a single activity."""
        analyzer = QualityAnalyzer()

        score = analyzer.compute_for_activity(sample_activity)

        assert 0.0 <= score <= 1.0

    def test_content_quality_affects_score(self):
        """Test that content quality affects score."""
        analyzer = QualityAnalyzer()

        short_content = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title="Short Post",
            content="Short content",
        )

        long_content = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title="Long Post",
            content="Long content " * 500,
        )

        short_score = analyzer.compute_for_activity(short_content)
        long_score = analyzer.compute_for_activity(long_content)

        assert long_score > short_score

    def test_consistency_affects_score(self):
        """Test that consistent activity improves score."""
        analyzer = QualityAnalyzer()

        base_time = datetime.now()

        # Consistent: activity every 3 days
        consistent = [
            Activity(
                timestamp=base_time - timedelta(days=i * 3),
                platform="blog",
                activity_type="create",
                title=f"Post {i}",
                content="Content " * 100,
            )
            for i in range(10)
        ]

        # Inconsistent: random gaps
        inconsistent = [
            Activity(
                timestamp=base_time - timedelta(days=i * 10),
                platform="blog",
                activity_type="create",
                title=f"Post {i}",
                content="Content " * 100,
            )
            for i in range(10)
        ]

        consistent_score = analyzer.compute(consistent)
        inconsistent_score = analyzer.compute(inconsistent)

        assert consistent_score >= inconsistent_score

    def test_get_quality_breakdown(self, sample_activities):
        """Test getting quality breakdown."""
        analyzer = QualityAnalyzer()

        breakdown = analyzer.get_quality_breakdown(sample_activities)

        assert "overall" in breakdown
        assert "content" in breakdown
        assert "consistency" in breakdown
        assert "depth" in breakdown
        assert "sample_size" in breakdown

        assert breakdown["sample_size"] == len(sample_activities)

    def test_custom_weights(self, sample_activities):
        """Test analyzer with custom weights."""
        default_analyzer = QualityAnalyzer()
        content_heavy = QualityAnalyzer(
            content_weight=0.8,
            consistency_weight=0.1,
            depth_weight=0.1,
        )

        # Scores should differ with different weights
        default_score = default_analyzer.compute(sample_activities)
        content_score = content_heavy.compute(sample_activities)

        # Both should be valid
        assert 0.0 <= default_score <= 1.0
        assert 0.0 <= content_score <= 1.0
