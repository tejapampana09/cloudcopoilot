from typing import Dict
from app.schemas.architecture import RepositoryContext
from app.schemas.analyzer import RepoMetadata


class RepositoryContextBuilder:
    @staticmethod
    def build(metadata: RepoMetadata, repo_name: str, owner: str) -> RepositoryContext:
        project_type = "Unknown"
        if metadata.frontend and metadata.backend:
            project_type = "Fullstack"
        elif metadata.frontend:
            project_type = "Frontend"
        elif metadata.backend:
            project_type = "Backend"

        project_complexity = RepositoryContextBuilder._estimate_complexity(metadata)
        expected_scalability = RepositoryContextBuilder._estimate_scalability(metadata)
        repository_structure = RepositoryContextBuilder._analyze_repository_structure(metadata)

        return RepositoryContext(
            project_name=repo_name,
            project_type=project_type,
            frontend_framework=metadata.frontend[0] if metadata.frontend else None,
            backend_framework=metadata.backend[0] if metadata.backend else None,
            programming_languages=[lang.name for lang in metadata.languages],
            package_managers=metadata.package_managers,
            databases=metadata.databases,
            orm=[],
            authentication=[],
            storage=[],
            caching=[],
            queues=[],
            third_party_apis=[],
            environment_variables=metadata.env_variables,
            deployment_requirements=metadata.run_commands + metadata.build_commands,
            docker_availability=metadata.docker_readiness,
            infrastructure_files=metadata.infrastructure_files,
            build_commands=metadata.build_commands,
            run_commands=metadata.run_commands,
            project_complexity=project_complexity,
            expected_scalability=expected_scalability,
            repository_structure=repository_structure,
            dependencies=[],
        )

    @staticmethod
    def _estimate_complexity(metadata: RepoMetadata) -> str:
        score = 0
        score += len(metadata.languages) * 2
        score += len(metadata.frameworks) * 3
        score += len(metadata.infrastructure_files) * 2
        score += len(metadata.package_managers)
        score += 5 if metadata.docker_compose else 0
        score += 3 if metadata.terraform else 0
        if score >= 12:
            return "High"
        if score >= 7:
            return "Medium"
        return "Low"

    @staticmethod
    def _estimate_scalability(metadata: RepoMetadata) -> str:
        if metadata.docker_readiness or metadata.terraform:
            return "Good"
        if metadata.frontend and metadata.backend:
            return "Moderate"
        return "Limited"

    @staticmethod
    def _analyze_repository_structure(metadata: RepoMetadata) -> Dict[str, int]:
        return {
            "languages": len(metadata.languages),
            "frameworks": len(metadata.frameworks),
            "frontend_components": len(metadata.frontend),
            "backend_components": len(metadata.backend),
            "databases": len(metadata.databases),
            "infrastructure_files": len(metadata.infrastructure_files)
        }
