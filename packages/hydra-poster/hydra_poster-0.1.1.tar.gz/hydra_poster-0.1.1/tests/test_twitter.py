"""Test cases for Twitter service implementation."""

from unittest.mock import Mock, patch

import pytest

from hydra_poster.base import MediaItem
from hydra_poster.exceptions import (
    MediaValidationError,
    PostCreationError,
    ThreadValidationError,
)
from hydra_poster.twitter import TwitterService, TwitterSettings


class TestTwitterService:
    """Test Twitter service basic functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        service = TwitterService("token")
        assert isinstance(service.settings, TwitterSettings)
        assert service.settings.max_image_count == 4
        assert service.settings.max_video_count == 1
        assert service.settings.max_characters == 280

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings."""
        settings = TwitterSettings(max_image_count=2, max_characters=100)
        service = TwitterService("token", settings)
        assert service.settings.max_image_count == 2
        assert service.settings.max_characters == 100


class TestTwitterMediaValidation:
    """Test Twitter media validation."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    def test_validate_media_empty_list(self):
        """Test validation with empty media list."""
        self.service.validate_media([])  # Should not raise

    def test_validate_media_valid_images(self):
        """Test validation with valid images."""
        media = [
            MediaItem(
                content=b"fake image data", media_type="image", filename="test1.jpg"
            ),
            MediaItem(
                content=b"fake image data", media_type="image", filename="test2.png"
            ),
        ]
        self.service.validate_media(media)  # Should not raise

    def test_validate_media_valid_video(self):
        """Test validation with valid video."""
        media = [
            MediaItem(
                content=b"fake video data", media_type="video", filename="test.mp4"
            )
        ]
        self.service.validate_media(media)  # Should not raise

    def test_validate_media_too_many_images(self):
        """Test validation fails with too many images."""
        media = [
            MediaItem(content=b"data", media_type="image", filename=f"test{i}.jpg")
            for i in range(5)  # Max is 4
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Too many images: 5 exceeds limit of 4" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_too_many_videos(self):
        """Test validation fails with too many videos."""
        media = [
            MediaItem(content=b"data", media_type="video", filename=f"test{i}.mp4")
            for i in range(2)  # Max is 1
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Too many videos: 2 exceeds limit of 1" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_mixed_images_and_videos(self):
        """Test validation fails with mixed media types."""
        media = [
            MediaItem(content=b"image", media_type="image", filename="test.jpg"),
            MediaItem(content=b"video", media_type="video", filename="test.mp4"),
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Cannot mix images and videos" in str(exc_info.value.errors[0]["error"])

    def test_validate_media_unsupported_document(self):
        """Test validation fails with unsupported document type."""
        media = [
            MediaItem(content=b"document", media_type="document", filename="test.pdf")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Twitter does not support document uploads" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_unsupported_image_format(self):
        """Test validation fails with unsupported image format."""
        media = [MediaItem(content=b"image", media_type="image", filename="test.bmp")]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Unsupported image format" in str(exc_info.value.errors[0]["error"])

    @patch("hydra_poster.twitter.MediaItem.get_file_size_mb")
    def test_validate_media_image_too_large(self, mock_size):
        """Test validation fails with oversized image."""
        mock_size.return_value = 10.0  # 10MB, limit is 5MB

        media = [
            MediaItem(content=b"large image", media_type="image", filename="large.jpg")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Image file size 10.0MB exceeds 5MB limit" in str(
            exc_info.value.errors[0]["error"]
        )

    @patch("hydra_poster.twitter.MediaItem.get_file_size_mb")
    def test_validate_media_video_too_large(self, mock_size):
        """Test validation fails with oversized video."""
        mock_size.return_value = 600.0  # 600MB, limit is 512MB

        media = [
            MediaItem(content=b"large video", media_type="video", filename="large.mp4")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Video file size 600.0MB exceeds 512MB limit" in str(
            exc_info.value.errors[0]["error"]
        )


class TestTwitterPosting:
    """Test Twitter posting functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    @patch("hydra_poster.twitter.requests.post")
    def test_create_tweet_success(self, mock_post):
        """Test successful tweet creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "123456789"}}
        mock_post.return_value = mock_response

        result = self.service.create_tweet("Hello world!")

        assert result.platform == "twitter"
        assert result.post_id == "123456789"
        assert result.url == "https://twitter.com/i/status/123456789"
        assert result.metadata and result.metadata["character_count"] == 12

    @patch("hydra_poster.twitter.requests.post")
    def test_create_tweet_with_reply(self, mock_post):
        """Test tweet creation as reply."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "123456789"}}
        mock_post.return_value = mock_response

        result = self.service.create_tweet("Reply text", reply_to_id="987654321")

        # Verify the request payload included reply info
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["reply"]["in_reply_to_tweet_id"] == "987654321"
        assert result.metadata and result.metadata["reply_to_id"] == "987654321"

    def test_create_tweet_text_too_long(self):
        """Test tweet creation fails with text too long."""
        long_text = "x" * 281  # Exceeds 280 character limit

        with pytest.raises(PostCreationError) as exc_info:
            self.service.create_tweet(long_text)

        assert "exceeds 280 character limit" in str(exc_info.value)

    @patch("hydra_poster.twitter.requests.post")
    def test_create_tweet_api_error(self, mock_post):
        """Test tweet creation handles API errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.return_value = {"errors": [{"message": "Invalid request"}]}
        mock_post.return_value = mock_response

        with pytest.raises(PostCreationError) as exc_info:
            self.service.create_tweet("Hello")

        assert "Invalid request" in str(exc_info.value)

    @patch("hydra_poster.twitter.requests.delete")
    def test_delete_tweet_success(self, mock_delete):
        """Test successful tweet deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        result = self.service.delete_post("123456789")
        assert result is True

    @patch("hydra_poster.twitter.requests.delete")
    def test_delete_tweet_not_found(self, mock_delete):
        """Test tweet deletion when tweet doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response

        result = self.service.delete_post("123456789")
        assert result is True  # 404 considered success (already deleted)


class TestTwitterMediaUpload:
    """Test Twitter media upload functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    @patch("hydra_poster.twitter.requests.post")
    def test_upload_media_success(self, mock_post):
        """Test successful media upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"media_id": 123456789}
        mock_post.return_value = mock_response

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        media_ids = self.service.upload_media(media)

        assert media_ids == ["123456789"]

        # Verify correct upload parameters
        call_args = mock_post.call_args
        assert "media" in call_args[1]["files"]
        assert call_args[1]["data"]["media_category"] == "tweet_image"

    @patch("hydra_poster.twitter.requests.post")
    def test_upload_video_media(self, mock_post):
        """Test video media upload uses correct category."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"media_id": 123456789}
        mock_post.return_value = mock_response

        media = [
            MediaItem(content=b"fake video", media_type="video", filename="test.mp4")
        ]

        self.service.upload_media(media)

        call_args = mock_post.call_args
        assert call_args[1]["data"]["media_category"] == "tweet_video"

    @patch("hydra_poster.twitter.requests.post")
    def test_upload_media_failure_cleanup(self, mock_post):
        """Test media upload failure triggers cleanup."""
        # First upload succeeds, second fails
        responses = [
            Mock(status_code=200, **{"json.return_value": {"media_id": 111}}),
            Mock(status_code=400, text="Upload failed"),
        ]
        mock_post.side_effect = responses

        media = [
            MediaItem(content=b"image1", media_type="image", filename="test1.jpg"),
            MediaItem(content=b"image2", media_type="image", filename="test2.jpg"),
        ]

        with patch.object(self.service, "delete_media") as mock_delete:
            with pytest.raises(Exception):
                self.service.upload_media(media)

            # Verify cleanup was attempted
            mock_delete.assert_called_once_with("111")


