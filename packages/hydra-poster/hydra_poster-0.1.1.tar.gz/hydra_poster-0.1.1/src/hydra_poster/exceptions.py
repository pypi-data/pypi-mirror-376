"""Exception hierarchy for social media posting library."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ValidationError


class SocialMediaError(Exception):
    """Base exception for all social media operations."""

    pass


class MediaValidationError(SocialMediaError):
    """Media validation failed."""

    def __init__(self, errors: list["ValidationError"]) -> None:
        """Initialize with list of validation errors."""
        self.errors = errors
        super().__init__(f"Media validation failed for {len(errors)} items")


class MediaTooLargeError(MediaValidationError):
    """Media file exceeds size limits."""

    pass


class UnsupportedMediaTypeError(MediaValidationError):
    """Media format not supported by platform."""

    pass


class MediaUploadError(SocialMediaError):
    """Failed to upload media to platform."""

    pass


class PostCreationError(SocialMediaError):
    """Failed to create post after media upload."""

    pass


class ThreadPostingError(SocialMediaError):
    """Thread posting failed."""

    def __init__(
        self, message: str, posted_count: int, rollback_attempted: bool
    ) -> None:
        """Initialize with posting details."""
        self.posted_count = posted_count
        self.rollback_attempted = rollback_attempted
        super().__init__(message)


class ThreadValidationError(SocialMediaError):
    """Thread validation failed before posting."""

    def __init__(self, errors: list["ValidationError"]) -> None:
        """Initialize with per-tweet error details."""
        self.errors = errors
        super().__init__(f"Thread validation failed for {len(errors)} posts")


# Platform-specific exceptions
class TwitterError(SocialMediaError):
    """Twitter-specific errors."""

    pass


class BlueSkyError(SocialMediaError):
    """Bluesky-specific errors."""

    pass


class LinkedInError(SocialMediaError):
    """LinkedIn-specific errors."""

    pass


class RedditError(SocialMediaError):
    """Reddit-specific errors."""

    pass


class GithubError(SocialMediaError):
    """GitHub-specific errors."""

    pass


class GhostError(SocialMediaError):
    """Ghost-specific errors."""

    pass
