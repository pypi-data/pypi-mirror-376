"""
// Copyright (c) William Newport
// SPDX-License-Identifier: BUSL-1.1
"""

from datasurface.platforms.yellow.yellow_dp import KubernetesEnvVarsCredentialStore
from datasurface.md.repo import GitHubRepository
from datasurface.md.credential import Credential, CredentialType
from datasurface.md.model_loader import loadEcosystemFromEcoModule
from datasurface.md import Ecosystem, DataPlatform, CredentialStore
from datasurface.md import ValidationTree
from datasurface.platforms.yellow.logging_utils import (
    setup_logging_for_environment, get_contextual_logger, set_context,
)
import os
import shutil
import time
import subprocess
import urllib.parse
import tempfile
from typing import Tuple, Optional

# Setup logging for environment
setup_logging_for_environment()
logger = get_contextual_logger(__name__)


def getNewModelFolder(modelFolderName: str) -> str:
    """This will return the new model folder name in the model folder. The model folder is expected to be a directory
    with subdirectories named model-{timestamp_secs}."""

    # Get the current time UTC in seconds and zero pad it to 10 digits
    timestamp = int(time.time())
    timestamp_str = f"{timestamp:010d}"

    # Return the new model folder name
    return f"{modelFolderName}/model-{timestamp_str}"


def getLatestModelFolder(modelFolderName: str) -> str:
    """This will return the latest model folder name in the model folder. The model folder is expected to be a directory
    with subdirectories named model-{timestamp_secs}."""

    # Get the list of model folders
    modelFolders = os.listdir(modelFolderName)

    # Find the latest model folder
    latestModelFolder = max(modelFolders, key=lambda x: int(x.split("-")[1]))

    return latestModelFolder


class CannotCloneGitRepositoryException(Exception):
    """This exception is raised when a git repository cannot be cloned."""
    pass


