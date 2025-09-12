"""Test cases for Bluesky service implementation."""

from unittest.mock import Mock, patch

import pytest

from hydra_poster.base import MediaItem
from hydra_poster.bluesky import (
    BlueSkyPostResult,
    BlueSkyService,
    BlueSkySettings,
)
from hydra_poster.exceptions import (
    MediaValidationError,
    PostCreationError,
    ThreadValidationError,
)


class TestBlueSkyService:
    """Test Bluesky service basic functionality."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-token"

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            service = BlueSkyService("handle", "password")
            assert isinstance(service.settings, BlueSkySettings)
            assert service.settings.max_image_count == 4
            assert service.settings.max_video_count == 1
            assert service.settings.max_characters == 300

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings."""
        settings = BlueSkySettings(max_image_count=2, max_characters=200)
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            service = BlueSkyService("handle", "password", settings)
            assert service.settings.max_image_count == 2
            assert service.settings.max_characters == 200


class TestBlueSkyPostResult:
    """Test BlueSkyPostResult dataclass functionality."""

    def test_post_init_extracts_post_id(self):
        """Test __post_init__ extracts post ID from URI."""
        result = BlueSkyPostResult(
            platform="bluesky",
            post_id="",  # Will be extracted from post_uri
            url="",  # Will be generated from author_handle and post_id
            post_uri="at://did:plc:user/app.bsky.feed.post/3k43tv4rft22g",
            post_cid="bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q",
            author_handle="test.bsky.social",
        )

        assert result.post_id == "3k43tv4rft22g"
        assert (
            result.url == "https://bsky.app/profile/test.bsky.social/post/3k43tv4rft22g"
        )

    def test_post_init_with_existing_post_id(self):
        """Test __post_init__ doesn't override existing post_id."""
        result = BlueSkyPostResult(
            platform="bluesky",
            post_id="existing_id",
            url="",  # Required parameter
            post_uri="at://did:plc:user/app.bsky.feed.post/3k43tv4rft22g",
            author_handle="test.bsky.social",
        )

        assert result.post_id == "existing_id"
        assert (
            result.url == "https://bsky.app/profile/test.bsky.social/post/existing_id"
        )


class TestBlueSkyMediaValidation:
    """Test Bluesky media validation."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"

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

    def test_validate_media_unsupported_document(self):
        """Test validation fails with unsupported document type."""
        media = [
            MediaItem(content=b"document", media_type="document", filename="test.pdf")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Bluesky does not support document uploads" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_unsupported_image_format(self):
        """Test validation fails with unsupported image format."""
        media = [MediaItem(content=b"image", media_type="image", filename="test.bmp")]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Unsupported image format" in str(exc_info.value.errors[0]["error"])

    @patch("hydra_poster.bluesky.MediaItem.get_file_size_mb")
    def test_validate_media_image_too_large(self, mock_size):
        """Test validation fails with oversized image."""
        mock_size.return_value = 2.0  # 2MB, limit is 1MB

        media = [
            MediaItem(content=b"large image", media_type="image", filename="large.jpg")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Image file size 2.0MB exceeds 1.0MB limit" in str(
            exc_info.value.errors[0]["error"]
        )

    @patch("hydra_poster.bluesky.MediaItem.get_file_size_mb")
    def test_validate_media_video_too_large(self, mock_size):
        """Test validation fails with oversized video."""
        mock_size.return_value = 60.0  # 60MB, limit is 50MB

        media = [
            MediaItem(content=b"large video", media_type="video", filename="large.mp4")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Video file size 60.0MB exceeds 50MB limit" in str(
            exc_info.value.errors[0]["error"]
        )


class TestBlueSkyPosting:
    """Test Bluesky posting functionality."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"

    @patch("hydra_poster.bluesky.requests.post")
    def test_create_post_success(self, mock_post):
        """Test successful post creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uri": "at://did:plc:test123/app.bsky.feed.post/3k43tv4rft22g",
            "cid": "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q",
        }
        mock_post.return_value = mock_response

        result = self.service.create_post("Hello Bluesky!")

        assert isinstance(result, BlueSkyPostResult)
        assert result.platform == "bluesky"
        assert (
            result.post_uri == "at://did:plc:test123/app.bsky.feed.post/3k43tv4rft22g"
        )
        assert result.post_id == "3k43tv4rft22g"
        assert result.author_handle == "test.bsky.social"
        assert "3k43tv4rft22g" in result.url

    @patch("hydra_poster.bluesky.requests.post")
    def test_create_post_with_reply(self, mock_post):
        """Test post creation as reply."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uri": "at://did:plc:test123/app.bsky.feed.post/reply123",
            "cid": "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q",
        }
        mock_post.return_value = mock_response

        result = self.service.create_post(
            "Reply text",
            reply_to_uri="at://did:plc:original/app.bsky.feed.post/original123",
            reply_to_cid="original_cid",
            root_uri="at://did:plc:root/app.bsky.feed.post/root123",
            root_cid="root_cid",
        )

        # Verify the request payload included reply info
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "reply" in payload["record"]
        assert (
            payload["record"]["reply"]["parent"]["uri"]
            == "at://did:plc:original/app.bsky.feed.post/original123"
        )
        assert (
            payload["record"]["reply"]["root"]["uri"]
            == "at://did:plc:root/app.bsky.feed.post/root123"
        )

    def test_create_post_text_too_long(self):
        """Test post creation fails with text too long."""
        long_text = "x" * 301  # Exceeds 300 character limit

        with pytest.raises(PostCreationError) as exc_info:
            self.service.create_post(long_text)

        assert "exceeds 300 character limit" in str(exc_info.value)

    @patch("hydra_poster.bluesky.requests.post")
    def test_create_post_api_error(self, mock_post):
        """Test post creation handles API errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.return_value = {"message": "Invalid request"}
        mock_post.return_value = mock_response

        with pytest.raises(PostCreationError) as exc_info:
            self.service.create_post("Hello")

        assert "Invalid request" in str(exc_info.value)

    @patch("hydra_poster.bluesky.requests.post")
    def test_delete_post_success(self, mock_post):
        """Test successful post deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.service.delete_post(
            "at://did:plc:test123/app.bsky.feed.post/3k43tv4rft22g"
        )
        assert result is True

    def test_delete_post_with_rkey_only(self):
        """Test post deletion with just rkey."""
        with patch("hydra_poster.bluesky.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.service.delete_post("3k43tv4rft22g")
            assert result is True

            # Verify correct URI was constructed
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["rkey"] == "3k43tv4rft22g"


class TestBlueSkyMediaUpload:
    """Test Bluesky media upload functionality."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"

    @patch("hydra_poster.bluesky.requests.post")
    def test_upload_media_success(self, mock_post):
        """Test successful media upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "blob": {
                "$type": "blob",
                "ref": {
                    "$link": "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q"
                },
                "mimeType": "image/jpeg",
                "size": 12345,
            }
        }
        mock_post.return_value = mock_response

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        blob_refs = self.service.upload_media(media)

        assert len(blob_refs) == 1
        assert blob_refs[0]["$type"] == "blob"

        # Verify correct upload parameters
        call_args = mock_post.call_args
        assert call_args[1]["data"] == b"fake image"
        assert call_args[1]["headers"]["Content-Type"] == "image/jpeg"

    def test_get_mime_type(self):
        """Test MIME type detection."""
        # Image types
        jpg_item = MediaItem(content=b"data", media_type="image", filename="test.jpg")
        assert self.service._get_mime_type(jpg_item) == "image/jpeg"

        png_item = MediaItem(content=b"data", media_type="image", filename="test.png")
        assert self.service._get_mime_type(png_item) == "image/png"

        gif_item = MediaItem(content=b"data", media_type="image", filename="test.gif")
        assert self.service._get_mime_type(gif_item) == "image/gif"

        webp_item = MediaItem(content=b"data", media_type="image", filename="test.webp")
        assert self.service._get_mime_type(webp_item) == "image/webp"

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


