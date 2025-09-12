"""Test cases for LinkedIn service implementation."""

from unittest.mock import Mock, patch

import pytest

from hydra_poster.base import MediaItem, PostConfig
from hydra_poster.exceptions import (
    MediaValidationError,
    PostCreationError,
)
from hydra_poster.linkedin import LinkedInService, LinkedInSettings


class TestLinkedInService:
    """Test LinkedIn service basic functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        service = LinkedInService("token", "urn:li:person:123")
        assert isinstance(service.settings, LinkedInSettings)
        assert service.settings.max_image_count == 9
        assert service.settings.max_video_count == 1
        assert service.settings.max_document_count == 1
        assert service.settings.max_characters == 3000

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings."""
        settings = LinkedInSettings(max_image_count=5, max_characters=1000)
        service = LinkedInService("token", "urn:li:person:123", settings)
        assert service.settings.max_image_count == 5
        assert service.settings.max_characters == 1000


class TestLinkedInMediaValidation:
    """Test LinkedIn media validation."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

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

    def test_validate_media_valid_document(self):
        """Test validation with valid document."""
        media = [
            MediaItem(
                content=b"fake document data",
                media_type="document",
                filename="test.pdf",
            )
        ]
        self.service.validate_media(media)  # Should not raise

    def test_validate_media_too_many_images(self):
        """Test validation fails with too many images."""
        media = [
            MediaItem(content=b"data", media_type="image", filename=f"test{i}.jpg")
            for i in range(10)  # Max is 9
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Too many images: 10 exceeds limit of 9" in str(
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

    def test_validate_media_too_many_documents(self):
        """Test validation fails with too many documents."""
        media = [
            MediaItem(content=b"data", media_type="document", filename=f"test{i}.pdf")
            for i in range(2)  # Max is 1
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Too many documents: 2 exceeds limit of 1" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_mixed_types_not_allowed(self):
        """Test validation fails with mixed media types."""
        media = [
            MediaItem(content=b"image", media_type="image", filename="test.jpg"),
            MediaItem(content=b"video", media_type="video", filename="test.mp4"),
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Cannot mix different media types" in str(
            exc_info.value.errors[0]["error"]
        )

    def test_validate_media_unsupported_type(self):
        """Test validation fails with unsupported media type."""
        media = [MediaItem(content=b"audio", media_type="audio", filename="test.mp3")]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Unsupported media type: audio" in str(exc_info.value.errors[0]["error"])

    def test_validate_media_unsupported_image_format(self):
        """Test validation fails with unsupported image format."""
        media = [MediaItem(content=b"image", media_type="image", filename="test.bmp")]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Unsupported image format" in str(exc_info.value.errors[0]["error"])

    @patch("hydra_poster.linkedin.MediaItem.get_file_size_mb")
    def test_validate_media_image_too_large(self, mock_size):
        """Test validation fails with oversized image."""
        mock_size.return_value = 150.0  # 150MB, limit is 100MB

        media = [
            MediaItem(content=b"large image", media_type="image", filename="large.jpg")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Image file size 150.0MB exceeds 100MB limit" in str(
            exc_info.value.errors[0]["error"]
        )

    @patch("hydra_poster.linkedin.MediaItem.get_file_size_mb")
    def test_validate_media_video_too_large(self, mock_size):
        """Test validation fails with oversized video."""
        mock_size.return_value = 6000.0  # 6000MB, limit is 5000MB

        media = [
            MediaItem(content=b"large video", media_type="video", filename="large.mp4")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service.validate_media(media)

        assert "Video file size 6000.0MB exceeds 5000MB limit" in str(
            exc_info.value.errors[0]["error"]
        )


class TestLinkedInMediaUpload:
    """Test LinkedIn media upload functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

    @patch("hydra_poster.linkedin.requests.put")
    @patch("hydra_poster.linkedin.requests.post")
    def test_upload_media_success(self, mock_post, mock_put):
        """Test successful media upload."""
        # Mock register upload response
        register_response = Mock()
        register_response.status_code = 200
        register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:C5522AQGiAAAAAAAAAA",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://upload.linkedin.com/upload/123"
                    }
                },
            }
        }
        mock_post.return_value = register_response

        # Mock actual upload response
        upload_response = Mock()
        upload_response.status_code = 200
        mock_put.return_value = upload_response

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        asset_urns = self.service.upload_media(media)

        assert asset_urns == ["urn:li:digitalmediaAsset:C5522AQGiAAAAAAAAAA"]

        # Verify register upload was called
        register_call_args = mock_post.call_args
        payload = register_call_args[1]["json"]
        assert payload["registerUploadRequest"]["owner"] == "urn:li:person:12345"

        # Verify actual upload was called
        upload_call_args = mock_put.call_args
        assert upload_call_args[1]["data"] == b"fake image"

    @patch("hydra_poster.linkedin.LinkedInService._register_upload")
    def test_register_upload_for_different_media_types(self, mock_register):
        """Test register upload uses correct recipes for different media types."""
        mock_register.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:test",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://upload.test"
                    }
                },
            }
        }

        # Test image recipe
        self.service._register_upload("image", "test.jpg")
        call_args = mock_register.call_args[0]  # Get positional args
        assert "image" in call_args and "test.jpg" in call_args

        # Test video recipe
        self.service._register_upload("video", "test.mp4")
        call_args = mock_register.call_args[0]  # Get positional args
        assert "video" in call_args and "test.mp4" in call_args

        # Test document recipe
        self.service._register_upload("document", "test.pdf")
        call_args = mock_register.call_args[0]  # Get positional args
        assert "document" in call_args and "test.pdf" in call_args