def cloneGitRepository(credStore: CredentialStore, repo: GitHubRepository, gitRepoPath: str) -> str:
    """This will clone the git repository into the given path. If the directory is empty, it will clone the repository.
    If the directory is not empty, it will not clone the repository.

    Returns:
        str: Path to the cloned repository folder

    Raises:
        Exception: If cloning fails or repository validation fails
    """

    # Create unique temporary folder to avoid concurrency conflicts
    # Use system temp directory to avoid path issues
    # Make sure the gitRepoPath exists
    os.makedirs(gitRepoPath, exist_ok=True)
    tempFolder = tempfile.mkdtemp(prefix="modeltemp-", dir=gitRepoPath)

    try:
        # Clone the git repository if the directory is empty
        if not os.path.exists(tempFolder) or not os.listdir(tempFolder):
            # Determine the git URL based on whether the repository has a credential
            git_url: str
            if repo.credential is not None:
                # Use the repository's specific credential
                git_token = credStore.getAsToken(repo.credential)

                # URL-encode the token to handle special characters
                encoded_token = urllib.parse.quote(git_token, safe='')
                git_url = f"https://{encoded_token}@github.com/{repo.repositoryName}.git"
                logger.info(f"Cloning repository: {repo.repositoryName} using credential: {repo.credential.name}")
            else:
                # No credential specified - attempt to clone without authentication (for public repos)
                git_url = f"https://github.com/{repo.repositoryName}.git"
                logger.info(f"Cloning repository: {repo.repositoryName} without authentication (public repository)")

            # Ensure the directory exists
            os.makedirs(tempFolder, exist_ok=True)

            logger.info(f"Cloning repository: {repo.repositoryName} into {tempFolder}")
            try:
                subprocess.run(
                    ['git', 'clone', '--branch', repo.branchName, git_url, '.'],
                    cwd=tempFolder,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info(f"Successfully cloned repository: {repo.repositoryName} branch: {repo.branchName}")

                # Validate that the repository was cloned successfully
                if not os.path.exists(os.path.join(tempFolder, '.git')):
                    raise CannotCloneGitRepositoryException(f"Repository was not cloned successfully - no .git directory found in {tempFolder}")

                # Check if eco.py exists (expected model file)
                if not os.path.exists(os.path.join(tempFolder, 'eco.py')):
                    logger.warning(f"Warning: eco.py not found in cloned repository {repo.repositoryName}")

                # List contents of cloned repository for debugging
                logger.debug(f"Contents of cloned repository {repo.repositoryName}:")
                for item in os.listdir(tempFolder):
                    logger.debug(f"  - {item}")

            except subprocess.CalledProcessError as e:
                # Sanitize error message to remove token exposure if token was used
                sanitized_error = e.stderr
                if repo.credential is not None and sanitized_error:
                    git_token = os.environ.get(f"{repo.credential.name}_TOKEN", "")
                    if git_token:
                        sanitized_error = sanitized_error.replace(git_token, "***TOKEN***")
                raise CannotCloneGitRepositoryException(f"Failed to clone repository {repo.repositoryName}: {sanitized_error or 'Unknown git error'}")
        else:
            logger.info(f"Using existing repository in {tempFolder}")

        # Get latest timestamp model folder and rename the temp folder to it. This means
        # jobs looking at a timestamp model folder never see a partial model while it
        # is being cloned.
        finalModelFolder = getNewModelFolder(gitRepoPath)
        os.rename(tempFolder, finalModelFolder)
        logger.info(f"Cloned git repository {repo.repositoryName} branch: {repo.branchName} into {finalModelFolder}")
        # Success - don't clean up tempFolder since it was renamed
        tempFolder = None
        return finalModelFolder
    except Exception as e:
        # Re-raise with appropriate exception type
        if isinstance(e, CannotCloneGitRepositoryException):
            raise
        else:
            raise CannotCloneGitRepositoryException(f"Failed to clone repository {repo.repositoryName}: {e}")
    finally:
        # Clean up temp folder if it still exists (any failure before successful rename)
        if tempFolder and os.path.exists(tempFolder):
            shutil.rmtree(tempFolder)


def getLatestModelAtTimestampedFolder(credStore: CredentialStore, repo: GitHubRepository, modelFolderBaseName: str, doClone: bool = False,
                                      useCache: bool = False, maxCacheAgeMinutes: int = 5) -> \
            tuple[Optional[Ecosystem], Optional[ValidationTree]]:
    """This will return the latest model at a timestamped folder. The model folder is expected to be a directory
    with subdirectories named model-{timestamp_secs}.

    Args:
        credStore: Credential store for authentication
        repo: GitHub repository information
        modelFolderBaseName: Base path for model storage
        doClone: Whether to clone if no local model exists
        useCache: Whether to use shared cache (recommended for jobs)
        maxCacheAgeMinutes: Maximum cache age before checking remote for updates
    """

    latestModelFolder: str
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    if useCache:
        # Use shared cache approach - recommended for production jobs
        eco, ecoTree = getCachedOrCloneModel(credStore, repo, modelFolderBaseName, maxCacheAgeMinutes)
        # Clean up old cached versions to save space
        cleanupOldCachedModels(modelFolderBaseName, repo, keep_count=3)
    elif doClone:
        # Legacy direct clone approach
        latestModelFolder = cloneGitRepository(credStore, repo, modelFolderBaseName)
        eco, ecoTree = loadEcosystemFromEcoModule(latestModelFolder)
    else:
        # Use existing local folder
        latestModelFolder = os.path.join(modelFolderBaseName, getLatestModelFolder(modelFolderBaseName))
        eco, ecoTree = loadEcosystemFromEcoModule(latestModelFolder)

    return eco, ecoTree


def handleModelMerge(modelFolderName: str, basePlatformDir: str, *pspNames: str) -> Ecosystem:
    """This creates the graph defined by the model and for the specified platform services providers, it asks each
    platform services provider to generate the artifacts needed to execute the data pipelines needed for this subset.
    These artifacts would include job schedule DAGs, terraform files and so on as needed."""

    # Load the model
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    eco, ecoTree = loadEcosystemFromEcoModule(modelFolderName)
    if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
        if ecoTree is not None:
            ecoTree.printTree()
        raise Exception(f"Failed to load ecosystem from {modelFolderName}")

    # Generate the platform bootstrap files
    assert eco is not None

    pspNamesSet: set[str] = set(pspNames)

    for psp in eco.platformServicesProviders:
        if psp.name in pspNamesSet:
            psp.mergeHandler(eco, basePlatformDir)
    return eco


def handleModelMergeWithGit(credStore: CredentialStore, repo: GitHubRepository, gitRepoPath: str, useCache: bool,
                            maxCacheAgeMinutes: int, basePlatformDir: str, *pspNames: str) -> Ecosystem:
    """Cache-aware version of handleModelMerge that loads ecosystem using git cache."""

    # Load the model using cache-aware loading
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    eco, ecoTree = getLatestModelAtTimestampedFolder(
        credStore, repo, gitRepoPath,
        doClone=not useCache, useCache=useCache, maxCacheAgeMinutes=maxCacheAgeMinutes
    )

    if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
        if ecoTree is not None:
            ecoTree.printTree()
        raise Exception(f"Failed to load ecosystem from git repository {repo.repositoryName}")

    # Generate the platform bootstrap files
    pspNamesSet: set[str] = set(pspNames)
    # Find the platform
    for psp in eco.platformServicesProviders:
        if psp.name in pspNamesSet:
            psp.mergeHandler(eco, basePlatformDir)
    return eco


def generatePlatformBootstrap(ringLevel: int, modelFolderName: str, basePlatformDir: str, *pspNames: str) -> Ecosystem:
    """This will generate the platform bootstrap files for a given platform using the model defined in
    the model folder, the model must be called 'eco.py'. The files will be generated in the {basePlatformDir}/{platformName} directory."""

    # Load the model
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    eco, ecoTree = loadEcosystemFromEcoModule(modelFolderName)
    if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
        if ecoTree is not None:
            ecoTree.printTree()
        raise Exception(f"Failed to load ecosystem from {modelFolderName}")

    # Generate the platform bootstrap files
    assert eco is not None

    # Find the platform
    pspNamesSet: set[str] = set(pspNames)
    for psp in eco.platformServicesProviders:
        if psp.name in pspNamesSet:
            # Generate the bootstrap files
            bootstrapArtifacts: dict[str, str] = psp.generateBootstrapArtifacts(eco, ringLevel)
            # Create the platform directory if it doesn't exist
            os.makedirs(os.path.join(basePlatformDir, psp.name), exist_ok=True)
            for name, content in bootstrapArtifacts.items():
                with open(os.path.join(basePlatformDir, psp.name, name), "w") as f:
                    f.write(content)

    return eco


def generatePlatformBootstrapWithGit(credStore: CredentialStore, repo: GitHubRepository, gitRepoPath: str, useCache: bool,
                                     maxCacheAgeMinutes: int, ringLevel: int, basePlatformDir: str, *pspNames: str) -> Ecosystem:
    """Cache-aware version of generatePlatformBootstrap that loads ecosystem using git cache."""

    # Load the model using cache-aware loading
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    eco, ecoTree = getLatestModelAtTimestampedFolder(
        credStore, repo, gitRepoPath,
        doClone=not useCache, useCache=useCache, maxCacheAgeMinutes=maxCacheAgeMinutes
    )

    if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
        if ecoTree is not None:
            ecoTree.printTree()
        raise Exception(f"Failed to load ecosystem from git repository {repo.repositoryName}")

    # Generate the platform bootstrap files
    assert eco is not None

    # Find the platform
    pspNamesSet: set[str] = set(pspNames)
    for psp in eco.platformServicesProviders:
        if psp.name in pspNamesSet:
            # Generate the bootstrap files
            bootstrapArtifacts: dict[str, str] = psp.generateBootstrapArtifacts(eco, ringLevel)
            # Create the platform directory if it doesn't exist
            os.makedirs(os.path.join(basePlatformDir, psp.name), exist_ok=True)
            for name, content in bootstrapArtifacts.items():
                with open(os.path.join(basePlatformDir, psp.name, name), "w") as f:
                    f.write(content)

    return eco


def resetBatchState(modelFolderName: str, platformName: str, storeName: str, datasetName: Optional[str] = None) -> None:
    """Reset batch state for a YellowDataPlatform store/dataset.

    Args:
        modelFolderName: Model folder name (containing eco.py)
        platformName: Name of the YellowDataPlatform
        storeName: Name of the datastore to reset
        datasetName: Optional dataset name for single-dataset reset
    """

    # Load the model
    eco: Optional[Ecosystem]
    ecoTree: Optional[ValidationTree]
    eco, ecoTree = loadEcosystemFromEcoModule(modelFolderName)
    if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
        if ecoTree is not None:
            ecoTree.printTree()
        raise Exception(f"Failed to load ecosystem from {modelFolderName}")

    assert eco is not None

    # Find the platform
    dp: DataPlatform = eco.getDataPlatformOrThrow(platformName)

    # Reset batch state
    dp.resetBatchState(eco, storeName, datasetName)


def getCachedModelPath(cacheBasePath: str, repo: GitHubRepository) -> str:
    """Get the cache directory path for a specific repository."""
    # Create a safe directory name from repo info
    repo_safe_name = repo.repositoryName.replace("/", "_").replace("-", "_")
    branch_safe_name = repo.branchName.replace("/", "_")
    return os.path.join(cacheBasePath, f"{repo_safe_name}_{branch_safe_name}")


def getAllCachedModels(cacheBasePath: str, repo: GitHubRepository) -> list[str]:
    """Get all cached model folders for a repository, sorted by timestamp (newest first)."""
    cache_path = getCachedModelPath(cacheBasePath, repo)
    if not os.path.exists(cache_path):
        return []

    try:
        model_folders = [f for f in os.listdir(cache_path) if f.startswith("model-")]
        if not model_folders:
            return []

        # Sort by timestamp (newest first)
        model_folders.sort(key=lambda x: int(x.split("-")[1]), reverse=True)
        return [os.path.join(cache_path, folder) for folder in model_folders]
    except (OSError, ValueError):
        return []


def getLatestCachedModel(cacheBasePath: str, repo: GitHubRepository) -> Optional[str]:
    """Get the latest cached model folder for a repository, or None if no cache exists."""
    cached_models = getAllCachedModels(cacheBasePath, repo)
    return cached_models[0] if cached_models else None


def getLatestValidCachedModel(cacheBasePath: str, repo: GitHubRepository) -> Tuple[Optional[Ecosystem], Optional[ValidationTree]]:
    """Get the latest VALID cached model folder for a repository, or None if no valid cache exists.

    This scans through cached models (newest first) and returns the first one that passes validation.
    Critical for graceful degradation when recent cached models may be invalid.
    """
    cached_models = getAllCachedModels(cacheBasePath, repo)

    for cached_model in cached_models:
        try:
            eco, ecoTree = loadEcosystemFromEcoModule(cached_model)
            is_valid = eco is not None and (ecoTree is None or not ecoTree.hasErrors())
            if is_valid:
                logger.info(f"Found valid cached model: {cached_model}")
                return eco, ecoTree
            else:
                logger.warning(f"Cached model is invalid, checking older versions: {cached_model}")
        except Exception as e:
            logger.warning(f"Failed to validate cached model {cached_model}: {e}")
            continue

    logger.warning("No valid cached models found")
    return None, None


def isModelCacheStale(cached_model_path: str, repo: GitHubRepository, credStore: CredentialStore, max_age_minutes: int = 5) -> bool:
    """Check if cached model is stale by comparing with remote repository."""
    if not os.path.exists(cached_model_path):
        logger.info(f"Cache miss: cached model path does not exist: {cached_model_path}")
        return True

    # Check cache age first (quick check)
    cache_timestamp = int(os.path.basename(cached_model_path).split("-")[1])
    current_timestamp = int(time.time())
    age_minutes = (current_timestamp - cache_timestamp) / 60

    logger.info(f"Cache age analysis: {age_minutes:.1f} minutes old (max: {max_age_minutes} minutes), " +
                f"cache is {'fresh' if age_minutes < max_age_minutes else 'stale by age'}")

    if age_minutes < max_age_minutes:
        logger.info(f"Cache is fresh ({age_minutes:.1f} minutes old), skipping remote check")
        return False

    # For older caches, check if remote has changes
    try:
        logger.info("Checking remote repository for updates...")
        git_url = _buildGitUrl(repo, credStore)

        # Use git ls-remote to check latest commit hash without cloning
        result = subprocess.run(
            ['git', 'ls-remote', git_url, repo.branchName],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"Failed to check remote repository: {result.stderr}")
            return False  # Assume cache is still good if we can't check remote

        remote_commit = result.stdout.split('\t')[0]
        logger.info(f"Remote commit hash: {remote_commit[:8]}...")

        # Check if cached commit matches remote
        local_commit_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=cached_model_path,
            capture_output=True,
            text=True
        )

        if local_commit_result.returncode == 0:
            local_commit = local_commit_result.stdout.strip()
            is_stale = local_commit != remote_commit
            logger.info(f"Local commit hash: {local_commit[:8]}...")

            if is_stale:
                logger.info(f"Cache is STALE - commits differ (local: {local_commit[:8]}, remote: {remote_commit[:8]})")
            else:
                logger.info(f"Cache is FRESH - commits match (local: {local_commit[:8]}, remote: {remote_commit[:8]})")

            return is_stale
        else:
            logger.error(f"Failed to get local commit hash: {local_commit_result.stderr}")
            logger.warning("Cannot verify local commit, assuming cache is stale to force refresh")
            return True

    except subprocess.TimeoutExpired:
        logger.warning("Remote check timed out, assuming cache is still good")
    except Exception as e:
        logger.error(f"Error checking remote repository: {e}")

    return False  # Assume cache is still good if we can't verify


