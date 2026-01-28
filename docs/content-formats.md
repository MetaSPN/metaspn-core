# Content Formats

This document describes the canonical JSON formats for each content type in MetaSPN repositories.

## General Structure

All activities share a common base structure:

```json
{
  "activity_id": "platform_uniqueid",
  "timestamp": "2024-01-28T12:00:00Z",
  "platform": "twitter",
  "activity_type": "create",
  "title": "Optional title",
  "content": "The actual content text",
  "url": "https://...",
  "duration_seconds": 3600,
  "raw_data": {}
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | string | Unique identifier in format `{platform}_{id}` |
| `timestamp` | string | ISO 8601 datetime with timezone |
| `platform` | string | Platform name (twitter, podcast, blog, youtube) |
| `activity_type` | string | Either `"create"` or `"consume"` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Title of the content (if applicable) |
| `content` | string | The actual text content |
| `url` | string | URL to the original content |
| `duration_seconds` | integer | Duration in seconds (for audio/video) |
| `raw_data` | object | Platform-specific additional data |

---

## Twitter

### Your Tweets (Artifacts)

**File:** `artifacts/twitter/tweets.jsonl`

```json
{
  "activity_id": "twitter_1327008879046225921",
  "timestamp": "2020-11-12T17:02:26Z",
  "platform": "twitter",
  "activity_type": "create",
  "content": "Just shipped a new feature! Here's what I learned...",
  "url": "https://twitter.com/leo_guinan/status/1327008879046225921",
  "raw_data": {
    "tweet_id": "1327008879046225921",
    "username": "leo_guinan",
    "tweet_type": "original",
    "metrics": {
      "likes": 42,
      "retweets": 5,
      "replies": 3
    },
    "is_reply": false,
    "is_retweet": false,
    "is_quote": false,
    "in_reply_to_user": null,
    "quoted_tweet_id": null
  }
}
```

#### Tweet Types

| Type | Description |
|------|-------------|
| `original` | Original tweet |
| `reply` | Reply to another tweet |
| `retweet` | Retweet (use `RT @user:` prefix in content) |
| `quote` | Quote tweet |

### Engagement Events (Sources)

**File:** `sources/twitter/engagement-events.jsonl`

Others' tweets you liked, retweeted, or replied to:

```json
{
  "activity_id": "twitter_engage_1327008879046225921",
  "timestamp": "2024-01-28T12:00:00Z",
  "platform": "twitter",
  "activity_type": "consume",
  "content": "Original tweet content you engaged with",
  "url": "https://twitter.com/other_user/status/1327008879046225921",
  "raw_data": {
    "tweet_id": "1327008879046225921",
    "author_username": "other_user",
    "engagement_type": "like",
    "original_metrics": {
      "likes": 1000,
      "retweets": 50
    }
  }
}
```

---

## Podcast

### Your Episodes (Artifacts)

**File:** `artifacts/podcast/episodes.jsonl`

```json
{
  "activity_id": "podcast_ep_123",
  "timestamp": "2024-01-28T12:00:00Z",
  "platform": "podcast",
  "activity_type": "create",
  "title": "Episode 42: Building in Public",
  "content": "In this episode, we discuss the benefits of building in public...",
  "url": "https://yourpodcast.com/episodes/42",
  "duration_seconds": 3600,
  "raw_data": {
    "episode_id": "ep_123",
    "episode_number": 42,
    "season": 2,
    "show_title": "Your Podcast Name",
    "show_id": "show_456",
    "guid": "unique-guid-123",
    "audio_url": "https://cdn.example.com/episode42.mp3",
    "transcript_url": "https://yourpodcast.com/episodes/42/transcript"
  }
}
```

### Listening Events (Sources)

**File:** `sources/podcasts/listening-events.jsonl`

Podcast episodes you listened to:

```json
{
  "activity_id": "podcast_listen_789",
  "timestamp": "2024-01-28T14:30:00Z",
  "platform": "podcast",
  "activity_type": "consume",
  "title": "How I Built This: Airbnb",
  "url": "https://npr.org/podcasts/hibt/airbnb",
  "duration_seconds": 2700,
  "raw_data": {
    "episode_id": "hibt_airbnb",
    "show_title": "How I Built This",
    "show_id": "hibt",
    "listening": {
      "start_time": "2024-01-28T14:00:00Z",
      "end_time": "2024-01-28T14:30:00Z",
      "duration_seconds": 1800,
      "completion_percentage": 67,
      "playback_speed": 1.5
    }
  }
}
```

---

## Blog

### Your Posts (Artifacts)

**File:** `artifacts/blog/posts.jsonl`

```json
{
  "activity_id": "blog_post_abc123",
  "timestamp": "2024-01-28T10:00:00Z",
  "platform": "blog",
  "activity_type": "create",
  "title": "Why I'm Building in Public",
  "content": "Full blog post content here. This should be the plain text version of your post, ideally the full content rather than just an excerpt...",
  "url": "https://yourblog.com/building-in-public",
  "raw_data": {
    "post_id": "abc123",
    "slug": "building-in-public",
    "word_count": 1500,
    "reading_time_minutes": 6,
    "categories": ["entrepreneurship", "building-in-public"],
    "tags": ["startup", "transparency"],
    "excerpt": "A shorter version for previews...",
    "featured_image": "https://yourblog.com/images/building.jpg"
  }
}
```

### Reading Events (Sources)

**File:** `sources/blogs/reading-events.jsonl`

Blog posts/articles you read:

```json
{
  "activity_id": "blog_read_xyz789",
  "timestamp": "2024-01-28T09:15:00Z",
  "platform": "blog",
  "activity_type": "consume",
  "title": "The Mom Test",
  "url": "https://otherblog.com/mom-test-summary",
  "raw_data": {
    "source_url": "https://otherblog.com/mom-test-summary",
    "author": "Other Author",
    "reading": {
      "start_time": "2024-01-28T09:00:00Z",
      "end_time": "2024-01-28T09:15:00Z",
      "duration_seconds": 900,
      "completion_percentage": 100
    }
  }
}
```

---

## YouTube

### Your Videos (Artifacts)

**File:** `artifacts/youtube/videos.jsonl`

```json
{
  "activity_id": "youtube_video_dQw4w9WgXcQ",
  "timestamp": "2024-01-28T16:00:00Z",
  "platform": "youtube",
  "activity_type": "create",
  "title": "How to Build a Startup in 2024",
  "content": "Video description and/or transcript...",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_seconds": 1200,
  "raw_data": {
    "video_id": "dQw4w9WgXcQ",
    "channel_id": "UC123456",
    "channel_name": "Your Channel",
    "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "metrics": {
      "views": 10000,
      "likes": 500,
      "comments": 50
    },
    "categories": ["Education"],
    "tags": ["startup", "entrepreneurship"],
    "transcript_available": true
  }
}
```

---

## Books

### Reading Events (Sources)

**File:** `sources/books/reading-events.jsonl`

```json
{
  "activity_id": "book_read_isbn123",
  "timestamp": "2024-01-28T22:00:00Z",
  "platform": "book",
  "activity_type": "consume",
  "title": "Zero to One",
  "content": "Notes or highlights from the book...",
  "url": "https://goodreads.com/book/show/18050143",
  "raw_data": {
    "isbn": "9780804139298",
    "author": "Peter Thiel",
    "publisher": "Crown Business",
    "year": 2014,
    "reading": {
      "start_date": "2024-01-15",
      "end_date": "2024-01-28",
      "status": "completed",
      "rating": 5,
      "pages_read": 224,
      "total_pages": 224
    },
    "source": "kindle",
    "highlights_count": 42
  }
}
```

---

## Activity ID Format

Activity IDs must be unique across the entire repository. Use this format:

```
{platform}_{unique_identifier}
```

### Examples

| Platform | Format | Example |
|----------|--------|---------|
| Twitter | `twitter_{tweet_id}` | `twitter_1327008879046225921` |
| Podcast (created) | `podcast_ep_{id}` | `podcast_ep_123` |
| Podcast (consumed) | `podcast_listen_{id}` | `podcast_listen_789` |
| Blog (created) | `blog_post_{id}` | `blog_post_abc123` |
| Blog (consumed) | `blog_read_{id}` | `blog_read_xyz789` |
| YouTube | `youtube_video_{id}` | `youtube_video_dQw4w9WgXcQ` |
| Book | `book_read_{isbn}` | `book_read_9780804139298` |

### Uniqueness Requirements

- IDs must be unique within the repository
- Use platform-specific identifiers when available (tweet IDs, video IDs, ISBNs)
- For consumed content without unique IDs, generate a UUID or hash

---

## Timestamp Format

All timestamps must be ISO 8601 format with timezone:

```
2024-01-28T12:00:00Z          # UTC
2024-01-28T12:00:00+00:00     # UTC (explicit)
2024-01-28T07:00:00-05:00     # Eastern Time
```

**Best practice:** Store all timestamps in UTC (`Z` suffix).

---

## Content Guidelines

### Content Field

The `content` field should contain:

- **Tweets:** Full tweet text
- **Podcast episodes:** Description or transcript
- **Blog posts:** Full post text (plain text, not HTML)
- **YouTube videos:** Description or transcript
- **Books:** Notes, highlights, or summary

### Raw Data

The `raw_data` field stores platform-specific information that doesn't fit the common schema. This data is preserved for potential future use but isn't used in standard computations.

Include:
- Platform-specific IDs
- Metrics and engagement data
- Metadata (categories, tags, etc.)
- Playback/reading progress

---

## JSONL Format

All activity files use JSONL (JSON Lines) format:

- One JSON object per line
- No trailing commas
- UTF-8 encoding
- Newline character (`\n`) between records

```jsonl
{"activity_id": "twitter_1", "timestamp": "2024-01-28T12:00:00Z", ...}
{"activity_id": "twitter_2", "timestamp": "2024-01-28T13:00:00Z", ...}
{"activity_id": "twitter_3", "timestamp": "2024-01-28T14:00:00Z", ...}
```

**Benefits of JSONL:**
- Append-only writes (no need to read/parse entire file)
- Line-by-line streaming for large files
- Easy to grep and process with standard tools
