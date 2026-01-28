"""Base platform interface for MetaSPN."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class BasePlatform(ABC):
    """Abstract base class for platform integrations.
    
    Each platform implementation handles:
        - Ingesting raw platform data into Activity objects
        - Computing platform-specific metrics
        - Validating platform-specific data
    
    Subclasses must implement:
        - ingest(): Convert raw data to Activity
        - compute_metrics(): Calculate platform metrics
        - get_platform_name(): Return platform identifier
    """
    
    @abstractmethod
    def ingest(self, data: Dict[str, Any]) -> "Activity":
        """Convert platform-specific data to an Activity.
        
        Args:
            data: Raw platform data dictionary
        
        Returns:
            Activity object
        
        Raises:
            ValueError: If data is invalid or missing required fields
        """
        pass
    
    @abstractmethod
    def compute_metrics(self, activities: List["Activity"]) -> Dict[str, Any]:
        """Compute platform-specific metrics from activities.
        
        Args:
            activities: List of activities for this platform
        
        Returns:
            Dictionary of platform-specific metrics
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform identifier.
        
        Returns:
            Platform name string (e.g., "podcast", "youtube")
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that data can be ingested.
        
        Args:
            data: Raw platform data to validate
        
        Returns:
            True if data is valid
        """
        required_fields = self.get_required_fields()
        return all(field in data for field in required_fields)
    
    def get_required_fields(self) -> List[str]:
        """Get list of required fields for this platform.
        
        Returns:
            List of required field names
        """
        return ["timestamp"]
    
    def get_optional_fields(self) -> List[str]:
        """Get list of optional fields for this platform.
        
        Returns:
            List of optional field names
        """
        return ["title", "content", "url"]
    
    def parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp from various formats.
        
        Args:
            timestamp: Timestamp in various formats
        
        Returns:
            datetime object
        """
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            from metaspn.utils.dates import parse_date
            return parse_date(timestamp)
        
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        
        raise ValueError(f"Cannot parse timestamp: {timestamp}")
    
    def ingest_batch(self, data_list: List[Dict[str, Any]]) -> List["Activity"]:
        """Ingest multiple data items.
        
        Args:
            data_list: List of raw platform data dictionaries
        
        Returns:
            List of Activity objects
        """
        activities = []
        for data in data_list:
            try:
                activity = self.ingest(data)
                activities.append(activity)
            except ValueError:
                # Skip invalid entries
                continue
        return activities
    
    def filter_activities(
        self,
        activities: List["Activity"],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_type: Optional[str] = None,
    ) -> List["Activity"]:
        """Filter activities by criteria.
        
        Args:
            activities: List of activities to filter
            start_date: Minimum timestamp (inclusive)
            end_date: Maximum timestamp (inclusive)
            activity_type: Filter by activity type
        
        Returns:
            Filtered list of activities
        """
        result = activities
        
        if start_date:
            result = [a for a in result if a.timestamp >= start_date]
        
        if end_date:
            result = [a for a in result if a.timestamp <= end_date]
        
        if activity_type:
            result = [a for a in result if a.activity_type == activity_type]
        
        return result


class PlatformRegistry:
    """Registry for platform implementations.
    
    Allows dynamic registration and lookup of platform handlers.
    """
    
    _platforms: Dict[str, BasePlatform] = {}
    
    @classmethod
    def register(cls, platform: BasePlatform) -> None:
        """Register a platform implementation.
        
        Args:
            platform: Platform instance to register
        """
        name = platform.get_platform_name()
        cls._platforms[name] = platform
    
    @classmethod
    def get(cls, name: str) -> Optional[BasePlatform]:
        """Get a registered platform by name.
        
        Args:
            name: Platform name
        
        Returns:
            Platform instance or None if not registered
        """
        return cls._platforms.get(name)
    
    @classmethod
    def list_platforms(cls) -> List[str]:
        """Get list of registered platform names.
        
        Returns:
            List of platform names
        """
        return list(cls._platforms.keys())
    
    @classmethod
    def ingest_for_platform(
        cls,
        platform_name: str,
        data: Dict[str, Any],
    ) -> Optional["Activity"]:
        """Ingest data using the appropriate platform.
        
        Args:
            platform_name: Name of platform to use
            data: Raw platform data
        
        Returns:
            Activity or None if platform not found
        """
        platform = cls.get(platform_name)
        if platform:
            return platform.ingest(data)
        return None
