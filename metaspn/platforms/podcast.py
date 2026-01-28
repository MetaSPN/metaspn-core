"""Podcast platform integration for MetaSPN."""

from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from metaspn.platforms.base import BasePlatform
from metaspn.utils.stats import mean, percentile

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class PodcastPlatform(BasePlatform):
    """Platform handler for podcast content.
    
    Handles podcast episodes with:
        - Episode metadata (title, description, duration)
        - Show notes and transcripts
        - Guest information
        - Download/play metrics (when available)
    """
    
    # Typical episode durations for classification
    SHORT_EPISODE = 900     # 15 minutes
    MEDIUM_EPISODE = 2700   # 45 minutes
    LONG_EPISODE = 5400     # 90 minutes
    
    def get_platform_name(self) -> str:
        """Return platform identifier."""
        return "podcast"
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for podcast data."""
        return ["timestamp", "title"]
    
    def get_optional_fields(self) -> List[str]:
        """Get optional fields for podcast data."""
        return [
            "description",
            "content",
            "transcript",
            "duration_seconds",
            "episode_number",
            "season_number",
            "guests",
            "show_name",
            "url",
            "audio_url",
            "downloads",
            "plays",
        ]
    
    def ingest(self, data: Dict[str, Any]) -> "Activity":
        """Convert podcast data to Activity.
        
        Args:
            data: Raw podcast data with keys:
                - timestamp: Episode publish date
                - title: Episode title
                - description: Episode description (optional)
                - duration_seconds: Episode length (optional)
                - transcript: Full transcript (optional)
                - guests: List of guest names (optional)
        
        Returns:
            Activity object
        
        Raises:
            ValueError: If required fields are missing
        """
        from metaspn.core.profile import Activity
        
        if not self.validate_data(data):
            raise ValueError("Missing required fields for podcast")
        
        # Parse timestamp
        timestamp = self.parse_timestamp(data["timestamp"])
        
        # Combine description and transcript for content
        content = ""
        if data.get("description"):
            content = data["description"]
        if data.get("transcript"):
            if content:
                content += "\n\n" + data["transcript"]
            else:
                content = data["transcript"]
        if data.get("content"):
            if content:
                content += "\n\n" + data["content"]
            else:
                content = data["content"]
        
        # Build raw_data with podcast-specific fields
        raw_data = {
            "episode_number": data.get("episode_number"),
            "season_number": data.get("season_number"),
            "guests": data.get("guests", []),
            "show_name": data.get("show_name"),
            "audio_url": data.get("audio_url"),
            "downloads": data.get("downloads"),
            "plays": data.get("plays"),
        }
        
        return Activity(
            timestamp=timestamp,
            platform="podcast",
            activity_type="create",
            title=data["title"],
            content=content if content else None,
            url=data.get("url"),
            duration_seconds=data.get("duration_seconds"),
            raw_data={k: v for k, v in raw_data.items() if v is not None},
        )
    
    def compute_metrics(self, activities: List["Activity"]) -> Dict[str, Any]:
        """Compute podcast-specific metrics.
        
        Args:
            activities: List of podcast activities
        
        Returns:
            Dictionary with metrics:
                - total_episodes: Number of episodes
                - total_duration_hours: Total content hours
                - avg_duration_minutes: Average episode length
                - episodes_with_guests: Episodes featuring guests
                - episode_types: Breakdown by episode length
        """
        if not activities:
            return {
                "total_episodes": 0,
                "total_duration_hours": 0,
                "avg_duration_minutes": 0,
                "episodes_with_guests": 0,
                "episode_types": {"short": 0, "medium": 0, "long": 0},
            }
        
        # Calculate durations
        durations = []
        for a in activities:
            if a.duration_seconds:
                durations.append(a.duration_seconds)
        
        total_seconds = sum(durations) if durations else 0
        avg_seconds = mean(durations) if durations else 0
        
        # Count guests
        episodes_with_guests = sum(
            1 for a in activities
            if a.raw_data.get("guests")
        )
        
        # Classify episode types
        episode_types = {"short": 0, "medium": 0, "long": 0}
        for d in durations:
            if d < self.SHORT_EPISODE:
                episode_types["short"] += 1
            elif d < self.LONG_EPISODE:
                episode_types["medium"] += 1
            else:
                episode_types["long"] += 1
        
        return {
            "total_episodes": len(activities),
            "total_duration_hours": round(total_seconds / 3600, 1),
            "avg_duration_minutes": round(avg_seconds / 60, 1),
            "episodes_with_guests": episodes_with_guests,
            "episode_types": episode_types,
            "shortest_episode_minutes": round(min(durations) / 60, 1) if durations else 0,
            "longest_episode_minutes": round(max(durations) / 60, 1) if durations else 0,
        }
    
    def get_guest_frequency(self, activities: List["Activity"]) -> Dict[str, int]:
        """Get frequency of each guest across episodes.
        
        Args:
            activities: List of podcast activities
        
        Returns:
            Dictionary mapping guest name to appearance count
        """
        guest_counts: Dict[str, int] = {}
        
        for activity in activities:
            guests = activity.raw_data.get("guests", [])
            for guest in guests:
                guest_counts[guest] = guest_counts.get(guest, 0) + 1
        
        # Sort by frequency
        return dict(sorted(
            guest_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))
    
    def get_show_stats(self, activities: List["Activity"]) -> Dict[str, Any]:
        """Get statistics grouped by show name.
        
        Args:
            activities: List of podcast activities
        
        Returns:
            Dictionary with stats per show
        """
        shows: Dict[str, List["Activity"]] = {}
        
        for activity in activities:
            show_name = activity.raw_data.get("show_name", "Unknown Show")
            if show_name not in shows:
                shows[show_name] = []
            shows[show_name].append(activity)
        
        stats = {}
        for show_name, show_activities in shows.items():
            stats[show_name] = self.compute_metrics(show_activities)
        
        return stats
    
    def estimate_quality(self, activity: "Activity") -> float:
        """Estimate quality score for a podcast episode.
        
        Args:
            activity: Podcast activity
        
        Returns:
            Quality score 0.0-1.0
        """
        score = 0.3  # Base score
        
        # Duration quality (longer generally better for podcasts)
        if activity.duration_seconds:
            if activity.duration_seconds >= self.LONG_EPISODE:
                score += 0.3
            elif activity.duration_seconds >= self.MEDIUM_EPISODE:
                score += 0.25
            elif activity.duration_seconds >= self.SHORT_EPISODE:
                score += 0.15
        
        # Has transcript (indicates effort/accessibility)
        if activity.raw_data.get("transcript") or (
            activity.content and len(activity.content) > 1000
        ):
            score += 0.2
        
        # Has guests (indicates networking/depth)
        if activity.raw_data.get("guests"):
            score += 0.1
        
        # Has show notes/description
        if activity.content and len(activity.content) > 100:
            score += 0.1
        
        return min(1.0, score)
