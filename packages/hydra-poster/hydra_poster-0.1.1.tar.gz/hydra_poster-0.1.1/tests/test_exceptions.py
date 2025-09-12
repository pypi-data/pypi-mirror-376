"""Test cases for exception hierarchy."""

import pytest

from hydra_poster.base import ValidationError
from hydra_poster.exceptions import (
    BlueSkyError,
    GhostError,
    GithubError,
    LinkedInError,
    MediaTooLargeError,
    MediaUploadError,
    MediaValidationError,
    PostCreationError,
    RedditError,
    SocialMediaError,
    ThreadPostingError,
    ThreadValidationError,
    TwitterError,
    UnsupportedMediaTypeError,
)


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_social_media_error_is_base(self):
        """Test that SocialMediaError is the base exception."""
        error = SocialMediaError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)

    def test_media_validation_error_inheritance(self):
        """Test MediaValidationError inherits from SocialMediaError."""
        errors = [ValidationError(error="Test error", media_source="", media_type="")]
        error = MediaValidationError(errors)

        assert isinstance(error, SocialMediaError)
        assert error.errors == errors
        assert "Media validation failed for 1 items" in str(error)

    def test_media_too_large_error_inheritance(self):
        """Test MediaTooLargeError inherits from MediaValidationError."""
        errors = [
            ValidationError(error="File too large", media_source="", media_type="")
        ]
        error = MediaTooLargeError(errors)

        assert isinstance(error, MediaValidationError)
        assert isinstance(error, SocialMediaError)

    def test_unsupported_media_type_error_inheritance(self):
        """Test UnsupportedMediaTypeError inherits from MediaValidationError."""
        errors = [
            ValidationError(error="Unsupported format", media_source="", media_type="")
        ]
        error = UnsupportedMediaTypeError(errors)

        assert isinstance(error, MediaValidationError)
        assert isinstance(error, SocialMediaError)

    def test_platform_specific_errors(self):
        """Test platform-specific errors inherit from SocialMediaError."""
        platform_errors = [
            TwitterError("Twitter error"),
            BlueSkyError("Bluesky error"),
            LinkedInError("LinkedIn error"),
            RedditError("Reddit error"),
            GithubError("GitHub error"),
            GhostError("Ghost error"),
        ]

        for error in platform_errors:
            assert isinstance(error, SocialMediaError)


class TestMediaValidationError:
    """Test MediaValidationError specific functionality."""

    def test_single_error(self):
        """Test MediaValidationError with single error."""
        errors = [
            ValidationError(error="Missing filename", media_source="", media_type="")
        ]
        error = MediaValidationError(errors)

        assert error.errors == errors
        assert "Media validation failed for 1 items" in str(error)

    def test_multiple_errors(self):
        """Test MediaValidationError with multiple errors."""
        errors = [
            ValidationError(
                error="Missing filename", item_index="0", media_source="", media_type=""
            ),
            ValidationError(
                error="Invalid format", item_index="1", media_source="", media_type=""
            ),
            ValidationError(
                error="File too large", item_index="2", media_source="", media_type=""
            ),
        ]
        error = MediaValidationError(errors)

        assert error.errors == errors
        assert "Media validation failed for 3 items" in str(error)

    def test_empty_errors_list(self):
        """Test MediaValidationError with empty errors list."""
        error = MediaValidationError([])
        assert error.errors == []
        assert "Media validation failed for 0 items" in str(error)


class TestThreadPostingError:
    """Test ThreadPostingError specific functionality."""

    def test_thread_posting_error_attributes(self):
        """Test ThreadPostingError stores posting details."""
        error = ThreadPostingError(
            "Failed to post", posted_count=3, rollback_attempted=True
        )

        assert str(error) == "Failed to post"
        assert error.posted_count == 3
        assert error.rollback_attempted is True
        assert isinstance(error, SocialMediaError)

    def test_thread_posting_error_no_rollback(self):
        """Test ThreadPostingError with no rollback."""
        error = ThreadPostingError(
            "Partial failure", posted_count=2, rollback_attempted=False
        )

        assert error.posted_count == 2
        assert error.rollback_attempted is False


class TestThreadValidationError:
    """Test ThreadValidationError specific functionality."""

    def test_thread_validation_error(self):
        """Test ThreadValidationError with thread errors."""
        errors = [
            ValidationError(error="Tweet too long", media_source="", media_type=""),
            ValidationError(error="Invalid media", media_source="", media_type=""),
        ]
        error = ThreadValidationError(errors)

        assert error.errors == errors
        assert "Thread validation failed for 2 posts" in str(error)
        assert isinstance(error, SocialMediaError)


class TestOtherExceptions:
    """Test other exception classes."""

    def test_media_upload_error(self):
        """Test MediaUploadError."""
        error = MediaUploadError("Upload failed")
        assert str(error) == "Upload failed"
        assert isinstance(error, SocialMediaError)

    def test_post_creation_error(self):
        """Test PostCreationError."""
        error = PostCreationError("Post creation failed")
        assert str(error) == "Post creation failed"
        assert isinstance(error, SocialMediaError)


class TestExceptionUsagePatterns:
    """Test common exception usage patterns."""

    def test_nested_exception_handling(self):
        """Test handling nested MediaValidationError."""

        def raise_validation_error() -> None:
            errors = [
                ValidationError(
                    error="Test error", item_index="0", media_source="", media_type=""
                )
            ]
            raise MediaValidationError(errors)

        try:
            raise_validation_error()
        except MediaValidationError as e:
            assert len(e.errors) == 1
            assert e.errors[0]["error"] == "Test error"
        except SocialMediaError:
            pytest.fail("Should have caught MediaValidationError specifically")

    def test_platform_error_handling(self):
        """Test handling platform-specific errors."""

        def raise_twitter_error() -> None:
            raise TwitterError("Rate limit exceeded")

        try:
            raise_twitter_error()
        except TwitterError as e:
            assert str(e) == "Rate limit exceeded"
        except SocialMediaError:
            pytest.fail("Should have caught TwitterError specifically")
        else:
            pytest.fail("Exception should have been raised")
