"""GitHub package downloader for APM dependencies."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import re

import git
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from ..models.apm_package import (
    DependencyReference, 
    PackageInfo, 
    ResolvedReference, 
    GitReferenceType,
    validate_apm_package,
    APMPackage
)


class GitHubPackageDownloader:
    """Downloads and validates APM packages from GitHub repositories."""
    
    def __init__(self):
        """Initialize the GitHub package downloader."""
        self.git_env = self._setup_git_environment()
    
    def _setup_git_environment(self) -> Dict[str, Any]:
        """Set up Git environment with GitHub authentication.
        
        Reuses authentication patterns from existing MCP system.
        Priority: GITHUB_CLI_PAT > GITHUB_TOKEN
        
        Returns:
            Dict containing environment variables for Git operations
        """
        env = os.environ.copy()
        
        # Set up GitHub token environment for Git operations
        # Priority: GITHUB_CLI_PAT (fine-grained) > GITHUB_TOKEN (classic/built-in)
        if 'GITHUB_CLI_PAT' in env:
            # Fine-grained token for GitHub API and Git operations
            env['GITHUB_TOKEN'] = env['GITHUB_CLI_PAT']
            env['GH_TOKEN'] = env['GITHUB_CLI_PAT'] 
        elif 'GITHUB_TOKEN' in env:
            # Fallback: use existing GITHUB_TOKEN
            env['GH_TOKEN'] = env['GITHUB_TOKEN']
        
        return env
    
    def resolve_git_reference(self, repo_ref: str) -> ResolvedReference:
        """Resolve a Git reference (branch/tag/commit) to a specific commit SHA.
        
        Args:
            repo_ref: Repository reference string (e.g., "user/repo#branch")
            
        Returns:
            ResolvedReference: Resolved reference with commit SHA
            
        Raises:
            ValueError: If the reference format is invalid
            RuntimeError: If Git operations fail
        """
        # Parse the repository reference
        try:
            dep_ref = DependencyReference.parse(repo_ref)
        except ValueError as e:
            raise ValueError(f"Invalid repository reference '{repo_ref}': {e}")
        
        # Default to main branch if no reference specified
        ref = dep_ref.reference or "main"
        
        # Create a temporary directory for Git operations
        temp_dir = None
        try:
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            
            # Clone the repository with minimal depth for reference resolution
            repo_url = f"https://github.com/{dep_ref.repo_url}"
            
            try:
                # Try to clone with specific branch/tag first
                repo = Repo.clone_from(
                    repo_url,
                    temp_dir,
                    depth=1,
                    branch=ref,
                    env=self.git_env
                )
                ref_type = GitReferenceType.BRANCH  # Could be branch or tag
                resolved_commit = repo.head.commit.hexsha
                ref_name = ref
                
            except GitCommandError:
                # If branch/tag clone fails, try full clone and resolve reference
                try:
                    repo = Repo.clone_from(
                        repo_url,
                        temp_dir,
                        env=self.git_env
                    )
                    
                    # Try to resolve the reference
                    try:
                        # Check if it's a commit SHA
                        if re.match(r'^[a-f0-9]{7,40}$', ref.lower()):
                            commit = repo.commit(ref)
                            ref_type = GitReferenceType.COMMIT
                            resolved_commit = commit.hexsha
                            ref_name = ref
                        else:
                            # Try as branch first
                            try:
                                branch = repo.refs[f"origin/{ref}"]
                                ref_type = GitReferenceType.BRANCH
                                resolved_commit = branch.commit.hexsha
                                ref_name = ref
                            except IndexError:
                                # Try as tag
                                try:
                                    tag = repo.tags[ref]
                                    ref_type = GitReferenceType.TAG
                                    resolved_commit = tag.commit.hexsha
                                    ref_name = ref
                                except IndexError:
                                    raise ValueError(f"Reference '{ref}' not found in repository {dep_ref.repo_url}")
                    
                    except Exception as e:
                        raise ValueError(f"Could not resolve reference '{ref}' in repository {dep_ref.repo_url}: {e}")
                
                except GitCommandError as e:
                    raise RuntimeError(f"Failed to clone repository {dep_ref.repo_url}: {e}")
                    
        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return ResolvedReference(
            original_ref=repo_ref,
            ref_type=ref_type,
            resolved_commit=resolved_commit,
            ref_name=ref_name
        )
    
    def download_package(self, repo_ref: str, target_path: Path) -> PackageInfo:
        """Download a GitHub repository and validate it as an APM package.
        
        Args:
            repo_ref: Repository reference string (e.g., "user/repo#branch")
            target_path: Local path where package should be downloaded
            
        Returns:
            PackageInfo: Information about the downloaded package
            
        Raises:
            ValueError: If the repository reference is invalid
            RuntimeError: If download or validation fails
        """
        # Parse the repository reference
        try:
            dep_ref = DependencyReference.parse(repo_ref)
        except ValueError as e:
            raise ValueError(f"Invalid repository reference '{repo_ref}': {e}")
        
        # Resolve the Git reference to get specific commit
        resolved_ref = self.resolve_git_reference(repo_ref)
        
        # Create target directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        
        # If directory already exists and has content, remove it
        if target_path.exists() and any(target_path.iterdir()):
            shutil.rmtree(target_path)
            target_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone the repository
            repo_url = f"https://github.com/{dep_ref.repo_url}"
            
            # Use shallow clone for performance if we have a specific commit
            if resolved_ref.ref_type == GitReferenceType.COMMIT:
                # For commits, we need to clone and checkout the specific commit
                repo = Repo.clone_from(
                    repo_url,
                    target_path,
                    env=self.git_env
                )
                repo.git.checkout(resolved_ref.resolved_commit)
            else:
                # For branches and tags, we can use shallow clone
                repo = Repo.clone_from(
                    repo_url,
                    target_path,
                    depth=1,
                    branch=resolved_ref.ref_name,
                    env=self.git_env
                )
            
            # Remove .git directory to save space and prevent treating as a Git repository
            git_dir = target_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir, ignore_errors=True)
                
        except GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository {dep_ref.repo_url}: {e}")
        
        # Validate the downloaded package
        validation_result = validate_apm_package(target_path)
        if not validation_result.is_valid:
            # Clean up on validation failure
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            
            error_msg = f"Invalid APM package {dep_ref.repo_url}:\n"
            for error in validation_result.errors:
                error_msg += f"  - {error}\n"
            raise RuntimeError(error_msg.strip())
        
        # Load the APM package metadata
        if not validation_result.package:
            raise RuntimeError(f"Package validation succeeded but no package metadata found for {dep_ref.repo_url}")
        
        package = validation_result.package
        package.source = dep_ref.to_github_url()
        package.resolved_commit = resolved_ref.resolved_commit
        
        # Create and return PackageInfo
        return PackageInfo(
            package=package,
            install_path=target_path,
            resolved_reference=resolved_ref,
            installed_at=datetime.now().isoformat()
        )
    
    def _get_clone_progress_callback(self):
        """Get a progress callback for Git clone operations.
        
        Returns:
            Callable that can be used as progress callback for GitPython
        """
        def progress_callback(op_code, cur_count, max_count=None, message=''):
            """Progress callback for Git operations."""
            if max_count:
                percentage = int((cur_count / max_count) * 100)
                print(f"\r🚀 Cloning: {percentage}% ({cur_count}/{max_count}) {message}", end='', flush=True)
            else:
                print(f"\r🚀 Cloning: {message} ({cur_count})", end='', flush=True)
        
        return progress_callback