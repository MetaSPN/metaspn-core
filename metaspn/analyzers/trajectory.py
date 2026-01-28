"""Trajectory analyzer for MetaSPN."""

from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from collections import defaultdict

from metaspn.core.metrics import Trajectory
from metaspn.utils.stats import linear_regression, mean, moving_average

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class TrajectoryAnalyzer:
    """Analyzer for computing activity trajectories over time.
    
    Trajectories show whether activity is:
        - Ascending: Increasing over time
        - Stable: Consistent level
        - Descending: Decreasing over time
    
    Analysis is based on activity frequency and quality trends.
    """
    
    # Slope thresholds for direction classification
    ASCENDING_THRESHOLD = 0.05   # 5% increase per period
    DESCENDING_THRESHOLD = -0.05  # 5% decrease per period
    
    def __init__(self, window_days: int = 30) -> None:
        """Initialize trajectory analyzer.
        
        Args:
            window_days: Default analysis window in days
        """
        self.default_window = window_days
    
    def compute(
        self,
        activities: List["Activity"],
        window_days: Optional[int] = None,
    ) -> Trajectory:
        """Compute trajectory for activities.
        
        Args:
            activities: List of activities to analyze
            window_days: Analysis window (uses default if not specified)
        
        Returns:
            Trajectory object with direction and slope
        """
        if not activities:
            return Trajectory(
                direction="stable",
                slope=0.0,
                window_days=window_days or self.default_window,
            )
        
        window = window_days or self.default_window
        
        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        
        # Get date range
        end_date = sorted_activities[-1].timestamp
        start_date = end_date - timedelta(days=window)
        
        # Filter to window
        window_activities = [
            a for a in sorted_activities
            if a.timestamp >= start_date
        ]
        
        if len(window_activities) < 3:
            # Not enough data for trend analysis
            return Trajectory(
                direction="stable",
                slope=0.0,
                window_days=window,
                start_date=start_date,
                end_date=end_date,
                data_points=len(window_activities),
            )
        
        # Compute activity frequency trend
        frequency_trend = self._compute_frequency_trend(window_activities, window)
        
        # Compute quality trend
        quality_trend = self._compute_quality_trend(window_activities)
        
        # Combine trends (frequency weighted higher)
        combined_slope = frequency_trend * 0.7 + quality_trend * 0.3
        
        # Determine direction
        if combined_slope > self.ASCENDING_THRESHOLD:
            direction = "ascending"
        elif combined_slope < self.DESCENDING_THRESHOLD:
            direction = "descending"
        else:
            direction = "stable"
        
        return Trajectory(
            direction=direction,
            slope=combined_slope,
            window_days=window,
            start_date=start_date,
            end_date=end_date,
            data_points=len(window_activities),
        )
    
    def compute_multi_window(
        self,
        activities: List["Activity"],
        windows: List[int] = [7, 30, 90],
    ) -> dict:
        """Compute trajectories for multiple time windows.
        
        Args:
            activities: List of activities
            windows: List of window sizes in days
        
        Returns:
            Dictionary mapping window size to Trajectory
        """
        results = {}
        for window in windows:
            results[window] = self.compute(activities, window)
        return results
    
    def _compute_frequency_trend(
        self,
        activities: List["Activity"],
        window_days: int,
    ) -> float:
        """Compute trend in activity frequency."""
        if len(activities) < 2:
            return 0.0
        
        # Group activities by week
        weeks: dict = defaultdict(int)
        
        for activity in activities:
            # Get week number within window
            week_num = activity.timestamp.isocalendar()[1]
            weeks[week_num] += 1
        
        if len(weeks) < 2:
            return 0.0
        
        # Linear regression on weekly counts
        sorted_weeks = sorted(weeks.keys())
        x = list(range(len(sorted_weeks)))
        y = [weeks[w] for w in sorted_weeks]
        
        slope, _ = linear_regression(x, y)
        
        # Normalize slope relative to average
        avg = mean(y)
        if avg > 0:
            normalized_slope = slope / avg
        else:
            normalized_slope = 0.0
        
        return normalized_slope
    
    def _compute_quality_trend(self, activities: List["Activity"]) -> float:
        """Compute trend in activity quality."""
        # Get quality scores
        quality_scores = []
        for activity in activities:
            if activity.quality_score is not None:
                quality_scores.append(activity.quality_score)
            else:
                # Estimate quality from content length
                if activity.content:
                    estimated = min(1.0, len(activity.content) / 2000)
                    quality_scores.append(estimated)
                elif activity.duration_seconds:
                    estimated = min(1.0, activity.duration_seconds / 1800)
                    quality_scores.append(estimated)
                else:
                    quality_scores.append(0.5)
        
        if len(quality_scores) < 3:
            return 0.0
        
        # Linear regression on quality scores
        x = list(range(len(quality_scores)))
        slope, _ = linear_regression(x, quality_scores)
        
        return slope
    
    def get_trend_description(self, trajectory: Trajectory) -> str:
        """Get human-readable description of trajectory.
        
        Args:
            trajectory: Trajectory to describe
        
        Returns:
            Description string
        """
        if trajectory.direction == "ascending":
            if trajectory.slope > 0.2:
                return "Rapidly increasing activity"
            elif trajectory.slope > 0.1:
                return "Steadily increasing activity"
            else:
                return "Slightly increasing activity"
        elif trajectory.direction == "descending":
            if trajectory.slope < -0.2:
                return "Rapidly decreasing activity"
            elif trajectory.slope < -0.1:
                return "Steadily decreasing activity"
            else:
                return "Slightly decreasing activity"
        else:
            return "Stable activity level"
    
    def predict_next_period(
        self,
        activities: List["Activity"],
        periods_ahead: int = 1,
    ) -> dict:
        """Predict activity level for future periods.
        
        Args:
            activities: Historical activities
            periods_ahead: Number of periods to predict
        
        Returns:
            Prediction with confidence
        """
        trajectory = self.compute(activities)
        
        if not activities:
            return {
                "predicted_count": 0,
                "confidence": 0.0,
                "direction": "unknown",
            }
        
        # Calculate current period activity count
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        end_date = sorted_activities[-1].timestamp
        period_start = end_date - timedelta(days=7)
        
        current_count = len([
            a for a in activities
            if a.timestamp >= period_start
        ])
        
        # Predict based on trajectory
        if trajectory.direction == "ascending":
            predicted = current_count * (1 + trajectory.slope * periods_ahead)
        elif trajectory.direction == "descending":
            predicted = current_count * (1 + trajectory.slope * periods_ahead)
            predicted = max(0, predicted)
        else:
            predicted = current_count
        
        # Confidence based on data points and slope consistency
        confidence = min(1.0, trajectory.data_points / 20) * 0.5
        if abs(trajectory.slope) < 0.1:
            confidence += 0.3  # More confident in stable trends
        
        return {
            "predicted_count": int(predicted),
            "confidence": confidence,
            "direction": trajectory.direction,
            "current_count": current_count,
        }
