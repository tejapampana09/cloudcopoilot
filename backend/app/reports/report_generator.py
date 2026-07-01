from typing import List, Optional
from app.schemas.architecture import (
    ArchitectureSummary, AWSRecommendationDetail, VisualizationJSON, 
    VisualizationNode, VisualizationConnection, ArchitectureReport, RepositoryContext
)
from app.schemas.analyzer import RepoMetadata


class ReportGenerator:
    @staticmethod
    def build_report(
        metadata: RepoMetadata, 
        architecture: ArchitectureSummary, 
        aws_recommendations: List[AWSRecommendationDetail],
        repository_context: Optional[RepositoryContext] = None,
        reasons_list: Optional[List[str]] = None,
        cost_assumptions_str: str = "",
        health_score: int = 80
    ) -> dict:
        """
        Builds the comprehensive final Solutions Architect report in accordance with the ArchitectureReport schema.
        """
        # 1. Detected Components List
        detected = []
        if repository_context:
            if repository_context.frontend_framework:
                detected.append(f"Frontend: {repository_context.frontend_framework}")
            if repository_context.backend_framework:
                detected.append(f"Backend: {repository_context.backend_framework}")
            for db in repository_context.databases:
                detected.append(f"Database: {db}")
            for o in repository_context.orm:
                detected.append(f"ORM: {o}")
            for auth in repository_context.authentication:
                detected.append(f"Auth: {auth}")
            for st in repository_context.storage:
                detected.append(f"Storage: {st}")
            for c in repository_context.caching:
                detected.append(f"Cache: {c}")
            for q in repository_context.queues:
                detected.append(f"Queue/Workers: {q}")
        else:
            if metadata.frontend:
                detected.append(f"Frontend: {', '.join(metadata.frontend)}")
            if metadata.backend:
                detected.append(f"Backend: {', '.join(metadata.backend)}")
            if metadata.databases:
                detected.append(f"Database: {', '.join(metadata.databases)}")

        # 2. Extract reasons and trade-offs
        reasons = reasons_list or []
        trade_offs = []
        if aws_recommendations:
            trade_offs = aws_recommendations[0].trade_offs
            
        # 3. Formulate summaries
        repo_summary = (
            f"Repository analysis of {metadata.repo_url or 'local repository'}. "
            f"The application was detected as a {repository_context.project_type if repository_context else 'web'} service "
            f"utilizing {', '.join([l.name for l in metadata.languages[:3]])} code bases. "
            f"README documentation quality is assessed as {metadata.readme_quality}."
        )

        tech_stack = (
            f"Languages: {', '.join([l.name for l in metadata.languages])}. "
            f"Frameworks: {', '.join(metadata.frameworks) if metadata.frameworks else 'None declared'}. "
            f"Package Managers: {', '.join(metadata.package_managers)}. "
            f"Infrastructure Files: {', '.join(metadata.infrastructure_files) if metadata.infrastructure_files else 'None'}."
        )

        arch_overview = (
            f"Application boundaries: {architecture.application_boundaries} "
            f"Networking model: {architecture.networking} "
            f"State management logic: {architecture.state_management} "
            f"Deployment architecture: {architecture.deployment_model}."
        )

        # 4. Security, Performance & Scalability reviews
        security_review = (
            "1. Secrets Protection: Ensure no plain-text passwords or API keys are committed. "
            "Recommend using AWS Secrets Manager or Systems Manager Parameter Store. "
            "2. Networking Isolation: Deploy database clusters inside private VPC subnets with Security Group rules "
            "allowing ingress only from the compute service containers."
        )
        if repository_context and "AWS Cognito" in repository_context.authentication:
            security_review += " 3. User authentication is offloaded to AWS Cognito User Pools for secure token validation."

        performance_review = (
            "1. Caching Strategy: Highly recommend adding a caching tier (ElastiCache Redis) to reduce read queries to databases. "
            "2. Content Delivery: Serve static front-end assets via CloudFront globally to minimize latency andOrigin load."
        )
        if repository_context and repository_context.caching:
            performance_review = (
                f"Caching layer is configured using {', '.join(repository_context.caching)}. "
                "Ensure cache eviction policies (TTL) are configured to prevent stale data."
            )

        scalability_review = (
            "1. Auto-scaling: Compute target auto-scaling thresholds should trigger horizontal container launches "
            "at 70% CPU utilization. "
            "2. Database Scale: Implement Read Replicas for relational database engines to scale queries horizontally."
        )
        if repository_context and repository_context.expected_scalability == "Limited":
            scalability_review += " 3. Warning: SQLite or local upload directories limit scaling capabilities."

        # 5. Risk Assessment
        risk_assessment = "Low architectural risks identified."
        if architecture.bottlenecks and architecture.bottlenecks != "No critical architectural bottlenecks identified from static repository scan.":
            risk_assessment = f"Architectural Risks: {architecture.bottlenecks}"

        # 6. Future Improvements
        future_improvements = (
            "1. Codify all infrastructure into reusable Terraform modules. "
            "2. Implement automated Docker container build and push pipelines via GitHub Actions. "
            "3. Add integration test suites to run post-deployment validations."
        )
        if repository_context and not repository_context.caching:
            future_improvements += " 4. Introduce Redis in-memory storage for high-availability request caching."

        # 7. Overall Scores
        overall_score = 75
        if metadata.docker_readiness:
            overall_score += 10
        if metadata.terraform:
            overall_score += 10
        if metadata.ci_cd:
            overall_score += 5
        overall_score = min(overall_score, 100)

        report = ArchitectureReport(
            repository_summary=repo_summary,
            technology_stack=tech_stack,
            architecture_overview=arch_overview,
            detected_components=detected,
            aws_architecture_recommendation=aws_recommendations,
            reasons=reasons,
            trade_offs=trade_offs,
            security_review=security_review,
            performance_review=performance_review,
            scalability_review=scalability_review,
            cost_analysis=cost_assumptions_str,
            deployment_strategy=f"Deploy using {aws_recommendations[0].service if aws_recommendations else 'AWS compute'} with continuous Git integrations and automated IAM role credentials mapping.",
            risk_assessment=risk_assessment,
            future_improvements=future_improvements,
            overall_architecture_score=overall_score,
            cloud_readiness_score=health_score
        )

        return report.model_dump()

    @staticmethod
    def build_visualization_graph(metadata: RepoMetadata, architecture: ArchitectureSummary) -> VisualizationJSON:
        nodes = [
            VisualizationNode(id='frontend', label='Frontend CDN', type='component', metadata={'service': 'Amazon CloudFront'}),
            VisualizationNode(id='backend', label='App Compute', type='component', metadata={'service': 'AWS Compute'}),
            VisualizationNode(id='database', label='Managed DB', type='component', metadata={'service': 'Amazon RDS'}),
            VisualizationNode(id='storage', label='Object Storage', type='component', metadata={'service': 'Amazon S3'}),
            VisualizationNode(id='network', label='Networking Routing', type='component', metadata={'service': 'VPC'}),
        ]
        
        edges = [
            VisualizationConnection(source='frontend', target='backend', label='API / data flow'),
            VisualizationConnection(source='backend', target='database', label='persistence'),
            VisualizationConnection(source='backend', target='storage', label='assets & uploads'),
            VisualizationConnection(source='backend', target='network', label='ingress/egress'),
        ]

        if architecture.frontend == 'No dedicated frontend layer detected.':
            nodes = [node for node in nodes if node.id != 'frontend']
            edges = [edge for edge in edges if edge.source != 'frontend' and edge.target != 'frontend']

        return VisualizationJSON(nodes=nodes, connections=edges)
