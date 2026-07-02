from typing import Optional

from app.schemas.analyzer import RepoMetadata, DeploymentRecommendation


def build_production_ready_prompt(
    metadata: RepoMetadata,
    recommendation: DeploymentRecommendation,
    owner: str,
    repo_name: str,
) -> str:
    """Build a concrete production-ready prompt for the user and deployment team."""
    languages = ", ".join([lang.name for lang in metadata.languages]) or "unknown"
    frameworks = ", ".join(metadata.frameworks) or "unknown"
    databases = ", ".join(metadata.databases) or "none"
    env_vars = ", ".join(metadata.env_variables) or "none"
    docker_status = "present" if metadata.docker_readiness else "missing"
    terraform_status = "present" if metadata.terraform else "missing"

    return f"""You are working on the production hardening plan for {owner}/{repo_name}.

Repository snapshot:
- Languages: {languages}
- Frameworks: {frameworks}
- Databases: {databases}
- Env variables detected: {env_vars}
- Dockerfile: {docker_status}
- Terraform/IaC: {terraform_status}
- Recommended AWS target: {recommendation.target}
- Estimated monthly cost: ${recommendation.estimated_monthly_cost:.2f}

Create a production-ready deployment plan that includes:
1. A concise remediation checklist for code, security, and infrastructure gaps.
2. Exact deployment actions for AWS, including IAM permissions, networking, secrets management, and observability.
3. A clear rollout plan with staging, smoke tests, rollback steps, and a production launch checklist.
4. A short developer note explaining what must be fixed before the app can be safely deployed.
5. A final handoff prompt that a DevOps engineer can use to deploy the app with confidence.

Important requirements:
- Prefer containerized deployment and secure secrets injection.
- Use AWS Secrets Manager or SSM Parameter Store instead of hard-coded credentials.
- Add health checks, logging, and monitoring for the chosen service.
- If Dockerfile is missing, create one and explain why it is needed.
- If Terraform is missing, describe the minimum infrastructure baseline required for deployment.
- Mention the target service {recommendation.target} and why it fits this repository.
"""
