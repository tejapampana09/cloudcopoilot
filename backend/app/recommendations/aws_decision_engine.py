from typing import List, Tuple, Dict, Optional
from app.schemas.architecture import AWSRecommendationDetail, RepositoryContext, TechnologyAnalysis
from app.schemas.analyzer import RepoMetadata


class AWSDecisionEngine:
    @staticmethod
    def evaluate(
        metadata: RepoMetadata, 
        technology: TechnologyAnalysis, 
        context: Optional[RepositoryContext] = None
    ) -> Tuple[str, List[AWSRecommendationDetail], float]:
        """
        Runs the multi-stage AWS Decision Engine using a weighted decision matrix.
        Evaluates Amplify, App Runner, ECS (Fargate), and Lambda.
        Returns the primary target name, a list of detailed recommendations, and target confidence percentage.
        """
        # 1. Define Weights based on tech profile
        weights = AWSDecisionEngine._calculate_weights(metadata, technology, context)
        
        # 2. Score Candidates
        candidate_scores = AWSDecisionEngine._score_candidates(metadata, technology, context)
        
        # 3. Calculate Weighted Scores
        weighted_results: Dict[str, float] = {}
        for candidate, scores in candidate_scores.items():
            total_score = 0.0
            for factor, score in scores.items():
                total_score += score * weights[factor]
            weighted_results[candidate] = round(total_score, 2)
            
        # 4. Sort and select primary target
        sorted_candidates = sorted(weighted_results.items(), key=lambda x: x[1], reverse=True)
        primary_target = sorted_candidates[0][0]
        
        # Calculate target confidence (scale primary score to percentage)
        # Primary score of 9.0 -> 90% confidence
        primary_score = sorted_candidates[0][1]
        confidence = min(max(primary_score * 10.0, 50.0), 100.0)

        # 5. Build explainable recommendations
        recommendations = AWSDecisionEngine._build_explainable_recommendations(
            metadata=metadata,
            technology=technology,
            context=context,
            primary_target=primary_target,
            candidate_scores=candidate_scores,
            weighted_results=weighted_results,
            confidence=confidence
        )

        return primary_target, recommendations, confidence

    @staticmethod
    def _calculate_weights(
        metadata: RepoMetadata, 
        tech: TechnologyAnalysis, 
        ctx: Optional[RepositoryContext]
    ) -> Dict[str, float]:
        # Default Weights
        weights = {
            "deployment_simplicity": 0.10,
            "operational_complexity": 0.10,
            "scalability": 0.12,
            "high_availability": 0.10,
            "expected_traffic": 0.08,
            "cold_start_impact": 0.08,
            "cost_efficiency": 0.12,
            "developer_experience": 0.10,
            "security": 0.10,
            "maintainability": 0.10
        }
        
        is_static = (tech.backend_stack == 'Unknown' and tech.frontend_stack != 'Unknown') or (ctx and ctx.project_type == "Frontend")
        has_compose = metadata.docker_compose or (ctx and ctx.repository_structure.get("infrastructure_files", 0) > 0 and any("compose" in f.lower() for f in metadata.infrastructure_files))
        is_serverless = tech.serverless_readiness == 'High' or any("serverless" in f.lower() or "cdk" in f.lower() for f in metadata.infrastructure_files)

        if is_static:
            # Emphasize simplicity, low cost, devEx, low complexity
            weights = {
                "deployment_simplicity": 0.20,
                "operational_complexity": 0.10,
                "scalability": 0.10,
                "high_availability": 0.10,
                "expected_traffic": 0.05,
                "cold_start_impact": 0.02,
                "cost_efficiency": 0.20,
                "developer_experience": 0.13,
                "security": 0.05,
                "maintainability": 0.05
            }
        elif has_compose:
            # Emphasize container orchestration, high availability, scale, security
            weights = {
                "deployment_simplicity": 0.05,
                "operational_complexity": 0.12,
                "scalability": 0.15,
                "high_availability": 0.15,
                "expected_traffic": 0.10,
                "cold_start_impact": 0.08,
                "cost_efficiency": 0.10,
                "developer_experience": 0.05,
                "security": 0.12,
                "maintainability": 0.08
            }
        elif is_serverless:
            # Emphasize cost efficiency (scale-to-zero), scalability, cold start tolerance
            weights = {
                "deployment_simplicity": 0.10,
                "operational_complexity": 0.08,
                "scalability": 0.15,
                "high_availability": 0.10,
                "expected_traffic": 0.05,
                "cold_start_impact": 0.15,
                "cost_efficiency": 0.17,
                "developer_experience": 0.10,
                "security": 0.05,
                "maintainability": 0.05
            }
            
        # Normalize weights to sum exactly to 1.0 (safety check)
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            for k in weights:
                weights[k] = weights[k] / total
                
        return weights

    @staticmethod
    def _score_candidates(
        metadata: RepoMetadata, 
        tech: TechnologyAnalysis, 
        ctx: Optional[RepositoryContext]
    ) -> Dict[str, Dict[str, float]]:
        # Define Base Scores
        scores: Dict[str, Dict[str, float]] = {
            "AWS Amplify": {
                "deployment_simplicity": 9.5, "operational_complexity": 9.5, "scalability": 9.0, 
                "high_availability": 9.0, "expected_traffic": 9.0, "cold_start_impact": 10.0, 
                "cost_efficiency": 9.5, "developer_experience": 9.0, "security": 8.0, "maintainability": 9.5
            },
            "AWS App Runner": {
                "deployment_simplicity": 8.5, "operational_complexity": 8.0, "scalability": 8.0, 
                "high_availability": 8.5, "expected_traffic": 8.0, "cold_start_impact": 8.5, 
                "cost_efficiency": 7.0, "developer_experience": 8.0, "security": 8.0, "maintainability": 8.5
            },
            "AWS ECS": { # Represents AWS ECS on Fargate
                "deployment_simplicity": 4.0, "operational_complexity": 4.5, "scalability": 9.5, 
                "high_availability": 9.5, "expected_traffic": 9.5, "cold_start_impact": 10.0, 
                "cost_efficiency": 6.0, "developer_experience": 6.0, "security": 9.0, "maintainability": 7.0
            },
            "AWS Lambda": {
                "deployment_simplicity": 7.0, "operational_complexity": 7.0, "scalability": 10.0, 
                "high_availability": 9.5, "expected_traffic": 8.5, "cold_start_impact": 4.0, 
                "cost_efficiency": 9.0, "developer_experience": 7.5, "security": 8.5, "maintainability": 7.5
            }
        }
        
        is_static = (tech.backend_stack == 'Unknown' and tech.frontend_stack != 'Unknown') or (ctx and ctx.project_type == "Frontend")
        has_compose = metadata.docker_compose or (ctx and any("compose" in f.lower() for f in metadata.infrastructure_files))
        has_docker = metadata.docker_readiness
        has_db = len(metadata.databases) > 0 or (ctx and len(ctx.databases) > 0)
        has_workers = ctx and len(ctx.queues) > 0
        has_stateful = ctx and any("multer" in d.lower() for d in ctx.dependencies)
        
        # Adjust AWS Amplify scores
        if not is_static:
            if tech.backend_stack != 'Unknown' and 'Next.js' in metadata.frameworks:
                # Next.js SSR is supported on Amplify but with limitations
                scores["AWS Amplify"]["deployment_simplicity"] -= 1.5
                scores["AWS Amplify"]["scalability"] -= 1.5
                scores["AWS Amplify"]["cost_efficiency"] -= 1.5
            else:
                # Amplify is a very bad match for general Python/Go backend services
                for factor in scores["AWS Amplify"]:
                    scores["AWS Amplify"][factor] = max(1.0, scores["AWS Amplify"][factor] - 7.5)
        else:
            # Frontend only gets a boost on Amplify
            scores["AWS Amplify"]["deployment_simplicity"] = 10.0
            scores["AWS Amplify"]["cost_efficiency"] = 10.0
            
        # Adjust AWS App Runner scores
        if is_static:
            # Overkill for static hosting
            scores["AWS App Runner"]["cost_efficiency"] -= 3.0
            scores["AWS App Runner"]["deployment_simplicity"] -= 1.5
        if has_compose:
            # App Runner does not natively support multi-container docker compose setup
            scores["AWS App Runner"]["deployment_simplicity"] -= 5.0
            scores["AWS App Runner"]["scalability"] -= 3.0
            scores["AWS App Runner"]["maintainability"] -= 2.0
        if has_docker:
            scores["AWS App Runner"]["deployment_simplicity"] = min(9.5, scores["AWS App Runner"]["deployment_simplicity"] + 1.0)
            scores["AWS App Runner"]["developer_experience"] = min(9.5, scores["AWS App Runner"]["developer_experience"] + 0.5)

        # Adjust AWS ECS scores
        if is_static:
            # Major overkill
            scores["AWS ECS"]["cost_efficiency"] -= 4.0
            scores["AWS ECS"]["deployment_simplicity"] -= 2.0
            scores["AWS ECS"]["operational_complexity"] -= 2.0
        if has_compose:
            # Natively supports multi-containers sidecar and tasks definition
            scores["AWS ECS"]["deployment_simplicity"] = min(7.5, scores["AWS ECS"]["deployment_simplicity"] + 2.5)
            scores["AWS ECS"]["scalability"] = min(10.0, scores["AWS ECS"]["scalability"] + 0.5)
            scores["AWS ECS"]["cost_efficiency"] = min(9.0, scores["AWS ECS"]["cost_efficiency"] + 1.5) # more cost-effective than running many App Runner services
        if has_docker:
            scores["AWS ECS"]["deployment_simplicity"] = min(8.0, scores["AWS ECS"]["deployment_simplicity"] + 1.0)

        # Adjust AWS Lambda scores
        if is_static:
            scores["AWS Lambda"]["deployment_simplicity"] -= 1.5
            scores["AWS Lambda"]["cost_efficiency"] -= 1.0
        if has_stateful or has_compose:
            # Serverless functions are stateless, 15-min timeout, and single-purpose
            scores["AWS Lambda"]["cost_efficiency"] -= 3.0
            scores["AWS Lambda"]["deployment_simplicity"] -= 2.5
            scores["AWS Lambda"]["scalability"] -= 3.0
            scores["AWS Lambda"]["cold_start_impact"] -= 1.0
        if has_db:
            # RDS connection exhaustion is an issue on Lambda without RDS Proxy
            scores["AWS Lambda"]["operational_complexity"] -= 1.0
            scores["AWS Lambda"]["scalability"] -= 1.0
            
        return scores

    @staticmethod
    def _build_explainable_recommendations(
        metadata: RepoMetadata,
        technology: TechnologyAnalysis,
        context: Optional[RepositoryContext],
        primary_target: str,
        candidate_scores: Dict[str, Dict[str, float]],
        weighted_results: Dict[str, float],
        confidence: float
    ) -> List[AWSRecommendationDetail]:
        recommendations: List[AWSRecommendationDetail] = []
        
        # Sort alternative candidates
        alternatives = [c for c in weighted_results.keys() if c != primary_target]
        alternatives.sort(key=lambda x: weighted_results[x], reverse=True)
        
        # Build explanation texts
        why_selected, why_alternatives, benefits, trade_offs, scaling, operational, cost_impact = AWSDecisionEngine._generate_rationale(
            metadata, technology, context, primary_target, alternatives, candidate_scores, weighted_results
        )

        # Detailed reason combining Markdown sections
        full_reason = (
            f"### Primary Selection Rationale\n"
            f"{why_selected}\n\n"
            f"### Alternative Analysis\n"
            f"{why_alternatives}\n\n"
            f"### Operational & Scaling Characteristics\n"
            f"- **Scaling:** {scaling}\n"
            f"- **Operational Overhead:** {operational}\n\n"
            f"### Cost Strategy\n"
            f"{cost_impact}"
        )

        recommendations.append(AWSRecommendationDetail(
            service=primary_target if primary_target != "AWS ECS" else "AWS ECS on Fargate",
            purpose="Primary compute resource to execute the core application workload.",
            reason=full_reason,
            advantages=benefits,
            trade_offs=trade_offs,
            alternatives=[alt if alt != "AWS ECS" else "AWS ECS on Fargate" for alt in alternatives],
            estimated_monthly_cost_impact=weighted_results[primary_target] * 3.0,
            confidence_score=int(confidence)
        ))

        # Support services
        dbs = metadata.databases
        if context and context.databases:
            dbs = context.databases
            
        if dbs:
            db_engine = dbs[0]
            if db_engine in ["PostgreSQL", "MySQL"]:
                recommendations.append(AWSRecommendationDetail(
                    service="Amazon RDS",
                    purpose=f"Fully managed relational database cluster running {db_engine}.",
                    reason=(
                        f"### Primary Selection Rationale\n"
                        f"Amazon RDS was selected because the repository utilizes `{db_engine}` for relational structured data storage. "
                        f"RDS automates backups, patch application, and storage scaling, keeping database operations managed.\n\n"
                        f"### Alternative Analysis\n"
                        f"- **Amazon Aurora:** Highly scalable, but cost-prohibitive for low-to-medium traffic.\n"
                        f"- **Self-Hosted EC2:** Low cost but requires extreme manual maintenance, backup configurations, and vulnerability patching.\n\n"
                        f"### Operational & Scaling Characteristics\n"
                        f"- **Scaling:** Vertical scaling of database instance size, plus automatic storage volume expansion.\n"
                        f"- **HA:** Supports Multi-AZ deployments with synchronous replication.\n\n"
                        f"### Cost Strategy\n"
                        f"RDS runs on a continuous billing model. Single instance db.t4g.micro starts at $15/month."
                    ),
                    advantages=["Automated daily backups and point-in-time recovery", "One-click Multi-AZ failover setup", "Storage auto-scaling up to 64 TiB"],
                    trade_offs=["Requires active database instance hosting costs when idle", "Schema migrations must be managed outside AWS Console"],
                    alternatives=["Amazon Aurora PostgreSQL/MySQL", "Self-hosted Database on EC2"],
                    estimated_monthly_cost_impact=20.0,
                    confidence_score=90
                ))
            elif db_engine == "MongoDB":
                recommendations.append(AWSRecommendationDetail(
                    service="Amazon DocumentDB",
                    purpose="MongoDB-compatible fully managed NoSQL database cluster.",
                    reason=(
                        f"### Primary Selection Rationale\n"
                        f"Amazon DocumentDB is selected to support the MongoDB document database queries detected in the repository dependencies. "
                        f"It provides a scalable, enterprise-grade storage backend compatible with existing MongoDB drivers.\n\n"
                        f"### Alternative Analysis\n"
                        f"- **MongoDB Atlas:** Excellent SaaS offering, but running DocumentDB keeps all storage and networking isolated inside your private VPC.\n"
                        f"- **Self-hosted EC2 Mongo:** High operational burden for backup and scaling setup.\n\n"
                        f"### Operational & Scaling Characteristics\n"
                        f"- **Scaling:** Decoupled storage and compute scaling; storage scales automatically up to 64 TiB.\n"
                        f"- **HA:** Automated replicas with failover in under 30 seconds.\n\n"
                        f"### Cost Strategy\n"
                        f"DocumentDB starts at approximately $20-30/month for minimal instance configurations."
                    ),
                    advantages=["MongoDB driver compatibility", "Decoupled compute and storage scaling", "Enterprise security with VPC isolation"],
                    trade_offs=["Minimum pricing is higher than basic DynamoDB or SQLite options", "Some advanced MongoDB aggregation operators are unsupported"],
                    alternatives=["MongoDB Atlas on AWS", "Self-hosted MongoDB on EC2"],
                    estimated_monthly_cost_impact=25.0,
                    confidence_score=85
                ))
            elif db_engine == "Redis":
                recommendations.append(AWSRecommendationDetail(
                    service="Amazon ElastiCache for Redis",
                    purpose="High-performance in-memory cache and session store.",
                    reason=(
                        f"### Primary Selection Rationale\n"
                        f"Amazon ElastiCache for Redis is selected to host cache queries or background session stores. "
                        f"It keeps latency sub-millisecond, resolving performance bottlenecks on database reads.\n\n"
                        f"### Alternative Analysis\n"
                        f"- **Self-hosted Redis container:** Risk of data loss on container restart and lacks managed cluster replication.\n"
                        f"- **DynamoDB Accelerator (DAX):** Only works for DynamoDB, not generic key-value caching.\n\n"
                        f"### Operational & Scaling Characteristics\n"
                        f"- **Scaling:** Supports sharding and write-replica scaling.\n"
                        f"- **HA:** Managed failover across cache nodes.\n\n"
                        f"### Cost Strategy\n"
                        f"Continuous cache node instance costs starting at ~$10/month for t4g.micro nodes."
                    ),
                    advantages=["Sub-millisecond read/write latencies", "Automated cluster node backups", "Native support for pub/sub and Redis data structures"],
                    trade_offs=["In-memory storage is volatile and expensive per GB", "Requires VPC connection configuration"],
                    alternatives=["Self-hosted Redis in container", "Amazon MemoryDB"],
                    estimated_monthly_cost_impact=12.0,
                    confidence_score=85
                ))

        # Check for static assets storage and CDN
        if primary_target != "AWS Amplify" and (metadata.frontend or (context and context.project_type in ["Frontend", "Fullstack"])):
            recommendations.append(AWSRecommendationDetail(
                service="Amazon CloudFront & Amazon S3",
                purpose="CDN and Object Storage hosting for static web assets.",
                reason=(
                    f"### Primary Selection Rationale\n"
                    f"For serverful compute configurations (like App Runner or ECS), decoupling the static frontend files (assets/ images/ JS bundles) "
                    f"and serving them via S3 and CloudFront CDN is the AWS architectural best practice. "
                    f"It reduces load on your compute APIs and delivers static files from global edge locations with lower latencies.\n\n"
                    f"### Alternative Analysis\n"
                    f"- **Direct container serving:** Serving static files from NodeJS/Python containers exhausts compute resources unnecessarily.\n"
                    f"- **S3 Website Hosting without CDN:** Slower global delivery, lacks SSL/HTTPS support on custom domains.\n\n"
                    f"### Operational & Scaling Characteristics\n"
                    f"- **Scaling:** Handled entirely by AWS CloudFront Edge networks (virtually infinite scale).\n"
                    f"- **HA:** Globally distributed CDN edge locations.\n\n"
                    f"### Cost Strategy\n"
                    f"Pay-per-request and data transfer costs, typically costing less than $2.00/month."
                ),
                advantages=["Global CDN low latency content caching", "Free SSL certificate management via ACM", "Reduced CPU utilization on API compute nodes"],
                trade_offs=["Requires cache invalidation pipelines on frontend deployment changes", "Slightly complex custom DNS routing (Route 53 CNAMEs)"],
                alternatives=["S3 Static Web Hosting", "Serving assets from App Runner container"],
                estimated_monthly_cost_impact=3.0,
                confidence_score=88
            ))

        # Check for queues (Amazon SQS)
        if context and context.queues:
            recommendations.append(AWSRecommendationDetail(
                service="Amazon SQS",
                purpose="Fully managed distributed message queuing service.",
                reason=(
                    f"### Primary Selection Rationale\n"
                    f"Amazon SQS is selected to broker messages between API handlers and background job workers. "
                    f"It prevents server blocks and handles rate spikes gracefully.\n\n"
                    f"### Alternative Analysis\n"
                    f"- **Amazon MQ (ActiveMQ/RabbitMQ):** Good for legacy migrations, but requires provisioning instances. SQS is serverless and scales to zero.\n"
                    f"- **Self-hosted Redis Queue:** Risk of message loss during broker server crashes.\n\n"
                    f"### Operational & Scaling Characteristics\n"
                    f"- **Scaling:** Automatic serverless message buffering (scales to millions of messages).\n"
                    f"- **HA:** Redundant message storage across multiple availability zones.\n\n"
                    f"### Cost Strategy\n"
                    f"Pay-per-use, with first 1 million requests per month free."
                ),
                advantages=["Serverless scaling with zero pre-provisioned cost", "Dead-letter queues for failed messages", "Decoupled service API architectures"],
                trade_offs=["Message processing is restricted to basic polling models", "FIFO configurations reduce throughput limits slightly"],
                alternatives=["Amazon MQ (RabbitMQ)", "Redis-backed BullMQ/Celery Broker"],
                estimated_monthly_cost_impact=1.0,
                confidence_score=92
            ))

        # Container Registry (Amazon ECR)
        if metadata.docker_readiness and primary_target != "AWS Amplify":
            recommendations.append(AWSRecommendationDetail(
                service="Amazon ECR",
                purpose="Secure private Docker image registry.",
                reason=(
                    f"### Primary Selection Rationale\n"
                    f"Since the repository contains a `Dockerfile`, Amazon ECR is recommended to store built container images "
                    f"securely. It integrates with App Runner, ECS, and AWS IAM roles for secure pull configurations.\n\n"
                    f"### Alternative Analysis\n"
                    f"- **Docker Hub Private Repositories:** Requires external credentials setup, which increases credential leak risk.\n"
                    f"- **GitHub Container Registry (GHCR):** Good for builds, but ECR keeps container images close to AWS compute network for fast deployment spins.\n\n"
                    f"### Operational & Scaling Characteristics\n"
                    f"- **Scaling:** Managed S3-backed image storage.\n"
                    f"- **HA:** Multi-AZ container image delivery networks.\n\n"
                    f"### Cost Strategy\n"
                    f"ECR bills only on storage volume ($0.10 per GB/month). Most containers cost <$1.00/month."
                ),
                advantages=["IAM authentication credentials role mapping", "Automated image vulnerability scanning", "Fast container spin-up latencies within AWS network"],
                trade_offs=["Requires configuration of lifecycle rules to purge old image tags", "Storage costs can accumulate if builds run frequently"],
                alternatives=["Docker Hub", "GitHub Container Registry (GHCR)"],
                estimated_monthly_cost_impact=1.0,
                confidence_score=95
            ))

        return recommendations

    @staticmethod
    def _generate_rationale(
        metadata: RepoMetadata,
        tech: TechnologyAnalysis,
        context: Optional[RepositoryContext],
        primary: str,
        alternatives: List[str],
        scores: Dict[str, Dict[str, float]],
        weighted_results: Dict[str, float]
    ) -> Tuple[str, str, List[str], List[str], str, str, str]:
        # 1. Why Selected
        why_selected = ""
        if primary == "AWS Amplify":
            why_selected = (
                "AWS Amplify was selected because the codebase matches a static frontend profile. "
                "Amplify provides an out-of-the-box global CDN edge network, automated branch build previews, "
                "SSL certificate handling, and zero standby compute costs, making it the most maintainable option."
            )
        elif primary == "AWS App Runner":
            why_selected = (
                "AWS App Runner is recommended because this is a containerized single-workload application or web API. "
                "It abstracts cluster configurations, VPC security groups, and application load balancer setups "
                "while providing automated HTTPS, auto-scaling, and health check monitoring. This balances compute control with operational ease."
            )
        elif primary == "AWS ECS":
            why_selected = (
                "AWS ECS on Fargate is selected because the repository has multi-container configurations (e.g. Docker Compose) "
                "or requires advanced networking/VPC integrations. ECS Fargate allows serverless container orchestration "
                "with task-level CPU/Memory granular scaling, private networking subnets, and robust routing controls."
            )
        elif primary == "AWS Lambda":
            why_selected = (
                "AWS Lambda is selected because the application has high serverless readiness, event-driven files, "
                "or low/intermittent traffic requirements. It offers automatic scaling to zero when idle, paying only "
                "per-request, which represents significant cost savings and reduces server configuration overhead."
            )

        # 2. Why Alternatives Not Selected
        alt_reasons = []
        for alt in alternatives:
            alt_name = alt if alt != "AWS ECS" else "AWS ECS on Fargate"
            diff = weighted_results[primary] - weighted_results[alt]
            
            if alt == "AWS Amplify":
                alt_reasons.append(
                    f"- **{alt_name} (Score: {weighted_results[alt]}/10):** Reject. Not designed to run persistent Python/NodeJS API backend "
                    f"listeners or execute custom container files."
                )
            elif alt == "AWS App Runner":
                if primary == "AWS ECS":
                    alt_reasons.append(
                        f"- **{alt_name} (Score: {weighted_results[alt]}/10):** Reject. App Runner cannot orchestrate multi-container "
                        f"Docker Compose services or manage private sidecar tasks natively."
                    )
                else:
                    alt_reasons.append(
                        f"- **{alt_name} (Score: {weighted_results[alt]}/10):** Not selected. App Runner has higher standby costs "
                        f"compared to the selected service for this application's resource profile."
                    )
            elif alt == "AWS ECS":
                alt_reasons.append(
                    f"- **{alt_name} (Score: {weighted_results[alt]}/10):** Reject. ECS Fargate introduces significant operational overhead "
                    f"(VPCs, Subnets, Target Groups, Task Definitions) which is unnecessary for this scale."
                )
            elif alt == "AWS Lambda":
                alt_reasons.append(
                    f"- **{alt_name} (Score: {weighted_results[alt]}/10):** Reject. Serverless functions suffer from cold start latency "
                    f"spikes, execution timeouts (max 15 mins), and connection limits which are incompatible with this server lifecycle."
                )
                
        why_alternatives = "\n".join(alt_reasons)

        # 3. Benefits (Advantages)
        benefits = []
        if primary == "AWS Amplify":
            benefits = [
                "Zero standby compute charges (pay only for builds and bandwidth)",
                "Out-of-the-box global CloudFront CDN routing and HTTPS security",
                "Automated CI/CD pipelines connected directly to git branches"
            ]
        elif primary == "AWS App Runner":
            benefits = [
                "No Kubernetes, VPC, or ALB cluster components to configure",
                "Automatic scaling based on requests concurrency thresholds",
                "Native HTTPS routing with managed SSL certificates"
            ]
        elif primary == "AWS ECS":
            benefits = [
                "Native multi-container Docker Compose task orchestration support",
                "Granular task IAM roles and private networking (VPC) isolation",
                "No execution time limits; support for persistent web socket connections"
            ]
        elif primary == "AWS Lambda":
            benefits = [
                "True scale-to-zero when idle, minimizing server running costs",
                "Sub-second horizontal scaling to handle sudden traffic surges",
                "No server configurations, container runtimes, or OS patching to maintain"
            ]

        # 4. Trade-offs
        trade_offs = []
        if primary == "AWS Amplify":
            trade_offs = [
                "Lacks server shell access or persistent disk attachments",
                "API functionality is limited to simple serverless handlers (AWS Lambda)"
            ]
        elif primary == "AWS App Runner":
            trade_offs = [
                "Standby costs apply even when idle (unless configured to scale down to 0 instances, which increases cold starts)",
                "Lacks multi-container task configurations and custom sidecars"
            ]
        elif primary == "AWS ECS":
            trade_offs = [
                "Requires manually configuring VPCs, private subnets, target groups, and Route 53 entries",
                "Higher base costing due to Application Load Balancer (ALB) hosting fees (~$22/mo)"
            ]
        elif primary == "AWS Lambda":
            trade_offs = [
                "Cold starts introduce latency spikes for initial API requests",
                "15-minute max execution limits and stateless temporary directories (/tmp)"
            ]

        # 5. Scaling
        scaling = ""
        if primary == "AWS Amplify":
            scaling = "Managed globally via Amazon CloudFront CDN edge locations. Scales virtually infinitely without server configuration."
        elif primary == "AWS App Runner":
            scaling = "Scales instance count horizontally based on request concurrency thresholds. Scales back down when load declines."
        elif primary == "AWS ECS":
            scaling = "Horizontal scaling of Fargate tasks based on Target Tracking scaling policies (CPU/Memory metrics, or active request counts)."
        elif primary == "AWS Lambda":
            scaling = "Instant horizontal execution scaling (up to 1,000 concurrent functions per region) on a per-request basis."

        # 6. Operational Considerations
        operational = ""
        if primary == "AWS Amplify":
            operational = "Zero maintenance. AWS fully controls the CDN, SSL renewals, and build pipelines."
        elif primary == "AWS App Runner":
            operational = "Low maintenance. Managed infrastructure runtime; you configure scaling limits, custom domain, and port mappings."
        elif primary == "AWS ECS":
            operational = "Medium-High maintenance. Requires configuring and updating Task Definitions, Service scale parameters, and networking routes."
        elif primary == "AWS Lambda":
            operational = "Low maintenance. Monitor execution time limits, package zip sizes, and DB pool limits (using RDS Proxy)."

        # 7. Cost Strategy
        cost_impact = ""
        if primary == "AWS Amplify":
            cost_impact = "Extremely cost-efficient. High free tier coverage ($0.015 per GB served, $0.01 per build minute)."
        elif primary == "AWS App Runner":
            cost_impact = "Moderate base cost. Standard vCPU and Memory configurations cost ~$10/month, and billing continues while containers scale."
        elif primary == "AWS ECS":
            cost_impact = "Higher base cost. Running 2 tasks for high availability, plus ALB base costs, starts at ~$45/month."
        elif primary == "AWS Lambda":
            cost_impact = "Highly cost-efficient for bursty or low-traffic apps. Scale-to-zero results in $0 standby costs."

        return why_selected, why_alternatives, benefits, trade_offs, scaling, operational, cost_impact
