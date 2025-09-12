"""Test cases for base classes."""

from pathlib import Path

from hydra_poster.base import MediaItem, PostResult, ThreadResult


class TestMediaItem:
    """Test MediaItem class."""

    def test_is_url_true(self):
        """Test URL detection."""
        item = MediaItem(content="https://example.com/image.jpg", media_type="image")
        assert item.is_url() is True

    def test_is_url_false(self):
        """Test non-URL detection."""
        item = MediaItem(content="/path/to/file.jpg", media_type="image")
        assert item.is_url() is False

    def test_is_file_path_true(self):
        """Test file path detection."""
        item = MediaItem(content="/path/to/file.jpg", media_type="image")
        assert item.is_file_path() is True

    def test_is_file_path_false_for_url(self):
        """Test file path detection returns false for URLs."""
        item = MediaItem(content="https://example.com/image.jpg", media_type="image")
        assert item.is_file_path() is False

    def test_is_file_path_pathlib(self):
        """Test file path detection with pathlib Path."""
        item = MediaItem(content=Path("/path/to/file.jpg"), media_type="image")
        assert item.is_file_path() is True

    def test_is_bytes_true(self):
        """Test bytes detection."""
        item = MediaItem(content=b"image data", media_type="image", filename="test.jpg")
        assert item.is_bytes() is True

    def test_is_bytes_false(self):
        """Test non-bytes detection."""
        item = MediaItem(content="/path/to/file.jpg", media_type="image")
        assert item.is_bytes() is False


class TestPostResult:
    """Test PostResult class."""

    def test_creation(self):
        """Test PostResult creation."""
        result = PostResult(
            platform="twitter",
            post_id="123456789",
            url="https://twitter.com/user/status/123456789",
            media_ids=["media_1", "media_2"],
        )
        assert result.platform == "twitter"
        assert result.post_id == "123456789"
        assert result.media_ids == ["media_1", "media_2"]


class TestThreadResult:
    """Test ThreadResult class."""

    def test_post_count(self):
        """Test post_count property."""
        posts = [
            PostResult("twitter", "1", "url1"),
            PostResult("twitter", "2", "url2"),
        ]
        thread = ThreadResult("twitter", "1", posts, "url1")
        assert thread.post_count == 2

    def test_last_post_id(self):
        """Test last_post_id property."""
        posts = [
            PostResult("twitter", "1", "url1"),
            PostResult("twitter", "2", "url2"),
        ]
        thread = ThreadResult("twitter", "1", posts, "url1")
        assert thread.last_post_id == "2"

    def test_empty_thread(self):
        """Test empty thread."""
        thread = ThreadResult("twitter", "1", [], "url1")
        assert thread.post_count == 0
        assert thread.last_post_id == ""