class TestLinkedInPosting:
    """Test LinkedIn posting functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

    @patch("hydra_poster.linkedin.requests.post")
    def test_create_post_success(self, mock_post):
        """Test successful post creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "urn:li:ugcPost:6789012345678901234"}
        mock_post.return_value = mock_response

        result = self.service.create_post("Hello LinkedIn!")

        assert result.platform == "linkedin"
        assert result.post_id == "urn:li:ugcPost:6789012345678901234"
        assert "6789012345678901234" in result.url
        assert result.metadata and result.metadata["character_count"] == 15
        assert (
            result.metadata and result.metadata["author_urn"] == "urn:li:person:12345"
        )

    @patch("hydra_poster.linkedin.requests.post")
    def test_create_post_with_images(self, mock_post):
        """Test post creation with images."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "urn:li:ugcPost:6789012345678901234"}
        mock_post.return_value = mock_response

        asset_urns = [
            "urn:li:digitalmediaAsset:test1",
            "urn:li:digitalmediaAsset:test2",
        ]
        media_items = [
            MediaItem(
                content=b"image1",
                media_type="image",
                filename="test1.jpg",
                alt_text="Test image 1",
            ),
            MediaItem(
                content=b"image2",
                media_type="image",
                filename="test2.jpg",
                alt_text="Test image 2",
            ),
        ]

        result = self.service.create_post("Post with images", asset_urns, media_items)

        # Verify the request payload included media
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        share_content = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
        assert share_content["shareMediaCategory"] == "IMAGE"
        assert len(share_content["media"]) == 2
        assert share_content["media"][0]["media"] == asset_urns[0]
        assert share_content["media"][0]["description"]["text"] == "Test image 1"

    def test_create_post_text_too_long(self):
        """Test post creation fails with text too long."""
        long_text = "x" * 3001  # Exceeds 3000 character limit

        with pytest.raises(PostCreationError) as exc_info:
            self.service.create_post(long_text)

        assert "exceeds 3000 character limit" in str(exc_info.value)

    @patch("hydra_poster.linkedin.requests.post")
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

    @patch("hydra_poster.linkedin.requests.delete")
    def test_delete_post_success(self, mock_delete):
        """Test successful post deletion."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        result = self.service.delete_post("urn:li:ugcPost:6789012345678901234")
        assert result is True

    @patch("hydra_poster.linkedin.requests.delete")
    def test_delete_post_not_found(self, mock_delete):
        """Test post deletion when post doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response

        result = self.service.delete_post("urn:li:ugcPost:nonexistent")
        assert result is True  # 404 considered success (already deleted)

    def test_delete_post_formats_urn(self):
        """Test delete_post properly formats URN."""
        with patch("hydra_poster.linkedin.requests.delete") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response

            # Test with plain ID
            self.service.delete_post("6789012345678901234")

            call_args = mock_delete.call_args
            assert "urn:li:ugcPost:6789012345678901234" in call_args[0][0]


class TestLinkedInMainPosting:
    """Test LinkedIn main posting functionality."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

    def test_post_with_reply_config_raises_error(self):
        """Test that reply-to functionality raises error."""
        config = PostConfig(reply_to_id="some_post_id")

        with pytest.raises(PostCreationError) as exc_info:
            self.service.post("Test post", config=config)

        assert "LinkedIn does not support reply-to functionality" in str(exc_info.value)

    @patch("hydra_poster.linkedin.LinkedInService.upload_media")
    @patch("hydra_poster.linkedin.LinkedInService.create_post")
    def test_post_with_media_end_to_end(self, mock_create, mock_upload):
        """Test complete posting workflow with media."""
        mock_upload.return_value = ["urn:li:digitalmediaAsset:test123"]
        mock_create.return_value = Mock(
            platform="linkedin",
            post_id="urn:li:ugcPost:test",
            url="https://linkedin.com/test",
        )

        media = [
            MediaItem(content=b"fake image", media_type="image", filename="test.jpg")
        ]

        result = self.service.post("Check out this image!", media=media)

        # Verify upload was called
        mock_upload.assert_called_once_with(media)

        # Verify create_post was called with uploaded assets
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][1] == ["urn:li:digitalmediaAsset:test123"]  # asset_urns
        assert call_args[0][2] == media  # media_items


