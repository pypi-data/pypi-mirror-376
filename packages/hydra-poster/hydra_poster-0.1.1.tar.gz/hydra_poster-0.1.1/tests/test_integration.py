"""Integration tests for social media posting library.

These tests validate end-to-end workflows including:
- Complete validation pipeline (structure → accessibility → platform validation)
- Threading behavior with realistic scenarios
- Error propagation through the entire stack
- Performance characteristics of validation patterns
"""

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hydra_poster.base import (
    MediaItem,
    PostConfig,
    PostResult,
    SocialMediaService,
    ValidationError,
    _media_validator,
)
from hydra_poster.exceptions import (
    MediaValidationError,
    ThreadPostingError,
)


class IntegrationTestService(SocialMediaService):
    """Test service for integration testing with realistic constraints."""

    def __init__(
        self,
        max_media_size_mb: float = 10.0,
        max_media_count: int = 4,
        fail_conditions: dict[str, str | int | list[str]] | None = None,
        upload_delay: float = 0.0,
    ):
        """Initialize with platform-like constraints.

        Args:
            max_media_size_mb: Maximum file size in MB per media item
            max_media_count: Maximum number of media items per post
            fail_conditions: Dict of conditions that trigger failures
            upload_delay: Simulated upload delay per media item
        """
        super().__init__()  # Initialize parent class with TimeProvider
        self.max_media_size_mb = max_media_size_mb
        self.max_media_count = max_media_count
        self.fail_conditions = fail_conditions or {}
        self.upload_delay = upload_delay

        # Track service usage for performance testing
        self.post_count = 0
        self.validation_calls = 0
        self.deleted_posts: list[str] = []
        self.upload_times: list[float] = []

    def post(
        self,
        text: str,
        media: list[MediaItem] | None = None,
        config: PostConfig | None = None,
    ) -> PostResult:
        """Post with validation and simulated constraints."""
        self.post_count += 1

        # Simulate text-based failures
        fail_text = self.fail_conditions.get("fail_on_text")
        if isinstance(fail_text, str) and fail_text in text:
            raise Exception(f"Text contains prohibited content: {text}")

        # Validate and process media
        if media:
            start_time = time.time()
            self.validate_media_pipeline(media)

            # Simulate upload delay
            if self.upload_delay > 0:
                self._time.sleep(self.upload_delay * len(media))

            self.upload_times.append(time.time() - start_time)

        # Simulate posting failure after successful validation
        fail_count = self.fail_conditions.get("fail_after_validation")
        if isinstance(fail_count, int) and fail_count == self.post_count:
            raise Exception("Simulated posting failure after validation")

        post_id = f"integration_post_{self.post_count}"
        return PostResult(
            platform="integration-test",
            post_id=post_id,
            url=f"https://integration-test.com/{post_id}",
            media_ids=[f"media_{i}" for i in range(len(media))] if media else None,
            metadata={
                "reply_to": config.reply_to_id if config and config.reply_to_id else ""
            },
        )

    def validate_media(self, media: list[MediaItem]) -> None:
        """Platform-specific validation with realistic constraints."""
        self.validation_calls += 1
        errors: list[ValidationError] = []

        # Check media count limit
        if len(media) > self.max_media_count:
            errors.append(
                ValidationError(
                    error=f"Too many media items: {len(media)} exceeds limit of {self.max_media_count}",
                    item_index=str(len(media) - 1),
                    media_source="",
                    media_type="",
                )
            )

        # Check individual media constraints
        for i, item in enumerate(media):
            file_size = item.get_file_size_mb()
            if file_size > self.max_media_size_mb:
                errors.append(
                    ValidationError(
                        error=f"Media too large: {file_size:.2f}MB exceeds {self.max_media_size_mb}MB limit",
                        item_index=str(i),
                        media_source=str(item.content)[:50],
                        media_type=item.media_type,
                    )
                )

            # Check specific failure conditions
            filename = item.get_filename()
            reject_filename = self.fail_conditions.get("reject_filename")
            if isinstance(reject_filename, str) and reject_filename in filename:
                errors.append(
                    ValidationError(
                        error=f"Filename not allowed: {filename}",
                        item_index=str(i),
                        media_source=str(item.content)[:50],
                        media_type=item.media_type,
                    )
                )

        if errors:
            raise MediaValidationError(errors)

    def delete_post(self, post_id: str) -> bool:
        """Delete post with potential failures."""
        fail_delete = self.fail_conditions.get("fail_delete", [])
        if isinstance(fail_delete, list) and post_id in fail_delete:
            raise Exception(f"Simulated deletion failure for {post_id}")

        self.deleted_posts.append(post_id)
        return True


