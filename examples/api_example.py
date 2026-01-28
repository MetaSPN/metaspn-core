#!/usr/bin/env python3
"""API usage example for MetaSPN.

This script demonstrates how to use the MetaSPN API:
1. Starting the server
2. Making API calls with httpx
3. Working with the responses

Note: This is for demonstration purposes. In production,
you would run the server separately.
"""

import asyncio

# Check if httpx is available
import importlib.util
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

HAS_HTTPX = importlib.util.find_spec("httpx") is not None
if not HAS_HTTPX:
    print("Note: Install httpx to run the API example: pip install httpx")


async def main():
    if not HAS_HTTPX:
        print("httpx not installed. Skipping API example.")
        return

    from metaspn import init_repo
    from metaspn.core.profile import Activity
    from metaspn.repo import add_activity

    # Create a temporary directory for this example
    temp_dir = Path(tempfile.mkdtemp())
    repo_path = temp_dir / "api-example"

    try:
        print("MetaSPN API Usage Example")
        print("=" * 50)

        # Set up a test repository
        print("\n1. Setting up test repository...")
        init_repo(
            str(repo_path),
            {
                "user_id": "api_user",
                "name": "API User",
                "handle": "@api_user",
            },
        )

        # Add some activities
        for i in range(5):
            activity = Activity(
                timestamp=datetime.now() - timedelta(days=i * 5),
                platform="blog",
                activity_type="create",
                title=f"Blog Post {i+1}",
                content="Content " * 100,
            )
            add_activity(str(repo_path), activity)

        print(f"   Created repository at: {repo_path}")

        # Note: In a real scenario, you would start the server first:
        # metaspn serve --port 8000
        #
        # Then make requests to it. Here we'll show the API structure.

        print("\n2. API Endpoints (when server is running):")
        print(
            """
   GET  /                  - API information
   GET  /health            - Health check
   POST /profile           - Compute profile from repo path
   GET  /profile/{user_id} - Get profile by user ID
   POST /cards             - Generate cards
   GET  /cards/{user_id}   - Get cards by user ID
   POST /repo/init         - Initialize a new repository
   GET  /repo/validate     - Validate repository structure
   POST /activity          - Add an activity
   GET  /activities        - List activities
   GET  /stats             - Get repository statistics
"""
        )

        print("\n3. Example API calls (using httpx):")
        print(
            """
# Start the server
# $ metaspn serve --port 8000

# In another terminal or script:
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
    # Health check
    response = await client.get("/health")
    print(response.json())
    # {"status": "healthy", "version": "0.1.0", ...}

    # Compute profile
    response = await client.post("/profile", json={
        "repo_path": "/path/to/repo",
        "force_recompute": False
    })
    profile = response.json()
    print(f"Level: {profile['cards']['level']}")

    # Generate cards
    response = await client.post("/cards", json={
        "repo_path": "/path/to/repo"
    })
    cards = response.json()
    for card in cards:
        print(f"{card['card_type']}: {card['rarity']}")

    # Add activity
    response = await client.post("/activity", json={
        "repo_path": "/path/to/repo",
        "platform": "podcast",
        "activity_type": "create",
        "title": "New Episode",
        "duration_seconds": 3600
    })
    print(response.json())
"""
        )

        print("\n" + "=" * 50)
        print("See the API documentation at http://localhost:8000/docs")
        print("when the server is running.")

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
