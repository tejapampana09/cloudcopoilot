from typing import Optional
from app.schemas.architecture import ArchitectureSummary, RepositoryContext
from app.schemas.analyzer import RepoMetadata


class ArchitectureAnalyzer:
    @staticmethod
    def analyze(metadata: RepoMetadata, repository_context: Optional[RepositoryContext] = None) -> ArchitectureSummary:
        application_boundaries = ArchitectureAnalyzer._detect_application_boundaries(metadata, repository_context)
        frontend = ArchitectureAnalyzer._describe_frontend(metadata, repository_context)
        backend = ArchitectureAnalyzer._describe_backend(metadata, repository_context)
        database = ArchitectureAnalyzer._describe_database(metadata, repository_context)
        storage = ArchitectureAnalyzer._describe_storage(metadata, repository_context)
        networking = ArchitectureAnalyzer._describe_networking(metadata, repository_context)
        authentication_flow = ArchitectureAnalyzer._describe_authentication_flow(metadata, repository_context)
        external_integrations = ArchitectureAnalyzer._describe_external_integrations(metadata, repository_context)
        background_jobs = ArchitectureAnalyzer._describe_background_jobs(metadata, repository_context)
        static_assets = ArchitectureAnalyzer._describe_static_assets(metadata, repository_context)
        media_handling = ArchitectureAnalyzer._describe_media_handling(metadata, repository_context)
        state_management = ArchitectureAnalyzer._describe_state_management(metadata, repository_context)
        deployment_model = ArchitectureAnalyzer._describe_deployment_model(metadata, repository_context)
        bottlenecks = ArchitectureAnalyzer._identify_bottlenecks(metadata, repository_context)
        scaling_risks = ArchitectureAnalyzer._identify_scaling_risks(metadata, repository_context)
        availability_requirements = ArchitectureAnalyzer._estimate_availability_requirements(metadata, repository_context)

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
    def _detect_application_boundaries(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.frontend and metadata.backend:
            return "Multi-layer architecture with a separate frontend presentation web app and backend API service tier."
        if metadata.frontend:
            return "Single-layer static frontend layout designed for client-side routing and static hosting."
        if metadata.backend:
            return "Backend service layer exposing API routes, handling business logic, and managing persistence."
        return "Generic codebase structure with mixed utility or script layouts."

    @staticmethod
    def _describe_frontend(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.frontend:
            tech = metadata.frontend[0]
            if ctx and ctx.frontend_framework:
                tech = ctx.frontend_framework
            return f"Client layer built with {tech}. Handles interactive UI routing, state, and HTTP client requests."
        return "No presentation or client-side frontend layer detected."

    @staticmethod
    def _describe_backend(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.backend:
            tech = metadata.backend[0]
            if ctx and ctx.backend_framework:
                tech = ctx.backend_framework
            return f"Service API tier powered by {tech}, managing incoming routing, request middleware, and business workflows."
        return "No backend web server or API routing tier detected."

    @staticmethod
    def _describe_database(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        dbs = metadata.databases
        if ctx and ctx.databases:
            dbs = ctx.databases
            
        if dbs:
            orm_str = ""
            if ctx and ctx.orm:
                orm_str = f" using {', '.join(ctx.orm)} ORM/driver mapping"
            return f"Persistence tier utilizes {', '.join(dbs)}{orm_str} for relational/non-relational data storage."
        return "Database persistence is not explicitly declared in this codebase."

    @staticmethod
    def _describe_storage(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        detected = []
        if ctx and ctx.storage:
            detected.extend(ctx.storage)
        if metadata.infrastructure_files:
            if any('s3' in f.lower() for f in metadata.infrastructure_files):
                detected.append('Amazon S3 Cloud storage configurations')
        
        if detected:
            return f"Storage is structured around: {', '.join(detected)}."
        return "No explicit cloud object storage configuration found; defaults to local file system writes."

    @staticmethod
    def _describe_networking(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.terraform:
            return "VPC and subnet isolation are codified in Terraform configuration."
        if metadata.docker_compose:
            return "Docker bridged container network defined for service-to-service DNS resolution."
        return "Networking is platform-managed, utilizing standard HTTPS ingress to the container/app target."

    @staticmethod
    def _describe_authentication_flow(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if ctx and ctx.authentication:
            return f"Authentication uses: {', '.join(ctx.authentication)}. Token mapping verify handlers are present."
        if metadata.env_variables:
            if any(k in "".join(metadata.env_variables).upper() for k in ["JWT", "TOKEN", "SECRET"]):
                return "Token-based / session verification verified via environment secret keys."
        return "Authentication flows are not configured or are delegated to external identity gateways."

    @staticmethod
    def _describe_external_integrations(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if ctx and ctx.third_party_apis:
            return f"Integrates with external third-party APIs: {', '.join(ctx.third_party_apis)}."
        return "No third-party SaaS integrations (like Stripe, Twilio, SendGrid) are declared in dependencies."

    @staticmethod
    def _describe_background_jobs(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if ctx and ctx.queues:
            return f"Asynchronous task workers are powered by: {', '.join(ctx.queues)}."
        return "Asynchronous background task runner engines are not present."

    @staticmethod
    def _describe_static_assets(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.frontend:
            return "Compiled client-side assets (HTML/JS/CSS bundles) are generated and optimized during build stage."
        return "Static assets build pipelines are not configured."

    @staticmethod
    def _describe_media_handling(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if ctx and any("multer" in d.lower() or "upload" in d.lower() for d in ctx.dependencies):
            return "Local file system multipart/form-data upload handlers (e.g. Multer) process media uploads."
        if ctx and any("s3" in d.lower() or "boto3" in d.lower() for d in ctx.dependencies):
            return "Direct-to-cloud file streams publish uploads directly to S3 object buckets."
        return "No explicit file upload/media streaming logic detected."

    @staticmethod
    def _describe_state_management(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.frontend:
            return "Frontend manages state locally within client framework memory (SPA hooks, Redux, or Vuex)."
        return "State management is serverless and stateless across requests."

    @staticmethod
    def _describe_deployment_model(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.terraform:
            return "Infrastructure as Code (IaC) deployment via Terraform."
        if metadata.docker_readiness:
            return "Containerized execution deployment using a Dockerfile."
        return "Direct source-code deployment model relying on buildpack runtimes."

    @staticmethod
    def _identify_bottlenecks(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if ctx:
            from app.analysis.context_builder import RepositoryContextBuilder
            has_local_uploads = any(upload_dir in "".join(ctx.dependencies).lower() for upload_dir in ["multer", "uploads"])
            # check files in repository_structure
            has_sqlite = "SQLite" in ctx.databases
            bottlenecks = RepositoryContextBuilder._detect_bottlenecks(
                metadata=metadata,
                dependencies=ctx.dependencies,
                authentication=ctx.authentication,
                storage=ctx.storage,
                caching=ctx.caching,
                queues=ctx.queues,
                has_local_uploads=has_local_uploads,
                has_sqlite=has_sqlite
            )
            if bottlenecks:
                return " | ".join(bottlenecks)
        
        return "No critical architectural bottlenecks identified from static repository scan."

    @staticmethod
    def _identify_scaling_risks(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        risks = []
        if ctx:
            if "SQLite" in ctx.databases:
                risks.append("File-locked database database (SQLite) blocks multiple instance scaling.")
            if any("multer" in d.lower() for d in ctx.dependencies):
                risks.append("Stateful local disk writes break stateless container scaling assumptions.")
            if metadata.backend and not ctx.queues:
                risks.append("Lack of worker task queue can cause request timeout bottlenecks under compute-heavy requests.")
            if not ctx.caching and ctx.databases:
                risks.append("No memory caching layer can lead to high database read strain under high traffic load.")

        if risks:
            return " | ".join(risks)
        return "Moderate scaling risk; standard cloud architecture is recommended."

    @staticmethod
    def _estimate_availability_requirements(metadata: RepoMetadata, ctx: Optional[RepositoryContext]) -> str:
        if metadata.terraform or metadata.ci_cd:
            return "Requires high availability setup (Multi-AZ deploy) with CI/CD deployment pipeline automation."
        return "Standard availability via basic managed service scaling and automated health restarts."
