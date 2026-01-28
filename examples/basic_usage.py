#!/usr/bin/env python3
"""Basic usage example for MetaSPN.

This script demonstrates the core functionality of the MetaSPN package:
1. Initializing a repository
2. Adding activities
3. Computing a profile
4. Generating cards
"""

import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from metaspn import init_repo, compute_profile, generate_cards
from metaspn.core.profile import Activity
from metaspn.repo import add_activity


def main():
    # Create a temporary directory for this example
    temp_dir = Path(tempfile.mkdtemp())
    repo_path = temp_dir / "my-content"
    
    try:
        print("MetaSPN Basic Usage Example")
        print("=" * 50)
        
        # 1. Initialize a repository
        print("\n1. Initializing repository...")
        init_repo(str(repo_path), {
            "user_id": "example_user",
            "name": "Example User",
            "handle": "@example_user",
        })
        print(f"   Repository created at: {repo_path}")
        
        # 2. Add some activities
        print("\n2. Adding activities...")
        
        activities_data = [
            {
                "platform": "podcast",
                "type": "create",
                "title": "Episode 1: Introduction",
                "content": "Welcome to the show! " * 100,
                "duration_seconds": 3600,
                "days_ago": 30,
            },
            {
                "platform": "podcast",
                "type": "create",
                "title": "Episode 2: Deep Dive",
                "content": "Today we explore in depth... " * 150,
                "duration_seconds": 5400,
                "days_ago": 20,
            },
            {
                "platform": "blog",
                "type": "create",
                "title": "Building a Framework",
                "content": "In this tutorial, I'll show you step by step how to build a framework. " * 200,
                "days_ago": 15,
            },
            {
                "platform": "twitter",
                "type": "create",
                "title": "Quick thought",
                "content": "Just shipped something cool! Check out my new project.",
                "days_ago": 5,
            },
            {
                "platform": "youtube",
                "type": "consume",
                "title": "Learning New Skills",
                "duration_seconds": 1800,
                "days_ago": 2,
            },
        ]
        
        for data in activities_data:
            activity = Activity(
                timestamp=datetime.now() - timedelta(days=data["days_ago"]),
                platform=data["platform"],
                activity_type=data["type"],
                title=data["title"],
                content=data.get("content"),
                duration_seconds=data.get("duration_seconds"),
            )
            add_activity(str(repo_path), activity)
            print(f"   Added: {data['title'][:40]}...")
        
        # 3. Compute profile
        print("\n3. Computing profile...")
        profile = compute_profile(str(repo_path))
        
        print(f"\n   Profile for: {profile.name}")
        print(f"   Handle: {profile.handle}")
        print(f"   Level: {profile.cards.level if profile.cards else 'N/A'}")
        print(f"   XP: {profile.cards.xp if profile.cards else 0}")
        print(f"   Rarity: {profile.cards.rarity if profile.cards else 'common'}")
        
        if profile.lifecycle:
            print(f"   Phase: {profile.lifecycle.phase}")
            print(f"   Progress: {profile.lifecycle.phase_progress * 100:.0f}%")
        
        print(f"\n   Platforms ({len(profile.platforms)}):")
        for platform in profile.platforms:
            print(f"      - {platform.platform}: {platform.role} ({platform.activity_count} activities)")
        
        if profile.metrics.creator:
            print(f"\n   Creator Metrics:")
            cm = profile.metrics.creator
            print(f"      Quality Score: {cm.quality_score:.2f}")
            print(f"      Game Alignment: {cm.game_alignment:.2f}")
            print(f"      Impact Factor: {cm.impact_factor:.2f}")
            print(f"      Primary Game: {cm.game_signature.primary_game or 'N/A'}")
        
        if profile.cards and profile.cards.badges:
            print(f"\n   Achievements ({len(profile.cards.badges)}):")
            for badge in profile.cards.badges[:5]:
                print(f"      {badge.icon} {badge.name}")
        
        # 4. Generate cards
        print("\n4. Generating cards...")
        cards = generate_cards(profile)
        
        print(f"\n   Generated {len(cards)} cards:")
        for card in cards:
            print(f"      - {card.card_type.upper()}: {card.card_number} ({card.rarity})")
        
        print("\n" + "=" * 50)
        print("Example completed successfully!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