def _buildGitUrl(repo: GitHubRepository, credStore: CredentialStore) -> str:
    """Build git URL with or without credentials."""
    if repo.credential is not None:
        git_token = credStore.getAsToken(repo.credential)
        encoded_token = urllib.parse.quote(git_token, safe='')
        return f"https://{encoded_token}@github.com/{repo.repositoryName}.git"
    else:
        return f"https://github.com/{repo.repositoryName}.git"


class ModelCloneHasValidationErrorsException(Exception):
    """Exception raised when a model clone has validation errors."""
    def __init__(self, message: str):
        super().__init__(message)


def cloneToCache(credStore: CredentialStore, repo: GitHubRepository, cacheBasePath: str) -> Tuple[Optional[Ecosystem], Optional[ValidationTree]]:
    """Clone repository to cache using atomic timestamp-based approach."""
    cache_path = getCachedModelPath(cacheBasePath, repo)
    os.makedirs(cache_path, exist_ok=True)

    # Use unique temporary directory to avoid concurrency conflicts
    temp_folder = tempfile.mkdtemp(prefix="modeltemp-", dir=cache_path)

    git_url = _buildGitUrl(repo, credStore)

    logger.info(f"Cloning repository: {repo.repositoryName} to cache at {cache_path}")
    try:
        subprocess.run(
            ['git', 'clone', '--branch', repo.branchName, git_url, '.'],
            cwd=temp_folder,
            capture_output=True,
            text=True,
            check=True
        )

        # Validate clone
        if not os.path.exists(os.path.join(temp_folder, '.git')):
            raise Exception("Repository was not cloned successfully - no .git directory found")

        # Load the model
        eco: Optional[Ecosystem]
        ecoTree: Optional[ValidationTree]
        eco, ecoTree = loadEcosystemFromEcoModule(temp_folder)
        # If the new model is invalid then log the errors and
        if eco is None or (ecoTree is not None and ecoTree.hasErrors()):
            if ecoTree is not None:
                ecoTree.printTree()
            raise ModelCloneHasValidationErrorsException(f"Failed to load ecosystem from {temp_folder}")

        # Atomic rename to timestamped folder
        timestamp = int(time.time())
        final_model_folder = os.path.join(cache_path, f"model-{timestamp:010d}")
        os.rename(temp_folder, final_model_folder)

        logger.info(f"Successfully cached repository: {repo.repositoryName} at {final_model_folder}")
        # Success - don't clean up temp_folder since it was renamed
        temp_folder = None
        return eco, ecoTree

    except subprocess.CalledProcessError as e:
        # Sanitize error message
        sanitized_error = e.stderr
        if repo.credential is not None and sanitized_error:
            git_token = credStore.getAsToken(repo.credential)
            if git_token in sanitized_error:
                sanitized_error = sanitized_error.replace(git_token, "***TOKEN***")
        raise Exception(f"Failed to clone repository {repo.repositoryName}: {sanitized_error or 'Unknown git error'}")
    finally:
        # Clean up temp folder if it still exists (any failure before successful rename)
        if temp_folder and os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)


