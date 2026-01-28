"""Tests for repository structure module."""

import pytest
import json
from pathlib import Path

from metaspn.repo.structure import (
    RepoStructure,
    init_repo,
    validate_repo,
    get_repo_info,
)


class TestRepoStructure:
    """Tests for RepoStructure class."""
    
    def test_create_structure(self, temp_dir):
        """Test creating repository structure."""
        repo_path = temp_dir / "new_repo"
        structure = RepoStructure(str(repo_path))
        
        structure.create_structure()
        
        # Verify directories exist
        assert structure.metaspn_dir.exists()
        assert structure.sources_dir.exists()
        assert structure.artifacts_dir.exists()
        assert structure.reports_dir.exists()
    
    def test_validate_incomplete(self, temp_dir):
        """Test validation fails for incomplete repo."""
        repo_path = temp_dir / "incomplete"
        repo_path.mkdir()
        
        structure = RepoStructure(str(repo_path))
        
        assert structure.validate() is False
    
    def test_validate_complete(self, sample_repo):
        """Test validation passes for complete repo."""
        structure = RepoStructure(str(sample_repo))
        
        assert structure.validate() is True
    
    def test_paths(self, sample_repo):
        """Test path properties."""
        structure = RepoStructure(str(sample_repo))
        
        assert structure.profile_path.exists()
        assert structure.sources_dir.is_dir()
    
    def test_get_platform_dir(self, sample_repo):
        """Test get_platform_dir method."""
        structure = RepoStructure(str(sample_repo))
        
        podcast_dir = structure.get_platform_dir("podcast")
        
        assert podcast_dir.is_dir()
    
    def test_get_activity_files(self, sample_repo):
        """Test get_activity_files method."""
        structure = RepoStructure(str(sample_repo))
        
        all_files = structure.get_activity_files()
        podcast_files = structure.get_activity_files("podcast")
        
        assert len(all_files) > 0
        assert len(podcast_files) > 0
        assert len(podcast_files) <= len(all_files)


class TestInitRepo:
    """Tests for init_repo function."""
    
    def test_init_repo_basic(self, temp_dir):
        """Test basic repository initialization."""
        repo_path = temp_dir / "init_test"
        
        init_repo(str(repo_path), {
            "user_id": "test_user",
            "name": "Test User",
        })
        
        # Verify structure
        assert (repo_path / ".metaspn").exists()
        assert (repo_path / ".metaspn" / "profile.json").exists()
        assert (repo_path / "sources").exists()
    
    def test_init_repo_with_all_options(self, temp_dir):
        """Test initialization with all options."""
        repo_path = temp_dir / "full_init"
        
        init_repo(str(repo_path), {
            "user_id": "full_user",
            "name": "Full User",
            "handle": "@fulluser",
            "avatar_url": "https://example.com/avatar.png",
        })
        
        # Verify profile content
        with open(repo_path / ".metaspn" / "profile.json") as f:
            profile = json.load(f)
        
        assert profile["user_id"] == "full_user"
        assert profile["handle"] == "@fulluser"
        assert profile["avatar_url"] == "https://example.com/avatar.png"
    
    def test_init_repo_already_exists(self, sample_repo):
        """Test initialization fails if repo exists."""
        with pytest.raises(FileExistsError):
            init_repo(str(sample_repo), {
                "user_id": "another_user",
                "name": "Another User",
            })
    
    def test_init_repo_missing_required(self, temp_dir):
        """Test initialization fails without required fields."""
        repo_path = temp_dir / "missing_fields"
        
        with pytest.raises(ValueError):
            init_repo(str(repo_path), {"user_id": "test"})  # Missing name
        
        with pytest.raises(ValueError):
            init_repo(str(repo_path), {"name": "Test"})  # Missing user_id


class TestValidateRepo:
    """Tests for validate_repo function."""
    
    def test_validate_valid_repo(self, sample_repo):
        """Test validation of valid repo."""
        assert validate_repo(str(sample_repo)) is True
    
    def test_validate_nonexistent(self, temp_dir):
        """Test validation of nonexistent path."""
        assert validate_repo(str(temp_dir / "nonexistent")) is False
    
    def test_validate_empty_dir(self, temp_dir):
        """Test validation of empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        assert validate_repo(str(empty_dir)) is False


class TestGetRepoInfo:
    """Tests for get_repo_info function."""
    
    def test_get_info_valid_repo(self, sample_repo):
        """Test getting info from valid repo."""
        info = get_repo_info(str(sample_repo))
        
        assert info["user_id"] == "test_user"
        assert info["name"] == "Test User"
        assert info["activity_files"] > 0
    
    def test_get_info_invalid_repo(self, temp_dir):
        """Test getting info from invalid repo."""
        with pytest.raises(ValueError):
            get_repo_info(str(temp_dir / "invalid"))
