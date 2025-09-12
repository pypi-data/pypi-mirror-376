"""Test cases for media validation functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from hydra_poster.base import MediaItem
from hydra_poster.exceptions import MediaValidationError


class TestMediaItemValidation:
    """Test MediaItem validation methods."""

    def test_validate_structure_success(self):
        """Test successful structure validation."""
        item = MediaItem(content="test.jpg", media_type="image")
        item.validate_structure()  # Should not raise

    def test_validate_structure_missing_media_type(self):
        """Test validation fails with missing media_type."""
        item = MediaItem(content="test.jpg", media_type="")

        with pytest.raises(MediaValidationError) as exc_info:
            item.validate_structure()

        assert len(exc_info.value.errors) == 1
        assert "media_type is required" in exc_info.value.errors[0]["error"]

    def test_validate_structure_invalid_media_type(self):
        """Test validation fails with invalid media_type."""
        item = MediaItem(content="test.jpg", media_type="audio")

        with pytest.raises(MediaValidationError) as exc_info:
            item.validate_structure()

        assert len(exc_info.value.errors) == 1
        assert "Invalid media_type: audio" in exc_info.value.errors[0]["error"]

    def test_validate_structure_bytes_without_filename(self):
        """Test validation fails for bytes content without filename."""
        item = MediaItem(content=b"image data", media_type="image")

        with pytest.raises(MediaValidationError) as exc_info:
            item.validate_structure()

        assert len(exc_info.value.errors) == 1
        assert (
            "filename is required when content is bytes"
            in exc_info.value.errors[0]["error"]
        )

    def test_validate_structure_bytes_with_filename_success(self):
        """Test validation succeeds for bytes content with filename."""
        item = MediaItem(content=b"image data", media_type="image", filename="test.jpg")
        item.validate_structure()  # Should not raise


class TestMediaItemContentHandling:
    """Test MediaItem content normalization and file operations."""

    def test_normalize_content_bytes(self):
        """Test normalization of bytes content."""
        content_bytes = b"test image data"
        item = MediaItem(content=content_bytes, media_type="image", filename="test.jpg")

        result = item.normalized_content
        assert result == content_bytes

    def test_normalize_content_file(self):
        """Test normalization of file path content."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            test_content = b"test file content"
            tmp_file.write(test_content)
            tmp_file.flush()

            item = MediaItem(content=tmp_file.name, media_type="image")
            result = item.normalized_content

            assert result == test_content
            Path(tmp_file.name).unlink()  # Clean up

    def test_normalize_content_nonexistent_file(self):
        """Test normalization fails for nonexistent file."""
        item = MediaItem(content="/nonexistent/file.jpg", media_type="image")

        with pytest.raises(MediaValidationError) as exc_info:
            _ = item.normalized_content

        assert "File does not exist" in exc_info.value.errors[0]["error"]

    @patch("hydra_poster.base.requests.get")
    def test_normalize_content_url_success(self, mock_get):
        """Test successful URL content normalization."""
        test_content = b"downloaded image data"
        mock_response = Mock()
        mock_response.content = test_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        item = MediaItem(content="https://example.com/image.jpg", media_type="image")
        result = item.normalized_content

        assert result == test_content
        mock_get.assert_called_once_with("https://example.com/image.jpg", timeout=30)

    @patch("hydra_poster.base.requests.get")
    def test_normalize_content_url_failure(self, mock_get):
        """Test URL content normalization failure."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        item = MediaItem(content="https://example.com/image.jpg", media_type="image")

        with pytest.raises(MediaValidationError) as exc_info:
            _ = item.normalized_content

        assert "Failed to download URL" in exc_info.value.errors[0]["error"]

    def test_get_file_size_mb(self):
        """Test file size calculation."""
        content_1mb = b"x" * (1024 * 1024)  # Exactly 1MB
        item = MediaItem(content=content_1mb, media_type="image", filename="test.jpg")

        size = item.get_file_size_mb()
        assert size == 1.0

    def test_get_filename_explicit(self):
        """Test filename when explicitly provided."""
        item = MediaItem(content=b"data", media_type="image", filename="custom.jpg")
        assert item.get_filename() == "custom.jpg"

    def test_get_filename_from_path(self):
        """Test filename inferred from file path."""
        item = MediaItem(content="/path/to/image.jpg", media_type="image")
        assert item.get_filename() == "image.jpg"

    def test_get_filename_from_url(self):
        """Test filename inferred from URL."""
        item = MediaItem(
            content="https://example.com/photos/sunset.png", media_type="image"
        )
        assert item.get_filename() == "sunset.png"

    def test_get_filename_fallback(self):
        """Test filename fallback for bytes without explicit name."""
        item = MediaItem(content=b"data", media_type="image", filename=None)
        # This would normally fail validation, but test the method directly
        item.filename = None  # Override after creation
        assert item.get_filename() == "content.image"


class TestMediaItemCaching:
    """Test content caching behavior."""

    @patch("hydra_poster.base.requests.get")
    def test_normalize_content_caching(self, mock_get):
        """Test that normalized content is cached."""
        test_content = b"cached content"
        mock_response = Mock()
        mock_response.content = test_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        item = MediaItem(content="https://example.com/image.jpg", media_type="image")

        # First call should hit the network
        result1 = item.normalized_content
        assert result1 == test_content
        assert mock_get.call_count == 1

        # Second call should use cache
        result2 = item.normalized_content
        assert result2 == test_content
        assert mock_get.call_count == 1  # Still only 1 call