def getCachedOrCloneModel(
        credStore: CredentialStore, repo: GitHubRepository,
        cacheBasePath: str, max_age_minutes: int = 5) -> Tuple[Optional[Ecosystem], Optional[ValidationTree]]:
    """Get cached model or clone if cache is stale. Returns path to model folder.

    Implements graceful degradation by searching for the latest VALID cached model
    when newly cloned models fail validation.
    """

    # Check for existing cache
    cached_path = getLatestCachedModel(cacheBasePath, repo)

    if cached_path and not isModelCacheStale(cached_path, repo, credStore, max_age_minutes):
        # Cache is fresh, but we should still validate it since recent cached models might be bad
        try:
            eco, ecoTree = loadEcosystemFromEcoModule(cached_path)
            is_valid = eco is not None and (ecoTree is None or not ecoTree.hasErrors())
            if is_valid:
                logger.info(f"Using fresh and valid cached model: {cached_path}")
                return eco, ecoTree
            else:
                logger.warning("Latest cached model is invalid despite being fresh - will clone and potentially fall back to older valid model")
        except Exception as e:
            logger.warning(f"Failed to validate latest cached model: {e} - will clone and potentially fall back")

    # Cache miss, stale, or invalid - try to clone fresh copy
    logger.info(f"Cache miss, stale, or invalid for {repo.repositoryName}, cloning fresh copy")
    try:
        return cloneToCache(credStore, repo, cacheBasePath)
    except ModelCloneHasValidationErrorsException as e:
        logger.error(f"Failed to clone repository {repo.repositoryName}: {e}")

        # CRITICAL: Search for the latest VALID cached model, not just the latest one
        logger.warning("Searching for latest VALID cached model for graceful degradation...")
        valid_eco, valid_ecoTree = getLatestValidCachedModel(cacheBasePath, repo)

        if valid_eco is not None:
            logger.warning("GRACEFUL DEGRADATION: Using latest valid cached model")
            return valid_eco, valid_ecoTree
        else:
            logger.error(f"CRITICAL: No valid cached models found for {repo.repositoryName}, and failed to clone fresh copy: {e}")
            raise Exception(f"No valid models available for {repo.repositoryName} - clone failed and no valid cached versions exist")


