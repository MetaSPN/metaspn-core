"""Quality analyzer for MetaSPN."""

from typing import TYPE_CHECKING

from metaspn.utils.stats import clamp, mean, std_dev

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class QualityAnalyzer:
    """Analyzer for computing quality scores.

    Quality is measured on a 0.00-1.00 scale based on multiple factors:

    Factors:
        - Content depth (length, duration)
        - Consistency (regular output)
        - Engagement signals (if available)
        - Completion rate (for consumption)

    The analyzer uses heuristics when detailed data is not available.
    """

    # Thresholds for quality assessment
    MIN_CONTENT_LENGTH = 100  # characters
    IDEAL_CONTENT_LENGTH = 2000  # characters
    MIN_DURATION = 60  # seconds (1 minute)
    IDEAL_DURATION = 1800  # seconds (30 minutes)

    def __init__(
        self,
        content_weight: float = 0.4,
        consistency_weight: float = 0.3,
        depth_weight: float = 0.3,
    ) -> None:
        """Initialize quality analyzer.

        Args:
            content_weight: Weight for content-based score
            consistency_weight: Weight for consistency score
            depth_weight: Weight for depth/engagement score
        """
        self.content_weight = content_weight
        self.consistency_weight = consistency_weight
        self.depth_weight = depth_weight

    def compute(self, activities: list["Activity"]) -> float:
        """Compute overall quality score for activities.

        Args:
            activities: List of activities to analyze

        Returns:
            Quality score from 0.00 to 1.00
        """
        if not activities:
            return 0.0

        # Calculate component scores
        content_score = self._compute_content_score(activities)
        consistency_score = self._compute_consistency_score(activities)
        depth_score = self._compute_depth_score(activities)

        # Weighted average
        quality = (
            content_score * self.content_weight
            + consistency_score * self.consistency_weight
            + depth_score * self.depth_weight
        )

        return clamp(quality, 0.0, 1.0)

    def compute_for_activity(self, activity: "Activity") -> float:
        """Compute quality score for a single activity.

        Args:
            activity: Activity to analyze

        Returns:
            Quality score from 0.00 to 1.00
        """
        scores = []

        # Content length score
        if activity.content:
            length = len(activity.content)
            length_score = min(1.0, length / self.IDEAL_CONTENT_LENGTH)
            scores.append(length_score)

        # Duration score
        if activity.duration_seconds:
            duration_score = min(1.0, activity.duration_seconds / self.IDEAL_DURATION)
            scores.append(duration_score)

        # Title quality (simple heuristic: length and capitalization)
        if activity.title:
            title_score = self._score_title(activity.title)
            scores.append(title_score)

        # If we have existing quality score, weight it heavily
        if activity.quality_score is not None:
            return activity.quality_score

        if not scores:
            return 0.5  # Default for activities with no measurable content

        return mean(scores)

    def _compute_content_score(self, activities: list["Activity"]) -> float:
        """Compute content-based quality score."""
        if not activities:
            return 0.0

        scores = []

        for activity in activities:
            score = 0.5  # Default

            # Content length
            if activity.content:
                length = len(activity.content)
                if length >= self.IDEAL_CONTENT_LENGTH:
                    score = 1.0
                elif length >= self.MIN_CONTENT_LENGTH:
                    score = length / self.IDEAL_CONTENT_LENGTH
                else:
                    score = length / self.MIN_CONTENT_LENGTH * 0.5

            # Duration (for media content)
            elif activity.duration_seconds:
                if activity.duration_seconds >= self.IDEAL_DURATION:
                    score = 1.0
                elif activity.duration_seconds >= self.MIN_DURATION:
                    score = activity.duration_seconds / self.IDEAL_DURATION
                else:
                    score = 0.3

            scores.append(score)

        return mean(scores)

    def _compute_consistency_score(self, activities: list["Activity"]) -> float:
        """Compute consistency score based on activity regularity."""
        if len(activities) < 2:
            return 0.5  # Not enough data

        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)

        # Calculate gaps between activities
        gaps = []
        for i in range(1, len(sorted_activities)):
            gap = sorted_activities[i].timestamp - sorted_activities[i - 1].timestamp
            gaps.append(gap.total_seconds() / 86400)  # Convert to days

        if not gaps:
            return 0.5

        avg_gap = mean(gaps)
        gap_std = std_dev(gaps)

        # Lower average gap = better (more frequent)
        # Lower std dev = better (more consistent)

        # Frequency score: ideal is 1-7 days between activities
        if avg_gap <= 1:
            freq_score = 1.0
        elif avg_gap <= 7:
            freq_score = 1.0 - (avg_gap - 1) / 6 * 0.3
        elif avg_gap <= 30:
            freq_score = 0.7 - (avg_gap - 7) / 23 * 0.4
        else:
            freq_score = max(0.1, 0.3 - (avg_gap - 30) / 100)

        # Regularity score: lower coefficient of variation = better
        cv = gap_std / avg_gap if avg_gap > 0 else 0
        regularity_score = max(0.0, 1.0 - cv)

        return (freq_score + regularity_score) / 2

    def _compute_depth_score(self, activities: list["Activity"]) -> float:
        """Compute depth/engagement score."""
        if not activities:
            return 0.0

        scores = []

        for activity in activities:
            # Use multiple signals for depth
            depth_signals = []

            # Content depth
            if activity.content:
                word_count = len(activity.content.split())
                if word_count >= 1000:
                    depth_signals.append(1.0)
                elif word_count >= 500:
                    depth_signals.append(0.8)
                elif word_count >= 200:
                    depth_signals.append(0.6)
                else:
                    depth_signals.append(0.4)

            # Duration depth
            if activity.duration_seconds:
                if activity.duration_seconds >= 3600:  # 1 hour+
                    depth_signals.append(1.0)
                elif activity.duration_seconds >= 1800:  # 30 min+
                    depth_signals.append(0.8)
                elif activity.duration_seconds >= 600:  # 10 min+
                    depth_signals.append(0.6)
                else:
                    depth_signals.append(0.4)

            # URL presence suggests external resource
            if activity.url:
                depth_signals.append(0.6)

            # Use existing quality if available
            if activity.quality_score is not None:
                depth_signals.append(activity.quality_score)

            if depth_signals:
                scores.append(mean(depth_signals))
            else:
                scores.append(0.5)

        return mean(scores)

    def _score_title(self, title: str) -> float:
        """Score a title based on quality heuristics."""
        if not title:
            return 0.0

        score = 0.5

        # Length: too short or too long is bad
        length = len(title)
        if 20 <= length <= 100:
            score += 0.2
        elif 10 <= length <= 150:
            score += 0.1

        # Proper capitalization
        words = title.split()
        if words and words[0][0].isupper():
            score += 0.1

        # Not all caps
        if not title.isupper():
            score += 0.1

        # Contains meaningful words (not just numbers)
        alpha_chars = sum(1 for c in title if c.isalpha())
        if alpha_chars / max(len(title), 1) > 0.5:
            score += 0.1

        return min(1.0, score)

    def get_quality_breakdown(self, activities: list["Activity"]) -> dict:
        """Get detailed breakdown of quality components.

        Args:
            activities: List of activities

        Returns:
            Dictionary with component scores
        """
        return {
            "overall": self.compute(activities),
            "content": self._compute_content_score(activities),
            "consistency": self._compute_consistency_score(activities),
            "depth": self._compute_depth_score(activities),
            "sample_size": len(activities),
        }
