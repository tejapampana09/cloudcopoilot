import pytest
from app.schemas.analyzer import RepoMetadata, LanguageInfo
from app.schemas.architecture import TechnologyAnalysis, AWSRecommendationDetail
from app.analysis.context_builder import RepositoryContextBuilder
from app.architecture.architecture_analyzer import ArchitectureAnalyzer
from app.reasoning.reasoning_engine import ReasoningEngine
from app.recommendations.aws_decision_engine import AWSDecisionEngine
from app.services.cost_estimator import CostEstimator
from app.reports.report_generator import ReportGenerator

def test_context_builder_inferences():
    # Construct a full-stack RepoMetadata mock
    metadata = RepoMetadata(
        languages=[LanguageInfo(name="TypeScript", percentage=80.0), LanguageInfo(name="HTML", percentage=20.0)],
        frameworks=["React", "Express"],
        frontend=["React SPA"],
        backend=["Express API"],
        databases=["PostgreSQL"],
        package_managers=["npm"],
        docker_readiness=True,
        docker_compose=True,
        env_variables=["DATABASE_URL", "JWT_SECRET", "STRIPE_API_KEY"],
        ci_cd=["GitHub Actions"],
        terraform=False,
        infrastructure_files=["Dockerfile", "docker-compose.yml"],
        readme_quality="High"
    )

    # Build context without a clone_path first (or dummy clone path)
    ctx = RepositoryContextBuilder.build(metadata, "test-repo", "test-owner")
    
    assert ctx.project_type == "Fullstack"
    assert ctx.project_complexity in ["Medium", "High"]
    assert ctx.expected_scalability in ["Good", "Excellent", "Moderate"]
    assert ctx.databases == ["PostgreSQL"]

def test_decision_engine_matrix_amplify():
    # Test a frontend-only SPA technology profile
    metadata = RepoMetadata(
        languages=[LanguageInfo(name="JavaScript", percentage=100.0)],
        frameworks=["React"],
        frontend=["React SPA"],
        backend=[],
        databases=[],
        package_managers=["npm"],
        docker_readiness=False,
        docker_compose=False,
        env_variables=["REACT_APP_API_URL"],
        ci_cd=[],
        terraform=False,
        infrastructure_files=[],
        readme_quality="Medium"
    )
    
    technology = TechnologyAnalysis(
        frontend_stack="React",
        backend_stack="Unknown",
        database=None,
        api_style="Static",
        authentication="Unknown",
        service_architecture="Static frontend",
        ssr_vs_spa="SPA",
        serverless_readiness="Low",
        container_readiness="Low",
        cloud_readiness="Low",
        detection_confidence={}
    )
    
    ctx = RepositoryContextBuilder.build(metadata, "test-spa", "test-owner")
    target, recs, confidence = AWSDecisionEngine.evaluate(metadata, technology, ctx)
    
    assert target == "AWS Amplify"
    assert confidence > 70.0
    assert len(recs) >= 1
    assert recs[0].service == "AWS Amplify"
    assert "Primary Selection Rationale" in recs[0].reason

def test_decision_engine_matrix_ecs():
    # Test a multi-container docker compose profile
    metadata = RepoMetadata(
        languages=[LanguageInfo(name="Python", percentage=60.0), LanguageInfo(name="TypeScript", percentage=40.0)],
        frameworks=["FastAPI", "React"],
        frontend=["React SPA"],
        backend=["FastAPI API"],
        databases=["PostgreSQL", "Redis"],
        package_managers=["pip", "npm"],
        docker_readiness=True,
        docker_compose=True,
        env_variables=["DB_HOST", "REDIS_HOST"],
        ci_cd=[],
        terraform=False,
        infrastructure_files=["Dockerfile", "docker-compose.yml"],
        readme_quality="High"
    )
    
    technology = TechnologyAnalysis(
        frontend_stack="React",
        backend_stack="FastAPI",
        database="PostgreSQL",
        api_style="REST",
        authentication="Token-based / JWT",
        service_architecture="Monolith with clear frontend/backend separation",
        ssr_vs_spa="SPA",
        serverless_readiness="Medium",
        container_readiness="High",
        cloud_readiness="Medium",
        detection_confidence={}
    )
    
    ctx = RepositoryContextBuilder.build(metadata, "test-compose", "test-owner")
    target, recs, confidence = AWSDecisionEngine.evaluate(metadata, technology, ctx)
    
    assert target == "AWS ECS"
    assert len(recs) >= 3  # ECS + RDS + Redis + ECR
    services = [r.service for r in recs]
    assert "AWS ECS on Fargate" in services
    assert "Amazon RDS" in services

def test_cost_estimator_pricing():
    # Test app runner cost estimation
    total, breakdown = CostEstimator.estimate_cost("AWS App Runner", ["PostgreSQL"], "Medium")
    assert total > 20.0
    assert breakdown.compute == 12.50
    assert breakdown.database == 17.30
    
    # Test generate assumptions
    text = CostEstimator.generate_assumptions_text("AWS App Runner", ["PostgreSQL"], "Medium", total, breakdown)
    assert "Compute & Routing:" in text
    assert "Amazon RDS:" in text

def test_report_generator_schema():
    # Mock parameters
    metadata = RepoMetadata(
        languages=[LanguageInfo(name="Python", percentage=100.0)],
        frameworks=["FastAPI"],
        frontend=[],
        backend=["FastAPI API"],
        databases=["PostgreSQL"],
        package_managers=["pip"],
        docker_readiness=True,
        docker_compose=False,
        env_variables=["DATABASE_URL"],
        ci_cd=[],
        terraform=False,
        infrastructure_files=["Dockerfile"],
        readme_quality="High"
    )
    
    ctx = RepositoryContextBuilder.build(metadata, "test-api", "test-owner")
    arch = ArchitectureAnalyzer.analyze(metadata, ctx)
    
    recs = [
        AWSRecommendationDetail(
            service="AWS App Runner",
            purpose="Compute",
            reason="Test reason",
            advantages=["Advantage 1"],
            trade_offs=["Tradeoff 1"],
            alternatives=["AWS ECS"],
            estimated_monthly_cost_impact=15.0,
            confidence_score=85
        )
    ]
    
    report_dict = ReportGenerator.build_report(
        metadata=metadata,
        architecture=arch,
        aws_recommendations=recs,
        repository_context=ctx,
        reasons_list=["Reason 1"],
        cost_assumptions_str="Assumptions text",
        health_score=90
    )
    
    # Check fields
    assert report_dict["repository_summary"] is not None
    assert report_dict["overall_architecture_score"] > 50
    assert report_dict["cloud_readiness_score"] == 90
    assert len(report_dict["detected_components"]) >= 2
