"""Repository module - manage repository structure and data I/O."""

from metaspn.repo.reader import (
    MinimalState,
    RepoReader,
    load_activities,
    load_minimal_state,
    try_load_cached_profile,
)
from metaspn.repo.structure import RepoStructure, get_repo_info, init_repo, validate_repo
from metaspn.repo.writer import RepoWriter, add_activity, cache_profile, save_activity

__all__ = [
    # Structure
    "init_repo",
    "validate_repo",
    "RepoStructure",
    "get_repo_info",
    # Reader
    "RepoReader",
    "load_activities",
    "load_minimal_state",
    "MinimalState",
    "try_load_cached_profile",
    # Writer
    "RepoWriter",
    "save_activity",
    "add_activity",
    "cache_profile",
]
