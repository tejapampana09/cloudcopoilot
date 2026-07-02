from app.schemas.analyzer import RepoMetadata, DeploymentRecommendation, CostBreakdown
from app.services.production_prompt_service import build_production_ready_prompt


def test_build_production_ready_prompt_includes_actions_and_deployment_guidance():
    metadata = RepoMetadata(
        languages=[{"name": "Python", "percentage": 100.0}],
        frameworks=["FastAPI"],
        frontend=[],
        backend=["FastAPI"],
        databases=["SQLite"],
        docker_readiness=False,
        env_variables=["DATABASE_URL"],
        ci_cd=[],
        terraform=False,
        infrastructure_files=[],
        readme_quality="Medium",
        detected_secrets=[],
        large_files=[],
        circular_dependencies=[],
        stale_branches=[],
        release_tags=[],
    )
    recommendation = DeploymentRecommendation(
        target="AWS App Runner",
        why="Containerized web service",
        estimated_monthly_cost=35.86,
        cost_breakdown=CostBreakdown(compute=20.0, database=10.0, storage=3.0, data_transfer=2.86),
        confidence_score=88,
    )

    prompt = build_production_ready_prompt(
        metadata=metadata,
        recommendation=recommendation,
        owner="demo",
        repo_name="sample-api",
    )

    assert "sample-api" in prompt
    assert "Dockerfile" in prompt
    assert "AWS Secrets Manager" in prompt
    assert "AWS App Runner" in prompt
    assert "deploy" in prompt.lower()
