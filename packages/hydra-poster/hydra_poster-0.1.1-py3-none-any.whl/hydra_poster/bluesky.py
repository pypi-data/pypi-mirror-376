"""Bluesky platform implementation with AT Protocol threading support."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
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
    BlueSkyError,
    MediaUploadError,
    MediaValidationError,
    PostCreationError,
    ThreadPostingError,
    ThreadValidationError,
)
from .time_provider import TimeProvider


@dataclass
class BlueSkySettings:
    """Bluesky platform-specific settings."""

    max_image_count: int = 4
    max_image_size_mb: float = 1.0
    max_video_count: int = 1
    max_video_size_mb: int = 50
    max_characters: int = 300
    supported_image_formats: list[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "gif", "webp"]
    )
    supported_video_formats: list[str] = field(default_factory=lambda: ["mp4", "mov"])


@dataclass
class BlueSkyPostResult(PostResult):
    """Extended PostResult with Bluesky-specific fields."""

    post_uri: str = ""
    post_cid: str = ""
    author_handle: str = ""

    def __post_init__(self) -> None:
        """Extract post ID from URI and generate human-readable URL."""
        if self.post_uri and not self.post_id:
            # Extract rkey from URI for post_id compatibility
            self.post_id = self.post_uri.split("/")[-1]

        if self.author_handle and self.post_id and not self.url:
            # Convert AT URI to human-readable URL
            self.url = (
                f"https://bsky.app/profile/{self.author_handle}/post/{self.post_id}"
            )

        # Store URI and CID in metadata for threading support
        if not self.metadata:
            self.metadata = {}
        if self.post_uri:
            self.metadata["post_uri"] = self.post_uri
        if self.post_cid:
            self.metadata["post_cid"] = self.post_cid


class BlueSkyService(SocialMediaService):
    """Bluesky social media service implementation."""

    def __init__(
        self,
        handle: str,
        password: str,
        settings: BlueSkySettings | None = None,
        time_provider: TimeProvider | None = None,
    ):
        """Initialize Bluesky service.

        Args:
            handle: Bluesky handle (e.g., 'user.bsky.social')
            password: App password or account password
            settings: Optional custom settings, uses defaults if not provided
            time_provider: Optional time provider for testing
        """
        super().__init__(time_provider)
        self.handle = handle
        self.password = password
        self.settings = settings or BlueSkySettings()
        self.base_url = "https://bsky.social/xrpc"
        self.session_token: str | None = None
        self.did: str | None = None

        # Authenticate on initialization
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Bluesky and get session token."""
        try:
            response = requests.post(
                f"{self.base_url}/com.atproto.server.createSession",
                json={"identifier": self.handle, "password": self.password},
                timeout=30,
            )

            if response.status_code != 200:
                raise BlueSkyError(f"Authentication failed: {response.text}")

            data = response.json()
            self.session_token = data["accessJwt"]
            self.did = data["did"]

        except requests.RequestException as e:
            raise BlueSkyError(f"Network error during authentication: {e}") from e

    def _get_headers(self) -> dict[str, str]:
        """Get API request headers with authentication."""
        if not self.session_token:
            self._authenticate()

        return {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json",
        }

    def validate_media(self, media: list[MediaItem]) -> None:
        """Validate media items against Bluesky constraints."""
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
                        error="Bluesky does not support document uploads",
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

        if errors:
            raise MediaValidationError(errors)

    def upload_media(self, media: list[MediaItem]) -> list[dict[str, Any]]:
        """Upload media files to Bluesky and return blob references."""
        if not media:
            return []

        blob_refs = []

        try:
            for item in media:
                # Get media content as bytes
                content = item.normalized_content

                # Upload blob
                response = requests.post(
                    f"{self.base_url}/com.atproto.repo.uploadBlob",
                    headers={
                        "Authorization": f"Bearer {self.session_token}",
                        "Content-Type": self._get_mime_type(item),
                    },
                    data=content,
                    timeout=60,
                )

                if response.status_code != 200:
                    raise MediaUploadError(
                        f"Failed to upload {item.get_filename()}: {response.text}"
                    )

                result = response.json()
                blob_refs.append(result["blob"])

        except Exception as e:
            if isinstance(e, MediaUploadError):
                raise
            raise MediaUploadError(f"Media upload failed: {e}") from e

        return blob_refs

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

    def create_post(
        self,
        text: str,
        blob_refs: list[dict[str, Any]] | None = None,
        reply_to_uri: str | None = None,
        reply_to_cid: str | None = None,
        root_uri: str | None = None,
        root_cid: str | None = None,
        media_items: list[MediaItem] | None = None,
    ) -> BlueSkyPostResult:
        """Create a Bluesky post with optional media and reply references."""
        # Validate text length
        if len(text) > self.settings.max_characters:
            raise PostCreationError(
                f"Post text exceeds {self.settings.max_characters} character limit ({len(text)} chars)"
            )

        # Build record payload
        record: dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(UTC).isoformat(),
        }

        # Add media embeds if present
        if blob_refs and media_items:
            images = []
            for i, blob_ref in enumerate(blob_refs):
                if i < len(media_items):
                    image_data = {
                        "alt": media_items[i].alt_text or "",
                        "image": blob_ref,
                    }
                    images.append(image_data)

            if images:
                record["embed"] = {"$type": "app.bsky.embed.images", "images": images}

        # Add reply structure if present
        if reply_to_uri and reply_to_cid:
            reply_data = {"parent": {"uri": reply_to_uri, "cid": reply_to_cid}}

            # Use root references if provided, otherwise parent is also root
            if root_uri and root_cid:
                reply_data["root"] = {"uri": root_uri, "cid": root_cid}
            else:
                reply_data["root"] = reply_data["parent"]

            record["reply"] = reply_data

        # Create the post
        payload = {
            "repo": self.did,
            "collection": "app.bsky.feed.post",
            "record": record,
        }

        try:
            response = requests.post(
                f"{self.base_url}/com.atproto.repo.createRecord",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except Exception:
                    pass
                raise PostCreationError(f"Failed to create post: {error_msg}")

            result = response.json()

            return BlueSkyPostResult(
                platform="bluesky",
                post_id="",  # Will be extracted from post_uri
                url="",  # Will be generated from author_handle and post_id
                post_uri=result["uri"],
                post_cid=result["cid"],
                author_handle=self.handle,
                metadata={
                    **{"character_count": len(text)},
                    **({"reply_to_uri": reply_to_uri} if reply_to_uri else {}),
                    **({"reply_to_cid": reply_to_cid} if reply_to_cid else {}),
                    **({"root_uri": root_uri} if root_uri else {}),
                    **({"root_cid": root_cid} if root_cid else {}),
                },
            )

        except requests.RequestException as e:
            raise PostCreationError(f"Network error creating post: {e}") from e

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Post to Bluesky with optional media."""
        # Run validation pipeline
        if media:
            self.validate_media_pipeline(media)

        try:
            # Upload media if present
            blob_refs = self.upload_media(media) if media else None

            # Extract reply information from config
            reply_to_uri = None
            reply_to_cid = None
            root_uri = None
            root_cid = None

            if config and config.reply_to_id:
                # In our system, reply_to_id might contain URI:CID format
                # For simplicity, assume it's just a URI and we need to look up CID
                # In a full implementation, you'd store both URI and CID
                reply_to_uri = config.reply_to_id
                # This is a simplification - in practice you'd need to resolve the CID
                reply_to_cid_raw = (
                    config.metadata.get("reply_to_cid") if config.metadata else None
                )
                root_uri_raw = (
                    config.metadata.get("root_uri") if config.metadata else None
                )
                root_cid_raw = (
                    config.metadata.get("root_cid") if config.metadata else None
                )

                reply_to_cid = str(reply_to_cid_raw) if reply_to_cid_raw else None
                root_uri = str(root_uri_raw) if root_uri_raw else None
                root_cid = str(root_cid_raw) if root_cid_raw else None

            # Create post
            result = self.create_post(
                text, blob_refs, reply_to_uri, reply_to_cid, root_uri, root_cid, media
            )

            return result

        except Exception:
            # Note: Bluesky doesn't require explicit cleanup of uploaded blobs
            # They will be garbage collected if not referenced
            raise

    def delete_post(self, post_id: str) -> bool:
        """Delete a post by URI."""
        try:
            # post_id might be a URI or just the rkey
            if post_id.startswith("at://"):
                post_uri = post_id
            else:
                post_uri = f"at://{self.did}/app.bsky.feed.post/{post_id}"

            # Extract rkey from URI
            rkey = post_uri.split("/")[-1]

            response = requests.post(
                f"{self.base_url}/com.atproto.repo.deleteRecord",
                headers=self._get_headers(),
                json={
                    "repo": self.did,
                    "collection": "app.bsky.feed.post",
                    "rkey": rkey,
                },
                timeout=30,
            )

            if response.status_code == 200:
                return True
            else:
                raise BlueSkyError(f"Failed to delete post {post_id}: {response.text}")

        except requests.RequestException as e:
            raise BlueSkyError(f"Network error deleting post {post_id}: {e}") from e

    def reply_to_post(
        self,
        reply_to_uri: str,
        reply_to_cid: str,
        root_uri: str,
        root_cid: str,
        text: str,
        media: list[MediaItem] | None = None,
    ) -> PostResult:
        """Reply to a specific post with proper AT Protocol references."""
        config = PostConfig(
            reply_to_id=reply_to_uri,
            metadata={
                "reply_to_cid": reply_to_cid,
                "root_uri": root_uri,
                "root_cid": root_cid,
            },
        )
        return self.post(text, media, config)

    def validate_thread_length(self, messages: list[str]) -> None:
        """Inform about thread length without strict quotas."""
        if len(messages) > 25:
            print(
                f"Info: Posting {len(messages)} messages in a thread. "
                f"Consider breaking into smaller threads for better engagement."
            )

    def post_thread(
        self,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
        config: PostConfig | None = None,
    ) -> ThreadResult:
        """Post a series of connected posts as a thread."""
        if not messages:
            raise ValueError("Thread must contain at least one message")

        # Inform about thread length
        self.validate_thread_length(messages)

        # Validate each message
        errors: list[ValidationError] = []
        for i, message in enumerate(messages):
            if len(message) > self.settings.max_characters:
                errors.append(
                    ValidationError(
                        error=f"Post {i + 1}: Text exceeds {self.settings.max_characters} character limit ({len(message)} chars)",
                        item_index=str(i),
                        media_source=message[:50] + "...",
                    )
                )

        # Validate media for each post
        if media:
            for i, post_media in enumerate(media):
                if i >= len(messages):
                    break  # More media than messages
                try:
                    self.validate_media_pipeline(post_media)
                except MediaValidationError as e:
                    for error in e.errors:
                        errors.append(
                            ValidationError(
                                error=f"Post {i + 1}: {error['error']}",
                                item_index=str(i),
                                media_source=error.get("media_source", ""),
                                media_type=error.get("media_type", ""),
                            )
                        )

        if errors:
            raise ThreadValidationError(errors)

        # Post the thread with proper AT Protocol URI/CID handling
        posted_results = []

        try:
            # Post the first message (becomes thread root)
            first_result = self.post(
                messages[0], media=media[0] if media else None, config=config
            )
            posted_results.append(first_result)

            # For Bluesky threading, we need to track URI/CID of each post
            root_uri_raw = (
                first_result.metadata.get("post_uri") if first_result.metadata else None
            )
            root_cid_raw = (
                first_result.metadata.get("post_cid") if first_result.metadata else None
            )
            root_uri = str(root_uri_raw) if root_uri_raw else None
            root_cid = str(root_cid_raw) if root_cid_raw else None

            # Post subsequent messages as replies with proper AT Protocol references
            for i, message in enumerate(messages[1:], 1):
                # Get previous post's URI and CID for parent reference
                previous_result = posted_results[-1]
                parent_uri_raw = (
                    previous_result.metadata.get("post_uri")
                    if previous_result.metadata
                    else None
                )
                parent_cid_raw = (
                    previous_result.metadata.get("post_cid")
                    if previous_result.metadata
                    else None
                )
                parent_uri = str(parent_uri_raw) if parent_uri_raw else None
                parent_cid = str(parent_cid_raw) if parent_cid_raw else None

                if not parent_uri or not parent_cid:
                    raise ThreadPostingError(
                        "Failed to get URI/CID from previous post for threading",
                        posted_count=len(posted_results),
                        rollback_attempted=False,
                    )

                # Create reply configuration with proper AT Protocol references
                reply_config = PostConfig(
                    reply_to_id=parent_uri,  # AT Protocol URI
                    thread_mode=True,
                    metadata={
                        **({"reply_to_cid": parent_cid} if parent_cid else {}),
                        **({"root_uri": root_uri} if root_uri else {}),
                        **({"root_cid": root_cid} if root_cid else {}),
                        **(config.metadata if config and config.metadata else {}),
                    },
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
                        f"Bluesky thread posting failed: {e}. Failed to rollback posts: {failed_deletions}",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
                else:
                    raise ThreadPostingError(
                        f"Bluesky thread posting failed: {e}. All posted content has been rolled back.",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
            else:
                raise ThreadPostingError(
                    f"Bluesky thread posting failed: {e}",
                    posted_count=len(posted_results),
                    rollback_attempted=False,
                ) from e

        # Success - create thread result
        first_result = posted_results[0]
        return ThreadResult(
            platform="bluesky",
            thread_id=first_result.post_id,
            post_results=posted_results,
            thread_url=first_result.url,
        )

    def continue_thread(
        self,
        thread_uri: str,
        thread_cid: str,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
    ) -> ThreadResult:
        """Add more posts to an existing thread."""
        if not messages:
            raise ValueError("Must provide messages to continue thread")

        posted_results = []

        try:
            # Start by replying to the provided thread post
            last_uri = thread_uri
            last_cid = thread_cid
            root_uri = thread_uri  # Original thread root
            root_cid = thread_cid  # Original thread root CID

            for i, message in enumerate(messages):
                post_media = media[i] if media and i < len(media) else None

                result = self.reply_to_post(
                    reply_to_uri=last_uri,
                    reply_to_cid=last_cid,
                    root_uri=root_uri,
                    root_cid=root_cid,
                    text=message,
                    media=post_media,
                )
                posted_results.append(result)

                # Next post replies to this one
                if isinstance(result, BlueSkyPostResult):
                    last_uri = result.post_uri
                    last_cid = result.post_cid
                else:
                    # Fallback if not BlueSkyPostResult
                    last_uri = f"at://{self.did}/app.bsky.feed.post/{result.post_id}"
                    last_cid = "unknown"  # Would need to fetch in real implementation

        except Exception as e:
            # Handle rollback
            if rollback_on_failure and posted_results:
                failed_deletions = self._rollback_posts(posted_results)
                if failed_deletions:
                    raise ThreadPostingError(
                        f"Thread continuation failed: {e}. Failed to rollback posts: {failed_deletions}",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
                else:
                    raise ThreadPostingError(
                        f"Thread continuation failed: {e}. All posted messages have been rolled back.",
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
            platform="bluesky",
            thread_id=thread_uri,
            post_results=posted_results,
            thread_url=f"https://bsky.app/profile/{self.handle}/post/{thread_uri.split('/')[-1]}",
        )
