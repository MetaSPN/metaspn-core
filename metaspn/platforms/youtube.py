"""YouTube platform integration for MetaSPN."""

from typing import TYPE_CHECKING, Any

from metaspn.platforms.base import BasePlatform
from metaspn.utils.stats import mean

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class YouTubePlatform(BasePlatform):
    """Platform handler for YouTube content.

    Handles YouTube videos with:
        - Video metadata (title, description, duration)
        - Engagement metrics (views, likes, comments)
        - Category and tags
        - Thumbnail information
    """

    # Video duration classifications
    SHORT_VIDEO = 60  # 1 minute (shorts territory)
    MEDIUM_VIDEO = 600  # 10 minutes
    LONG_VIDEO = 1800  # 30 minutes
    VERY_LONG_VIDEO = 3600  # 1 hour

    def get_platform_name(self) -> str:
        """Return platform identifier."""
        return "youtube"

    def get_required_fields(self) -> list[str]:
        """Get required fields for YouTube data."""
        return ["timestamp", "title"]

    def get_optional_fields(self) -> list[str]:
        """Get optional fields for YouTube data."""
        return [
            "description",
            "duration_seconds",
            "video_id",
            "channel_id",
            "channel_name",
            "views",
            "likes",
            "dislikes",
            "comments",
            "category",
            "tags",
            "thumbnail_url",
            "is_short",
            "is_live",
            "is_premiere",
        ]

    def ingest(self, data: dict[str, Any]) -> "Activity":
        """Convert YouTube data to Activity.

        Args:
            data: Raw YouTube data with keys:
                - timestamp: Video publish date
                - title: Video title
                - description: Video description (optional)
                - duration_seconds: Video length (optional)
                - video_id: YouTube video ID (optional)

        Returns:
            Activity object
        """
        from metaspn.core.profile import Activity

        if not self.validate_data(data):
            raise ValueError("Missing required fields for YouTube")

        timestamp = self.parse_timestamp(data["timestamp"])

        # Build URL from video_id if available
        url = data.get("url")
        if not url and data.get("video_id"):
            url = f"https://www.youtube.com/watch?v={data['video_id']}"

        # Raw data for YouTube-specific fields
        raw_data = {
            "video_id": data.get("video_id"),
            "channel_id": data.get("channel_id"),
            "channel_name": data.get("channel_name"),
            "views": data.get("views"),
            "likes": data.get("likes"),
            "dislikes": data.get("dislikes"),
            "comments": data.get("comments"),
            "category": data.get("category"),
            "tags": data.get("tags", []),
            "thumbnail_url": data.get("thumbnail_url"),
            "is_short": data.get("is_short", False),
            "is_live": data.get("is_live", False),
            "is_premiere": data.get("is_premiere", False),
        }

        return Activity(
            timestamp=timestamp,
            platform="youtube",
            activity_type="create",
            title=data["title"],
            content=data.get("description"),
            url=url,
            duration_seconds=data.get("duration_seconds"),
            raw_data={k: v for k, v in raw_data.items() if v is not None},
        )

    def compute_metrics(self, activities: list["Activity"]) -> dict[str, Any]:
        """Compute YouTube-specific metrics.

        Args:
            activities: List of YouTube activities

        Returns:
            Dictionary with metrics
        """
        if not activities:
            return {
                "total_videos": 0,
                "total_duration_hours": 0,
                "avg_duration_minutes": 0,
                "shorts_count": 0,
                "total_views": 0,
                "avg_views": 0,
                "video_types": {"short": 0, "medium": 0, "long": 0, "very_long": 0},
            }

        # Duration stats
        durations = [a.duration_seconds for a in activities if a.duration_seconds]
        total_seconds = sum(durations) if durations else 0
        avg_seconds = mean(durations) if durations else 0

        # Views stats
        views = [a.raw_data.get("views", 0) for a in activities]
        total_views = sum(views)
        avg_views = mean(views) if views else 0

        # Count shorts
        shorts_count = sum(1 for a in activities if a.raw_data.get("is_short"))

        # Classify video types
        video_types = {"short": 0, "medium": 0, "long": 0, "very_long": 0}
        for d in durations:
            if d < self.SHORT_VIDEO:
                video_types["short"] += 1
            elif d < self.MEDIUM_VIDEO:
                video_types["medium"] += 1
            elif d < self.VERY_LONG_VIDEO:
                video_types["long"] += 1
            else:
                video_types["very_long"] += 1

        # Engagement metrics
        likes = [a.raw_data.get("likes", 0) for a in activities]
        comments = [a.raw_data.get("comments", 0) for a in activities]

        return {
            "total_videos": len(activities),
            "total_duration_hours": round(total_seconds / 3600, 1),
            "avg_duration_minutes": round(avg_seconds / 60, 1),
            "shorts_count": shorts_count,
            "total_views": total_views,
            "avg_views": int(avg_views),
            "total_likes": sum(likes),
            "total_comments": sum(comments),
            "video_types": video_types,
        }

    def get_top_videos(
        self,
        activities: list["Activity"],
        metric: str = "views",
        limit: int = 10,
    ) -> list["Activity"]:
        """Get top performing videos by a metric.

        Args:
            activities: List of YouTube activities
            metric: Metric to sort by (views, likes, comments)
            limit: Number of videos to return

        Returns:
            List of top activities
        """
        sorted_activities = sorted(
            activities, key=lambda a: a.raw_data.get(metric, 0), reverse=True
        )
        return sorted_activities[:limit]

    def get_category_breakdown(self, activities: list["Activity"]) -> dict[str, int]:
        """Get count of videos by category.

        Args:
            activities: List of YouTube activities

        Returns:
            Dictionary mapping category to count
        """
        categories: dict[str, int] = {}

        for activity in activities:
            category = activity.raw_data.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1

        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    def estimate_quality(self, activity: "Activity") -> float:
        """Estimate quality score for a YouTube video.

        Args:
            activity: YouTube activity

        Returns:
            Quality score 0.0-1.0
        """
        score = 0.3  # Base score

        # Duration quality
        if activity.duration_seconds:
            if activity.duration_seconds >= self.LONG_VIDEO:
                score += 0.25
            elif activity.duration_seconds >= self.MEDIUM_VIDEO:
                score += 0.2
            elif activity.duration_seconds >= 180:  # 3+ minutes
                score += 0.1

        # Description quality
        if activity.content:
            desc_length = len(activity.content)
            if desc_length >= 500:
                score += 0.15
            elif desc_length >= 200:
                score += 0.1
            elif desc_length >= 50:
                score += 0.05

        # Engagement signals
        views = activity.raw_data.get("views", 0)
        likes = activity.raw_data.get("likes", 0)

        if views > 0:
            like_ratio = likes / views if views else 0
            if like_ratio >= 0.05:
                score += 0.15
            elif like_ratio >= 0.02:
                score += 0.1

        # View count bonus
        if views >= 100000:
            score += 0.15
        elif views >= 10000:
            score += 0.1
        elif views >= 1000:
            score += 0.05

        return min(1.0, score)
