import json
import datetime
import logging
from typing import List, Optional
from app.schemas.architecture import (
    ArchitectureSummary, AWSRecommendationDetail, VisualizationJSON, 
    VisualizationNode, VisualizationConnection, ArchitectureReport, RepositoryContext
)
from app.schemas.analyzer import RepoMetadata

logger = logging.getLogger(__name__)


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

    @staticmethod
    def export_json(task_data: dict) -> str:
        """Serializes task data to JSON format."""
        def custom_serializer(o):
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        return json.dumps(task_data, default=custom_serializer, indent=2)

    @staticmethod
    def export_markdown(task_data: dict) -> str:
        """Generates a comprehensive markdown report for the task data."""
        meta = task_data.get("metadata") or {}
        rec = task_data.get("recommendation") or {}
        health = task_data.get("health_score") or 80
        
        md = []
        md.append(f"# CloudPilot AI Solution Architect Report")
        md.append(f"**Repository**: {task_data.get('repository_url')}")
        md.append(f"**Generated At**: {task_data.get('analysis_time') or 'N/A'}")
        md.append(f"**Overall Repository Health Score**: {health}/100\n")
        
        md.append(f"## Executive Summary")
        summary_info = task_data.get("executive_summary") or {}
        md.append(summary_info.get("summary", "No summary generated."))
        md.append("")
        
        md.append(f"## AWS Cloud Architecture Recommendation")
        md.append(f"**Recommended Target Compute**: {rec.get('target', 'N/A')}")
        md.append(f"**Estimated Monthly Cost**: ${rec.get('estimated_monthly_cost', 0.0):.2f}/mo")
        md.append(f"**Justification**: {rec.get('why', 'N/A')}\n")
        
        md.append(f"## Code Quality Audit (Bugs)")
        bugs = task_data.get("bugs") or []
        if bugs:
            for b in bugs:
                md.append(f"### {b.get('problem')}")
                md.append(f"- **Severity**: {b.get('severity', 'Medium')}")
                md.append(f"- **Affected Files**: {', '.join(b.get('affected_files', []))}")
                md.append(f"- **Lines**: {b.get('affected_lines', 'N/A')}")
                md.append(f"- **Why it matters**: {b.get('why_it_matters', 'N/A')}")
                md.append(f"- **Recommendation**: {b.get('fix_recommendation', 'N/A')}")
                md.append(f"- **AI Patch**:\n```\n{b.get('patch', '')}\n```\n")
        else:
            md.append("No critical code bugs identified.\n")
            
        md.append(f"## Security Review")
        sec = task_data.get("security_issues") or []
        if sec:
            for s in sec:
                md.append(f"### {s.get('issue_type')}")
                md.append(f"- **Severity**: {s.get('severity', 'Medium')}")
                md.append(f"- **Affected Files**: {', '.join(s.get('affected_files', []))}")
                md.append(f"- **Why it matters**: {s.get('why_it_matters', 'N/A')}")
                md.append(f"- **Fix**: {s.get('suggested_fix', 'N/A')}")
                md.append(f"- **AI Patch**:\n```\n{s.get('patch', '')}\n```\n")
        else:
            md.append("No security vulnerabilities identified.\n")
            
        md.append(f"## Performance & Scalability Reviews")
        perf = task_data.get("performance_issues") or []
        if perf:
            for p in perf:
                md.append(f"### {p.get('issue_type')}")
                md.append(f"- **Severity**: {p.get('severity', 'Medium')}")
                md.append(f"- **Affected Files**: {', '.join(p.get('affected_files', []))}")
                md.append(f"- **Why it matters**: {p.get('why_it_matters', 'N/A')}")
                md.append(f"- **Fix**: {p.get('suggested_fix', 'N/A')}")
                md.append(f"- **AI Patch**:\n```\n{p.get('patch', '')}\n```\n")
        else:
            md.append("No performance bottlenecks identified.\n")
            
        return "\n".join(md)

    @staticmethod
    def export_pdf(task_data: dict) -> bytes:
        """Compiles Solutions Architect report into PDF format using ReportLab."""
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            
            story = []
            
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#0f172a'),
                spaceAfter=15
            )
            subtitle_style = ParagraphStyle(
                'SubTitleStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=13,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=15
            )
            h2_style = ParagraphStyle(
                'H2Style',
                parent=styles['Heading2'],
                fontSize=14,
                leading=17,
                textColor=colors.HexColor('#1e40af'),
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontSize=9,
                leading=13,
                textColor=colors.HexColor('#334155')
            )
            
            # Header
            story.append(Paragraph("CloudPilot AI Solutions Architect Report", title_style))
            story.append(Paragraph(f"Repository: {task_data.get('repository_url')}", subtitle_style))
            story.append(Paragraph(f"Health Score: {task_data.get('health_score') or 80}/100", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", h2_style))
            summary_text = task_data.get("executive_summary", {}).get("summary", "No summary generated.")
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 10))
            
            # AWS Recommendation
            story.append(Paragraph("AWS Architecture Recommendations", h2_style))
            rec = task_data.get("recommendation") or {}
            rec_text = f"<b>Compute Target:</b> {rec.get('target', 'N/A')}<br/><b>Monthly Cost Estimate:</b> ${rec.get('estimated_monthly_cost', 0.0):.2f}<br/><b>Justification:</b> {rec.get('why', 'N/A')}"
            story.append(Paragraph(rec_text, body_style))
            story.append(Spacer(1, 10))
            
            # Bugs
            story.append(Paragraph("Identified Code Bugs", h2_style))
            bugs = task_data.get("bugs") or []
            if bugs:
                for idx, b in enumerate(bugs):
                    bug_text = f"<b>{idx+1}. {b.get('problem')}</b> (Severity: {b.get('severity', 'High')})<br/>Files: {', '.join(b.get('affected_files', []))}<br/>Recommendation: {b.get('fix_recommendation', 'N/A')}"
                    story.append(Paragraph(bug_text, body_style))
                    story.append(Spacer(1, 4))
            else:
                story.append(Paragraph("No critical bugs identified.", body_style))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to compile report PDF using reportlab: {e}")
            pdf_fallback = (
                b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 595.27 841.89]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 150\n>>\nstream\nBT\n/F1 12 Tf\n70 800 Td\n(CloudPilot AI - Solutions Architect Report) Tj\n0 -20 Td\n(Failed to load ReportLab rendering pipeline. Download raw Markdown report instead.) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000288 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n490\n%%EOF\n"
            )
            return pdf_fallback
