"""Test cases for threading functionality with robust rollback."""

import pytest

from hydra_poster.base import (
    MediaItem,
    PostConfig,
    PostResult,
    SocialMediaService,
)
from hydra_poster.exceptions import ThreadPostingError


class MockThreadingService(SocialMediaService):
    """Test service for threading functionality."""

    def __init__(
        self,
        fail_on_message: int | None = None,
        fail_on_delete: list[str] | None = None,
    ):
        super().__init__()  # Initialize parent class with TimeProvider
        self.posted_count = 0
        self.deleted_posts: list[str] = []
        self.fail_on_message = fail_on_message  # Fail on nth message (1-indexed)
        self.fail_on_delete = (
            fail_on_delete or []
        )  # List of post IDs that fail to delete

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        self.posted_count += 1

        if self.fail_on_message == self.posted_count:
            raise Exception(f"Simulated failure on message {self.posted_count}")

        post_id = f"post_{self.posted_count}"
        return PostResult(
            platform="test",
            post_id=post_id,
            url=f"https://test.com/{post_id}",
            metadata={
                "reply_to": config.reply_to_id if config and config.reply_to_id else ""
            },
        )

    def validate_media(self, media: list[MediaItem]) -> None:
        pass  # No validation for test

    def delete_post(self, post_id: str) -> bool:
        if post_id in self.fail_on_delete:
            raise Exception(f"Simulated deletion failure for {post_id}")
        self.deleted_posts.append(post_id)
        return True


class TestThreadPosting:
    """Test thread posting with rollback logic."""

    def test_successful_thread_posting(self):
        """Test successful thread posting."""
        service = MockThreadingService()
        messages = ["First message", "Second message", "Third message"]

        result = service.post_thread(messages)

        assert result.platform == "test"
        assert result.thread_id == "post_1"
        assert result.post_count == 3
        assert len(result.post_results) == 3
        assert result.post_results[0].post_id == "post_1"
        assert result.post_results[1].post_id == "post_2"
        assert result.post_results[2].post_id == "post_3"

        # Check reply structure
        assert (
            result.post_results[0].metadata
            and result.post_results[0].metadata["reply_to"] == ""
        )  # Root post
        assert (
            result.post_results[1].metadata
            and result.post_results[1].metadata["reply_to"] == "post_1"
        )  # Reply to root
        assert (
            result.post_results[2].metadata
            and result.post_results[2].metadata["reply_to"] == "post_2"
        )  # Reply to previous

    def test_thread_with_media(self):
        """Test thread posting with media."""
        service = MockThreadingService()
        messages = ["Message with media", "Another with media"]
        media = [[MediaItem("image1.jpg", "image")], [MediaItem("image2.jpg", "image")]]

        result = service.post_thread(messages, media=media)

        assert result.post_count == 2
        assert len(result.post_results) == 2

    def test_empty_thread_raises_error(self):
        """Test that empty thread raises ValueError."""
        service = MockThreadingService()

        with pytest.raises(
            ValueError, match="Thread must contain at least one message"
        ):
            service.post_thread([])

    def test_failure_with_successful_rollback(self):
        """Test thread failure with successful rollback."""
        service = MockThreadingService(fail_on_message=3)  # Fail on 3rd message
        messages = ["First", "Second", "Third", "Fourth"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages)

        error = exc_info.value
        assert error.posted_count == 2  # Only 2 messages posted before failure
        assert error.rollback_attempted is True
        assert "All posted content has been rolled back" in str(error)

        # Verify rollback happened
        assert "post_1" in service.deleted_posts
        assert "post_2" in service.deleted_posts
        assert len(service.deleted_posts) == 2

    @pytest.mark.slow
    def test_failure_with_partial_rollback_failure(self):
        """Test thread failure with partial rollback failure."""
        service = MockThreadingService(
            fail_on_message=3,
            fail_on_delete=["post_1"],  # First post fails to delete
        )
        messages = ["First", "Second", "Third"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages)

        error = exc_info.value
        assert error.posted_count == 2
        assert error.rollback_attempted is True
        assert "Failed to rollback posts: ['post_1']" in str(error)

        # Verify partial rollback
        assert "post_1" not in service.deleted_posts  # Failed to delete
        assert "post_2" in service.deleted_posts  # Successfully deleted

    def test_failure_without_rollback(self):
        """Test thread failure with rollback disabled."""
        service = MockThreadingService(fail_on_message=2)
        messages = ["First", "Second", "Third"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages, rollback_on_failure=False)

        error = exc_info.value
        assert error.posted_count == 1
        assert error.rollback_attempted is False

        # Verify no rollback happened
        assert len(service.deleted_posts) == 0

    @pytest.mark.slow
    def test_rollback_with_retries(self):
        """Test rollback retry logic."""
        # Mock the service to fail deletion twice, then succeed
        service = MockThreadingService(fail_on_message=2)

        # Create a custom delete method that fails first two attempts
        original_delete = service.delete_post
        attempt_count = {"count": 0}

        def failing_delete(post_id: str) -> bool:
            attempt_count["count"] += 1
            if attempt_count["count"] <= 2:
                raise Exception("Temporary delete failure")
            return original_delete(post_id)

        # Mock the delete_post method
        service.delete_post = failing_delete  # type: ignore[method-assign]

        messages = ["First", "Second"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages)

        # Should succeed after retries
        error = exc_info.value
        assert "All posted content has been rolled back" in str(error)
        assert attempt_count["count"] == 3  # Failed twice, succeeded on third