class TestValidationPipelineIntegration:
    """Test complete validation pipeline with realistic scenarios."""

    def test_mixed_media_sources_success(self):
        """Test validation pipeline with URLs, files, and bytes."""
        service = IntegrationTestService()

        # Create temporary test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            test_content = b"test image content" * 1000  # ~18KB
            tmp_file.write(test_content)
            tmp_file.flush()

            try:
                with patch("hydra_poster.base.requests.get") as mock_get:
                    # Mock successful URL download
                    mock_response = Mock()
                    mock_response.content = b"downloaded image data" * 500  # ~9KB
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response

                    media = [
                        MediaItem(
                            content="https://example.com/image.jpg", media_type="image"
                        ),
                        MediaItem(content=tmp_file.name, media_type="image"),
                        MediaItem(
                            content=b"raw bytes content" * 800,
                            media_type="image",
                            filename="raw.jpg",
                        ),  # ~14KB
                        MediaItem(
                            content="https://example.com/doc.pdf", media_type="document"
                        ),
                    ]

                    # Should complete all validation phases successfully
                    result = service.post("Test with mixed media sources", media=media)

                    assert result.post_id == "integration_post_1"
                    assert result.media_ids == [
                        "media_0",
                        "media_1",
                        "media_2",
                        "media_3",
                    ]
                    assert service.validation_calls == 1

            finally:
                Path(tmp_file.name).unlink()

    def test_validation_pipeline_failure_modes(self):
        """Test validation pipeline with various failure modes."""
        service = IntegrationTestService(
            max_media_size_mb=0.01
        )  # Very small limit (10KB)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            # Create file larger than limit
            large_content = b"x" * (20 * 1024)  # 20KB
            tmp_file.write(large_content)
            tmp_file.flush()

            try:
                with patch("hydra_poster.base.requests.get") as mock_get:
                    # Mock failed URL download
                    mock_get.side_effect = Exception("Network error")

                    media = [
                        # Structure error - missing media_type
                        MediaItem(content=b"data", media_type="", filename="bad.jpg"),
                        # Accessibility error - URL download fails
                        MediaItem(
                            content="https://fail.com/image.jpg", media_type="image"
                        ),
                        # Platform error - file too large
                        MediaItem(content=tmp_file.name, media_type="image"),
                    ]

                    with pytest.raises(MediaValidationError) as exc_info:
                        service.validate_media_pipeline(media)

                    # Should fail at structure validation phase (first error)
                    errors = exc_info.value.errors
                    assert (
                        len(errors) == 1
                    )  # Only structure error, pipeline stops early
                    assert "media_type is required" in errors[0]["error"]
                    assert errors[0]["item_index"] == "0"

            finally:
                Path(tmp_file.name).unlink()

    def test_validation_pipeline_phases_isolation(self):
        """Test that validation phases are properly isolated."""
        service = IntegrationTestService()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(b"valid content")
            tmp_file.flush()

            try:
                # Test each phase can succeed independently

                # Phase 1: Structure validation only
                media_structure_invalid = [
                    MediaItem(content=b"data", media_type="", filename="test.jpg")
                ]
                with pytest.raises(MediaValidationError) as exc_info:
                    service._validate_media_structure(media_structure_invalid)
                assert len(exc_info.value.errors) == 1

                # Phase 2: Accessibility validation (structure valid)
                media_access_invalid = [
                    MediaItem(content="nonexistent.jpg", media_type="image")
                ]
                with pytest.raises(MediaValidationError):
                    service._validate_media_accessibility(media_access_invalid)

                # Phase 3: Platform validation (structure + accessibility valid)
                media_platform_invalid = [
                    MediaItem(
                        content=tmp_file.name, media_type="image"
                    )  # Valid structure + accessibility
                ]
                # Override to make it fail platform validation
                service.max_media_size_mb = 0.000001  # Impossibly small
                with pytest.raises(MediaValidationError):
                    service.validate_media(media_platform_invalid)

            finally:
                Path(tmp_file.name).unlink()


