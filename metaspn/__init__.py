"""
MetaSPN - Measure transformation, not engagement.

A Python package for computing development metrics and generating
trading cards from content repositories.
"""

from metaspn.core.profile import compute_profile, UserProfile, Activity
from metaspn.core.card import generate_cards
from metaspn.repo import init_repo, add_activity

__version__ = "0.1.0"
__all__ = [
    "compute_profile",
    "generate_cards",
    "init_repo",
    "add_activity",
    "UserProfile",
    "Activity",
    "__version__",
]
