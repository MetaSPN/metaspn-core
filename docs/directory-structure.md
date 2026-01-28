# Directory Structure

This document describes the complete directory structure for MetaSPN content repositories.

## Overview

```
my-content/
├── .metaspn/                     # Repository metadata
│   ├── profile.json              # User identity
│   └── config.json               # Repository configuration
│
├── sources/                      # EXTERNAL INPUTS (consumed content)
│   ├── podcasts/
│   │   └── listening-events.jsonl
│   ├── books/
│   │   └── reading-events.jsonl
│   ├── blogs/
│   │   └── reading-events.jsonl
│   └── twitter/
│       └── engagement-events.jsonl
│
├── artifacts/                    # YOUR OUTPUTS (created content)
│   ├── twitter/
│   │   └── tweets.jsonl
│   ├── podcast/
│   │   └── episodes.jsonl
│   ├── blog/
│   │   └── posts.jsonl
│   ├── youtube/
│   │   └── videos.jsonl
│   │
│   ├── enhancements/             # Computed layers
│   │   ├── quality_scores/
│   │   │   ├── latest.jsonl
│   │   │   └── history/
│   │   │       └── 2024-01-28_v1.0_algorithm_update.jsonl
│   │   ├── game_signatures/
│   │   │   ├── latest.jsonl
│   │   │   └── history/
│   │   └── embeddings/
│   │       ├── latest.jsonl
│   │       └── history/
│   │
│   └── indexes/                  # Fast lookup indexes
│       ├── manifest.json
│       ├── by_date/
│       │   ├── 2024-01.json
│       │   └── 2024-02.json
│       └── by_platform/
│           ├── twitter.json
│           └── podcast.json
│
└── reports/                      # Computed outputs
    ├── profiles/
    │   └── latest.json
    └── cards/
        └── *.json
```

## Directory Details

### `.metaspn/` - Repository Metadata

Contains repository configuration and user identity.

#### `profile.json`

User identity and basic metadata:

```json
{
  "user_id": "leo_guinan",
  "name": "Leo Guinan",
  "handle": "@leo_guinan",
  "avatar_url": "https://...",
  "created_at": "2024-01-28T12:00:00Z",
  "version": "2.0.0"
}
```

#### `config.json`

Repository configuration:

```json
{
  "version": "2.0.0",
  "source_platforms": ["podcasts", "books", "blogs", "twitter"],
  "artifact_platforms": ["twitter", "podcast", "blog", "youtube"],
  "created_at": "2024-01-28T12:00:00Z"
}
```

---

### `sources/` - External Inputs

Content you **consumed** (read, listened to, watched, engaged with).

| Directory | File | Description |
|-----------|------|-------------|
| `sources/podcasts/` | `listening-events.jsonl` | Podcast episodes you listened to |
| `sources/books/` | `reading-events.jsonl` | Books you read |
| `sources/blogs/` | `reading-events.jsonl` | Blog posts/articles you read |
| `sources/twitter/` | `engagement-events.jsonl` | Others' tweets you engaged with |

**Key principle:** Sources represent content created by others that you consumed or engaged with.

---

### `artifacts/` - Your Outputs

Content **you created** (wrote, published, posted).

| Directory | File | Description |
|-----------|------|-------------|
| `artifacts/twitter/` | `tweets.jsonl` | Your tweets |
| `artifacts/podcast/` | `episodes.jsonl` | Your podcast episodes |
| `artifacts/blog/` | `posts.jsonl` | Your blog posts |
| `artifacts/youtube/` | `videos.jsonl` | Your YouTube videos |

**Key principle:** Artifacts represent content you authored and published.

---

### `artifacts/enhancements/` - Computed Layers

Computed metrics and classifications stored separately from raw data.

```
enhancements/
├── quality_scores/
│   ├── latest.jsonl           # Current scores
│   └── history/               # Archived when algorithm changes
│       └── 2024-01-28_v1.0_algorithm_update.jsonl
├── game_signatures/
│   ├── latest.jsonl
│   └── history/
└── embeddings/
    ├── latest.jsonl
    └── history/
```

**Enhancement types:**

| Type | Description |
|------|-------------|
| `quality_scores` | Content quality metrics (0-1 scale) |
| `game_signatures` | Founder game classifications (G1-G6) |
| `embeddings` | Vector embeddings for semantic search |

**History preservation:**
- When algorithms are updated, current `latest.jsonl` is archived to `history/`
- Archive filename format: `{date}_v{version}_{reason}.jsonl`
- This enables tracking how scores evolved over time

---

### `artifacts/indexes/` - Fast Lookup Indexes

Pre-computed indexes for efficient querying without scanning all files.

#### `manifest.json`

Master catalog of all activities:

```json
{
  "version": "2.0",
  "last_updated": "2024-01-28T12:00:00Z",
  "total_activities": 42390,
  "activities": {
    "twitter_1327008879046225921": {
      "activity_id": "twitter_1327008879046225921",
      "source_type": "artifact",
      "platform": "twitter",
      "activity_type": "create",
      "timestamp": "2020-11-12T17:02:26Z",
      "file_path": "artifacts/twitter/tweets.jsonl",
      "line_number": 1
    }
  },
  "stats": {
    "by_platform": {"twitter": 38880, "podcast": 3000},
    "by_year": {"2020": 5000, "2021": 12000},
    "by_type": {"create": 40000, "consume": 2390}
  }
}
```

#### `by_date/{YYYY-MM}.json`

Activity IDs grouped by month:

```json
{
  "month": "2024-01",
  "activity_ids": ["twitter_123", "podcast_456", "..."]
}
```

#### `by_platform/{platform}.json`

Activity IDs grouped by platform:

```json
{
  "platform": "twitter",
  "activity_ids": ["twitter_123", "twitter_456", "..."]
}
```

---

### `reports/` - Computed Outputs

Generated reports and cards.

| Directory | Description |
|-----------|-------------|
| `reports/profiles/` | Cached profile computations |
| `reports/cards/` | Generated trading card data |

---

## File Naming Conventions

### Activity Files

All activity files use JSONL format (one JSON object per line):

- `tweets.jsonl` - Twitter activities
- `episodes.jsonl` - Podcast activities
- `posts.jsonl` - Blog activities
- `videos.jsonl` - YouTube activities
- `listening-events.jsonl` - Podcast consumption
- `reading-events.jsonl` - Book/blog consumption
- `engagement-events.jsonl` - Social engagement

### Enhancement Files

- `latest.jsonl` - Current enhancement records
- `{date}_v{version}_{reason}.jsonl` - Historical archives

### Index Files

- `manifest.json` - Master activity index
- `{YYYY-MM}.json` - Date-based index
- `{platform}.json` - Platform-based index

---

## Creating a New Repository

Use the CLI to initialize a new repository with the correct structure:

```bash
metaspn init ./my-content \
  --user-id "your_username" \
  --name "Your Name" \
  --handle "@your_handle"
```

This creates all required directories with `.gitkeep` files.

---

## Platform Mapping

Note the singular/plural naming differences:

| Sources (consumed) | Artifacts (created) |
|--------------------|---------------------|
| `sources/podcasts/` | `artifacts/podcast/` |
| `sources/books/` | (no artifact equivalent) |
| `sources/blogs/` | `artifacts/blog/` |
| `sources/twitter/` | `artifacts/twitter/` |
| (no source equivalent) | `artifacts/youtube/` |

This reflects the semantic difference:
- Sources: "podcasts I listened to" (plural, collection of others' content)
- Artifacts: "my podcast" (singular, your own show)