class TestThreadingWorkflowIntegration:
    """Test complete threading workflows with complex scenarios."""

    def test_thread_with_progressive_media_complexity(self):
        """Test threading with increasingly complex media configurations."""
        service = IntegrationTestService(upload_delay=0.1)  # Small delay to test timing

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(b"test content" * 100)
            tmp_file.flush()

            try:
                with patch("hydra_poster.base.requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.content = b"url content"
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response

                    messages = [
                        "First post with no media",
                        "Second post with single image",
                        "Third post with mixed media types",
                        "Fourth post with maximum media count",
                    ]

                    media = [
                        [],  # No media
                        [
                            MediaItem(
                                content=b"image1",
                                media_type="image",
                                filename="img1.jpg",
                            )
                        ],  # Single
                        [
                            MediaItem(content=tmp_file.name, media_type="image"),
                            MediaItem(
                                content="https://example.com/doc.pdf",
                                media_type="document",
                            ),
                        ],  # Mixed
                        [
                            MediaItem(
                                content=b"img" + str(i).encode(),
                                media_type="image",
                                filename=f"img{i}.jpg",
                            )
                            for i in range(4)
                        ],  # Maximum count
                    ]

                    start_time = time.time()
                    result = service.post_thread(messages, media=media)
                    total_time = time.time() - start_time

                    assert result.post_count == 4
                    assert len(result.post_results) == 4
                    assert result.thread_id == "integration_post_1"

                    # Verify reply chain structure
                    assert (
                        result.post_results[0].metadata
                        and result.post_results[0].metadata["reply_to"] == ""
                    )
                    assert (
                        result.post_results[1].metadata
                        and result.post_results[1].metadata["reply_to"]
                        == "integration_post_1"
                    )
                    assert (
                        result.post_results[2].metadata
                        and result.post_results[2].metadata["reply_to"]
                        == "integration_post_2"
                    )
                    assert (
                        result.post_results[3].metadata
                        and result.post_results[3].metadata["reply_to"]
                        == "integration_post_3"
                    )

                    # Verify media was processed correctly
                    assert result.post_results[0].media_ids is None
                    assert result.post_results[1].media_ids == ["media_0"]
                    assert result.post_results[2].media_ids == ["media_0", "media_1"]
                    assert result.post_results[3].media_ids == [
                        "media_0",
                        "media_1",
                        "media_2",
                        "media_3",
                    ]

                    # Should have some upload delay
                    assert total_time >= 0.7  # 0 + 0.1 + 0.2 + 0.4 = 0.7s minimum

            finally:
                Path(tmp_file.name).unlink()

    @pytest.mark.slow
    def test_thread_validation_failure_rollback_behavior(self):
        """Test threading with validation failure and complex rollback scenarios."""
        service = IntegrationTestService(
            fail_conditions={
                "fail_after_validation": 3,  # Fail on 3rd post after validation
                "fail_delete": [
                    "integration_post_2"
                ],  # Simulate partial rollback failure
            }
        )

        messages = ["Post 1", "Post 2", "Post 3", "Post 4"]
        media = [
            [MediaItem(content=b"content1", media_type="image", filename="img1.jpg")],
            [MediaItem(content=b"content2", media_type="image", filename="img2.jpg")],
            [MediaItem(content=b"content3", media_type="image", filename="img3.jpg")],
            [MediaItem(content=b"content4", media_type="image", filename="img4.jpg")],
        ]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages, media=media)

        error = exc_info.value
        assert error.posted_count == 2  # Only first 2 posts succeeded
        assert error.rollback_attempted is True
        assert "Failed to rollback posts: ['integration_post_2']" in str(error)

        # Verify partial rollback occurred
        assert "integration_post_1" in service.deleted_posts  # Successfully deleted
        assert "integration_post_2" not in service.deleted_posts  # Failed to delete
        assert service.validation_calls == 3  # Validated 3 posts before failure

    def test_thread_mixed_validation_failures(self):
        """Test thread where different posts have different validation failures."""
        service = IntegrationTestService(
            max_media_count=2, fail_conditions={"reject_filename": "bad.jpg"}
        )

        messages = [
            "Good post",
            "Bad filename post",
            "Too many media post",
            "Another good post",
        ]
        media = [
            [
                MediaItem(content=b"ok", media_type="image", filename="good.jpg")
            ],  # Valid
            [
                MediaItem(content=b"bad", media_type="image", filename="bad.jpg")
            ],  # Invalid filename
            [
                MediaItem(content=b"too", media_type="image", filename="img1.jpg"),
                MediaItem(content=b"many", media_type="image", filename="img2.jpg"),
                MediaItem(content=b"media", media_type="image", filename="img3.jpg"),
            ],  # Too many media
            [
                MediaItem(content=b"good", media_type="image", filename="final.jpg")
            ],  # Valid
        ]

        # First post should succeed, second should fail during validation
        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages, media=media)

        error = exc_info.value
        assert error.posted_count == 1  # Only first post succeeded
        assert error.rollback_attempted is True
        assert "All posted content has been rolled back" in str(error)
        assert "integration_post_1" in service.deleted_posts


