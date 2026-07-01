import os
import re
import shutil
import stat
from typing import Tuple
import git

class GitServiceError(Exception):
    """Custom exception for Git service errors."""
    pass

class GitService:
    @staticmethod
    def validate_and_parse_url(url: str) -> Tuple[str, str, str]:
        """
        Validates GitHub URL and extracts owner, repo, and clean https clone URL.
        Supports:
        - https://github.com/owner/repo
        - git@github.com:owner/repo.git
        - github.com/owner/repo
        
        Returns:
            Tuple[owner, repo_name, clean_https_url]
        """
        # Clean whitespaces
        url = url.strip()
        
        # Regex patterns
        https_pattern = r'^(https?://)?(www\.)?github\.com/([^/]+)/([^/.]+)(\.git)?/?$'
        ssh_pattern = r'^git@github\.com:([^/]+)/([^/.]+)(\.git)?$'
        shorthand_pattern = r'^github\.com/([^/]+)/([^/.]+)(\.git)?/?$'
        
        if re.match(https_pattern, url, re.IGNORECASE):
            match = re.match(https_pattern, url, re.IGNORECASE)
            owner, repo = match.group(3), match.group(4)
        elif re.match(ssh_pattern, url, re.IGNORECASE):
            match = re.match(ssh_pattern, url, re.IGNORECASE)
            owner, repo = match.group(1), match.group(2)
        elif re.match(shorthand_pattern, url, re.IGNORECASE):
            match = re.match(shorthand_pattern, url, re.IGNORECASE)
            owner, repo = match.group(1), match.group(2)
        else:
            # Check for general Github path (e.g. nested or trailing slashes)
            clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
            parts = [p for p in clean_url.split("/") if p]
            if len(parts) >= 3 and parts[0] == "github.com":
                owner, repo = parts[1], parts[2]
            else:
                raise GitServiceError("Invalid GitHub Repository URL. Please provide a public GitHub URL.")

        clean_https_url = f"https://github.com/{owner}/{repo}.git"
        return owner, repo, clean_https_url

    @staticmethod
    def get_directory_size_mb(path: str) -> float:
        """Returns the total size of a directory in Megabytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
        return total_size / (1024 * 1024)

    @staticmethod
    def clone_repository(repo_url: str, clone_path: str) -> None:
        """
        Performs a fast, shallow clone of a public GitHub repository.
        Enforces a 30-second timeout and a 50MB file size limit.
        """
        import subprocess
        try:
            # Validate URL
            owner, repo_name, clean_url = GitService.validate_and_parse_url(repo_url)
            
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(clone_path), exist_ok=True)
            
            # Perform shallow clone via subprocess with 30s timeout
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--single-branch", clean_url, clone_path],
                capture_output=True,
                text=True,
                timeout=30.0
            )
            
            if result.returncode != 0:
                err = result.stderr.strip()
                if "Repository not found" in err or "Could not resolve host" in err:
                    raise GitServiceError("GitHub repository not found. Please verify the URL and ensure it is public.")
                elif "Permission denied" in err or "terminal prompts disabled" in err:
                    raise GitServiceError("Access denied. The repository might be private or require authentication.")
                else:
                    raise GitServiceError(f"Failed to clone repository: {err}")
            
            # Enforce 50MB maximum repository size limit
            size_mb = GitService.get_directory_size_mb(clone_path)
            if size_mb > 50.0:
                raise GitServiceError(f"Repository exceeds the maximum allowed size of 50MB (cloned size: {size_mb:.1f}MB).")
                
        except subprocess.TimeoutExpired:
            GitService.cleanup_directory(clone_path)
            raise GitServiceError("Git clone operation timed out (limit: 30 seconds).")
        except GitServiceError:
            GitService.cleanup_directory(clone_path)
            raise
        except Exception as e:
            GitService.cleanup_directory(clone_path)
            raise GitServiceError(f"An unexpected error occurred while cloning: {str(e)}")

    @staticmethod
    def cleanup_directory(dir_path: str) -> None:
        """
        Safely deletes a directory, handles read-only files in .git (Windows specific issue).
        """
        if not os.path.exists(dir_path):
            return

        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        try:
            shutil.rmtree(dir_path, onerror=remove_readonly)
        except Exception as e:
            # Fallback if onerror fails (force delete files first)
            try:
                for root, dirs, files in os.walk(dir_path, topdown=False):
                    for name in files:
                        filepath = os.path.join(root, name)
                        os.chmod(filepath, stat.S_IWRITE)
                        os.remove(filepath)
                    for name in dirs:
                        dirpath = os.path.join(root, name)
                        os.chmod(dirpath, stat.S_IWRITE)
                        os.rmdir(dirpath)
                os.rmdir(dir_path)
            except Exception as ex:
                # Log or suppress, we want to fail-safe
                pass
