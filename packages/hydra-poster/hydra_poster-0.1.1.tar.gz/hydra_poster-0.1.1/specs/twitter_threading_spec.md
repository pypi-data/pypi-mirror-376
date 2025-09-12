# Twitter Threading Specification

## Overview

Extension to the TwitterService class to support native Twitter threading functionality. Maintains the library's core principles of stateless operations, all-or-nothing posting, and comprehensive error handling.

## Core Threading Methods

### Required Methods

```python
class TwitterService(SocialMediaService):
    # Core methods from main spec...
    
    def post_thread(self, messages: List[str], 
                   media: List[List[MediaItem]] = None,
                   rollback_on_failure: bool = True) -> ThreadResult:
        """Post a series of connected tweets as a thread"""
        pass
    
    def reply_to_tweet(self, reply_to_id: str, text: str, 
                      media: List[MediaItem] = None) -> PostResult:
        """Reply to a specific tweet (building block for threads)"""
        pass
```

### Optional Methods

```python
    def continue_thread(self, thread_id: str, messages: List[str],
                       media: List[List[MediaItem]] = None,
                       rollback_on_failure: bool = True) -> ThreadResult:
        """Add more tweets to an existing thread"""
        pass
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a specific tweet (used for rollback)"""
        pass
```

## Data Structures

### ThreadResult Schema

```python
@dataclass
class ThreadResult:
    platform: str = "twitter"
    thread_id: str              # ID of the first tweet in thread
    post_results: List[PostResult]  # All individual tweet results
    thread_url: str             # URL to the first tweet
    
    @property
    def tweet_count(self) -> int:
        return len(self.post_results)
    
    @property
    def last_tweet_id(self) -> str:
        return self.post_results[-1].post_id if self.post_results else None
```

### ThreadPostingError

```python
class ThreadPostingError(TwitterError):
    """Thread posting failed"""
    def __init__(self, message: str, posted_count: int, rollback_attempted: bool):
        self.posted_count = posted_count
        self.rollback_attempted = rollback_attempted
        super().__init__(message)
```

## Threading Behavior

### All-or-Nothing Guarantee

- **Success**: All tweets posted successfully, ThreadResult returned
- **Failure with rollback=True**: All posted tweets deleted, ThreadPostingError raised
- **Failure with rollback=False**: Partial thread remains, ThreadPostingError raised with posted_count

### Sequential Posting Process

1. **Validate all messages** - check character limits, media constraints
2. **Post first tweet** - becomes the thread root
3. **Post subsequent tweets as replies** - each replies to the previous tweet
4. **On failure**: Delete all posted tweets if rollback_on_failure=True

### Media Handling

- `media` parameter is `List[List[MediaItem]]` - one list per tweet
- Each tweet's media validated independently
- Media validation follows same rules as single posts

## Usage Examples

### Basic Threading

```python
from hydra_poster import TwitterService

messages = [
    "This is tweet 1/3 about Python threading...",
    "Tweet 2/3: Here's how we implement it...", 
    "Tweet 3/3: And that's how it works! 🧵"
]

twitter = TwitterService(credentials)
try:
    thread = twitter.post_thread(messages)
    print(f"Thread posted: {thread.thread_url}")
    print(f"Posted {thread.tweet_count} tweets")
except ThreadPostingError as e:
    print(f"Thread failed after {e.posted_count} tweets")
    if e.rollback_attempted:
        print("Posted tweets have been deleted")
```

### Threading with Media

```python
messages = ["Check out these photos!", "And here's a video:"]
media = [
    [MediaItem("photo1.jpg", "image"), MediaItem("photo2.jpg", "image")],
    [MediaItem("video.mp4", "video")]
]

thread = twitter.post_thread(messages, media=media)
```

### No Rollback Mode

```python
# Keep partial threads on failure
thread = twitter.post_thread(messages, rollback_on_failure=False)
```

### Manual Thread Building

```python
# Post individual tweets manually
first_tweet = twitter.post("Starting a thread...")
reply = twitter.reply_to_tweet(first_tweet.post_id, "This is tweet 2...")
final = twitter.reply_to_tweet(reply.post_id, "End of thread!")
```

### Continue Existing Thread

```python
# Add more tweets to an existing thread
existing_thread_id = "1234567890"
more_messages = ["Additional point 1", "Additional point 2"]
extended = twitter.continue_thread(existing_thread_id, more_messages)
```

## Validation Rules

### Thread Validation

- **Message count**: No hard limit, but warn for threads >20 tweets (quota concerns)
- **Character limits**: Each tweet must meet Twitter's character requirements
- **Media limits**: Each tweet's media must pass individual validation
- **Content policy**: Each tweet validated against Twitter's content rules

### Media Validation per Tweet

- **Images**: Max 4 per tweet, same format/size rules as single posts
- **Videos**: Max 1 per tweet, same format/size rules as single posts
- **Mixed media**: Cannot mix images and videos in single tweet

## Error Handling

### Validation Errors

```python
class ThreadValidationError(TwitterError):
    """Thread validation failed before posting"""
    def __init__(self, errors: List[Dict]):
        self.errors = errors  # Per-tweet error details
        super().__init__(f"Thread validation failed for {len(errors)} tweets")
```

### Example Validation Error

```
ThreadValidationError: Thread validation failed for 2 tweets
- Tweet 2: Text exceeds 280 character limit (285 chars)
- Tweet 4: Image 'large.jpg' (8MB) exceeds 5MB limit
```

### Posting Errors

- **Network failures**: Retry logic for temporary failures
- **Rate limiting**: Preserve partial thread, provide clear error message
- **Content violations**: Stop immediately, rollback if enabled
- **Auth errors**: Stop immediately, no rollback needed

## Rate Limiting Considerations

### Free Tier Impact

- **Monthly quota**: Each tweet consumes 1 of 500 monthly posts
- **Hourly limits**: 300 posts per 3 hours (app-level)
- **Thread cost**: 10-tweet thread = 10 posts from monthly quota
- **Rollback cost**: Deleting tweets does NOT refund quota

### Usage Warnings

```python
def validate_thread_quota_impact(self, messages: List[str]) -> None:
    """Warn about quota consumption for large threads"""
    if len(messages) > 10:
        print(f"Warning: {len(messages)} tweets will consume "
              f"{len(messages)}/500 of your monthly free tier quota")
```

## Implementation Notes

### API Endpoints Used

- `POST /2/tweets` - Create tweets and replies
- `DELETE /2/tweets/:id` - Delete tweets (for rollback)
- Standard Twitter API v2 rate limits apply

### Rollback Limitations

- Deletion removes tweets from timelines but traces may remain in:
  - Email notifications already sent
  - Third-party tools that cached the tweets  
  - Screenshots taken by users
  - Web archives

### Authentication

- Uses same OAuth credentials as single tweet posting
- No additional permissions required for threading
- Delete permission required if rollback enabled

## Testing Strategy

### Unit Tests

- Mock Twitter API responses for consistent testing
- Test rollback scenarios with simulated failures
- Validate media handling across multiple tweets
- Test rate limiting behavior

### Integration Tests

- Test against Twitter API with test accounts
- Verify thread creation and linking
- Test deletion/rollback functionality
- Validate error message accuracy

### Edge Cases

- Very long threads (50+ tweets)
- Mixed media types across thread
- Network failures mid-thread
- Rate limiting during thread posting
- Authentication failures mid-thread

This spec provides Claude Code with clear implementation guidance while maintaining the library's core design principles.