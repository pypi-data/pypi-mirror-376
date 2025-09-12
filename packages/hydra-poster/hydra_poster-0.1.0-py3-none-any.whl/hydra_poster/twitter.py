"""Twitter/X platform implementation with threading support."""

import contextlib
from dataclasses import dataclass, field
from typing import Any

import requests

from .base import (
    MediaItem,
    PostConfig,
    PostResult,
    SocialMediaService,
    ThreadResult,
    ValidationError,
)
from .exceptions import (
    MediaUploadError,
    MediaValidationError,
    PostCreationError,
    ThreadPostingError,
    TwitterError,
)
from .time_provider import TimeProvider


@dataclass
class TwitterSettings:
    """Twitter platform-specific settings."""

    max_image_count: int = 4
    max_image_size_mb: int = 5
    max_video_count: int = 1
    max_video_size_mb: int = 512
    max_characters: int = 280
    supported_image_formats: list[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "gif", "webp"]
    )
    supported_video_formats: list[str] = field(default_factory=lambda: ["mp4", "mov"])


class TwitterService(SocialMediaService):
    """Twitter/X social media service implementation."""

    def __init__(
        self,
        bearer_token: str,
        settings: TwitterSettings | None = None,
        time_provider: TimeProvider | None = None,
    ):
        """Initialize Twitter service.

        Args:
            bearer_token: Twitter API Bearer token
            settings: Optional custom settings, uses defaults if not provided
            time_provider: Optional time provider for testing
        """
        super().__init__(time_provider)
        self.bearer_token = bearer_token
        self.settings = settings or TwitterSettings()
        self.base_url = "https://api.twitter.com/2"
        self.upload_url = "https://upload.twitter.com/1.1/media"

    def _get_headers(self) -> dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

    def _get_upload_headers(self) -> dict[str, str]:
        """Get media upload request headers."""
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def validate_media(self, media: list[MediaItem]) -> None:
        """Validate media items against Twitter constraints."""
        if not media:
            return

        errors = []
        image_count = 0
        video_count = 0

        for i, item in enumerate(media):
            # Count media types
            if item.media_type == "image":
                image_count += 1
            elif item.media_type == "video":
                video_count += 1
            elif item.media_type == "document":
                errors.append(
                    ValidationError(
                        error="Twitter does not support document uploads",
                        media_type=item.media_type,
                        media_source=str(item.content)[:50],
                        item_index=str(i),
                    )
                )
                continue

            # Validate file formats
            filename = item.get_filename().lower()
            if item.media_type == "image":
                if not any(
                    filename.endswith(f".{fmt}")
                    for fmt in self.settings.supported_image_formats
                ):
                    errors.append(
                        ValidationError(
                            error=f"Unsupported image format. Supported formats: {', '.join(self.settings.supported_image_formats)}",
                            media_type=item.media_type,
                            media_source=filename,
                            item_index=str(i),
                        )
                    )
            elif item.media_type == "video" and not any(
                filename.endswith(f".{fmt}")
                for fmt in self.settings.supported_video_formats
            ):
                errors.append(
                    ValidationError(
                        error=f"Unsupported video format. Supported formats: {', '.join(self.settings.supported_video_formats)}",
                        media_type=item.media_type,
                        media_source=filename,
                        item_index=str(i),
                    )
                )

            # Validate file sizes
            try:
                file_size_mb = item.get_file_size_mb()
                if (
                    item.media_type == "image"
                    and file_size_mb > self.settings.max_image_size_mb
                ):
                    errors.append(
                        ValidationError(
                            error=f"Image file size {file_size_mb:.1f}MB exceeds {self.settings.max_image_size_mb}MB limit",
                            media_type=item.media_type,
                            media_source=item.get_filename(),
                            item_index=str(i),
                        )
                    )
                elif (
                    item.media_type == "video"
                    and file_size_mb > self.settings.max_video_size_mb
                ):
                    errors.append(
                        ValidationError(
                            error=f"Video file size {file_size_mb:.1f}MB exceeds {self.settings.max_video_size_mb}MB limit",
                            media_type=item.media_type,
                            media_source=item.get_filename(),
                            item_index=str(i),
                        )
                    )
            except Exception as e:
                errors.append(
                    ValidationError(
                        error=f"Could not determine file size: {e}",
                        media_type=item.media_type,
                        media_source=str(item.content)[:50],
                        item_index=str(i),
                    )
                )

        # Validate counts
        if image_count > self.settings.max_image_count:
            errors.append(
                ValidationError(
                    error=f"Too many images: {image_count} exceeds limit of {self.settings.max_image_count}",
                    media_type="image",
                    media_source=f"{image_count} images",
                    item_index="",
                )
            )

        if video_count > self.settings.max_video_count:
            errors.append(
                ValidationError(
                    error=f"Too many videos: {video_count} exceeds limit of {self.settings.max_video_count}",
                    media_type="video",
                    media_source=f"{video_count} videos",
                    item_index="",
                )
            )

        # Cannot mix images and videos
        if image_count > 0 and video_count > 0:
            errors.append(
                ValidationError(
                    error="Cannot mix images and videos in a single tweet",
                    media_type="mixed",
                    media_source=f"{image_count} images, {video_count} videos",
                    item_index="",
                )
            )

        if errors:
            raise MediaValidationError(errors)

    def upload_media(self, media: list[MediaItem]) -> list[str]:
        """Upload media files to Twitter and return media IDs."""
        if not media:
            return []

        media_ids = []

        try:
            for item in media:
                # Get media content as bytes
                content = item.normalized_content

                # Determine media category
                media_category = (
                    "tweet_image" if item.media_type == "image" else "tweet_video"
                )

                # Upload media
                files = {
                    "media": (item.get_filename(), content, self._get_mime_type(item))
                }
                data = {"media_category": media_category}

                response = requests.post(
                    f"{self.upload_url}/upload.json",
                    headers=self._get_upload_headers(),
                    files=files,
                    data=data,
                    timeout=60,
                )

                if response.status_code != 200:
                    raise MediaUploadError(
                        f"Failed to upload {item.get_filename()}: {response.text}"
                    )

                result = response.json()
                media_ids.append(str(result["media_id"]))

        except Exception as e:
            # Clean up any uploaded media on failure
            for media_id in media_ids:
                with contextlib.suppress(Exception):
                    self.delete_media(media_id)  # Best effort cleanup

            if isinstance(e, MediaUploadError):
                raise
            raise MediaUploadError(f"Media upload failed: {e}") from e

        return media_ids

    def delete_media(self, media_id: str) -> bool:  # noqa: ARG002
        """Delete uploaded media by ID."""
        # Note: Twitter doesn't provide a public endpoint to delete uploaded media
        # Media will be automatically cleaned up if not used in tweets
        return True

    def _get_mime_type(self, item: MediaItem) -> str:
        """Get MIME type for media item."""
        filename = item.get_filename().lower()

        if item.media_type == "image":
            if filename.endswith((".jpg", ".jpeg")):
                return "image/jpeg"
            elif filename.endswith(".png"):
                return "image/png"
            elif filename.endswith(".gif"):
                return "image/gif"
            elif filename.endswith(".webp"):
                return "image/webp"
        elif item.media_type == "video":
            if filename.endswith(".mp4"):
                return "video/mp4"
            elif filename.endswith(".mov"):
                return "video/quicktime"

        return "application/octet-stream"

    def create_tweet(
        self,
        text: str,
        media_ids: list[str] | None = None,
        reply_to_id: str | None = None,
    ) -> PostResult:
        """Create a tweet with optional media and reply-to."""
        # Validate text length
        if len(text) > self.settings.max_characters:
            raise PostCreationError(
                f"Tweet text exceeds {self.settings.max_characters} character limit ({len(text)} chars)"
            )

        payload: dict[str, Any] = {"text": text}

        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        try:
            response = requests.post(
                f"{self.base_url}/tweets",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code != 201:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        error_msg = error_data["errors"][0].get("message", error_msg)
                except Exception:
                    pass
                raise PostCreationError(f"Failed to create tweet: {error_msg}")

            result = response.json()
            tweet_id = result["data"]["id"]

            return PostResult(
                platform="twitter",
                post_id=tweet_id,
                url=f"https://twitter.com/i/status/{tweet_id}",
                media_ids=media_ids,
                metadata={
                    **{"character_count": len(text)},
                    **({"reply_to_id": reply_to_id} if reply_to_id else {}),
                },
            )

        except requests.RequestException as e:
            raise PostCreationError(f"Network error creating tweet: {e}") from e

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Post a tweet with optional media."""
        # Run validation pipeline
        if media:
            self.validate_media_pipeline(media)

        try:
            # Upload media if present
            media_ids = self.upload_media(media) if media else None

            # Create tweet
            reply_to_id = config.reply_to_id if config else None
            result = self.create_tweet(text, media_ids, reply_to_id)

            return result

        except Exception:
            # Clean up uploaded media on failure
            if media and "media_ids" in locals() and media_ids:
                for media_id in media_ids:
                    with contextlib.suppress(Exception):
                        self.delete_media(media_id)
            raise

    def delete_post(self, post_id: str) -> bool:
        """Delete a tweet by ID."""
        try:
            response = requests.delete(
                f"{self.base_url}/tweets/{post_id}",
                headers=self._get_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                # Tweet already deleted or doesn't exist
                return True
            else:
                raise TwitterError(f"Failed to delete tweet {post_id}: {response.text}")

        except requests.RequestException as e:
            raise TwitterError(f"Network error deleting tweet {post_id}: {e}") from e

    def reply_to_tweet(
        self, reply_to_id: str, text: str, media: list[MediaItem] | None = None
    ) -> PostResult:
        """Reply to a specific tweet."""
        config = PostConfig(reply_to_id=reply_to_id)
        return self.post(text, media, config)

    def validate_thread_quota_impact(self, messages: list[str]) -> None:
        """Warn about quota consumption for large threads."""
        if len(messages) > 10:
            print(
                f"Warning: {len(messages)} tweets will consume "
                f"{len(messages)}/500 of your monthly free tier quota"
            )

    def post_thread(
        self,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
        config: PostConfig | None = None,
    ) -> ThreadResult:
        """Post a series of connected tweets as a thread."""
        if not messages:
            raise ValueError("Thread must contain at least one message")

        # Warn about quota impact
        self.validate_thread_quota_impact(messages)

        # Validate each message
        errors: list[ValidationError] = []
        for i, message in enumerate(messages):
            if len(message) > self.settings.max_characters:
                errors.append(
                    ValidationError(
                        error=f"Tweet {i + 1}: Text exceeds {self.settings.max_characters} character limit ({len(message)} chars)",
                        item_index=str(i),
                        media_source=message[:50] + "...",
                    )
                )

        # Validate media for each tweet
        if media:
            for i, tweet_media in enumerate(media):
                if i >= len(messages):
                    break  # More media than messages
                try:
                    self.validate_media_pipeline(tweet_media)
                except MediaValidationError as e:
                    for error in e.errors:
                        errors.append(
                            ValidationError(
                                error=f"Tweet {i + 1}: {error['error']}",
                                item_index=str(i),
                                media_source=error.get("media_source", ""),
                                media_type=error.get("media_type", ""),
                            )
                        )

        if errors:
            from .exceptions import ThreadValidationError

            raise ThreadValidationError(errors)

        # Post the thread using the base implementation
        return super().post_thread(messages, media, rollback_on_failure, config)

    def continue_thread(
        self,
        thread_id: str,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
    ) -> ThreadResult:
        """Add more tweets to an existing thread."""
        if not messages:
            raise ValueError("Must provide messages to continue thread")

        # Find the last tweet in the thread to reply to
        # For simplicity, assume thread_id is the last tweet's ID
        # In a full implementation, you'd need to traverse the thread
        last_tweet_id = thread_id

        posted_results = []

        try:
            for i, message in enumerate(messages):
                tweet_media = media[i] if media and i < len(media) else None

                reply_config = PostConfig(reply_to_id=last_tweet_id)
                result = self.post(message, tweet_media, reply_config)
                posted_results.append(result)

                # Next tweet replies to this one
                last_tweet_id = result.post_id

        except Exception as e:
            # Handle rollback
            if rollback_on_failure and posted_results:
                failed_deletions = self._rollback_posts(posted_results)
                if failed_deletions:
                    raise ThreadPostingError(
                        f"Thread continuation failed: {e}. Failed to rollback tweets: {failed_deletions}",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
                else:
                    raise ThreadPostingError(
                        f"Thread continuation failed: {e}. All posted tweets have been rolled back.",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
            else:
                raise ThreadPostingError(
                    f"Thread continuation failed: {e}",
                    posted_count=len(posted_results),
                    rollback_attempted=False,
                ) from e

        return ThreadResult(
            platform="twitter",
            thread_id=thread_id,
            post_results=posted_results,
            thread_url=f"https://twitter.com/i/status/{thread_id}",
        )
