"""Blog platform integration for MetaSPN."""

from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from metaspn.platforms.base import BasePlatform
from metaspn.utils.stats import mean, percentile

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class BlogPlatform(BasePlatform):
    """Platform handler for blog/written content.
    
    Handles blog posts with:
        - Post content and metadata
        - Word counts and reading time
        - Categories and tags
        - Publication info
    """
    
    # Word count classifications
    SHORT_POST = 500       # Quick article
    MEDIUM_POST = 1500     # Standard blog post
    LONG_POST = 3000       # In-depth article
    VERY_LONG_POST = 5000  # Comprehensive piece
    
    # Average reading speed (words per minute)
    READING_SPEED = 200
    
    def get_platform_name(self) -> str:
        """Return platform identifier."""
        return "blog"
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for blog data."""
        return ["timestamp", "title"]
    
    def get_optional_fields(self) -> List[str]:
        """Get optional fields for blog data."""
        return [
            "content",
            "excerpt",
            "word_count",
            "reading_time_minutes",
            "post_id",
            "slug",
            "author",
            "categories",
            "tags",
            "url",
            "featured_image",
            "views",
            "comments",
            "shares",
            "publication",
            "is_draft",
            "is_premium",
        ]
    
    def ingest(self, data: Dict[str, Any]) -> "Activity":
        """Convert blog data to Activity.
        
        Args:
            data: Raw blog data with keys:
                - timestamp: Post publish date
                - title: Post title
                - content: Post content (optional)
        
        Returns:
            Activity object
        """
        from metaspn.core.profile import Activity
        
        if not self.validate_data(data):
            raise ValueError("Missing required fields for blog")
        
        timestamp = self.parse_timestamp(data["timestamp"])
        
        # Get or calculate word count
        content = data.get("content", "")
        word_count = data.get("word_count")
        if not word_count and content:
            word_count = len(content.split())
        
        # Calculate reading time if not provided
        reading_time = data.get("reading_time_minutes")
        if not reading_time and word_count:
            reading_time = word_count / self.READING_SPEED
        
        # Convert reading time to seconds for duration field
        duration_seconds = None
        if reading_time:
            duration_seconds = int(reading_time * 60)
        
        # Raw data for blog-specific fields
        raw_data = {
            "post_id": data.get("post_id"),
            "slug": data.get("slug"),
            "author": data.get("author"),
            "categories": data.get("categories", []),
            "tags": data.get("tags", []),
            "featured_image": data.get("featured_image"),
            "views": data.get("views"),
            "comments": data.get("comments"),
            "shares": data.get("shares"),
            "publication": data.get("publication"),
            "is_draft": data.get("is_draft", False),
            "is_premium": data.get("is_premium", False),
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "excerpt": data.get("excerpt"),
        }
        
        return Activity(
            timestamp=timestamp,
            platform="blog",
            activity_type="create",
            title=data["title"],
            content=content if content else data.get("excerpt"),
            url=data.get("url"),
            duration_seconds=duration_seconds,
            raw_data={k: v for k, v in raw_data.items() if v is not None},
        )
    
    def compute_metrics(self, activities: List["Activity"]) -> Dict[str, Any]:
        """Compute blog-specific metrics.
        
        Args:
            activities: List of blog activities
        
        Returns:
            Dictionary with metrics
        """
        if not activities:
            return {
                "total_posts": 0,
                "total_words": 0,
                "avg_words": 0,
                "total_reading_hours": 0,
                "total_views": 0,
                "post_types": {"short": 0, "medium": 0, "long": 0, "very_long": 0},
            }
        
        # Word count stats
        word_counts = []
        for a in activities:
            wc = a.raw_data.get("word_count")
            if wc:
                word_counts.append(wc)
            elif a.content:
                word_counts.append(len(a.content.split()))
        
        total_words = sum(word_counts) if word_counts else 0
        avg_words = mean(word_counts) if word_counts else 0
        
        # Reading time
        total_reading_minutes = total_words / self.READING_SPEED
        
        # Views
        views = [a.raw_data.get("views", 0) for a in activities]
        total_views = sum(views)
        
        # Classify post types
        post_types = {"short": 0, "medium": 0, "long": 0, "very_long": 0}
        for wc in word_counts:
            if wc < self.SHORT_POST:
                post_types["short"] += 1
            elif wc < self.MEDIUM_POST:
                post_types["medium"] += 1
            elif wc < self.VERY_LONG_POST:
                post_types["long"] += 1
            else:
                post_types["very_long"] += 1
        
        # Category breakdown
        categories: Dict[str, int] = {}
        for a in activities:
            for cat in a.raw_data.get("categories", []):
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_posts": len(activities),
            "total_words": total_words,
            "avg_words": int(avg_words),
            "total_reading_hours": round(total_reading_minutes / 60, 1),
            "total_views": total_views,
            "avg_views": int(mean(views)) if views else 0,
            "post_types": post_types,
            "top_categories": dict(sorted(
                categories.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]),
        }
    
    def get_top_posts(
        self,
        activities: List["Activity"],
        metric: str = "views",
        limit: int = 10,
    ) -> List["Activity"]:
        """Get top performing posts by a metric.
        
        Args:
            activities: List of blog activities
            metric: Metric to sort by (views, comments, shares, word_count)
            limit: Number of posts to return
        
        Returns:
            List of top activities
        """
        sorted_activities = sorted(
            activities,
            key=lambda a: a.raw_data.get(metric, 0),
            reverse=True
        )
        return sorted_activities[:limit]
    
    def get_publication_breakdown(
        self,
        activities: List["Activity"],
    ) -> Dict[str, Dict[str, Any]]:
        """Get stats grouped by publication.
        
        Args:
            activities: List of blog activities
        
        Returns:
            Dictionary with stats per publication
        """
        pubs: Dict[str, List["Activity"]] = {}
        
        for activity in activities:
            pub = activity.raw_data.get("publication", "Personal Blog")
            if pub not in pubs:
                pubs[pub] = []
            pubs[pub].append(activity)
        
        stats = {}
        for pub_name, pub_activities in pubs.items():
            stats[pub_name] = self.compute_metrics(pub_activities)
        
        return stats
    
    def get_tag_usage(self, activities: List["Activity"]) -> Dict[str, int]:
        """Get frequency of tags used.
        
        Args:
            activities: List of blog activities
        
        Returns:
            Dictionary mapping tag to usage count
        """
        tags: Dict[str, int] = {}
        
        for activity in activities:
            for tag in activity.raw_data.get("tags", []):
                tag_lower = tag.lower()
                tags[tag_lower] = tags.get(tag_lower, 0) + 1
        
        return dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))
    
    def estimate_quality(self, activity: "Activity") -> float:
        """Estimate quality score for a blog post.
        
        Args:
            activity: Blog activity
        
        Returns:
            Quality score 0.0-1.0
        """
        score = 0.3  # Base score
        
        # Word count quality
        word_count = activity.raw_data.get("word_count")
        if not word_count and activity.content:
            word_count = len(activity.content.split())
        
        if word_count:
            if word_count >= self.VERY_LONG_POST:
                score += 0.3
            elif word_count >= self.LONG_POST:
                score += 0.25
            elif word_count >= self.MEDIUM_POST:
                score += 0.2
            elif word_count >= self.SHORT_POST:
                score += 0.1
        
        # Title quality
        if activity.title:
            title_length = len(activity.title)
            if 40 <= title_length <= 70:
                score += 0.1  # Good SEO range
            elif 20 <= title_length <= 100:
                score += 0.05
        
        # Has categories/tags (organized content)
        if activity.raw_data.get("categories") or activity.raw_data.get("tags"):
            score += 0.05
        
        # Has featured image
        if activity.raw_data.get("featured_image"):
            score += 0.05
        
        # Engagement signals
        views = activity.raw_data.get("views", 0)
        if views >= 10000:
            score += 0.15
        elif views >= 1000:
            score += 0.1
        elif views >= 100:
            score += 0.05
        
        # Comments (engagement)
        comments = activity.raw_data.get("comments", 0)
        if comments >= 20:
            score += 0.1
        elif comments >= 5:
            score += 0.05
        
        return min(1.0, score)
