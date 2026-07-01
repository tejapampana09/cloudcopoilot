from typing import List, Tuple
from app.schemas.architecture import AWSRecommendationDetail, TechnologyAnalysis
from app.schemas.analyzer import RepoMetadata


class AWSDecisionEngine:
    @staticmethod
    def evaluate(metadata: RepoMetadata, technology: TechnologyAnalysis) -> Tuple[str, List[AWSRecommendationDetail], float]:
        primary_target = AWSDecisionEngine._select_primary_target(metadata, technology)
        recommendations = AWSDecisionEngine._build_recommendations(metadata, technology, primary_target)
        confidence = AWSDecisionEngine._estimate_confidence(metadata, technology, primary_target)
        return primary_target, recommendations, confidence

    @staticmethod
    def _select_primary_target(metadata: RepoMetadata, technology: TechnologyAnalysis) -> str:
        if technology.backend_stack == 'Unknown' and technology.frontend_stack != 'Unknown':
            return 'AWS Amplify'
        if technology.serverless_readiness == 'High' and technology.backend_stack != 'Unknown':
            return 'AWS Lambda'
        if metadata.docker_compose:
            return 'AWS ECS'
        if metadata.docker_readiness:
            return 'AWS App Runner'
        if technology.frontend_stack != 'Unknown' and technology.backend_stack == 'Unknown':
            return 'AWS Amplify'
        return 'AWS App Runner'

    @staticmethod
    def _build_recommendations(metadata: RepoMetadata, technology: TechnologyAnalysis, primary_target: str) -> List[AWSRecommendationDetail]:
        recommendations: List[AWSRecommendationDetail] = []

        if primary_target == 'AWS Amplify':
            recommendations.append(AWSRecommendationDetail(
                service='AWS Amplify',
                purpose='Host static frontend apps and manage CI/CD from repository source.',
                reason='The repository appears to be a frontend-first application with no backend service or with static frontend delivery requirements.',
                advantages=['Automatic global CDN distribution', 'Built-in branch previews and SSL', 'Minimal infrastructure management'],
                trade_offs=['Less control over custom server configuration', 'Not ideal for complex backend services'],
                alternatives=['S3 + CloudFront', 'AWS App Runner'],
                estimated_monthly_cost_impact=3.0,
                confidence_score=90
            ))

        if primary_target == 'AWS App Runner':
            recommendations.append(AWSRecommendationDetail(
                service='AWS App Runner',
                purpose='Deploy containerized or source-based web applications with managed scaling.',
                reason='The repository has backend/service components and is container-ready or deployable without heavy orchestration.',
                advantages=['Managed runtime with auto-scaling', 'No cluster management', 'Simple deployment workflow'],
                trade_offs=['Less control than ECS/EKS', 'May be costlier at scale than self-managed compute'],
                alternatives=['AWS ECS', 'AWS Lambda'],
                estimated_monthly_cost_impact=10.0,
                confidence_score=85
            ))

        if primary_target == 'AWS ECS':
            recommendations.append(AWSRecommendationDetail(
                service='AWS ECS on Fargate',
                purpose='Run container workloads with managed orchestration and networking control.',
                reason='The repository indicates multi-container configurations or Docker Compose files which benefit from ECS service management.',
                advantages=['Task-level scaling', 'Flexible networking with VPC', 'Good for microservices'],
                trade_offs=['More operational complexity than App Runner', 'Requires container definition management'],
                alternatives=['AWS App Runner', 'Amazon EKS'],
                estimated_monthly_cost_impact=25.0,
                confidence_score=82
            ))

        if primary_target == 'AWS Lambda':
            recommendations.append(AWSRecommendationDetail(
                service='AWS Lambda',
                purpose='Execute backend functions in a serverless, event-driven model.',
                reason='The repository shows serverless readiness and is suitable for event-driven APIs or task functions.',
                advantages=['Pay-per-use cost model', 'Automatic scaling to zero', 'Minimal infrastructure to manage'],
                trade_offs=['Cold starts may impact latency', 'Not ideal for long-running processes'],
                alternatives=['AWS App Runner', 'AWS ECS'],
                estimated_monthly_cost_impact=5.0,
                confidence_score=88
            ))

        # Support services
        if metadata.databases:
            recommendations.append(AWSRecommendationDetail(
                service='Amazon RDS',
                purpose='Managed relational database service for backend persistence.',
                reason='Relational database dependencies were detected and require a durable managed data store.',
                advantages=['Automated backups', 'High availability options', 'Managed scaling'],
                trade_offs=['Higher cost than self-hosted databases', 'Provisioning complexity for scaling'],
                alternatives=['Amazon Aurora', 'Amazon DynamoDB'],
                estimated_monthly_cost_impact=20.0,
                confidence_score=80
            ))

        if technology.cloud_readiness == 'High' and 'AWS Amplify' not in [r.service for r in recommendations]:
            recommendations.append(AWSRecommendationDetail(
                service='Amazon CloudFront',
                purpose='Deliver cached frontend assets globally with low latency.',
                reason='Frontend assets and static file delivery can benefit from a CDN to improve performance worldwide.',
                advantages=['Low latency edge delivery', 'Built-in security with WAF integration', 'Reduced origin load'],
                trade_offs=['Additional configuration required', 'Costs scale with traffic'],
                alternatives=['S3 Transfer Acceleration', 'AWS Global Accelerator'],
                estimated_monthly_cost_impact=5.0,
                confidence_score=75
            ))

        if metadata.docker_readiness and primary_target != 'AWS ECS':
            recommendations.append(AWSRecommendationDetail(
                service='Amazon ECR',
                purpose='Store container images for managed deployment targets.',
                reason='Container readiness was detected, so a container registry is recommended for build and deployment workflows.',
                advantages=['Secure image storage', 'Integration with ECS and App Runner', 'Image version management'],
                trade_offs=['Additional repository management', 'Storage costs for large images'],
                alternatives=['Docker Hub', 'GitHub Container Registry'],
                estimated_monthly_cost_impact=2.0,
                confidence_score=80
            ))

        return recommendations

    @staticmethod
    def _estimate_confidence(metadata: RepoMetadata, technology: TechnologyAnalysis, primary_target: str) -> float:
        confidence = 50.0
        if primary_target == 'AWS Amplify':
            confidence += 30.0
        if primary_target == 'AWS App Runner':
            confidence += 20.0
        if primary_target == 'AWS ECS':
            confidence += 15.0
        if primary_target == 'AWS Lambda':
            confidence += 18.0
        if metadata.docker_readiness:
            confidence += 10.0
        if metadata.terraform:
            confidence += 8.0
        if metadata.ci_cd:
            confidence += 5.0
        return min(confidence, 100.0)