class TestPerformanceCharacteristics:
    """Test performance aspects of validation and posting."""

    def test_flyweight_validator_efficiency(self):
        """Test that MediaValidator flyweight pattern is memory efficient."""
        # Create many MediaItems with same validator
        items = []
        for i in range(1000):
            item = MediaItem(
                content=b"test" * 100, media_type="image", filename=f"test{i}.jpg"
            )
            items.append(item)

        # All items should use same validator instance
        for item in items:
            # Directly check the global validator is used
            errors1 = _media_validator.validate_structure(item)
            errors2 = _media_validator.validate_structure(item)
            assert errors1 == errors2  # Same results

        # Validator should be stateless - no cross-contamination
        good_item = MediaItem(content=b"good", media_type="image", filename="good.jpg")
        bad_item = MediaItem(content=b"bad", media_type="")  # Missing media_type

        good_errors = _media_validator.validate_structure(good_item)
        bad_errors = _media_validator.validate_structure(bad_item)

        assert len(good_errors) == 0
        assert len(bad_errors) == 2  # Missing media_type AND missing filename for bytes
        assert any("media_type is required" in error["error"] for error in bad_errors)
        assert any(
            "filename is required when content is bytes" in error["error"]
            for error in bad_errors
        )

    def test_concurrent_validation_performance(self):
        """Test validation performance under concurrent load."""
        service = IntegrationTestService(
            max_media_count=10
        )  # Allow larger batches for performance testing

        def validate_batch(batch_id: int) -> tuple[int, float]:
            """Validate a batch of media items and return timing."""
            media_batch = [
                MediaItem(
                    content=b"test" * (100 * i),
                    media_type="image",
                    filename=f"batch{batch_id}_item{i}.jpg",
                )
                for i in range(10)
            ]

            start_time = time.time()
            service.validate_media_pipeline(media_batch)
            end_time = time.time()

            return batch_id, end_time - start_time

        # Run concurrent validation
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(validate_batch, i) for i in range(20)]
            results = []

            for future in as_completed(futures):
                batch_id, duration = future.result()
                results.append((batch_id, duration))

        # All batches should complete successfully
        assert len(results) == 20

        # Performance should be reasonable (less than 1s per batch under normal conditions)
        avg_duration = sum(duration for _, duration in results) / len(results)
        assert avg_duration < 1.0, (
            f"Average validation time too slow: {avg_duration:.2f}s"
        )

    def test_content_caching_efficiency(self):
        """Test that content caching improves performance on repeated access."""
        with patch("hydra_poster.base.requests.get") as mock_get:
            # Mock network delay
            def slow_get(*args, **kwargs):
                time.sleep(0.1)  # Simulate network latency - keep real for this test
                mock_response = Mock()
                mock_response.content = b"cached content"
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = slow_get

            item = MediaItem(
                content="https://slow.example.com/image.jpg", media_type="image"
            )

            # First access should be slow
            start_time = time.time()
            content1 = item.normalized_content
            first_duration = time.time() - start_time

            # Second access should be fast (cached)
            start_time = time.time()
            content2 = item.normalized_content
            second_duration = time.time() - start_time

            assert content1 == content2
            assert first_duration >= 0.1  # First call hit network
            assert second_duration < 0.01  # Second call used cache
            assert mock_get.call_count == 1  # Only one network call


