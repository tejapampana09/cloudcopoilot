from typing import Dict
from app.schemas.architecture import TechnologyAnalysis
from app.schemas.analyzer import RepoMetadata


class TechnologyAnalyzer:
    @staticmethod
    def analyze(metadata: RepoMetadata) -> TechnologyAnalysis:
        frontend_stack = TechnologyAnalyzer._detect_frontend_stack(metadata)
        backend_stack = TechnologyAnalyzer._detect_backend_stack(metadata)
        database = metadata.databases[0] if metadata.databases else None
        api_style = TechnologyAnalyzer._detect_api_style(metadata)
        authentication = TechnologyAnalyzer._detect_authentication(metadata)
        service_architecture = TechnologyAnalyzer._detect_service_architecture(metadata)
        ssr_vs_spa = TechnologyAnalyzer._detect_ssr_vs_spa(metadata)
        serverless_readiness = TechnologyAnalyzer._detect_serverless_readiness(metadata)
        container_readiness = TechnologyAnalyzer._detect_container_readiness(metadata)
        cloud_readiness = TechnologyAnalyzer._detect_cloud_readiness(metadata)
        confidence = TechnologyAnalyzer._build_confidence(metadata)

        return TechnologyAnalysis(
            frontend_stack=frontend_stack,
            backend_stack=backend_stack,
            database=database,
            api_style=api_style,
            authentication=authentication,
            service_architecture=service_architecture,
            ssr_vs_spa=ssr_vs_spa,
            serverless_readiness=serverless_readiness,
            container_readiness=container_readiness,
            cloud_readiness=cloud_readiness,
            detection_confidence=confidence,
        )

    @staticmethod
    def _detect_frontend_stack(metadata: RepoMetadata) -> str:
        if any('React' in f for f in metadata.frontend):
            return 'React'
        if any('Vue' in f for f in metadata.frontend):
            return 'Vue'
        if any('Svelte' in f for f in metadata.frontend):
            return 'Svelte'
        if 'Next.js' in metadata.frameworks:
            return 'Next.js'
        return 'Unknown'

    @staticmethod
    def _detect_backend_stack(metadata: RepoMetadata) -> str:
        if any('FastAPI' in f for f in metadata.backend):
            return 'FastAPI'
        if any('Express' in f for f in metadata.backend):
            return 'Express'
        if any('Django' in f for f in metadata.backend):
            return 'Django'
        if any('NestJS' in f for f in metadata.backend):
            return 'NestJS'
        return 'Unknown'

    @staticmethod
    def _detect_api_style(metadata: RepoMetadata) -> str:
        if 'GraphQL' in metadata.frameworks or 'Apollo' in metadata.frameworks:
            return 'GraphQL'
        if metadata.backend:
            return 'REST'
        return 'Static'

    @staticmethod
    def _detect_authentication(metadata: RepoMetadata) -> str:
        if any('JWT' in env or 'AUTH' in env for env in metadata.env_variables):
            return 'Token-based / JWT'
        return 'Unknown'

    @staticmethod
    def _detect_service_architecture(metadata: RepoMetadata) -> str:
        if metadata.frontend and metadata.backend:
            return 'Monolith with clear frontend/backend separation'
        if metadata.backend and not metadata.frontend:
            return 'Backend API service'
        return 'Static frontend'

    @staticmethod
    def _detect_ssr_vs_spa(metadata: RepoMetadata) -> str:
        if any('Next.js' in f for f in metadata.frontend) or 'Next.js' in metadata.frameworks:
            return 'SSR or hybrid'
        if metadata.frontend:
            return 'SPA'
        return 'None'

    @staticmethod
    def _detect_serverless_readiness(metadata: RepoMetadata) -> str:
        if metadata.terraform or any('serverless' in path.lower() for path in metadata.infrastructure_files):
            return 'High'
        if metadata.docker_readiness:
            return 'Medium'
        return 'Low'

    @staticmethod
    def _detect_container_readiness(metadata: RepoMetadata) -> str:
        if metadata.docker_readiness:
            return 'High'
        if metadata.frontend and metadata.backend:
            return 'Medium'
        return 'Low'

    @staticmethod
    def _detect_cloud_readiness(metadata: RepoMetadata) -> str:
        if metadata.terraform or metadata.ci_cd:
            return 'High'
        if metadata.docker_readiness:
            return 'Medium'
        return 'Low'

    @staticmethod
    def _build_confidence(metadata: RepoMetadata) -> Dict[str, int]:
        return {
            'frontend_stack': 90 if metadata.frontend else 50,
            'backend_stack': 90 if metadata.backend else 50,
            'database': 90 if metadata.databases else 40,
            'api_style': 80 if metadata.backend else 50,
            'authentication': 70 if metadata.env_variables else 40,
            'service_architecture': 80,
            'ssr_vs_spa': 80,
            'serverless_readiness': 70,
            'container_readiness': 80 if metadata.docker_readiness else 50,
            'cloud_readiness': 70,
        }