class TestLinkedInThreading:
    """Test LinkedIn threading functionality (post series)."""

    def setup_method(self):
        """Set up test service."""
        # Create a mock time provider for testing
        from unittest.mock import Mock

        mock_time = Mock()
        self.mock_time = mock_time
        self.service = LinkedInService(
            "test-access-token", "urn:li:person:12345", time_provider=mock_time
        )

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_thread_success(self, mock_post):
        """Test successful post thread (series)."""
        mock_post.side_effect = [
            Mock(post_id="post1", url="https://linkedin.com/post1"),
            Mock(post_id="post2", url="https://linkedin.com/post2"),
            Mock(post_id="post3", url="https://linkedin.com/post3"),
        ]

        messages = ["First post", "Second post", "Third post"]

        result = self.service.post_thread(messages)

        assert result.platform == "linkedin"
        assert result.post_count == 3
        assert result.thread_id == "post1"
        assert result.thread_url == "https://linkedin.com/post1"

        # Verify posts were numbered
        call_args_list = mock_post.call_args_list
        assert "(1/3) First post" in call_args_list[0][0][0]
        assert "(2/3) Second post" in call_args_list[1][0][0]
        assert "(3/3) Third post" in call_args_list[2][0][0]

        # Verify delays were added (should be 2 delays for 3 posts)
        assert self.mock_time.sleep.call_count == 2
        self.mock_time.sleep.assert_called_with(2)

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_thread_single_message_no_numbering(self, mock_post):
        """Test single message doesn't get numbered."""
        mock_post.return_value = Mock(post_id="post1", url="https://linkedin.com/post1")

        messages = ["Single post"]

        self.service.post_thread(messages)

        # Verify post wasn't numbered
        call_args = mock_post.call_args
        assert call_args[0][0] == "Single post"  # No numbering added

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_thread_with_media(self, mock_post):
        """Test post thread with media per post."""
        mock_post.side_effect = [
            Mock(post_id="post1", url="https://linkedin.com/post1"),
            Mock(post_id="post2", url="https://linkedin.com/post2"),
        ]

        messages = ["First post with media", "Second post with media"]
        media = [
            [MediaItem(content=b"image1", media_type="image", filename="test1.jpg")],
            [MediaItem(content=b"image2", media_type="image", filename="test2.jpg")],
        ]

        result = self.service.post_thread(messages, media=media)

        assert result.post_count == 2

        # Verify media was passed to each post
        call_args_list = mock_post.call_args_list
        assert call_args_list[0][0][1] == media[0]  # First post's media
        assert call_args_list[1][0][1] == media[1]  # Second post's media


