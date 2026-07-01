import pytest
from app.services.git_service import GitService, GitServiceError

def test_validate_and_parse_url_success():
    # Test standard HTTPS url
    owner, repo, clean_url = GitService.validate_and_parse_url("https://github.com/fastapi/fastapi")
    assert owner == "fastapi"
    assert repo == "fastapi"
    assert clean_url == "https://github.com/fastapi/fastapi.git"

    # Test SSH url
    owner, repo, clean_url = GitService.validate_and_parse_url("git@github.com:openai/openai-python.git")
    assert owner == "openai"
    assert repo == "openai-python"
    assert clean_url == "https://github.com/openai/openai-python.git"

    # Test shorthand url
    owner, repo, clean_url = GitService.validate_and_parse_url("github.com/google/jax")
    assert owner == "google"
    assert repo == "jax"
    assert clean_url == "https://github.com/google/jax.git"

def test_validate_and_parse_url_failure():
    # Test invalid domain
    with pytest.raises(GitServiceError):
        GitService.validate_and_parse_url("https://gitlab.com/user/project")

    # Test malformed URL
    with pytest.raises(GitServiceError):
        GitService.validate_and_parse_url("not-a-url")
