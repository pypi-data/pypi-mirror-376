"""Base classes for social media posting library."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import requests

from .exceptions import MediaValidationError, ThreadPostingError
from .time_provider import RealTimeProvider, TimeProvider


class MediaValidator:
    """Stateless media validator using flyweight pattern for performance."""

    @staticmethod
    def validate_structure(item: "MediaItem") -> list["ValidationError"]:
        """Validate MediaItem structure without creating objects."""
        errors: list[ValidationError] = []

        if not item.media_type:
            errors.append(
                ValidationError(
                    error="media_type is required",
                    media_type="",
                    media_source=str(item.content)[:50],
                )
            )
        elif item.media_type not in ["image", "video", "document"]:
            errors.append(
                ValidationError(
                    error=f"Invalid media_type: {item.media_type}. Must be 'image', 'video', or 'document'",
                    media_type=item.media_type,
                    media_source=str(item.content)[:50],
                )
            )

        if item.is_bytes() and not item.filename:
            errors.append(
                ValidationError(
                    error="filename is required when content is bytes",
                    media_type=item.media_type,
                    media_source="<bytes data>",
                )
            )

        return errors

    @staticmethod
    def validate_accessibility(item: "MediaItem") -> list["ValidationError"]:
        """Validate media accessibility without caching failures."""
        try:
            # Force content normalization to test accessibility
            _ = item.normalized_content
            return []
        except MediaValidationError as e:
            return e.errors


# Global validator instance (flyweight pattern)
_media_validator = MediaValidator()


class ValidationError(TypedDict, total=False):
    """Structure for validation error information."""

    error: str
    item_index: str
    media_source: str
    media_type: str


@dataclass
class PostConfig:
    """Platform-agnostic post configuration."""

    reply_to_id: str | None = None
    scheduled_time: datetime | None = None
    visibility: str = "public"
    thread_mode: bool = False

    # Platform-specific configurations can be added to metadata
    metadata: dict[str, str | int | bool] | None = None


@dataclass
class MediaItem:
    """Represents a media item for posting."""

    content: str | bytes | os.PathLike[str]
    media_type: str
    alt_text: str | None = None
    filename: str | None = None

    def is_url(self) -> bool:
        """Check if content is a URL."""
        return isinstance(self.content, str) and self.content.startswith(
            ("http://", "https://")
        )

    def is_file_path(self) -> bool:
        """Check if content is a file path."""
        return isinstance(self.content, str | os.PathLike) and not self.is_url()

    def is_bytes(self) -> bool:
        """Check if content is raw bytes."""
        return isinstance(self.content, bytes)

    def validate_structure(self) -> None:
        """Validate MediaItem structure using flyweight validator."""
        errors = _media_validator.validate_structure(self)
        if errors:
            raise MediaValidationError(errors)

    def download_url_content(self) -> bytes:
        """Download content from URL and return bytes."""
        if not self.is_url():
            raise ValueError("Content is not a URL")

        try:
            response = requests.get(str(self.content), timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise MediaValidationError(
                [
                    {
                        "error": f"Failed to download URL {self.content!s}: {e}",
                        "media_source": str(self.content)[:100],
                        "media_type": self.media_type,
                    }
                ]
            ) from e
        except Exception as e:
            raise MediaValidationError(
                [
                    {
                        "error": f"Unexpected error downloading URL {self.content!s}: {e}",
                        "media_source": str(self.content)[:100],
                        "media_type": self.media_type,
                    }
                ]
            ) from e

    def read_file_content(self) -> bytes:
        """Read content from file path and return bytes."""
        if not self.is_file_path():
            raise ValueError("Content is not a file path")

        try:
            path = Path(str(self.content))
            if not path.exists():
                raise MediaValidationError(
                    [
                        {
                            "error": f"File does not exist: {path}",
                            "media_source": str(path),
                            "media_type": self.media_type,
                        }
                    ]
                )
            return path.read_bytes()
        except OSError as e:
            raise MediaValidationError(
                [
                    {
                        "error": f"Failed to read file {self.content!s}: {e}",
                        "media_source": str(self.content)[:100],
                        "media_type": self.media_type,
                    }
                ]
            ) from e

    @property
    def normalized_content(self) -> bytes:
        """Normalize content to bytes, downloading URLs and reading files as needed.

        Note: This method doesn't use @cached_property because we want to retry
        failed operations (network errors, file access issues, etc.) rather than
        caching failures permanently.
        """
        # Use manual caching that can be cleared on error
        if hasattr(self, "_normalized_content_cache"):
            cached: bytes = getattr(self, "_normalized_content_cache")
            return cached

        try:
            if self.is_bytes():
                result: bytes = self.content  # type: ignore[assignment]
            elif self.is_url():
                result = self.download_url_content()
            elif self.is_file_path():
                result = self.read_file_content()
            else:
                raise MediaValidationError(
                    [
                        {
                            "error": f"Unknown content type: {type(self.content)}",
                            "media_source": str(type(self.content)),
                            "media_type": self.media_type,
                        }
                    ]
                )

            # Cache successful result
            self._normalized_content_cache = result
            return result
        except MediaValidationError:
            # Don't cache failures - allow retries
            raise

    def clear_content_cache(self) -> None:
        """Clear the normalized content cache to force re-normalization."""
        if hasattr(self, "_normalized_content_cache"):
            delattr(self, "_normalized_content_cache")

    def get_file_size_mb(self) -> float:
        """Get file size in megabytes after normalization."""
        return len(self.normalized_content) / (1024 * 1024)

    def get_filename(self) -> str:
        """Get filename, inferring from URL or path if not explicitly set."""
        if self.filename:
            return self.filename
        elif self.is_url():
            return Path(str(self.content)).name or "downloaded_file"
        elif self.is_file_path():
            return Path(str(self.content)).name
        else:
            return f"content.{self.media_type}"


@dataclass
class PostResult:
    """Result of posting to a social media platform."""

    platform: str
    post_id: str
    url: str
    media_ids: list[str] | None = None
    metadata: dict[str, str | int | bool] | None = None


@dataclass
class ThreadResult:
    """Result of posting a thread to a social media platform."""

    platform: str
    thread_id: str
    post_results: list[PostResult]
    thread_url: str

    @property
    def post_count(self) -> int:
        """Number of posts in the thread."""
        return len(self.post_results)

    @property
    def last_post_id(self) -> str:
        """ID of the last post in the thread."""
        return self.post_results[-1].post_id if self.post_results else ""


class SocialMediaService(ABC):
    """Abstract base class for social media services."""

    def __init__(self, time_provider: TimeProvider | None = None) -> None:
        """Initialize service with optional time provider for testing."""
        self._time = time_provider or RealTimeProvider()

    @abstractmethod
    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Post text and optional media to the platform."""
        pass

    @abstractmethod
    def validate_media(self, media: list[MediaItem]) -> None:
        """Validate media items, raise exceptions on issues."""
        pass

    def _validate_media_structure(self, media: list[MediaItem]) -> None:
        """Validate basic MediaItem structure for all platforms."""
        errors = []

        for i, item in enumerate(media):
            try:
                item.validate_structure()
            except MediaValidationError as e:
                for error in e.errors:
                    error_with_index = error.copy()
                    error_with_index["item_index"] = str(i)
                    errors.append(error_with_index)

        if errors:
            raise MediaValidationError(errors)

    def _validate_media_accessibility(self, media: list[MediaItem]) -> None:
        """Validate that media content is accessible (URLs downloadable, files exist)."""
        errors = []

        for i, item in enumerate(media):
            try:
                # This will download URLs and read files to verify accessibility
                _ = item.normalized_content
            except MediaValidationError as e:
                for error in e.errors:
                    error_with_index = error.copy()
                    error_with_index["item_index"] = str(i)
                    errors.append(error_with_index)

        if errors:
            raise MediaValidationError(errors)

    def validate_media_pipeline(self, media: list[MediaItem]) -> None:
        """Run the complete media validation pipeline."""
        if not media:
            return

        # Phase 1: Structure validation
        self._validate_media_structure(media)

        # Phase 2: Content accessibility
        self._validate_media_accessibility(media)

        # Phase 3: Platform-specific validation (implemented by subclasses)
        self.validate_media(media)

    def post_thread(
        self,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
        config: PostConfig | None = None,
    ) -> ThreadResult:
        """Post a series of connected messages as a thread with robust rollback."""
        if not messages:
            raise ValueError("Thread must contain at least one message")

        posted_results: list[PostResult] = []

        try:
            # Post the first message (becomes thread root)
            first_result = self.post(
                messages[0], media=media[0] if media else None, config=config
            )
            posted_results.append(first_result)

            # Post subsequent messages as replies
            for i, message in enumerate(messages[1:], 1):
                reply_config = PostConfig(
                    reply_to_id=posted_results[-1].post_id,
                    thread_mode=True,
                    metadata=config.metadata if config else None,
                )

                result = self.post(
                    message,
                    media=media[i] if media and i < len(media) else None,
                    config=reply_config,
                )
                posted_results.append(result)

        except Exception as e:
            # Handle rollback on failure
            if rollback_on_failure and posted_results:
                failed_deletions = self._rollback_posts(posted_results)
                if failed_deletions:
                    raise ThreadPostingError(
                        f"Thread posting failed: {e}. Failed to rollback posts: {failed_deletions}",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
                else:
                    raise ThreadPostingError(
                        f"Thread posting failed: {e}. All posted content has been rolled back.",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
            else:
                raise ThreadPostingError(
                    f"Thread posting failed: {e}",
                    posted_count=len(posted_results),
                    rollback_attempted=False,
                ) from e

        # Success - create thread result
        return ThreadResult(
            platform=first_result.platform,
            thread_id=first_result.post_id,
            post_results=posted_results,
            thread_url=first_result.url,
        )

    def _rollback_posts(
        self, posted_results: list[PostResult], max_retries: int = 3
    ) -> list[str]:
        """Attempt to rollback posted content with retries.

        Returns list of post IDs that couldn't be deleted after all retries.
        """
        failed_deletions = []

        # Delete in reverse order (most recent first)
        for result in reversed(posted_results):
            for attempt in range(max_retries):
                try:
                    self.delete_post(result.post_id)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        failed_deletions.append(result.post_id)
                        print(f"Failed to delete post {result.post_id}: {e}")
                    else:
                        # Exponential backoff before retry
                        wait_time = 2**attempt
                        self._time.sleep(wait_time)

        return failed_deletions

    def delete_post(self, post_id: str) -> bool:
        """Delete a post by ID. Should be implemented by platform services.

        Returns True if deletion was successful, raises exception otherwise.
        """
        raise NotImplementedError("Platform services must implement delete_post()")
