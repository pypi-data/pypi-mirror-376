"""Test cases for SocialMediaService validation pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hydra_poster.base import (
    MediaItem,
    PostConfig,
    PostResult,
    SocialMediaService,
    ValidationError,
)
from hydra_poster.exceptions import MediaValidationError


class TestSocialMediaService(SocialMediaService):
    """Test implementation of SocialMediaService for testing."""

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Test implementation."""
        return PostResult("test", "123", "http://test.com/123")

    def validate_media(self, media: list[MediaItem]) -> None:
        """Test implementation - no platform-specific validation."""
        pass


class TestSocialMediaServiceValidation:
    """Test SocialMediaService validation methods."""

    def setup_method(self):
        """Set up test service."""
        self.service = TestSocialMediaService()

    def test_validate_media_structure_success(self):
        """Test successful structure validation."""
        media = [
            MediaItem(content="test1.jpg", media_type="image"),
            MediaItem(content="test2.jpg", media_type="image"),
        ]

        self.service._validate_media_structure(media)  # Should not raise

    def test_validate_media_structure_multiple_errors(self):
        """Test structure validation with multiple errors."""
        media = [
            MediaItem(content="test1.jpg", media_type=""),  # Missing media_type
            MediaItem(
                content=b"data", media_type="image"
            ),  # Missing filename for bytes
            MediaItem(content="test3.jpg", media_type="audio"),  # Invalid media_type
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service._validate_media_structure(media)

        errors = exc_info.value.errors
        assert len(errors) == 3

        # Check that errors include item indices
        assert errors[0]["item_index"] == "0"
        assert errors[1]["item_index"] == "1"
        assert errors[2]["item_index"] == "2"

    def test_validate_media_accessibility_success(self):
        """Test successful accessibility validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file.flush()

            media = [
                MediaItem(
                    content=b"bytes data", media_type="image", filename="test.jpg"
                ),
                MediaItem(content=tmp_file.name, media_type="image"),
            ]

            self.service._validate_media_accessibility(media)  # Should not raise
            Path(tmp_file.name).unlink()  # Clean up

    def test_validate_media_accessibility_file_not_found(self):
        """Test accessibility validation with missing file."""
        media = [
            MediaItem(content="nonexistent.jpg", media_type="image"),
            MediaItem(content="also_missing.jpg", media_type="image"),
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service._validate_media_accessibility(media)

        errors = exc_info.value.errors
        assert len(errors) == 2
        assert errors[0]["item_index"] == "0"
        assert errors[1]["item_index"] == "1"
        assert "File does not exist" in errors[0]["error"]

    @patch("hydra_poster.base.requests.get")
    def test_validate_media_accessibility_url_failure(self, mock_get):
        """Test accessibility validation with URL download failure."""
        mock_get.side_effect = Exception("Network error")

        media = [
            MediaItem(content="https://example.com/image.jpg", media_type="image"),
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            self.service._validate_media_accessibility(media)

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["item_index"] == "0"

    def test_validate_media_pipeline_empty_list(self):
        """Test validation pipeline with empty media list."""
        self.service.validate_media_pipeline([])  # Should not raise

    @patch("hydra_poster.base.requests.get")
    def test_validate_media_pipeline_full_success(self, mock_get):
        """Test complete validation pipeline success."""
        # Mock successful URL download
        mock_response = Mock()
        mock_response.content = b"downloaded image"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"file content")
            tmp_file.flush()

            media = [
                MediaItem(content="https://example.com/image.jpg", media_type="image"),
                MediaItem(content=tmp_file.name, media_type="image"),
                MediaItem(
                    content=b"bytes data", media_type="image", filename="test.jpg"
                ),
            ]

            self.service.validate_media_pipeline(media)  # Should not raise
            Path(tmp_file.name).unlink()

    def test_validate_media_pipeline_structure_failure(self):
        """Test validation pipeline fails at structure phase."""
        media = [
            MediaItem(content="test.jpg", media_type=""),  # Invalid structure
        ]

        with pytest.raises(MediaValidationError):
            self.service.validate_media_pipeline(media)


class TestServiceWithCustomValidation(SocialMediaService):
    """Test service with custom platform validation."""

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Test implementation."""
        return PostResult("test", "123", "http://test.com/123")

    def validate_media(self, media: list[MediaItem]) -> None:
        """Custom platform validation that rejects large files."""
        errors: list[ValidationError] = []
        for i, item in enumerate(media):
            if item.get_file_size_mb() > 1.0:
                errors.append(
                    ValidationError(
                        error=f"File too large: {item.get_file_size_mb():.1f}MB exceeds 1MB limit",
                        item_index=str(i),
                        media_source=str(item.content)[:50],
                        media_type=item.media_type,
                    )
                )

        if errors:
            raise MediaValidationError(errors)


class TestCustomValidation:
    """Test custom platform validation."""

    def test_platform_validation_called(self):
        """Test that platform-specific validation is called."""
        service = TestServiceWithCustomValidation()

        # Large content that will fail custom validation
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        media = [
            MediaItem(content=large_content, media_type="image", filename="large.jpg")
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            service.validate_media_pipeline(media)

        assert (
            "File too large: 2.0MB exceeds 1MB limit"
            in exc_info.value.errors[0]["error"]
        )