class TestLinkedInIntegration:
    """Test LinkedIn service integration scenarios."""

    def setup_method(self):
        """Set up test service."""
        self.service = LinkedInService("test-access-token", "urn:li:person:12345")

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

        wmv_item = MediaItem(content=b"data", media_type="video", filename="test.wmv")
        assert self.service._get_mime_type(wmv_item) == "video/x-ms-wmv"

        avi_item = MediaItem(content=b"data", media_type="video", filename="test.avi")
        assert self.service._get_mime_type(avi_item) == "video/x-msvideo"

        # Document types
        pdf_item = MediaItem(
            content=b"data", media_type="document", filename="test.pdf"
        )
        assert self.service._get_mime_type(pdf_item) == "application/pdf"

        doc_item = MediaItem(
            content=b"data", media_type="document", filename="test.doc"
        )
        assert self.service._get_mime_type(doc_item) == "application/msword"

        ppt_item = MediaItem(
            content=b"data", media_type="document", filename="test.ppt"
        )
        assert self.service._get_mime_type(ppt_item) == "application/vnd.ms-powerpoint"


class TestLinkedInPostSeries:
    """Test LinkedIn post_series() method (preferred over post_thread)."""

    def setup_method(self):
        """Set up test service."""
        # Create a mock time provider for testing
        from unittest.mock import Mock

        mock_time = Mock()
        self.mock_time = mock_time
        self.service = LinkedInService(
            "test-access-token", "urn:li:person:12345", time_provider=mock_time
        )

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_series_success(self, mock_post):
        """Test successful post series creation using preferred method."""
        mock_post.side_effect = [
            Mock(post_id="post1", url="https://linkedin.com/post1"),
            Mock(post_id="post2", url="https://linkedin.com/post2"),
            Mock(post_id="post3", url="https://linkedin.com/post3"),
        ]

        messages = ["First post", "Second post", "Third post"]

        result = self.service.post_series(messages)

        # Should behave identically to post_thread
        assert result.platform == "linkedin"
        assert result.thread_id == "post1"
        assert result.post_count == 3

        # Verify posts were numbered correctly
        call_args_list = mock_post.call_args_list
        assert "(1/3) First post" in call_args_list[0][0][0]
        assert "(2/3) Second post" in call_args_list[1][0][0]
        assert "(3/3) Third post" in call_args_list[2][0][0]

        # Verify delays were added
        assert self.mock_time.sleep.call_count == 2
        self.mock_time.sleep.assert_called_with(2)

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_series_single_message_no_numbering(self, mock_post):
        """Test single message in series doesn't get numbered."""
        mock_post.return_value = Mock(post_id="post1", url="https://linkedin.com/post1")

        messages = ["Single post"]

        self.service.post_series(messages)

        # Verify post wasn't numbered (same behavior as post_thread)
        call_args = mock_post.call_args
        assert call_args[0][0] == "Single post"  # No numbering prefix

    @patch("hydra_poster.linkedin.LinkedInService.post")
    def test_post_series_with_media(self, mock_post):
        """Test post series with media per post."""
        mock_post.side_effect = [
            Mock(post_id="post1", url="https://linkedin.com/post1"),
            Mock(post_id="post2", url="https://linkedin.com/post2"),
        ]

        messages = ["Post with media", "Post without media"]
        media = [
            [MediaItem(content=b"image", media_type="image", filename="image.jpg")],
            [],  # No media for second post
        ]

        result = self.service.post_series(messages, media=media)

        assert result.post_count == 2

        # Verify first post got media, second didn't
        first_call_media = mock_post.call_args_list[0][0][1]
        second_call_media = mock_post.call_args_list[1][0][1]

        assert len(first_call_media) == 1
        assert second_call_media == []
