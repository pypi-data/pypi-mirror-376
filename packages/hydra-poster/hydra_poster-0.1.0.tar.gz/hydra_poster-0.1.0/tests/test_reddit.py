"""Tests for Reddit social media service."""

from unittest.mock import Mock, patch

import pytest
import requests

from hydra_poster import MediaItem, PostConfig, RedditService
from hydra_poster.exceptions import MediaValidationError, RedditError


@pytest.fixture
def reddit_service():
    """Create a RedditService instance for testing."""
    return RedditService(
        access_token="test_access_token", user_agent="TestApp/1.0 by TestUser"
    )


@pytest.fixture
def mock_requests_post():
    """Mock successful requests.post for post submission."""
    with patch("hydra_poster.reddit.requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "json": {
                "errors": [],
                "data": {
                    "name": "t3_test123",
                    "url": "/r/test/comments/test123/test_post/",
                },
            }
        }
        mock_post.return_value = mock_response
        yield mock_post


class TestRedditServiceInitialization:
    """Test Reddit service initialization."""

    def test_initialization_success(self):
        """Test successful initialization."""
        service = RedditService(
            access_token="test_token", user_agent="TestApp/1.0 by TestUser"
        )

        assert service.access_token == "test_token"
        assert service.user_agent == "TestApp/1.0 by TestUser"
        assert service.base_url == "https://oauth.reddit.com"

    def test_initialization_invalid_user_agent(self):
        """Test initialization with invalid user agent."""
        with pytest.raises(RedditError, match="User agent must be descriptive"):
            RedditService(
                access_token="test_token",
                user_agent="short",  # Too short
            )

    def test_initialization_empty_user_agent(self):
        """Test initialization with empty user agent."""
        with pytest.raises(RedditError, match="User agent must be descriptive"):
            RedditService(access_token="test_token", user_agent="")


class TestRedditServiceHeaders:
    """Test Reddit service header generation."""

    def test_get_headers(self, reddit_service):
        """Test header generation."""
        headers = reddit_service._get_headers()

        expected_headers = {
            "Authorization": "Bearer test_access_token",
            "User-Agent": "TestApp/1.0 by TestUser",
        }

        assert headers == expected_headers


class TestRedditServiceMediaValidation:
    """Test Reddit service media validation."""

    def test_validate_media_empty_list(self, reddit_service):
        """Test validation with empty media list."""
        reddit_service.validate_media([])  # Should not raise

    def test_validate_media_any_item_rejected(self, reddit_service):
        """Test that any media item is rejected."""
        media = [MediaItem("test.jpg", "image")]

        with pytest.raises(MediaValidationError) as exc_info:
            reddit_service.validate_media(media)

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "Reddit service no longer supports media uploads" in errors[0]["error"]
        assert "Use external URLs with link posts instead" in errors[0]["error"]


