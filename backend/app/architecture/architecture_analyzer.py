from app.schemas.architecture import ArchitectureSummary
from app.schemas.analyzer import RepoMetadata


class ArchitectureAnalyzer:
    @staticmethod
    def analyze(metadata: RepoMetadata) -> ArchitectureSummary:
        application_boundaries = ArchitectureAnalyzer._detect_application_boundaries(metadata)
        frontend = ArchitectureAnalyzer._describe_frontend(metadata)
        backend = ArchitectureAnalyzer._describe_backend(metadata)
        database = ArchitectureAnalyzer._describe_database(metadata)
        storage = ArchitectureAnalyzer._describe_storage(metadata)
        networking = ArchitectureAnalyzer._describe_networking(metadata)
        authentication_flow = ArchitectureAnalyzer._describe_authentication_flow(metadata)
        external_integrations = ArchitectureAnalyzer._describe_external_integrations(metadata)
        background_jobs = ArchitectureAnalyzer._describe_background_jobs(metadata)
        static_assets = ArchitectureAnalyzer._describe_static_assets(metadata)
        media_handling = ArchitectureAnalyzer._describe_media_handling(metadata)
        state_management = ArchitectureAnalyzer._describe_state_management(metadata)
        deployment_model = ArchitectureAnalyzer._describe_deployment_model(metadata)
        bottlenecks = ArchitectureAnalyzer._identify_bottlenecks(metadata)
        scaling_risks = ArchitectureAnalyzer._identify_scaling_risks(metadata)
        availability_requirements = ArchitectureAnalyzer._estimate_availability_requirements(metadata)

        return ArchitectureSummary(
            application_boundaries=application_boundaries,
            frontend=frontend,
            backend=backend,
            database=database,
            storage=storage,
            networking=networking,
            authentication_flow=authentication_flow,
            external_integrations=external_integrations,
            background_jobs=background_jobs,
            static_assets=static_assets,
            media_handling=media_handling,
            state_management=state_management,
            deployment_model=deployment_model,
            bottlenecks=bottlenecks,
            scaling_risks=scaling_risks,
            availability_requirements=availability_requirements,
        )

    @staticmethod
    def _detect_application_boundaries(metadata: RepoMetadata) -> str:
        if metadata.frontend and metadata.backend:
            return "Separated frontend and backend layers with distinct delivery paths."
        if metadata.frontend:
            return "Frontend-only repository focused on static or SPA content delivery."
        return "Backend-focused API/service repository."

    @staticmethod
    def _describe_frontend(metadata: RepoMetadata) -> str:
        if metadata.frontend:
            return f"Frontend is built using {', '.join(metadata.frontend)} with support for modern client-side rendering techniques."
        return "No dedicated frontend layer detected."

    @staticmethod
    def _describe_backend(metadata: RepoMetadata) -> str:
        if metadata.backend:
            return f"Backend contains {', '.join(metadata.backend)} services and APIs, likely using the detected frameworks and package managers."
        return "No backend layer detected."

    @staticmethod
    def _describe_database(metadata: RepoMetadata) -> str:
        if metadata.databases:
            return f"Database layer includes {', '.join(metadata.databases)}."
        return "No direct database platform detected from repository files."

    @staticmethod
    def _describe_storage(metadata: RepoMetadata) -> str:
        storage = []
        if metadata.infrastructure_files:
            if any('s3' in f.lower() for f in metadata.infrastructure_files):
                storage.append('S3 or object storage patterns')
        if metadata.docker_readiness:
            storage.append('container image storage readiness')
        return ' and '.join(storage) if storage else 'Storage planning is not explicit in the repository.'

    @staticmethod
    def _describe_networking(metadata: RepoMetadata) -> str:
        if metadata.terraform or metadata.ci_cd:
            return "Networking and cloud resources are partially codified or ready for automation."
        return "Networking is likely managed by the target deployment platform."

    @staticmethod
    def _describe_authentication_flow(metadata: RepoMetadata) -> str:
        if metadata.env_variables:
            return "Authentication-related environment variables are present, suggesting token or key-based auth flows."
        return "Authentication flow is not explicitly detected from repository metadata."

    @staticmethod
    def _describe_external_integrations(metadata: RepoMetadata) -> str:
        if metadata.package_managers:
            return "Third-party API integration patterns likely exist but are not explicitly detected without dependency parsing."
        return "External integrations are not clearly defined in static analysis."

    @staticmethod
    def _describe_background_jobs(metadata: RepoMetadata) -> str:
        return "Background job frameworks are not explicitly detected from the current repository scan."

    @staticmethod
    def _describe_static_assets(metadata: RepoMetadata) -> str:
        if metadata.frontend:
            return "Static assets are likely handled by the frontend build output and can be hosted via CDN-backed storage."
        return "No frontend asset pipeline detected."

    @staticmethod
    def _describe_media_handling(metadata: RepoMetadata) -> str:
        return "Media handling is not clearly visible from repository dependencies and infrastructure files."

    @staticmethod
    def _describe_state_management(metadata: RepoMetadata) -> str:
        return "State management is inferred from frontend framework rather than explicit repository files."

    @staticmethod
    def _describe_deployment_model(metadata: RepoMetadata) -> str:
        if metadata.terraform:
            return "Deployment model is cloud-infrastructure-as-code ready."
        if metadata.docker_readiness:
            return "Deployment model is container-ready and suitable for managed container services."
        return "Deployment model is simpler and likely platform-hosted."

    @staticmethod
    def _identify_bottlenecks(metadata: RepoMetadata) -> str:
        if metadata.docker_readiness and metadata.docker_compose:
            return "Container orchestration may be the main complexity point and may require coordinated scaling."
        return "Repository has standard complexity; bottlenecks are not clearly visible from static scanning."

    @staticmethod
    def _identify_scaling_risks(metadata: RepoMetadata) -> str:
        if metadata.frontend and metadata.backend and not metadata.terraform:
            return "Scaling risks exist if infrastructure automation is not added, especially around backend service scaling."
        return "Scaling risks are moderate given detected repository readiness."

    @staticmethod
    def _estimate_availability_requirements(metadata: RepoMetadata) -> str:
        if metadata.ci_cd or metadata.terraform:
            return "Supports higher availability patterns due to infrastructure automation readiness."
        return "Availability requirements imply platform-managed resilience rather than custom architecture."
