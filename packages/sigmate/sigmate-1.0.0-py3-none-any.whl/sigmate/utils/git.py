import subprocess
import getpass
from pathlib import Path
from typing import Optional, Dict, Any


def get_git_repo_root(path: Path) -> Optional[Path]:
    """Finds the root of the Git repository containing the given path."""
    try:
        root_str = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return Path(root_str)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_git_remote_url(repo_root: Path) -> Optional[str]:
    """Gets the URL of the 'origin' remote for the Git repository."""
    try:
        # Try to get the URL of the 'origin' remote
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return url
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None  # No 'origin' remote or not a git repo


def get_git_ref(repo_root: Path) -> Optional[str]:
    """Gets the current Git reference (tag, branch, or commit hash)."""
    try:
        # Get the most descriptive reference (tag > commit)
        ref = subprocess.check_output(
            [
                "git",
                "describe",
                "--tags",
                "--always",
                "--dirty",
                "--long",
            ],  # --long gives more context
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return ref
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to current commit hash if describe fails (e.g., no tags)
        try:
            ref = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            # Check if dirty
            dirty_check = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if dirty_check:
                ref += "-dirty"
            return ref
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def get_git_info_object(path: Path) -> Optional[Dict[str, Dict[str, Optional[str]]]]:
    """
    Retrieves structured Git information (repository URL and reference) for a given path.

    The path provided should be within a Git repository. The function attempts to find
    the repository root, its 'origin' remote URL, and the current Git reference
    (tag, commit hash, or branch name with dirty status).

    Args:
        path: A Path object representing a location within a potential Git repository.

    Returns:
        A dictionary structured as {"git": {"url": "REPOSITORY_URL", "ref": "GIT_REFERENCE"}}
        if Git information can be retrieved. Returns None if the path is not part of a
        Git repository or if Git commands fail.
    """
    repo_root = get_git_repo_root(path)
    if not repo_root:
        return None

    repo_url = get_git_remote_url(repo_root)
    git_reference = get_git_ref(repo_root)

    if repo_url or git_reference:  # Return object if at least some info is found
        return {"git": {"url": repo_url, "ref": git_reference}}
    return None


def get_git_author() -> str:
    """
    Retrieves the Git author information (name and email) from the local Git configuration.
    Falls back to the current system username if Git author information is not configured.

    Returns:
        A string representing the Git author, typically in "Name <email>" format,
        or just the name, or the system username as a fallback.
    """
    try:
        name = subprocess.check_output(
            ["git", "config", "--get", "user.name"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        email = subprocess.check_output(
            ["git", "config", "--get", "user.email"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        if name and email:
            return f"{name} <{email}>"
        elif name:
            return name
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        return getpass.getuser()
    except Exception:
        return "unknown_user"
