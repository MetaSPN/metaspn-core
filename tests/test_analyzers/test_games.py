"""Tests for game analyzer using ML classification."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from metaspn.analyzers.games import GameAnalyzer
from metaspn.core.metrics import GameSignature
from metaspn.core.profile import Activity


class TestGameAnalyzerWithMock:
    """Tests for GameAnalyzer using mocked ML classifier."""

    @pytest.fixture
    def mock_classifier(self):
        """Create a mock GameClassifier."""
        mock = MagicMock()

        # Default predict response
        mock.predict.return_value = {
            "primary_game": "G3",
            "secondary_game": "G2",
            "confidence": 0.72,
            "probabilities": {
                "G1": 0.05,
                "G2": 0.20,
                "G3": 0.45,
                "G4": 0.10,
                "G5": 0.12,
                "G6": 0.08,
            },
        }

        # Default get_game_signature response
        mock.get_game_signature.return_value = {
            "G1": 0.08,
            "G2": 0.25,
            "G3": 0.30,
            "G4": 0.12,
            "G5": 0.15,
            "G6": 0.10,
        }

        return mock

    @pytest.fixture
    def analyzer_with_mock(self, mock_classifier):
        """Create GameAnalyzer with mocked classifier."""
        with patch(
            "metaspn.analyzers.games.GameClassifier.from_pretrained",
            return_value=mock_classifier,
        ):
            analyzer = GameAnalyzer()
            return analyzer, mock_classifier

    def test_compute_empty(self, analyzer_with_mock):
        """Test computing with no activities."""
        analyzer, _ = analyzer_with_mock

        signature = analyzer.compute([])

        assert isinstance(signature, GameSignature)
        assert signature.G1 == 0.0
        assert signature.G2 == 0.0
        assert signature.G3 == 0.0

    def test_compute_single_activity(self, analyzer_with_mock, sample_activity):
        """Test computing for single activity."""
        analyzer, mock_classifier = analyzer_with_mock

        signature = analyzer.compute([sample_activity])

        assert isinstance(signature, GameSignature)
        # Should have called get_game_signature with the text
        mock_classifier.get_game_signature.assert_called_once()
        # Check values match mock response
        assert signature.G3 == 0.30

    def test_compute_for_activity(self, analyzer_with_mock, sample_activity):
        """Test computing for a single activity."""
        analyzer, mock_classifier = analyzer_with_mock

        signature = analyzer.compute_for_activity(sample_activity)

        assert isinstance(signature, GameSignature)
        mock_classifier.predict.assert_called_once()
        # Check values match mock response
        assert signature.G3 == 0.45
        assert signature.G2 == 0.20

    def test_compute_for_activity_no_text(self, analyzer_with_mock):
        """Test computing for activity with no text content."""
        analyzer, mock_classifier = analyzer_with_mock

        activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title=None,
            content=None,
        )

        signature = analyzer.compute_for_activity(activity)

        assert isinstance(signature, GameSignature)
        assert signature.G1 == 0.0
        mock_classifier.predict.assert_not_called()

    def test_get_primary_game(self, analyzer_with_mock, sample_activity):
        """Test getting primary game."""
        analyzer, _ = analyzer_with_mock

        primary = analyzer.get_primary_game([sample_activity])

        assert primary == "G3"

    def test_get_game_breakdown(self, analyzer_with_mock, sample_activity):
        """Test getting game breakdown."""
        analyzer, _ = analyzer_with_mock

        breakdown = analyzer.get_game_breakdown([sample_activity])

        assert "signature" in breakdown
        assert "primary_game" in breakdown
        assert "is_specialist" in breakdown
        assert "is_multi_game" in breakdown
        assert "is_balanced" in breakdown
        assert "sample_size" in breakdown
        assert breakdown["sample_size"] == 1

    def test_classify_activity_type(self, analyzer_with_mock, sample_activity):
        """Test classifying activity type."""
        analyzer, _ = analyzer_with_mock

        classification = analyzer.classify_activity_type(sample_activity)

        # G3 maps to "framework"
        assert classification == "framework"

    def test_classify_activity_type_no_text(self, analyzer_with_mock):
        """Test classifying activity with no text."""
        analyzer, _ = analyzer_with_mock

        activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
        )

        classification = analyzer.classify_activity_type(activity)

        assert classification == "general"

    def test_predict_with_confidence(self, analyzer_with_mock, sample_activity):
        """Test getting full prediction with confidence."""
        analyzer, _ = analyzer_with_mock

        result = analyzer.predict_with_confidence(sample_activity)

        assert result["primary_game"] == "G3"
        assert result["secondary_game"] == "G2"
        assert result["confidence"] == 0.72
        assert "probabilities" in result

    def test_predict_with_confidence_no_text(self, analyzer_with_mock):
        """Test prediction with no text returns empty result."""
        analyzer, _ = analyzer_with_mock

        activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
        )

        result = analyzer.predict_with_confidence(activity)

        assert result["primary_game"] is None
        assert result["confidence"] == 0.0

    def test_text_extraction(self, analyzer_with_mock):
        """Test that text is properly extracted from activity."""
        analyzer, mock_classifier = analyzer_with_mock

        activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title="My Title",
            content="My content goes here",
        )

        analyzer.compute_for_activity(activity)

        # Check the text passed to predict
        call_args = mock_classifier.predict.call_args[0][0]
        assert "My Title" in call_args
        assert "My content goes here" in call_args


@pytest.mark.integration
class TestGameAnalyzerIntegration:
    """Integration tests that use the real ML model.

    These tests are marked with @pytest.mark.integration and should
    be run separately since they download the model (~100MB).

    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_analyzer(self):
        """Create GameAnalyzer with real classifier."""
        return GameAnalyzer()

    def test_real_model_loads(self, real_analyzer):
        """Test that the real model loads successfully."""
        assert real_analyzer._classifier is not None

    def test_real_classification(self, real_analyzer):
        """Test classification with real model."""
        activity = Activity(
            timestamp=datetime.now(),
            platform="blog",
            activity_type="create",
            title="Building a Framework for Success",
            content="Here's a step-by-step methodology for building systems.",
        )

        signature = real_analyzer.compute_for_activity(activity)

        assert isinstance(signature, GameSignature)
        # Should produce some distribution
        total = sum(
            [
                signature.G1,
                signature.G2,
                signature.G3,
                signature.G4,
                signature.G5,
                signature.G6,
            ]
        )
        assert 0.99 <= total <= 1.01  # Should sum to ~1.0

    def test_real_batch_classification(self, real_analyzer):
        """Test batch classification with real model."""
        activities = [
            Activity(
                timestamp=datetime.now(),
                platform="blog",
                activity_type="create",
                title="Framework Building",
                content="A systematic approach to problem solving.",
            ),
            Activity(
                timestamp=datetime.now(),
                platform="blog",
                activity_type="create",
                title="Community Building",
                content="How to build and coordinate a community.",
            ),
        ]

        signature = real_analyzer.compute(activities)

        assert isinstance(signature, GameSignature)
        assert signature.primary_game in ["G1", "G2", "G3", "G4", "G5", "G6"]
