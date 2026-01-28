# MetaSPN Content Repository Documentation

This documentation describes the data lake architecture used by MetaSPN content repositories. External tools and ingestion pipelines should follow these specifications when writing data to a MetaSPN repository.

## Overview

MetaSPN uses a **data lake architecture** with clear separation between:

- **Sources** - External inputs (content you consumed)
- **Artifacts** - Your outputs (content you created)
- **Enhancements** - Computed layers (scores, signatures, embeddings)
- **Indexes** - Fast lookup indexes (manifest, date/platform indexes)

## Key Principles

1. **Each activity exists in exactly ONE location** - no duplication between sources and artifacts
2. **Source data is append-only** - never modify raw data once written
3. **Enhancements are separate computed layers** - can be recomputed without touching source data
4. **Full audit trail** - enhancement history is preserved when algorithms change

## Documentation Index

| Document | Description |
|----------|-------------|
| [Directory Structure](./directory-structure.md) | Complete folder layout and purpose of each directory |
| [Content Formats](./content-formats.md) | Canonical JSON formats for each content type |
| [Enhancements](./enhancements.md) | How enhancement layers work and their formats |
| [CLI Reference](./cli-reference.md) | Command-line tools for managing repositories |
| [Ingestion Guide](./ingestion-guide.md) | Guide for building tools that write to repositories |

## Quick Start

### For Ingestion Tools

When building a tool that writes data to a MetaSPN repository:

1. **Determine if the content is consumed or created**
   - Consumed (read, listened, watched) → `sources/`
   - Created (wrote, published, posted) → `artifacts/`

2. **Use the canonical format** for your content type (see [Content Formats](./content-formats.md))

3. **Generate a unique `activity_id`** in the format `{platform}_{unique_id}`

4. **Write to the correct location**:
   ```
   # Your tweets (created)
   artifacts/twitter/tweets.jsonl

   # Podcasts you listened to (consumed)
   sources/podcasts/listening-events.jsonl
   ```

### For Analysis Tools

When building a tool that reads from a MetaSPN repository:

1. **Use the ActivityLoader** for efficient filtered loading:
   ```python
   from metaspn.repo import ActivityLoader

   loader = ActivityLoader("./my-content")

   # Query with filters
   tweets = list(loader.query(platform="twitter", limit=100))

   # Stream without loading all into memory
   for activity in loader.stream(platform="podcast"):
       process(activity)
   ```

2. **Use the EnhancementStore** to access computed scores:
   ```python
   from metaspn.repo import EnhancementStore

   store = EnhancementStore("./my-content")

   # Get enhanced activities with scores joined
   enhanced = store.get_all_enhanced(activities)
   for ea in enhanced:
       print(f"{ea.activity_id}: quality={ea.quality_score}")
   ```

## Architecture

This documentation describes the current data lake architecture for MetaSPN repositories.

Legacy repository layouts (with `meta.json` at root) are still supported for reading, but new repositories should use the standard structure described here.
