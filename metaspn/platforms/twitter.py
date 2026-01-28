"""Twitter/X platform integration for MetaSPN."""

from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from metaspn.platforms.base import BasePlatform
from metaspn.utils.stats import mean, percentile

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class TwitterPlatform(BasePlatform):
    """Platform handler for Twitter/X content.
    
    Handles tweets with:
        - Tweet content and metadata
        - Engagement metrics (likes, retweets, replies)
        - Thread detection
        - Media attachments
    """
    
    # Tweet length classifications
    SHORT_TWEET = 100       # Quick thought
    MEDIUM_TWEET = 200      # Developed idea
    LONG_TWEET = 280        # Full-length tweet
    
    def get_platform_name(self) -> str:
        """Return platform identifier."""
        return "twitter"
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for Twitter data."""
        return ["timestamp"]
    
    def get_optional_fields(self) -> List[str]:
        """Get optional fields for Twitter data."""
        return [
            "content",
            "text",
            "tweet_id",
            "user_id",
            "username",
            "likes",
            "retweets",
            "replies",
            "quotes",
            "impressions",
            "is_reply",
            "is_retweet",
            "is_quote",
            "is_thread",
            "thread_id",
            "thread_position",
            "media",
            "hashtags",
            "mentions",
            "urls",
        ]
    
    def ingest(self, data: Dict[str, Any]) -> "Activity":
        """Convert Twitter data to Activity.
        
        Args:
            data: Raw Twitter data with keys:
                - timestamp: Tweet publish date
                - content/text: Tweet text
                - tweet_id: Tweet ID (optional)
        
        Returns:
            Activity object
        """
        from metaspn.core.profile import Activity
        
        if not self.validate_data(data):
            raise ValueError("Missing required fields for Twitter")
        
        timestamp = self.parse_timestamp(data["timestamp"])
        
        # Content can be in 'content' or 'text' field
        content = data.get("content") or data.get("text") or ""
        
        # Build URL from tweet_id and username if available
        url = data.get("url")
        if not url and data.get("tweet_id") and data.get("username"):
            url = f"https://twitter.com/{data['username']}/status/{data['tweet_id']}"
        
        # Determine activity type
        activity_type = "create"
        if data.get("is_retweet"):
            activity_type = "consume"  # Retweets are more like consumption
        
        # Use first line as title for tweets
        title = content[:100].split('\n')[0] if content else None
        
        # Raw data for Twitter-specific fields
        raw_data = {
            "tweet_id": data.get("tweet_id"),
            "user_id": data.get("user_id"),
            "username": data.get("username"),
            "likes": data.get("likes"),
            "retweets": data.get("retweets"),
            "replies": data.get("replies"),
            "quotes": data.get("quotes"),
            "impressions": data.get("impressions"),
            "is_reply": data.get("is_reply", False),
            "is_retweet": data.get("is_retweet", False),
            "is_quote": data.get("is_quote", False),
            "is_thread": data.get("is_thread", False),
            "thread_id": data.get("thread_id"),
            "thread_position": data.get("thread_position"),
            "media": data.get("media", []),
            "hashtags": data.get("hashtags", []),
            "mentions": data.get("mentions", []),
            "urls": data.get("urls", []),
        }
        
        return Activity(
            timestamp=timestamp,
            platform="twitter",
            activity_type=activity_type,
            title=title,
            content=content if content else None,
            url=url,
            raw_data={k: v for k, v in raw_data.items() if v is not None},
        )
    
    def compute_metrics(self, activities: List["Activity"]) -> Dict[str, Any]:
        """Compute Twitter-specific metrics.
        
        Args:
            activities: List of Twitter activities
        
        Returns:
            Dictionary with metrics
        """
        if not activities:
            return {
                "total_tweets": 0,
                "original_tweets": 0,
                "replies": 0,
                "retweets": 0,
                "threads": 0,
                "total_likes": 0,
                "avg_likes": 0,
                "total_engagement": 0,
            }
        
        # Count tweet types
        original = sum(1 for a in activities if not a.raw_data.get("is_reply") 
                      and not a.raw_data.get("is_retweet"))
        replies = sum(1 for a in activities if a.raw_data.get("is_reply"))
        retweets = sum(1 for a in activities if a.raw_data.get("is_retweet"))
        threads = len(set(a.raw_data.get("thread_id") for a in activities 
                        if a.raw_data.get("is_thread")))
        
        # Engagement metrics
        likes = [a.raw_data.get("likes", 0) for a in activities]
        rt_counts = [a.raw_data.get("retweets", 0) for a in activities]
        reply_counts = [a.raw_data.get("replies", 0) for a in activities]
        
        total_engagement = sum(likes) + sum(rt_counts) + sum(reply_counts)
        
        # Character counts
        char_counts = [len(a.content or "") for a in activities]
        
        return {
            "total_tweets": len(activities),
            "original_tweets": original,
            "replies": replies,
            "retweets": retweets,
            "threads": threads,
            "total_likes": sum(likes),
            "avg_likes": int(mean(likes)) if likes else 0,
            "total_retweets": sum(rt_counts),
            "total_replies_received": sum(reply_counts),
            "total_engagement": total_engagement,
            "avg_engagement": int(total_engagement / len(activities)) if activities else 0,
            "avg_tweet_length": int(mean(char_counts)) if char_counts else 0,
        }
    
    def get_top_tweets(
        self,
        activities: List["Activity"],
        metric: str = "likes",
        limit: int = 10,
    ) -> List["Activity"]:
        """Get top performing tweets by a metric.
        
        Args:
            activities: List of Twitter activities
            metric: Metric to sort by (likes, retweets, replies)
            limit: Number of tweets to return
        
        Returns:
            List of top activities
        """
        sorted_activities = sorted(
            activities,
            key=lambda a: a.raw_data.get(metric, 0),
            reverse=True
        )
        return sorted_activities[:limit]
    
    def get_hashtag_usage(self, activities: List["Activity"]) -> Dict[str, int]:
        """Get frequency of hashtags used.
        
        Args:
            activities: List of Twitter activities
        
        Returns:
            Dictionary mapping hashtag to usage count
        """
        hashtags: Dict[str, int] = {}
        
        for activity in activities:
            for tag in activity.raw_data.get("hashtags", []):
                tag_lower = tag.lower()
                hashtags[tag_lower] = hashtags.get(tag_lower, 0) + 1
        
        return dict(sorted(hashtags.items(), key=lambda x: x[1], reverse=True))
    
    def reconstruct_threads(
        self,
        activities: List["Activity"],
    ) -> Dict[str, List["Activity"]]:
        """Group activities by thread.
        
        Args:
            activities: List of Twitter activities
        
        Returns:
            Dictionary mapping thread_id to ordered list of tweets
        """
        threads: Dict[str, List["Activity"]] = {}
        
        for activity in activities:
            thread_id = activity.raw_data.get("thread_id")
            if thread_id:
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append(activity)
        
        # Sort each thread by position
        for thread_id in threads:
            threads[thread_id].sort(
                key=lambda a: a.raw_data.get("thread_position", 0)
            )
        
        return threads
    
    def estimate_quality(self, activity: "Activity") -> float:
        """Estimate quality score for a tweet.
        
        Args:
            activity: Twitter activity
        
        Returns:
            Quality score 0.0-1.0
        """
        score = 0.3  # Base score
        
        # Content length
        content_length = len(activity.content or "")
        if content_length >= self.LONG_TWEET:
            score += 0.15
        elif content_length >= self.MEDIUM_TWEET:
            score += 0.1
        elif content_length >= self.SHORT_TWEET:
            score += 0.05
        
        # Thread bonus (more effort)
        if activity.raw_data.get("is_thread"):
            score += 0.15
        
        # Original content bonus
        if not activity.raw_data.get("is_retweet"):
            score += 0.1
        
        # Engagement signals
        likes = activity.raw_data.get("likes", 0)
        retweets = activity.raw_data.get("retweets", 0)
        
        if likes >= 100:
            score += 0.15
        elif likes >= 50:
            score += 0.1
        elif likes >= 10:
            score += 0.05
        
        if retweets >= 50:
            score += 0.1
        elif retweets >= 10:
            score += 0.05
        
        # Media bonus
        if activity.raw_data.get("media"):
            score += 0.05
        
        return min(1.0, score)
