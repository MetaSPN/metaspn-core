"""Impact analyzer for MetaSPN."""

from typing import List, Optional, Dict, TYPE_CHECKING
from datetime import datetime, timedelta
from collections import defaultdict

from metaspn.utils.stats import mean, percentile, clamp

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class ImpactAnalyzer:
    """Analyzer for computing impact/influence scores.
    
    Impact is measured based on:
        - Content reach (inferred from platform and type)
        - Content depth (quality signals)
        - Consistency of output
        - Cross-platform presence
        - Engagement signals (when available)
    
    Since we don't have direct engagement data in most cases,
    we use heuristics based on activity patterns.
    """
    
    # Platform impact multipliers (some platforms have wider reach)
    PLATFORM_MULTIPLIERS = {
        "podcast": 1.2,      # Podcasts tend to have dedicated listeners
        "youtube": 1.3,      # Video has broad reach
        "twitter": 1.0,      # Twitter is common
        "blog": 1.1,         # Blogs attract search traffic
    }
    
    # Activity type impact weights
    TYPE_WEIGHTS = {
        "create": 2.0,    # Creating content has higher impact
        "consume": 0.5,   # Consumption shows engagement but less impact
    }
    
    def __init__(self) -> None:
        """Initialize impact analyzer."""
        pass
    
    def compute(self, activities: List["Activity"]) -> float:
        """Compute overall impact factor for activities.
        
        Args:
            activities: List of activities to analyze
        
        Returns:
            Impact factor from 0.00 to 1.00
        """
        if not activities:
            return 0.0
        
        # Separate creation and consumption
        create_activities = [a for a in activities if a.activity_type == "create"]
        consume_activities = [a for a in activities if a.activity_type == "consume"]
        
        # Calculate component scores
        output_score = self._compute_output_score(create_activities)
        depth_score = self._compute_depth_score(create_activities)
        reach_score = self._compute_reach_score(activities)
        consistency_score = self._compute_consistency_score(create_activities)
        engagement_score = self._compute_engagement_proxy(consume_activities)
        
        # Weighted combination
        impact = (
            output_score * 0.25 +
            depth_score * 0.25 +
            reach_score * 0.20 +
            consistency_score * 0.15 +
            engagement_score * 0.15
        )
        
        return clamp(impact, 0.0, 1.0)
    
    def compute_for_activity(self, activity: "Activity") -> float:
        """Compute impact score for a single activity.
        
        Args:
            activity: Activity to analyze
        
        Returns:
            Impact score from 0.00 to 1.00
        """
        base_score = 0.3  # Base impact for any activity
        
        # Type multiplier
        type_mult = self.TYPE_WEIGHTS.get(activity.activity_type, 1.0)
        
        # Platform multiplier
        platform_mult = self.PLATFORM_MULTIPLIERS.get(activity.platform, 1.0)
        
        # Quality contribution
        quality_bonus = 0.0
        if activity.quality_score:
            quality_bonus = activity.quality_score * 0.3
        
        # Content depth contribution
        depth_bonus = 0.0
        if activity.content:
            word_count = len(activity.content.split())
            depth_bonus = min(0.2, word_count / 5000)
        elif activity.duration_seconds:
            depth_bonus = min(0.2, activity.duration_seconds / 7200)
        
        impact = (base_score + quality_bonus + depth_bonus) * type_mult * platform_mult
        return clamp(impact / 2.0, 0.0, 1.0)  # Normalize to 0-1
    
    def _compute_output_score(self, activities: List["Activity"]) -> float:
        """Compute score based on output volume."""
        if not activities:
            return 0.0
        
        count = len(activities)
        
        # Logarithmic scaling: diminishing returns after certain thresholds
        if count >= 500:
            return 1.0
        elif count >= 200:
            return 0.9
        elif count >= 100:
            return 0.8
        elif count >= 50:
            return 0.7
        elif count >= 25:
            return 0.6
        elif count >= 10:
            return 0.5
        else:
            return count / 20.0
    
    def _compute_depth_score(self, activities: List["Activity"]) -> float:
        """Compute score based on content depth."""
        if not activities:
            return 0.0
        
        depth_scores = []
        
        for activity in activities:
            score = 0.3  # Base
            
            # Content length
            if activity.content:
                word_count = len(activity.content.split())
                if word_count >= 2000:
                    score += 0.4
                elif word_count >= 1000:
                    score += 0.3
                elif word_count >= 500:
                    score += 0.2
                elif word_count >= 200:
                    score += 0.1
            
            # Duration
            if activity.duration_seconds:
                if activity.duration_seconds >= 3600:
                    score += 0.3
                elif activity.duration_seconds >= 1800:
                    score += 0.2
                elif activity.duration_seconds >= 600:
                    score += 0.1
            
            depth_scores.append(min(1.0, score))
        
        return mean(depth_scores)
    
    def _compute_reach_score(self, activities: List["Activity"]) -> float:
        """Compute score based on platform reach."""
        if not activities:
            return 0.0
        
        # Count by platform
        platform_counts: Dict[str, int] = defaultdict(int)
        for activity in activities:
            platform_counts[activity.platform] += 1
        
        # Calculate weighted reach
        weighted_counts = []
        for platform, count in platform_counts.items():
            multiplier = self.PLATFORM_MULTIPLIERS.get(platform, 1.0)
            weighted_counts.append(count * multiplier)
        
        total_weighted = sum(weighted_counts)
        
        # Multi-platform bonus
        platform_diversity = len(platform_counts)
        diversity_bonus = min(0.2, platform_diversity * 0.05)
        
        # Normalize
        if total_weighted >= 200:
            base_score = 0.8
        elif total_weighted >= 100:
            base_score = 0.6
        elif total_weighted >= 50:
            base_score = 0.4
        else:
            base_score = total_weighted / 125.0
        
        return min(1.0, base_score + diversity_bonus)
    
    def _compute_consistency_score(self, activities: List["Activity"]) -> float:
        """Compute score based on output consistency."""
        if len(activities) < 2:
            return 0.3  # Not enough data
        
        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        
        # Calculate gaps
        gaps = []
        for i in range(1, len(sorted_activities)):
            gap = (sorted_activities[i].timestamp - sorted_activities[i-1].timestamp).days
            gaps.append(gap)
        
        if not gaps:
            return 0.3
        
        avg_gap = mean(gaps)
        
        # Lower average gap = higher consistency
        if avg_gap <= 3:
            return 1.0
        elif avg_gap <= 7:
            return 0.8
        elif avg_gap <= 14:
            return 0.6
        elif avg_gap <= 30:
            return 0.4
        else:
            return max(0.1, 0.3 - (avg_gap - 30) / 100)
    
    def _compute_engagement_proxy(self, consume_activities: List["Activity"]) -> float:
        """Compute engagement proxy from consumption patterns."""
        if not consume_activities:
            return 0.5  # Neutral when no data
        
        # More consumption suggests engagement with ecosystem
        count = len(consume_activities)
        
        if count >= 100:
            return 0.9
        elif count >= 50:
            return 0.7
        elif count >= 20:
            return 0.5
        elif count >= 10:
            return 0.4
        else:
            return 0.3
    
    def get_impact_breakdown(self, activities: List["Activity"]) -> dict:
        """Get detailed breakdown of impact components.
        
        Args:
            activities: List of activities
        
        Returns:
            Dictionary with component scores
        """
        create_activities = [a for a in activities if a.activity_type == "create"]
        consume_activities = [a for a in activities if a.activity_type == "consume"]
        
        return {
            "overall": self.compute(activities),
            "output": self._compute_output_score(create_activities),
            "depth": self._compute_depth_score(create_activities),
            "reach": self._compute_reach_score(activities),
            "consistency": self._compute_consistency_score(create_activities),
            "engagement": self._compute_engagement_proxy(consume_activities),
            "create_count": len(create_activities),
            "consume_count": len(consume_activities),
        }
    
    def rank_activities_by_impact(
        self,
        activities: List["Activity"],
        top_n: int = 10,
    ) -> List[tuple]:
        """Rank activities by their individual impact.
        
        Args:
            activities: List of activities
            top_n: Number of top activities to return
        
        Returns:
            List of (activity, impact_score) tuples sorted by impact
        """
        scored = [(a, self.compute_for_activity(a)) for a in activities]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]