class TestErrorPropagationIntegration:
    """Test error propagation through the complete stack."""

    def test_nested_exception_propagation(self):
        """Test that exceptions bubble up correctly through all layers."""
        service = IntegrationTestService()

        # Test structure validation error propagation
        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(
                ["Test post"],
                media=[
                    [MediaItem(content=b"data", media_type="")]
                ],  # Invalid structure
            )

        # Should have original MediaValidationError as cause
        assert isinstance(exc_info.value.__cause__, MediaValidationError)
        # Check that the underlying errors contain the expected error
        errors = exc_info.value.__cause__.errors
        assert any("media_type is required" in error["error"] for error in errors)

        # Test accessibility error propagation
        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(
                ["Test post"],
                media=[[MediaItem(content="nonexistent.jpg", media_type="image")]],
            )

        assert isinstance(exc_info.value.__cause__, MediaValidationError)
        errors = exc_info.value.__cause__.errors
        assert any("File does not exist" in error["error"] for error in errors)

    def test_platform_specific_error_enrichment(self):
        """Test that platform validation adds context to errors."""
        service = IntegrationTestService(
            max_media_size_mb=0.001,  # Very small limit
            fail_conditions={"reject_filename": "forbidden"},
        )

        large_content = b"x" * (10 * 1024)  # 10KB, exceeds 0.001MB limit
        media = [
            MediaItem(content=large_content, media_type="image", filename="large.jpg"),
            MediaItem(content=b"small", media_type="image", filename="forbidden.jpg"),
        ]

        with pytest.raises(MediaValidationError) as exc_info:
            service.validate_media_pipeline(media)

        errors = exc_info.value.errors
        assert len(errors) == 2

        # Errors should have item indices for debugging
        error_by_index = {error["item_index"]: error for error in errors}
        assert "0" in error_by_index
        assert "1" in error_by_index

        # Should have detailed error messages
        assert "exceeds 0.001MB limit" in error_by_index["0"]["error"]
        assert "forbidden.jpg" in error_by_index["1"]["error"]

    @pytest.mark.slow
    def test_rollback_error_aggregation(self):
        """Test proper aggregation of rollback errors."""
        service = IntegrationTestService(
            fail_conditions={
                "fail_after_validation": 4,  # Fail on 4th post
                "fail_delete": [
                    "integration_post_1",
                    "integration_post_3",
                ],  # Multiple delete failures
            }
        )

        messages = ["Post 1", "Post 2", "Post 3", "Post 4", "Post 5"]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(messages)

        error = exc_info.value
        assert error.posted_count == 3
        assert error.rollback_attempted is True

        # Should report all failed deletions
        assert (
            "Failed to rollback posts: ['integration_post_3', 'integration_post_1']"
            in str(error)
        )

        # Partial rollback should still delete what it can
        assert "integration_post_2" in service.deleted_posts
        assert "integration_post_1" not in service.deleted_posts
        assert "integration_post_3" not in service.deleted_posts


