"""Game analyzer for MetaSPN using ML classification."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from founder_game_classifier import GameClassifier

from metaspn.core.enhancements import GAME_SIGNATURE_ALGORITHM_VERSION, GameSignatureEnhancement
from metaspn.core.metrics import GameSignature

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class GameAnalyzer:
    """Analyzer for classifying content into the six games framework.

    Uses a trained ML model (sentence-transformers + logistic regression) to
    classify content into six founder games.

    The Six Games:
        G1 (Identity/Canon): Recruiting into identity, lineage, belonging, status
        G2 (Ideas/Play Mining): Extracting reusable tactics, heuristics
        G3 (Models/Understanding): Building mental models, frameworks, explanations
        G4 (Performance/Competition): Winning, execution, metrics, zero-sum edges
        G5 (Meaning/Therapy): Healing, values, emotional processing, transformation
        G6 (Network/Coordination): Community building, protocols, collective action

    The classifier model is downloaded from Hugging Face Hub on first use
    and cached locally (~100MB).
    """

    def __init__(
        self,
        model_name: str = "leoguinan/founder-game-classifier",
    ) -> None:
        """Initialize game analyzer with ML classifier.

        Args:
            model_name: Hugging Face model identifier or local path
        """
        self._classifier = GameClassifier.from_pretrained(model_name)

    def compute(self, activities: list["Activity"]) -> GameSignature:
        """Compute aggregate game signature from activities.

        Uses batch classification for efficiency, then averages the
        probability distributions across all activities.

        Args:
            activities: List of activities to analyze

        Returns:
            GameSignature with distribution across games
        """
        if not activities:
            return GameSignature()

        # Extract text from activities
        texts = []
        for activity in activities:
            text = self._get_text(activity)
            if text:
                texts.append(text)

        if not texts:
            return GameSignature()

        # Use ML model's aggregate signature method
        probs = self._classifier.get_game_signature(texts)

        return GameSignature(
            G1=probs.get("G1", 0.0),
            G2=probs.get("G2", 0.0),
            G3=probs.get("G3", 0.0),
            G4=probs.get("G4", 0.0),
            G5=probs.get("G5", 0.0),
            G6=probs.get("G6", 0.0),
        )

    def compute_for_activity(self, activity: "Activity") -> GameSignature:
        """Compute game signature for a single activity.

        Args:
            activity: Activity to analyze

        Returns:
            GameSignature for this activity
        """
        text = self._get_text(activity)
        if not text:
            return GameSignature()

        result = self._classifier.predict(text)
        probs = result["probabilities"]

        return GameSignature(
            G1=probs.get("G1", 0.0),
            G2=probs.get("G2", 0.0),
            G3=probs.get("G3", 0.0),
            G4=probs.get("G4", 0.0),
            G5=probs.get("G5", 0.0),
            G6=probs.get("G6", 0.0),
        )

    def _get_text(self, activity: "Activity") -> str:
        """Extract text content from an activity.

        Combines title and content into a single string for classification.

        Args:
            activity: Activity to extract text from

        Returns:
            Combined text string
        """
        parts = []
        if activity.title:
            parts.append(activity.title)
        if activity.content:
            parts.append(activity.content)
        return " ".join(parts).strip()

    def get_primary_game(self, activities: list["Activity"]) -> Optional[str]:
        """Get the primary (highest scoring) game.

        Args:
            activities: List of activities

        Returns:
            Primary game identifier (G1-G6) or None
        """
        signature = self.compute(activities)
        return signature.primary_game

    def get_game_breakdown(self, activities: list["Activity"]) -> dict:
        """Get detailed breakdown of game classification.

        Args:
            activities: List of activities

        Returns:
            Dictionary with game analysis details
        """
        signature = self.compute(activities)

        return {
            "signature": signature.to_dict(),
            "primary_game": signature.primary_game,
            "is_specialist": signature.is_specialist,
            "is_multi_game": signature.is_multi_game,
            "is_balanced": signature.is_balanced,
            "sample_size": len(activities),
        }

    def classify_activity_type(self, activity: "Activity") -> str:
        """Classify what type of content an activity represents.

        Args:
            activity: Activity to classify

        Returns:
            Classification string describing the content type
        """
        text = self._get_text(activity)
        if not text:
            return "general"

        result = self._classifier.predict(text)
        primary = result.get("primary_game")

        if primary is None:
            return "general"

        type_names = {
            "G1": "identity",
            "G2": "tactical",
            "G3": "framework",
            "G4": "competitive",
            "G5": "transformative",
            "G6": "community",
        }

        return type_names.get(primary, "general")

    def predict_with_confidence(self, activity: "Activity") -> dict:
        """Get full prediction with confidence scores.

        Args:
            activity: Activity to analyze

        Returns:
            Dictionary with primary/secondary games, confidence, and descriptions
        """
        text = self._get_text(activity)
        if not text:
            return {
                "primary_game": None,
                "secondary_game": None,
                "confidence": 0.0,
                "probabilities": {},
            }

        return self._classifier.predict(text)

    def compute_enhancements(
        self,
        activities: list["Activity"],
        computed_at: Optional[datetime] = None,
        batch_size: int = 32,
    ) -> list[GameSignatureEnhancement]:
        """Compute game signature enhancements for all activities.

        Creates a GameSignatureEnhancement for each activity, suitable for
        storing in the enhancement layer. Uses batch processing for efficiency.

        Args:
            activities: List of activities to analyze
            computed_at: Timestamp for when computation occurred (defaults to now)
            batch_size: Number of texts to process in each batch

        Returns:
            List of GameSignatureEnhancement records
        """
        if computed_at is None:
            computed_at = datetime.now()

        enhancements = []

        # Process activities with text
        activities_with_text = []
        for activity in activities:
            if activity.activity_id and self._get_text(activity):
                activities_with_text.append(activity)

        if not activities_with_text:
            return enhancements

        # Extract texts for batch processing
        texts = [self._get_text(a) for a in activities_with_text]

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_activities = activities_with_text[i : i + batch_size]

            # Get batch predictions
            batch_results = self._classifier.predict_batch(batch_texts)

            for activity, result in zip(batch_activities, batch_results):
                probs = result.get("probabilities", {})
                confidence = result.get("confidence", 0.0)

                game_signature = GameSignature(
                    G1=probs.get("G1", 0.0),
                    G2=probs.get("G2", 0.0),
                    G3=probs.get("G3", 0.0),
                    G4=probs.get("G4", 0.0),
                    G5=probs.get("G5", 0.0),
                    G6=probs.get("G6", 0.0),
                )

                enhancement = GameSignatureEnhancement(
                    activity_id=activity.activity_id,
                    computed_at=computed_at,
                    algorithm_version=GAME_SIGNATURE_ALGORITHM_VERSION,
                    game_signature=game_signature,
                    confidence=confidence,
                )
                enhancements.append(enhancement)

        return enhancements

    def compute_enhancement_for_activity(
        self,
        activity: "Activity",
        computed_at: Optional[datetime] = None,
    ) -> Optional[GameSignatureEnhancement]:
        """Compute game signature enhancement for a single activity.

        Args:
            activity: Activity to analyze
            computed_at: Timestamp for when computation occurred

        Returns:
            GameSignatureEnhancement or None if activity has no text/ID
        """
        if not activity.activity_id:
            return None

        text = self._get_text(activity)
        if not text:
            return None

        if computed_at is None:
            computed_at = datetime.now()

        result = self._classifier.predict(text)
        probs = result.get("probabilities", {})
        confidence = result.get("confidence", 0.0)

        game_signature = GameSignature(
            G1=probs.get("G1", 0.0),
            G2=probs.get("G2", 0.0),
            G3=probs.get("G3", 0.0),
            G4=probs.get("G4", 0.0),
            G5=probs.get("G5", 0.0),
            G6=probs.get("G6", 0.0),
        )

        return GameSignatureEnhancement(
            activity_id=activity.activity_id,
            computed_at=computed_at,
            algorithm_version=GAME_SIGNATURE_ALGORITHM_VERSION,
            game_signature=game_signature,
            confidence=confidence,
        )
