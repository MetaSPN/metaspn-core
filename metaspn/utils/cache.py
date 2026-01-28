"""Caching utilities for MetaSPN."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached value with metadata."""

    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    key: str = ""

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "key": self.key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Deserialize from dictionary."""
        return cls(
            value=data["value"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            key=data.get("key", ""),
        )


class CacheManager:
    """File-based cache manager.

    Provides persistent caching with TTL support.
    """

    def __init__(
        self,
        cache_dir: str,
        default_ttl: Optional[timedelta] = None,
    ) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live for cache entries
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._memory_cache: dict[str, CacheEntry] = {}

    def _key_to_filename(self, key: str) -> str:
        """Convert cache key to safe filename."""
        hash_val = hashlib.sha256(key.encode()).hexdigest()[:16]
        safe_key = "".join(c if c.isalnum() else "_" for c in key[:32])
        return f"{safe_key}_{hash_val}.json"

    def _get_cache_path(self, key: str) -> Path:
        """Get path to cache file for key."""
        return self.cache_dir / self._key_to_filename(key)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired:
                return entry.value
            else:
                del self._memory_cache[key]

        # Check file cache
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
            entry = CacheEntry.from_dict(data)

            if entry.is_expired:
                cache_path.unlink()
                return None

            # Store in memory cache
            self._memory_cache[key] = entry
            return entry.value
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live (uses default if not specified)
        """
        if ttl is None:
            ttl = self.default_ttl

        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + ttl

        entry = CacheEntry(
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            key=key,
        )

        # Store in memory cache
        self._memory_cache[key] = entry

        # Store in file cache
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w") as f:
                json.dump(entry.to_dict(), f)
        except (OSError, TypeError):
            # If we can't write to file, at least memory cache works
            pass

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        deleted = False

        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True

        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            deleted = True

        return deleted

    def clear(self) -> int:
        """Clear all cached values.

        Returns:
            Number of entries cleared
        """
        count = len(self._memory_cache)
        self._memory_cache.clear()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

        return count

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        count = 0

        # Clean memory cache
        expired_keys = [key for key, entry in self._memory_cache.items() if entry.is_expired]
        for key in expired_keys:
            del self._memory_cache[key]
            count += 1

        # Clean file cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                entry = CacheEntry.from_dict(data)
                if entry.is_expired:
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                continue

        return count

    def stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        memory_count = len(self._memory_cache)
        file_count = len(list(self.cache_dir.glob("*.json")))

        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            "memory_entries": memory_count,
            "file_entries": file_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }


def cached_result(
    cache_key: Optional[str] = None,
    ttl: Optional[timedelta] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for caching function results.

    Uses in-memory caching within a session.

    Args:
        cache_key: Static cache key (if None, derived from function name and args)
        ttl: Time-to-live for cached result

    Example:
        >>> @cached_result(ttl=timedelta(hours=1))
        ... def expensive_computation(x):
        ...     return x ** 2
    """
    _cache: dict[str, CacheEntry] = {}

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            if cache_key:
                key = cache_key
            else:
                key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Check cache
            if key in _cache:
                entry = _cache[key]
                if not entry.is_expired:
                    return entry.value
                del _cache[key]

            # Compute and cache
            result = func(*args, **kwargs)

            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + ttl

            _cache[key] = CacheEntry(
                value=result,
                created_at=datetime.now(),
                expires_at=expires_at,
                key=key,
            )

            return result

        # Attach cache clear function
        def clear_cache() -> None:
            _cache.clear()

        wrapper.clear_cache = clear_cache  # type: ignore

        return wrapper

    return decorator
