from typing import List, Optional, Dict
from app.schemas.architecture import RepositoryContext, TechnologyAnalysis
from app.schemas.analyzer import RepoMetadata


class ReasoningEngine:
    @staticmethod
    def generate_reasons(
        metadata: RepoMetadata, 
        target: str, 
        context: Optional[RepositoryContext] = None
    ) -> List[str]:
        """
        Generates step-by-step solutions architect reasoning statements based on the decision engine logic.
        """
        reasons = []
        
        # Step 1: Understand repository size & languages
        langs = [l.name for l in metadata.languages[:2]]
        reasons.append(
            f"Step 1 (Repository Understanding): Codebase is structured around {', '.join(langs)} "
            f"with {len(metadata.frameworks)} detected framework(s) and {metadata.readme_quality} quality documentation."
        )

        # Step 2: Understand architecture layers
        if context:
            reasons.append(
                f"Step 2 (Architecture Layering): Identified a `{context.project_type}` application boundary "
                f"with {len(context.databases)} database dependencies, {len(context.orm)} ORM mapping, "
                f"and {len(context.queues)} queue workers."
            )
        else:
            reasons.append("Step 2 (Architecture Layering): Inferred application layout based on repository scanner directories.")

        # Step 3: Infer operational requirements
        if context:
            has_stateful = any("multer" in d.lower() for d in context.dependencies)
            has_workers = len(context.queues) > 0
            
            if has_stateful:
                reasons.append(
                    "Step 3 (Operational Requirements): The application uses stateful local disk operations, "
                    "which demands cloud object storage integration (S3) to enable horizontal scaling."
                )
            elif has_workers:
                reasons.append(
                    "Step 3 (Operational Requirements): Background queue worker dependencies are present, "
                    "requiring continuous compute task execution and managed broker routing."
                )
            else:
                reasons.append(
                    "Step 3 (Operational Requirements): Standard stateless HTTP request processing. "
                    "Prioritizes low-latency container delivery or CDN edge hosting."
                )

        # Step 4: Evaluate AWS deployment options
        reasons.append(
            f"Step 4 (Candidate Evaluation): Evaluated AWS compute options. "
            f"Selected {target} as the primary candidate. Alternatives considered were: "
            f"{', '.join([alt for alt in ['AWS Amplify', 'AWS App Runner', 'AWS ECS on Fargate', 'AWS Lambda'] if target not in alt])}."
        )

        # Step 5: Compare Trade-offs
        if target in ["AWS ECS", "AWS ECS on Fargate"]:
            reasons.append(
                "Step 5 (Trade-off Analysis): ECS Fargate was selected over App Runner because of "
                "multi-container orchestration capability, despite requiring complex VPC and ALB setups."
            )
        elif target == "AWS App Runner":
            reasons.append(
                "Step 5 (Trade-off Analysis): App Runner was selected over ECS Fargate to minimize "
                "operational overhead (managed scaling, direct container deployments), and over Lambda to avoid execution timeouts."
            )
        elif target == "AWS Lambda":
            reasons.append(
                "Step 5 (Trade-off Analysis): AWS Lambda was selected over App Runner because of "
                "scale-to-zero cost efficiencies, despite the trade-off of function cold start times."
            )
        elif target == "AWS Amplify":
            reasons.append(
                "Step 5 (Trade-off Analysis): AWS Amplify was selected because the application has no "
                "backend service, making S3 website and CloudFront edge delivery the most performant and cost-efficient configuration."
            )

        # Step 6: Final decision
        reasons.append(
            f"Step 6 (Selection): Confirmed {target} as the optimal primary architecture. "
            f"Secondary resources (ECR, RDS, CloudFront, SQS) are configured to support the primary compute."
        )

        return reasons