class TestTwitterThreading:
    """Test Twitter threading functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    def test_validate_thread_quota_impact(self, capsys):
        """Test quota impact warning for large threads."""
        messages = ["message"] * 15  # More than 10

        self.service.validate_thread_quota_impact(messages)

        captured = capsys.readouterr()
        assert "15 tweets will consume 15/500" in captured.out

    def test_validate_thread_quota_impact_small_thread(self, capsys):
        """Test no warning for small threads."""
        messages = ["message"] * 5

        self.service.validate_thread_quota_impact(messages)

        captured = capsys.readouterr()
        assert captured.out == ""  # No warning

    def test_post_thread_validation_text_too_long(self):
        """Test thread validation fails with text too long."""
        messages = [
            "Normal message",
            "x" * 281,  # Too long
            "Another normal message",
        ]

        with pytest.raises(ThreadValidationError) as exc_info:
            self.service.post_thread(messages)

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "Tweet 2: Text exceeds 280 character limit" in errors[0]["error"]
        assert errors[0]["item_index"] == "1"

    @patch("hydra_poster.twitter.TwitterService.validate_media_pipeline")
    def test_post_thread_validation_media_error(self, mock_validate):
        """Test thread validation fails with media errors."""

        def selective_validate(media):
            if media:  # Only raise for non-empty media
                raise MediaValidationError(
                    [
                        {
                            "error": "File too large",
                            "media_type": "image",
                            "media_source": "large.jpg",
                        }
                    ]
                )

        mock_validate.side_effect = selective_validate

        messages = ["Message 1", "Message 2"]
        media = [
            [MediaItem(content=b"data", media_type="image", filename="large.jpg")],
            [],
        ]

        with pytest.raises(ThreadValidationError) as exc_info:
            self.service.post_thread(messages, media=media)

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "Tweet 1: File too large" in errors[0]["error"]

    @patch("hydra_poster.twitter.TwitterService.post")
    def test_reply_to_tweet(self, mock_post):
        """Test reply functionality."""
        mock_post.return_value = Mock(post_id="reply_id")

        result = self.service.reply_to_tweet("original_id", "Reply text")

        # Verify post was called with correct config
        call_args = mock_post.call_args
        config = call_args[0][2]  # Third argument is config
        assert config.reply_to_id == "original_id"


class TestTwitterIntegration:
    """Test Twitter service integration scenarios."""

    def setup_method(self):
        """Set up test service."""
        self.service = TwitterService("test-bearer-token")

    @patch("hydra_poster.twitter.requests.post")
    def test_post_with_media_end_to_end(self, mock_post):
        """Test complete posting workflow with media."""
        # Mock upload response
        upload_response = Mock()
        upload_response.status_code = 200
        upload_response.json.return_value = {"media_id": 123456789}

        # Mock tweet creation response
        tweet_response = Mock()
        tweet_response.status_code = 201
        tweet_response.json.return_value = {"data": {"id": "987654321"}}

        mock_post.side_effect = [upload_response, tweet_response]

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        result = self.service.post("Check out this image!", media=media)

        assert result.platform == "twitter"
        assert result.post_id == "987654321"
        assert result.media_ids == ["123456789"]

        # Verify two API calls were made
        assert mock_post.call_count == 2

    def test_get_mime_type(self):
        """Test MIME type detection."""
        # Image types
        jpg_item = MediaItem(content=b"data", media_type="image", filename="test.jpg")
        assert self.service._get_mime_type(jpg_item) == "image/jpeg"

        png_item = MediaItem(content=b"data", media_type="image", filename="test.png")
        assert self.service._get_mime_type(png_item) == "image/png"

        gif_item = MediaItem(content=b"data", media_type="image", filename="test.gif")
        assert self.service._get_mime_type(gif_item) == "image/gif"

        # Video types
        mp4_item = MediaItem(content=b"data", media_type="video", filename="test.mp4")
        assert self.service._get_mime_type(mp4_item) == "video/mp4"

        mov_item = MediaItem(content=b"data", media_type="video", filename="test.mov")
        assert self.service._get_mime_type(mov_item) == "video/quicktime"

        # Unknown type
        unknown_item = MediaItem(
            content=b"data", media_type="unknown", filename="test.xyz"
        )
        assert self.service._get_mime_type(unknown_item) == "application/octet-stream"
