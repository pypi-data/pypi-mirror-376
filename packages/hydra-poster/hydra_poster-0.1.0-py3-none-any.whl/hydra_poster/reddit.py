"""Reddit social media service implementation."""

import json
from dataclasses import dataclass

import requests

from .base import MediaItem, PostConfig, PostResult, SocialMediaService, ValidationError
from .exceptions import MediaValidationError, RedditError
from .time_provider import TimeProvider


@dataclass
class RedditSettings:
    """Configuration settings for Reddit posting."""

    # Post limits
    max_title_length: int = 300
    max_text_length: int = 40000


@dataclass
class RedditPostResult(PostResult):
    """Reddit-specific post result with additional metadata."""

    subreddit: str = ""
    permalink: str = ""

    def __post_init__(self) -> None:
        """Set URL from Reddit post data if not provided."""
        if not self.url and self.permalink:
            self.url = f"https://reddit.com{self.permalink}"

        # Store Reddit-specific data in metadata
        if not self.metadata:
            self.metadata = {}
        if self.subreddit:
            self.metadata["subreddit"] = self.subreddit
        if self.permalink:
            self.metadata["permalink"] = self.permalink


class RedditService(SocialMediaService):
    """Reddit social media service implementation."""

    def __init__(
        self,
        access_token: str,
        user_agent: str,
        settings: RedditSettings | None = None,
        time_provider: TimeProvider | None = None,
    ):
        """Initialize Reddit service.

        Args:
            access_token: OAuth2 access token for Reddit API
            user_agent: Unique user agent string (required by Reddit)
            settings: Optional Reddit-specific settings
            time_provider: Optional time provider for testing
        """
        super().__init__(time_provider)
        self.access_token = access_token
        self.user_agent = user_agent
        self.settings = settings or RedditSettings()
        self.base_url = "https://oauth.reddit.com"

        # Validate user agent
        if not user_agent or len(user_agent.strip()) < 10:
            raise RedditError(
                "User agent must be descriptive and unique (minimum 10 characters)"
            )

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Reddit API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": self.user_agent,
        }

    def validate_media(self, media: list[MediaItem]) -> None:
        """Validate media items for Reddit posting.

        Note: Reddit service no longer supports media uploads.
        Media validation will reject all media items.
        """
        if not media:
            return

        # Reddit service no longer supports media uploads for simplicity
        errors = [
            ValidationError(
                error="Reddit service no longer supports media uploads. Use external URLs with link posts instead.",
                media_type=item.media_type,
                media_source=str(item.content)[:50],
                item_index=str(i),
            )
            for i, item in enumerate(media)
        ]

        raise MediaValidationError(errors)

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> RedditPostResult:
        """Post text or link to Reddit.

        Args:
            text: Post content for self posts, or URL for link posts
            media: Not supported - will raise error if provided
            config: Required - must contain subreddit and title in metadata
                   - can contain 'url' in metadata for explicit link posts

        Note: If text starts with http:// or https://, it will be treated as a link post.
              Alternatively, provide 'url' in config.metadata for explicit link posts.
        """
        # Validate required config
        if not config or not config.metadata:
            raise RedditError("PostConfig with metadata is required for Reddit posts")

        subreddit_raw = config.metadata.get("subreddit")
        title_raw = config.metadata.get("title")

        if not subreddit_raw:
            raise RedditError("'subreddit' must be specified in PostConfig.metadata")
        if not title_raw:
            raise RedditError("'title' must be specified in PostConfig.metadata")

        # Ensure types are strings
        subreddit = str(subreddit_raw)
        title = str(title_raw)

        # Validate title length
        if len(title) > self.settings.max_title_length:
            raise RedditError(
                f"Title length {len(title)} exceeds maximum {self.settings.max_title_length} characters"
            )

        # Validate media - not supported
        if media:
            self.validate_media_pipeline(media)

        # Determine post type - check for explicit URL in config or URL-like text
        url_raw = config.metadata.get("url")
        url = str(url_raw) if url_raw else None
        if url or (text and text.strip().startswith(("http://", "https://"))):
            # Link post
            post_url = url or text.strip()
            if not post_url.startswith(("http://", "https://")):
                raise RedditError("URL must start with http:// or https://")

            post_kind = "link"
            post_content = post_url
        else:
            # Text post - validate text length
            if len(text) > self.settings.max_text_length:
                raise RedditError(
                    f"Text length {len(text)} exceeds maximum {self.settings.max_text_length} characters"
                )
            post_kind = "self"
            post_content = text

        try:
            # Prepare post data
            post_data = {
                "api_type": "json",
                "sr": subreddit,
                "title": title,
                "kind": post_kind,
            }

            # Add content based on post type
            if post_kind == "link":
                post_data["url"] = post_content
            else:
                post_data["text"] = post_content

            # Optional flair
            flair_id_raw = config.metadata.get("flair_id")
            if flair_id_raw:
                post_data["flair_id"] = str(flair_id_raw)

            # Submit post
            response = requests.post(
                f"{self.base_url}/api/submit",
                headers=self._get_headers(),
                data=post_data,
                timeout=30,
            )

            # Check if request was successful
            if response.status_code == 200:
                data = response.json()

                # Check for Reddit API errors
                if (
                    "json" in data
                    and "errors" in data["json"]
                    and data["json"]["errors"]
                ):
                    error_msg = "; ".join(
                        [str(error) for error in data["json"]["errors"]]
                    )
                    raise RedditError(f"Reddit API error: {error_msg}")

                # Extract post information
                if "json" in data and "data" in data["json"]:
                    post_info = data["json"]["data"]
                    post_url = post_info.get("url", "")
                    post_id = post_info.get("name", "")

                    # Convert relative URL to absolute if needed
                    if post_url and not post_url.startswith("http"):
                        post_url = f"https://reddit.com{post_url}"

                    return RedditPostResult(
                        platform="reddit",
                        post_id=post_id,
                        url=post_url,
                        subreddit=subreddit,
                        permalink=post_url.replace("https://reddit.com", "")
                        if post_url
                        else "",
                        metadata={
                            "subreddit": subreddit,
                            "title": title,
                            "post_type": post_kind,
                            "post_url": post_url,
                        },
                    )
                else:
                    raise RedditError("Unexpected response format from Reddit API")
            else:
                raise RedditError(f"Error: {response.status_code}, {response.text}")

        except requests.RequestException as e:
            raise RedditError(f"Failed to post to Reddit: {e}") from e
        except (KeyError, json.JSONDecodeError) as e:
            raise RedditError(f"Invalid response from Reddit API: {e}") from e

    def delete_post(self, post_id: str) -> bool:
        """Delete a Reddit post by ID."""
        try:
            delete_data = {
                "id": post_id,
            }

            response = requests.post(
                f"{self.base_url}/api/del",
                headers=self._get_headers(),
                data=delete_data,
                timeout=30,
            )

            if response.status_code == 200:
                return True
            else:
                raise RedditError(
                    f"Delete failed: {response.status_code}, {response.text}"
                )

        except requests.RequestException as e:
            raise RedditError(f"Failed to delete Reddit post {post_id}: {e}") from e