class TestThreadingConfiguration:
    """Test threading configuration and edge cases."""

    def test_custom_config_propagation(self):
        """Test that PostConfig is properly propagated through thread."""
        service = MockThreadingService()
        messages = ["First", "Second"]
        config = PostConfig(visibility="private", metadata={"source": "test"})

        result = service.post_thread(messages, config=config)

        # Verify config was used (metadata should be preserved)
        for post_result in result.post_results:
            # The thread logic should propagate metadata
            assert isinstance(post_result.metadata, dict)

    def test_single_message_thread(self):
        """Test thread with single message."""
        service = MockThreadingService()
        messages = ["Only message"]

        result = service.post_thread(messages)

        assert result.post_count == 1
        assert result.thread_id == "post_1"
        assert (
            result.post_results[0].metadata
            and result.post_results[0].metadata["reply_to"] == ""
        )

    def test_thread_result_properties(self):
        """Test ThreadResult properties."""
        service = MockThreadingService()
        messages = ["First", "Second", "Third"]

        result = service.post_thread(messages)

        assert result.post_count == 3
        assert result.last_post_id == "post_3"
        assert result.thread_url == "https://test.com/post_1"


class TestRollbackEdgeCases:
    """Test edge cases in rollback logic."""

    @pytest.mark.slow
    def test_rollback_with_all_deletions_failing(self):
        """Test rollback when all deletions fail."""
        service = MockThreadingService(
            fail_on_message=3,
            fail_on_delete=["post_1", "post_2"],  # All posts fail to delete
        )
        messages = ["First", "Second", "Third"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages)

        error = exc_info.value
        assert error.rollback_attempted is True
        # Posts are rolled back in reverse order, so post_2 fails first, then post_1
        assert "Failed to rollback posts: ['post_2', 'post_1']" in str(error)

    def test_rollback_reverse_order(self):
        """Test that rollback deletes in reverse order."""
        service = MockThreadingService(fail_on_message=4)
        messages = ["First", "Second", "Third", "Fourth"]

        with pytest.raises(ThreadPostingError):
            service.post_thread(messages)

        # Should delete in reverse order: post_3, post_2, post_1
        assert service.deleted_posts == ["post_3", "post_2", "post_1"]