class TestBlueSkyThreading:
    """Test Bluesky threading functionality."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"

    def test_validate_thread_length(self, capsys):
        """Test thread length information for large threads."""
        messages = ["message"] * 30  # More than 25

        self.service.validate_thread_length(messages)

        captured = capsys.readouterr()
        assert "Posting 30 messages in a thread" in captured.out
        assert "Consider breaking into smaller threads" in captured.out

    def test_validate_thread_length_small_thread(self, capsys):
        """Test no information for small threads."""
        messages = ["message"] * 10

        self.service.validate_thread_length(messages)

        captured = capsys.readouterr()
        assert captured.out == ""  # No output

    def test_post_thread_validation_text_too_long(self):
        """Test thread validation fails with text too long."""
        messages = [
            "Normal message",
            "x" * 301,  # Too long
            "Another normal message",
        ]

        with pytest.raises(ThreadValidationError) as exc_info:
            self.service.post_thread(messages)

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "Post 2: Text exceeds 300 character limit" in errors[0]["error"]
        assert errors[0]["item_index"] == "1"

    @patch("hydra_poster.bluesky.BlueSkyService.validate_media_pipeline")
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
        assert "Post 1: File too large" in errors[0]["error"]

    @patch("hydra_poster.bluesky.BlueSkyService.post")
    def test_reply_to_post(self, mock_post):
        """Test reply functionality."""
        mock_post.return_value = Mock(post_id="reply_uri")

        result = self.service.reply_to_post(
            "original_uri", "original_cid", "root_uri", "root_cid", "Reply text"
        )

        # Verify post was called with correct config
        call_args = mock_post.call_args
        config = call_args[0][2]  # Third argument is config
        assert config.reply_to_id == "original_uri"
        assert config.metadata["reply_to_cid"] == "original_cid"
        assert config.metadata["root_uri"] == "root_uri"
        assert config.metadata["root_cid"] == "root_cid"


class TestBlueSkyIntegration:
    """Test Bluesky service integration scenarios."""

    def setup_method(self):
        """Set up test service."""
        with patch("hydra_poster.bluesky.BlueSkyService._authenticate"):
            self.service = BlueSkyService("test.bsky.social", "test-password")
            self.service.did = "did:plc:test123"
            self.service.session_token = "test-session-token"
            self.service.did = "did:plc:test123"

    @patch("hydra_poster.bluesky.requests.post")
    def test_post_with_media_end_to_end(self, mock_post):
        """Test complete posting workflow with media."""
        # Mock upload response
        upload_response = Mock()
        upload_response.status_code = 200
        upload_response.json.return_value = {
            "blob": {
                "$type": "blob",
                "ref": {
                    "$link": "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q"
                },
                "mimeType": "image/jpeg",
                "size": 12345,
            }
        }

        # Mock post creation response
        post_response = Mock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/app.bsky.feed.post/3k43tv4rft22g",
            "cid": "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q",
        }

        mock_post.side_effect = [upload_response, post_response]

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        result = self.service.post("Check out this image!", media=media)

        assert isinstance(result, BlueSkyPostResult)
        assert result.platform == "bluesky"
        assert (
            result.post_uri == "at://did:plc:test123/app.bsky.feed.post/3k43tv4rft22g"
        )
        assert result.post_id == "3k43tv4rft22g"

        # Verify two API calls were made
        assert mock_post.call_count == 2
