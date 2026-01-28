"""Platforms module - platform-specific data ingestion and processing."""

from metaspn.platforms.base import BasePlatform
from metaspn.platforms.podcast import PodcastPlatform
from metaspn.platforms.youtube import YouTubePlatform
from metaspn.platforms.twitter import TwitterPlatform
from metaspn.platforms.blog import BlogPlatform

__all__ = [
    "BasePlatform",
    "PodcastPlatform",
    "YouTubePlatform",
    "TwitterPlatform",
    "BlogPlatform",
]
