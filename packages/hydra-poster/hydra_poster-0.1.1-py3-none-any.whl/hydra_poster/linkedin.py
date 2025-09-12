"""LinkedIn platform implementation with business features."""

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
    LinkedInError,
    MediaUploadError,
    MediaValidationError,
    PostCreationError,
    ThreadPostingError,
)
from .time_provider import TimeProvider


@dataclass
class LinkedInSettings:
    """LinkedIn platform-specific settings."""

    max_image_count: int = 9
    max_image_size_mb: int = 100
    max_video_count: int = 1
    max_video_size_mb: int = 5000  # 5GB
    max_document_count: int = 1
    max_document_size_mb: int = 100
    max_characters: int = 3000  # LinkedIn allows up to 3000 characters
    supported_image_formats: list[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "gif"]
    )
    supported_video_formats: list[str] = field(
        default_factory=lambda: ["mp4", "mov", "wmv", "avi"]
    )
    supported_document_formats: list[str] = field(
        default_factory=lambda: ["pdf", "doc", "docx", "ppt", "pptx"]
    )


class LinkedInService(SocialMediaService):
    """LinkedIn social media service implementation."""

    def __init__(
        self,
        access_token: str,
        person_urn: str,
        settings: LinkedInSettings | None = None,
        time_provider: TimeProvider | None = None,
    ):
        """Initialize LinkedIn service.

        Args:
            access_token: LinkedIn OAuth 2.0 access token
            person_urn: LinkedIn person URN (e.g., 'urn:li:person:12345')
            settings: Optional custom settings, uses defaults if not provided
            time_provider: Optional time provider for testing
        """
        super().__init__(time_provider)
        self.access_token = access_token
        self.person_urn = person_urn
        self.settings = settings or LinkedInSettings()
        self.base_url = "https://api.linkedin.com/v2"

    def _get_headers(self) -> dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _get_upload_headers(self) -> dict[str, str]:
        """Get media upload request headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def validate_media(self, media: list[MediaItem]) -> None:
        """Validate media items against LinkedIn constraints."""
        if not media:
            return

        errors = []
        image_count = 0
        video_count = 0
        document_count = 0

        for i, item in enumerate(media):
            # Count media types
            if item.media_type == "image":
                image_count += 1
            elif item.media_type == "video":
                video_count += 1
            elif item.media_type == "document":
                document_count += 1
            else:
                errors.append(
                    ValidationError(
                        error=f"Unsupported media type: {item.media_type}. Supported: image, video, document",
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
            elif item.media_type == "video":
                if not any(
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
            elif item.media_type == "document" and not any(
                filename.endswith(f".{fmt}")
                for fmt in self.settings.supported_document_formats
            ):
                errors.append(
                    ValidationError(
                        error=f"Unsupported document format. Supported formats: {', '.join(self.settings.supported_document_formats)}",
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
                elif (
                    item.media_type == "document"
                    and file_size_mb > self.settings.max_document_size_mb
                ):
                    errors.append(
                        ValidationError(
                            error=f"Document file size {file_size_mb:.1f}MB exceeds {self.settings.max_document_size_mb}MB limit",
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

        if document_count > self.settings.max_document_count:
            errors.append(
                ValidationError(
                    error=f"Too many documents: {document_count} exceeds limit of {self.settings.max_document_count}",
                    media_type="document",
                    media_source=f"{document_count} documents",
                    item_index="",
                )
            )

        # Cannot mix different media types in LinkedIn
        media_types = sum(
            [
                1 if image_count > 0 else 0,
                1 if video_count > 0 else 0,
                1 if document_count > 0 else 0,
            ]
        )

        if media_types > 1:
            errors.append(
                ValidationError(
                    error="Cannot mix different media types in a LinkedIn post",
                    media_type="mixed",
                    media_source=f"Images: {image_count}, Videos: {video_count}, Documents: {document_count}",
                    item_index="",
                )
            )

        if errors:
            raise MediaValidationError(errors)

    def _register_upload(self, media_type: str, filename: str) -> dict[str, Any]:
        """Register media upload and get upload URL."""
        upload_request = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"]
                if media_type == "image"
                else ["urn:li:digitalmediaRecipe:feedshare-video"]
                if media_type == "video"
                else ["urn:li:digitalmediaRecipe:feedshare-document"],
                "owner": self.person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/assets?action=registerUpload",
                headers=self._get_headers(),
                json=upload_request,
                timeout=30,
            )

            if response.status_code != 200:
                raise MediaUploadError(
                    f"Failed to register upload for {filename}: {response.text}"
                )

            json_response = response.json()
            if not isinstance(json_response, dict):
                raise MediaUploadError(
                    f"Unexpected response format: {type(json_response)}"
                )
            return json_response

        except requests.RequestException as e:
            raise MediaUploadError(f"Network error registering upload: {e}") from e

    def upload_media(self, media: list[MediaItem]) -> list[str]:
        """Upload media files to LinkedIn and return asset URNs."""
        if not media:
            return []

        asset_urns = []

        try:
            for item in media:
                # Register upload
                upload_info = self._register_upload(
                    item.media_type, item.get_filename()
                )

                # Get upload URL and asset URN
                upload_url = upload_info["value"]["uploadMechanism"][
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
                ]["uploadUrl"]
                asset_urn = upload_info["value"]["asset"]

                # Upload content to the provided URL
                content = item.normalized_content

                upload_response = requests.put(
                    upload_url,
                    headers=self._get_upload_headers(),
                    data=content,
                    timeout=120,  # Longer timeout for large files
                )

                if upload_response.status_code not in [200, 201]:
                    raise MediaUploadError(
                        f"Failed to upload {item.get_filename()}: {upload_response.text}"
                    )

                asset_urns.append(asset_urn)

        except Exception as e:
            # LinkedIn doesn't provide a cleanup mechanism for registered uploads
            # Assets will be automatically cleaned up if not used
            if isinstance(e, MediaUploadError):
                raise
            raise MediaUploadError(f"Media upload failed: {e}") from e

        return asset_urns

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
        elif item.media_type == "video":
            if filename.endswith(".mp4"):
                return "video/mp4"
            elif filename.endswith(".mov"):
                return "video/quicktime"
            elif filename.endswith(".wmv"):
                return "video/x-ms-wmv"
            elif filename.endswith(".avi"):
                return "video/x-msvideo"
        elif item.media_type == "document":
            if filename.endswith(".pdf"):
                return "application/pdf"
            elif filename.endswith((".doc", ".docx")):
                return "application/msword"
            elif filename.endswith((".ppt", ".pptx")):
                return "application/vnd.ms-powerpoint"

        return "application/octet-stream"

    def create_post(
        self,
        text: str,
        asset_urns: list[str] | None = None,
        media_items: list[MediaItem] | None = None,
    ) -> PostResult:
        """Create a LinkedIn post with optional media."""
        # Validate text length
        if len(text) > self.settings.max_characters:
            raise PostCreationError(
                f"Post text exceeds {self.settings.max_characters} character limit ({len(text)} chars)"
            )

        # Build post payload
        share_content: dict[str, Any] = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }

        # Add media if present
        if asset_urns and media_items:
            if media_items[0].media_type == "image":
                share_content["shareMediaCategory"] = "IMAGE"
                share_content["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": item.alt_text or ""},
                        "media": asset_urn,
                        "title": {"text": item.get_filename()},
                    }
                    for asset_urn, item in zip(asset_urns, media_items, strict=False)
                ]
            elif media_items[0].media_type == "video":
                share_content["shareMediaCategory"] = "VIDEO"
                share_content["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": media_items[0].alt_text or ""},
                        "media": asset_urns[0],
                        "title": {"text": media_items[0].get_filename()},
                    }
                ]
            elif media_items[0].media_type == "document":
                share_content["shareMediaCategory"] = "ARTICLE"
                share_content["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": media_items[0].alt_text or ""},
                        "media": asset_urns[0],
                        "title": {"text": media_items[0].get_filename()},
                    }
                ]

        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        try:
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code != 201:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except Exception:
                    pass
                raise PostCreationError(f"Failed to create LinkedIn post: {error_msg}")

            result = response.json()
            post_id = result["id"]

            # Extract post ID from URN for URL construction
            post_id_clean = post_id.split(":")[-1] if ":" in post_id else post_id

            return PostResult(
                platform="linkedin",
                post_id=post_id,
                url=f"https://www.linkedin.com/feed/update/{post_id_clean}/",
                media_ids=asset_urns,
                metadata={
                    "character_count": len(text),
                    "media_category": share_content["shareMediaCategory"],
                    "author_urn": self.person_urn,
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
        """Post to LinkedIn with optional media."""
        # LinkedIn doesn't support threading/replies in the same way as Twitter
        if config and config.reply_to_id:
            raise PostCreationError(
                "LinkedIn does not support reply-to functionality for posts"
            )

        # Run validation pipeline
        if media:
            self.validate_media_pipeline(media)

        try:
            # Upload media if present
            asset_urns = self.upload_media(media) if media else None

            # Create post
            result = self.create_post(text, asset_urns, media)

            return result

        except Exception:
            # LinkedIn assets will be cleaned up automatically if not used
            raise

    def delete_post(self, post_id: str) -> bool:
        """Delete a LinkedIn post by ID."""
        try:
            # Ensure post_id is in URN format
            if not post_id.startswith("urn:"):
                post_id = f"urn:li:ugcPost:{post_id}"

            response = requests.delete(
                f"{self.base_url}/ugcPosts/{post_id}",
                headers=self._get_headers(),
                timeout=30,
            )

            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                # Post already deleted or doesn't exist
                return True
            else:
                raise LinkedInError(f"Failed to delete post {post_id}: {response.text}")

        except requests.RequestException as e:
            raise LinkedInError(f"Network error deleting post {post_id}: {e}") from e

    def post_thread(
        self,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
        config: PostConfig | None = None,
    ) -> ThreadResult:
        """Create a numbered post series (DEPRECATED - use post_series() instead).

        DEPRECATED: The method name 'post_thread' is misleading for LinkedIn since
        it doesn't create actual threads. Use post_series() instead for clarity.

        CRITICAL: LinkedIn has NO native threading functionality. This method creates
        INDEPENDENT posts with automatic numbering - they are NOT connected in any way.

        What This Actually Does:
        - Creates multiple SEPARATE LinkedIn posts
        - Adds numbering like "(1/3)", "(2/3)", "(3/3)" to indicate sequence
        - Posts appear in followers' feeds as unconnected individual posts
        - No reply chain, no thread UI, no discoverability as a group

        Platform Comparison:
        - Twitter: Creates actual reply chains (post 2 replies to post 1)
        - Bluesky: Creates AT Protocol threads with URI/CID linking
        - LinkedIn: Creates numbered but UNCONNECTED posts

        Args:
            messages: List of message texts that will become separate posts
            media: Optional media for each post (one list per message)
            rollback_on_failure: Delete all posts if any posting fails
            config: Applied to all posts (reply_to_id is IGNORED)

        Returns:
            ThreadResult containing all post results (misnomer - not a real thread)

        Example Output:
            Input: ["Hello!", "More info", "Conclusion"]
            Creates 3 SEPARATE posts visible as:
            - "(1/3) Hello!"
            - "(2/3) More info"
            - "(3/3) Conclusion"

        Warning: Method name 'post_thread' is maintained for API consistency
        but is technically incorrect for LinkedIn. Use post_series() instead.

        Deprecated: Use post_series() for more accurate method naming.
        """
        if not messages:
            raise ValueError("Thread must contain at least one message")

        # LinkedIn doesn't have native threading, so we simulate it by posting
        # individual posts with automatic numbering and delays for rate limiting
        posted_results = []

        try:
            for i, message in enumerate(messages):
                # Extract media for this specific post (if provided)
                post_media = media[i] if media and i < len(media) else None

                # Add automatic numbering for multi-post series (e.g., "(1/3)")
                # Single posts are left unnumbered to avoid unnecessary clutter
                if len(messages) > 1:
                    numbered_message = f"({i + 1}/{len(messages)}) {message}"
                else:
                    numbered_message = message

                # Post as a regular LinkedIn post (not connected to previous posts)
                result = self.post(numbered_message, post_media, config)
                posted_results.append(result)

                # Rate limiting protection: Add delay between posts (but not after the last one)
                # LinkedIn has stricter rate limits than Twitter/Bluesky
                if i < len(messages) - 1:  # Don't delay after final post
                    self._time.sleep(2)

        except Exception as e:
            # Handle rollback
            if rollback_on_failure and posted_results:
                failed_deletions = self._rollback_posts(posted_results)
                if failed_deletions:
                    raise ThreadPostingError(
                        f"LinkedIn post series failed: {e}. Failed to rollback posts: {failed_deletions}",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
                else:
                    raise ThreadPostingError(
                        f"LinkedIn post series failed: {e}. All posted content has been rolled back.",
                        posted_count=len(posted_results),
                        rollback_attempted=True,
                    ) from e
            else:
                raise ThreadPostingError(
                    f"LinkedIn post series failed: {e}",
                    posted_count=len(posted_results),
                    rollback_attempted=False,
                ) from e

        return ThreadResult(
            platform="linkedin",
            thread_id=posted_results[0].post_id if posted_results else "",
            post_results=posted_results,
            thread_url=posted_results[0].url if posted_results else "",
        )

    def post_series(
        self,
        messages: list[str],
        media: list[list[MediaItem]] | None = None,
        rollback_on_failure: bool = True,
        config: PostConfig | None = None,
    ) -> ThreadResult:
        """Create a numbered series of LinkedIn posts (preferred method).

        This is the preferred method for LinkedIn since it accurately describes
        what actually happens - creating a series of separate, numbered posts.

        LinkedIn has no native threading functionality, so this method creates
        independent posts with automatic numbering to indicate sequence.

        Behavior:
        - Each message becomes a separate, independent LinkedIn post
        - Multi-message series are automatically numbered: (1/3), (2/3), (3/3)
        - Single messages are posted without numbering
        - 2-second delays between posts to avoid rate limiting
        - Posts are NOT connected as replies (LinkedIn has no threading API)
        - Posts appear as regular LinkedIn posts, not discoverable as a series

        Args:
            messages: List of message texts to post as a numbered series
            media: Optional list of media items for each message (one list per message)
            rollback_on_failure: Whether to delete all posts if any post fails
            config: Optional post configuration (applied to all posts in series)

        Returns:
            ThreadResult with all posted results (note: misnomer for LinkedIn)

        Example:
            Input: ["Hello LinkedIn!", "This is post 2", "Final thoughts"]
            Creates 3 separate posts:
            - "(1/3) Hello LinkedIn!"
            - "(2/3) This is post 2"
            - "(3/3) Final thoughts"

        Note:
            These are completely independent posts that only appear connected
            through numbering. They are NOT threaded like Twitter replies or
            Bluesky AT Protocol threads.
        """
        return self.post_thread(messages, media, rollback_on_failure, config)
