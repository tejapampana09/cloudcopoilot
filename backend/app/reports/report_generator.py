from typing import List
from app.schemas.architecture import ArchitectureSummary, AWSRecommendationDetail, VisualizationJSON
from app.schemas.analyzer import RepoMetadata


class ReportGenerator:
    @staticmethod
    def build_report(metadata: RepoMetadata, architecture: ArchitectureSummary, aws_recommendations: List[AWSRecommendationDetail]) -> dict:
        return {
            'summary': {
                'scope': metadata.repo_url or 'Local repository analysis',
                'application_boundaries': architecture.application_boundaries,
                'deployment_model': architecture.deployment_model,
                'primary_recommendation': aws_recommendations[0].service if aws_recommendations else 'TBD',
                'confidence_score': aws_recommendations[0].confidence_score if aws_recommendations else 0,
            },
            'architecture': architecture.dict(),
            'aws_recommendations': [recommendation.dict() for recommendation in aws_recommendations],
            'best_practices': ReportGenerator._best_practices(metadata, architecture),
        }

    @staticmethod
    def _best_practices(metadata: RepoMetadata, architecture: ArchitectureSummary) -> List[str]:
        best_practices = []
        if metadata.terraform:
            best_practices.append('Maintain infrastructure as code and version controlled deployment definitions.')
        if metadata.ci_cd:
            best_practices.append('Establish CI/CD pipelines to validate repository changes and automate deployments.')
        if architecture.frontend != 'No dedicated frontend layer detected.':
            best_practices.append('Use a CDN for frontend static asset delivery to improve performance.')
        if metadata.databases:
            best_practices.append('Use managed database services with automated backups and security controls.')
        return best_practices

    @staticmethod
    def build_visualization_graph(metadata: RepoMetadata, architecture: ArchitectureSummary) -> VisualGraph:
        nodes = [
            {'id': 'frontend', 'label': 'Frontend', 'type': 'component'},
            {'id': 'backend', 'label': 'Backend', 'type': 'component'},
            {'id': 'database', 'label': 'Database', 'type': 'component'},
            {'id': 'storage', 'label': 'Storage', 'type': 'component'},
            {'id': 'network', 'label': 'Networking', 'type': 'component'},
        ]
        edges = [
            {'from': 'frontend', 'to': 'backend', 'label': 'API / data flow'},
            {'from': 'backend', 'to': 'database', 'label': 'persistence'},
            {'from': 'backend', 'to': 'storage', 'label': 'assets & logs'},
            {'from': 'backend', 'to': 'network', 'label': 'ingress/egress'},
        ]

        if architecture.frontend == 'No dedicated frontend layer detected.':
            nodes = [node for node in nodes if node['id'] != 'frontend']
            edges = [edge for edge in edges if edge['from'] != 'frontend' and edge['to'] != 'frontend']

        return VisualizationJSON(nodes=nodes, connections=edges)
