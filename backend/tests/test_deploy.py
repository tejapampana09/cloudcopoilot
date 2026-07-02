from app.utils.database import init_db
init_db()

from app.services.deployment_service import DeploymentService
from app.utils.helpers import deployments

def test_validate_aws_credentials():
    # Verify that invalid credentials return a structured failure result
    validation = DeploymentService.validate_aws_credentials("fake_key", "fake_secret", "us-east-1")
    assert validation["valid"] is False
    assert "AWS" in validation["reason"] or "Unable" in validation["reason"]

def test_deployment_trigger_state():
    dep_id = "test-dep-123"
    DeploymentService.start_deployment(
        deployment_id=dep_id,
        user_id=None,
        repo_url="https://github.com/fastapi/fastapi",
        repo_name="fastapi",
        access_key="fake_key",
        secret_key="fake_secret",
        region="ap-south-1",
        service_name="test-fastapi"
    )
    assert dep_id in deployments
    assert deployments[dep_id]["status"] == "pending"
    assert deployments[dep_id]["repo_name"] == "fastapi"
