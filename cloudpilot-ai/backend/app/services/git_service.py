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
    def clone_repository(repo_url: str, clone_path: str) -> None:
        """
        Performs a fast, shallow clone of a public GitHub repository.
        """
        try:
            # Validate URL
            owner, repo_name, clean_url = GitService.validate_and_parse_url(repo_url)
            
            # Perform shallow clone
            git.Repo.clone_from(
                url=clean_url,
                to_path=clone_path,
                depth=1,
                multi_options=["--single-branch"]
            )
        except git.exc.GitCommandError as e:
            # Clean up the folder if it was partially created
            GitService.cleanup_directory(clone_path)
            
            error_message = str(e)
            if "Repository not found" in error_message or "Could not resolve host" in error_message:
                raise GitServiceError("GitHub repository not found. Please verify the URL and ensure it is public.")
            elif "Permission denied" in error_message or "terminal prompts disabled" in error_message:
                raise GitServiceError("Access denied. The repository might be private or require authentication.")
            else:
                raise GitServiceError(f"Failed to clone repository: {e.stderr or error_message}")
        except GitServiceError:
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