class TestRealisticScenarios:
    """Test realistic usage scenarios that combine multiple aspects."""

    def test_social_media_campaign_workflow(self):
        """Test posting a complete social media campaign with mixed content."""
        service = IntegrationTestService(upload_delay=0.05)  # Realistic upload timing

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as hero_image:
            hero_image.write(b"hero image content" * 1000)  # ~17KB
            hero_image.flush()

            try:
                with patch("hydra_poster.base.requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.content = b"brand logo" * 500
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response

                    # Campaign: Announcement → Details → Call to Action → Thank You
                    campaign_messages = [
                        "🚀 Exciting news! We're launching our new product next week. Stay tuned for details! #ProductLaunch",
                        "Here's what makes our product special: innovative design, user-friendly interface, and powerful features.",
                        "Ready to try it? Sign up for early access at our website. Limited spots available! ⏰",
                        "Thanks to everyone who signed up! We're overwhelmed by the positive response. 🙏",
                    ]

                    campaign_media = [
                        [
                            MediaItem(content=hero_image.name, media_type="image")
                        ],  # Hero image
                        [
                            MediaItem(
                                content=b"feature screenshot" * 800,
                                media_type="image",
                                filename="features.png",
                            )
                        ],  # Screenshot
                        [
                            MediaItem(
                                content="https://cdn.example.com/logo.png",
                                media_type="image",
                            )
                        ],  # Logo from CDN
                        [],  # No media for thank you
                    ]

                    # Post campaign as connected thread
                    result = service.post_thread(
                        campaign_messages,
                        media=campaign_media,
                        config=PostConfig(
                            visibility="public",
                            metadata={
                                "campaign": "product_launch",
                                "team": "marketing",
                            },
                        ),
                    )

                    assert result.post_count == 4
                    assert result.platform == "integration-test"
                    assert all(
                        "integration_post_" in post.post_id
                        for post in result.post_results
                    )

                    # Verify media processing
                    assert (
                        result.post_results[0].media_ids
                        and len(result.post_results[0].media_ids) == 1
                    )  # Hero image
                    assert (
                        result.post_results[1].media_ids
                        and len(result.post_results[1].media_ids) == 1
                    )  # Screenshot
                    assert (
                        result.post_results[2].media_ids
                        and len(result.post_results[2].media_ids) == 1
                    )  # Logo
                    assert result.post_results[3].media_ids is None  # No media

                    # Campaign should complete in reasonable time
                    assert len(service.upload_times) == 3  # 3 posts with media
                    assert all(
                        t >= 0.05 for t in service.upload_times
                    )  # Minimum upload delay

            finally:
                Path(hero_image.name).unlink()

    def test_high_volume_content_batch(self):
        """Test posting high volume content with resource management."""
        service = IntegrationTestService(max_media_count=2)  # Constrained service

        # Generate batch of 50 posts with various media configurations
        batch_messages = [f"Batch post #{i + 1} with unique content" for i in range(50)]
        batch_media: list[list[MediaItem]] = []

        for i in range(50):
            if i % 3 == 0:  # Every 3rd post has no media
                batch_media.append([])
            elif i % 3 == 1:  # Every 3rd post has single media
                batch_media.append(
                    [
                        MediaItem(
                            content=f"content_{i}".encode() * 100,
                            media_type="image",
                            filename=f"img_{i}.jpg",
                        )
                    ]
                )
            else:  # Every 3rd post has max media
                batch_media.append(
                    [
                        MediaItem(
                            content=f"content_{i}_1".encode() * 100,
                            media_type="image",
                            filename=f"img_{i}_1.jpg",
                        ),
                        MediaItem(
                            content=f"content_{i}_2".encode() * 100,
                            media_type="image",
                            filename=f"img_{i}_2.jpg",
                        ),
                    ]
                )

        # Post batch as thread (this would be a very long thread in reality)
        result = service.post_thread(batch_messages, media=batch_media)

        assert result.post_count == 50

        # Verify media distribution
        no_media_count = sum(
            1 for post in result.post_results if post.media_ids is None
        )
        single_media_count = sum(
            1
            for post in result.post_results
            if post.media_ids and len(post.media_ids) == 1
        )
        double_media_count = sum(
            1
            for post in result.post_results
            if post.media_ids and len(post.media_ids) == 2
        )

        assert no_media_count == 17  # Posts 0, 3, 6, ..., 48 (17 posts)
        assert single_media_count == 17  # Posts 1, 4, 7, ..., 49 (17 posts)
        assert double_media_count == 16  # Posts 2, 5, 8, ..., 47 (16 posts)

        # Note: validation_calls might be less than 50 if some posts have no media
        # and the service optimizes by not calling validate_media for empty lists
        assert service.validation_calls <= 50  # Should not exceed the number of posts
        assert (
            service.validation_calls >= 33
        )  # At least the posts with media were validated

    @pytest.mark.slow
    def test_disaster_recovery_workflow(self):
        """Test system behavior under various failure conditions."""
        failure_conditions: dict[str, str | int | list[str]] = {
            "fail_after_validation": 15,  # Fail after 15 successful posts
            "fail_delete": [
                f"integration_post_{i}" for i in range(5, 10)
            ],  # Fail to delete posts 5-9
        }
        service = IntegrationTestService(fail_conditions=failure_conditions)

        # Attempt large thread that will fail partway through
        disaster_messages = [f"Message {i}" for i in range(20)]

        with pytest.raises(ThreadPostingError) as exc_info:
            service.post_thread(disaster_messages)

        error = exc_info.value
        assert error.posted_count == 14  # 14 posts succeeded before failure
        assert error.rollback_attempted is True

        # Verify partial rollback behavior
        successful_deletions = [
            p for p in service.deleted_posts if "integration_post_" in p
        ]
        failed_deletions = [f"integration_post_{i}" for i in range(5, 10)]

        # Should have attempted to delete posts 14 down to 1 in reverse order
        # But posts 5-9 (inclusive) would fail to delete
        expected_successful_deletions = [
            f"integration_post_{i}" for i in range(14, 0, -1) if i not in range(5, 10)
        ]

        # Check that we successfully deleted what we expected
        assert set(successful_deletions) == set(expected_successful_deletions)

        # Verify the error message mentions the failed deletions
        error_message = str(error)
        assert "Failed to rollback posts:" in error_message
        # Check that posts 5-9 are mentioned as failures (they may be in reverse order)
        for i in range(5, 10):
            assert f"integration_post_{i}" in error_message
