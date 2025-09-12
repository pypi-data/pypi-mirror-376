"""Hydra Poster - A Python library for reliable social media posting across multiple platforms."""

__version__ = "0.1.0"

from .base import (
    MediaItem,
    PostConfig,
    PostResult,
    SocialMediaService,
    ThreadResult,
    ValidationError,
)
from .bluesky import BlueSkyPostResult, BlueSkyService, BlueSkySettings
from .exceptions import SocialMediaError
from .linkedin import LinkedInService, LinkedInSettings
from .reddit import RedditPostResult, RedditService, RedditSettings
from .twitter import TwitterService, TwitterSettings

__all__ = [
    # Base classes
    "MediaItem",
    "PostConfig",
    "PostResult",
    "SocialMediaService",
    "ThreadResult",
    "ValidationError",
    "SocialMediaError",
    # Platform services
    "TwitterService",
    "TwitterSettings",
    "BlueSkyService",
    "BlueSkySettings",
    "BlueSkyPostResult",
    "LinkedInService",
    "LinkedInSettings",
    "RedditService",
    "RedditSettings",
    "RedditPostResult",
]