def cleanupOldCachedModels(cacheBasePath: str, repo: GitHubRepository, keep_count: int = 3) -> None:
    """Clean up old cached model versions, keeping only the latest N versions."""
    cache_path = getCachedModelPath(cacheBasePath, repo)
    if not os.path.exists(cache_path):
        return

    try:
        model_folders = [f for f in os.listdir(cache_path) if f.startswith("model-")]
        if len(model_folders) <= keep_count:
            return

        # Sort by timestamp (newest first)
        model_folders.sort(key=lambda x: int(x.split("-")[1]), reverse=True)
        folders_to_delete = model_folders[keep_count:]

        for folder in folders_to_delete:
            folder_path = os.path.join(cache_path, folder)
            logger.warning(f"Cleaning up old cached model: {folder_path}")
            shutil.rmtree(folder_path)

    except Exception as e:
        logger.warning(f"Warning: Failed to cleanup old cached models: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Platform utilities for DataSurface")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: generatePlatformBootstrap
    parser_bootstrap = subparsers.add_parser("generatePlatformBootstrap", help="Generate platform bootstrap files")
    parser_bootstrap.add_argument("--ringLevel", type=int, required=True, help=", 0 to N, Ring level to generate bootstrap artifacts for")
    parser_bootstrap.add_argument("--model", required=False, help="Model folder name (containing eco.py) - legacy mode")
    parser_bootstrap.add_argument("--output", required=True, help="Base output directory for platform files")
    parser_bootstrap.add_argument("--psp", required=True, nargs="+", help="One or more platform service provider names")
    # Git repository parameters for cache-aware loading
    parser_bootstrap.add_argument("--git-repo-path", help="Path to git repository cache")
    parser_bootstrap.add_argument("--git-repo-owner", help="GitHub repository owner")
    parser_bootstrap.add_argument("--git-repo-name", help="GitHub repository name")
    parser_bootstrap.add_argument("--git-repo-branch", help="GitHub repository branch")
    parser_bootstrap.add_argument("--git-platform-repo-credential-name", help="GitHub credential name")
    parser_bootstrap.add_argument("--use-git-cache", action='store_true', default=False, help="Use shared git cache (default: False)")
    parser_bootstrap.add_argument("--max-cache-age-minutes", type=int, default=5, help="Maximum cache age in minutes (default: 5)")

    # Subcommand: handleModelMerge
    parser_merge = subparsers.add_parser("handleModelMerge", help="Generate pipeline artifacts for platforms")
    parser_merge.add_argument("--model", required=False, help="Model folder name (containing eco.py) - legacy mode")
    parser_merge.add_argument("--output", required=True, help="Base output directory for platform files")
    parser_merge.add_argument("--psp", required=True, nargs="+", help="One or more platform service provider names")
    # Git repository parameters for cache-aware loading
    parser_merge.add_argument("--git-repo-path", help="Path to git repository cache")
    parser_merge.add_argument("--git-repo-owner", help="GitHub repository owner")
    parser_merge.add_argument("--git-repo-name", help="GitHub repository name")
    parser_merge.add_argument("--git-repo-branch", help="GitHub repository branch")
    parser_merge.add_argument("--git-platform-repo-credential-name", help="GitHub credential name")
    parser_merge.add_argument("--use-git-cache", action='store_true', default=False, help="Use shared git cache (default: False)")
    parser_merge.add_argument("--max-cache-age-minutes", type=int, default=5, help="Maximum cache age in minutes (default: 5)")

    # Subcommand: resetBatchState
    parser_reset = subparsers.add_parser("resetBatchState", help="Reset batch state for YellowDataPlatform")
    parser_reset.add_argument("--model", required=True, help="Model folder name (containing eco.py)")
    parser_reset.add_argument("--platform", required=True, help="YellowDataPlatform name")
    parser_reset.add_argument("--store", required=True, help="Datastore name to reset")
    parser_reset.add_argument("--dataset", required=False, help="Optional dataset name for single-dataset reset")

    args = parser.parse_args()
    try:
        if args.command == "generatePlatformBootstrap":
            # Set logging context for the operation
            set_context(psp=",".join(args.psp))

            if args.model:
                # Legacy mode - use direct model folder path
                logger.info("Using legacy mode with direct model folder", model_folder=args.model)
                generatePlatformBootstrap(args.ringLevel, args.model, args.output, *args.psp)
            else:
                # New git-aware mode - validate git parameters
                if not all([args.git_repo_path, args.git_repo_owner, args.git_repo_name,
                            args.git_repo_branch, args.git_platform_repo_credential_name]):
                    logger.error("Error: For git-aware mode, all git parameters are required: " +
                                 "--git-repo-path, --git-repo-owner, --git-repo-name, --git-repo-branch, --git-platform-repo-credential-name")
                    exit(1)

                # Create credential store and repository
                set_context(psp=",".join(args.psp))

                cred_store = KubernetesEnvVarsCredentialStore("Job cred store", set())
                repo = GitHubRepository(
                    f"{args.git_repo_owner}/{args.git_repo_name}",
                    args.git_repo_branch,
                    credential=Credential(args.git_platform_repo_credential_name, CredentialType.API_TOKEN)
                )

                generatePlatformBootstrapWithGit(
                    cred_store, repo, args.git_repo_path, args.use_git_cache,
                    args.max_cache_age_minutes, args.ringLevel, args.output, *args.psp)
        elif args.command == "handleModelMerge":
            # Set logging context for the operation
            set_context(psp=",".join(args.psp))

            if args.model:
                # Legacy mode - use direct model folder path
                logger.info("Using legacy mode with direct model folder", model_folder=args.model)
                handleModelMerge(args.model, args.output, *args.psp)
            else:
                # New git-aware mode - validate git parameters
                if not all([args.git_repo_path, args.git_repo_owner, args.git_repo_name,
                            args.git_repo_branch, args.git_platform_repo_credential_name]):
                    logger.error("Error: For git-aware mode, all git parameters are required: " +
                                 "--git-repo-path, --git-repo-owner, --git-repo-name, --git-repo-branch, --git-platform-repo-credential-name")
                    exit(1)

                # Create credential store and repository
                set_context(psp=",".join(args.psp))

                cred_store = KubernetesEnvVarsCredentialStore("Job cred store", set())
                repo = GitHubRepository(
                    f"{args.git_repo_owner}/{args.git_repo_name}",
                    args.git_repo_branch,
                    credential=Credential(args.git_platform_repo_credential_name, CredentialType.API_TOKEN)
                )

                handleModelMergeWithGit(cred_store, repo, args.git_repo_path, args.use_git_cache,
                                        args.max_cache_age_minutes, args.output, *args.psp)
        elif args.command == "resetBatchState":
            # Set logging context for the operation
            set_context(platform=args.platform, workspace=args.store)
            logger.info("Resetting batch state", platform=args.platform, store=args.store, dataset=args.dataset)
            resetBatchState(args.model, args.platform, args.store, args.dataset)
        else:
            logger.error("Unknown command", command=args.command)
            parser.print_help()
        exit(0)  # Success
    except Exception as e:
        logger.error("Error", error=e)
        exit(1)  # Failure