class TestRedditServicePost:
    """Test Reddit service posting functionality."""

    def test_post_text_success(self, reddit_service, mock_requests_post):
        """Test successful text post."""
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Title"})

        result = reddit_service.post("Test content", config=config)

        assert result.platform == "reddit"
        assert result.post_id == "t3_test123"
        assert result.url == "https://reddit.com/r/test/comments/test123/test_post/"
        assert result.subreddit == "test"
        assert result.metadata["title"] == "Test Title"
        assert result.metadata["post_type"] == "self"

    def test_post_link_success(self, reddit_service, mock_requests_post):
        """Test successful link post using URL in config metadata."""
        config = PostConfig(
            metadata={
                "subreddit": "test",
                "title": "Test Link",
                "url": "https://example.com",
            }
        )

        result = reddit_service.post("Some description text", config=config)

        assert result.platform == "reddit"
        assert result.post_id == "t3_test123"
        assert result.metadata["post_type"] == "link"

        # Verify link post was submitted
        args, kwargs = mock_requests_post.call_args
        assert kwargs["data"]["kind"] == "link"
        assert kwargs["data"]["url"] == "https://example.com"

    def test_post_link_from_text_url(self, reddit_service, mock_requests_post):
        """Test successful link post by detecting URL in text."""
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Link"})

        result = reddit_service.post("https://example.com", config=config)

        assert result.platform == "reddit"
        assert result.post_id == "t3_test123"
        assert result.metadata["post_type"] == "link"

        # Verify link post was submitted
        args, kwargs = mock_requests_post.call_args
        assert kwargs["data"]["kind"] == "link"
        assert kwargs["data"]["url"] == "https://example.com"

    def test_post_missing_config(self, reddit_service):
        """Test posting without required config."""
        with pytest.raises(RedditError, match="PostConfig with metadata is required"):
            reddit_service.post("Test content")

    def test_post_missing_subreddit(self, reddit_service):
        """Test posting without subreddit."""
        config = PostConfig(metadata={"title": "Test Title"})

        with pytest.raises(RedditError, match="'subreddit' must be specified"):
            reddit_service.post("Test content", config=config)

    def test_post_missing_title(self, reddit_service):
        """Test posting without title."""
        config = PostConfig(metadata={"subreddit": "test"})

        with pytest.raises(RedditError, match="'title' must be specified"):
            reddit_service.post("Test content", config=config)

    def test_post_title_too_long(self, reddit_service):
        """Test posting with title too long."""
        long_title = "x" * 301  # Exceeds 300 character limit
        config = PostConfig(metadata={"subreddit": "test", "title": long_title})

        with pytest.raises(RedditError, match="Title length 301 exceeds maximum 300"):
            reddit_service.post("Test content", config=config)

    def test_post_text_too_long(self, reddit_service):
        """Test posting with text too long."""
        long_text = "x" * 40001  # Exceeds 40000 character limit
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Title"})

        with pytest.raises(
            RedditError, match="Text length 40001 exceeds maximum 40000"
        ):
            reddit_service.post(long_text, config=config)

    def test_post_invalid_url(self, reddit_service):
        """Test posting with invalid URL."""
        config = PostConfig(
            metadata={
                "subreddit": "test",
                "title": "Test Title",
                "url": "not-a-valid-url",
            }
        )

        with pytest.raises(
            RedditError, match="URL must start with http:// or https://"
        ):
            reddit_service.post("Some text", config=config)

    def test_post_with_media_rejected(self, reddit_service):
        """Test posting with media is rejected."""
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Title"})

        # Use bytes data to avoid base class file validation
        media = [MediaItem(b"fake image data", "image", filename="test.jpg")]

        with pytest.raises(MediaValidationError) as exc_info:
            reddit_service.post("Test content", media=media, config=config)

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "Reddit service no longer supports media uploads" in errors[0]["error"]

    def test_post_with_flair(self, reddit_service, mock_requests_post):
        """Test posting with flair."""
        config = PostConfig(
            metadata={"subreddit": "test", "title": "Test Title", "flair_id": "12345"}
        )

        reddit_service.post("Test content", config=config)

        # Verify flair was included in post data
        args, kwargs = mock_requests_post.call_args
        assert "flair_id" in kwargs["data"]
        assert kwargs["data"]["flair_id"] == "12345"

    def test_post_api_error(self, reddit_service):
        """Test posting with API error response."""
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Title"})

        with patch("hydra_poster.reddit.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "json": {"errors": [["SUBREDDIT_NOTALLOWED", "Not allowed to post"]]}
            }
            mock_post.return_value = mock_response

            with pytest.raises(RedditError, match="Reddit API error"):
                reddit_service.post("Test content", config=config)

    def test_post_network_error(self, reddit_service):
        """Test posting with network error."""
        config = PostConfig(metadata={"subreddit": "test", "title": "Test Title"})

        with patch("hydra_poster.reddit.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Network error")

            with pytest.raises(RedditError, match="Failed to post to Reddit"):
                reddit_service.post("Test content", config=config)


class TestRedditServiceDelete:
    """Test Reddit service post deletion."""

    def test_delete_post_success(self, reddit_service):
        """Test successful post deletion."""
        with patch("hydra_poster.reddit.requests.post") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            result = reddit_service.delete_post("t3_test123")

            assert result is True

            # Verify delete API call
            args, kwargs = mock_delete.call_args
            assert args[0] == "https://oauth.reddit.com/api/del"
            assert kwargs["data"]["id"] == "t3_test123"

    def test_delete_post_network_error(self, reddit_service):
        """Test post deletion with network error."""
        with patch("hydra_poster.reddit.requests.post") as mock_delete:
            mock_delete.side_effect = requests.RequestException("Network error")

            with pytest.raises(RedditError, match="Failed to delete Reddit post"):
                reddit_service.delete_post("t3_test123")


class TestRedditPostResult:
    """Test RedditPostResult functionality."""

    def test_reddit_post_result_url_generation(self):
        """Test URL generation from permalink."""
        from hydra_poster.reddit import RedditPostResult

        result = RedditPostResult(
            platform="reddit",
            post_id="t3_test123",
            url="",  # Empty, should be generated
            subreddit="test",
            permalink="/r/test/comments/test123/test_post/",
        )

        assert result.url == "https://reddit.com/r/test/comments/test123/test_post/"
        assert result.metadata and result.metadata["subreddit"] == "test"
        assert (
            result.metadata
            and result.metadata["permalink"] == "/r/test/comments/test123/test_post/"
        )

    def test_reddit_post_result_existing_url(self):
        """Test with existing URL."""
        from hydra_poster.reddit import RedditPostResult

        result = RedditPostResult(
            platform="reddit",
            post_id="t3_test123",
            url="https://existing.url",
            subreddit="test",
            permalink="/r/test/comments/test123/test_post/",
        )

        # Should keep existing URL
        assert result.url == "https://existing.url"
