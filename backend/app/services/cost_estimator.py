from typing import List, Tuple
from app.schemas.analyzer import CostBreakdown

class CostEstimator:
    @staticmethod
    def estimate_cost(target: str, databases: List[str], complexity: str = "Medium") -> Tuple[float, CostBreakdown]:
        """
        Estimates monthly AWS cost in USD based on target, databases, and complexity.
        Conforms to the CostBreakdown schema.
        """
        compute = 0.0
        database = 0.0
        storage = 0.0
        data_transfer = 0.0
        
        # Scaling multiplier based on project complexity
        mult = 1.0
        if complexity == "High":
            mult = 2.0
        elif complexity == "Low":
            mult = 0.8

        # 1. Compute costs (includes load balancers and monitoring to map to compute)
        if target == "AWS Amplify":
            compute = 3.0 * mult
        elif target == "AWS App Runner":
            # 1 container instance (0.25 vCPU, 0.5 GB RAM) running 24/7 = ~$7.50
            # Plus managed load balancer share + HTTPS SSL setup = $5.00
            compute = (7.50 + 5.00) * mult
        elif target in ["AWS ECS", "AWS ECS on Fargate"]:
            # 2 tasks for High Availability Multi-AZ = $18.00
            # Application Load Balancer (ALB) base = $22.26
            # AWS CloudWatch basic monitoring metrics = $3.00
            compute = (18.00 + 22.26 + 3.00) * mult
        elif target == "AWS Lambda":
            # 100k executions/month at 256MB RAM = $0.40
            # Amazon API Gateway / HTTP API routing = $1.50
            compute = (0.40 + 1.50) * mult
        else:
            compute = 15.00 * mult

        # 2. Database costs
        if databases:
            for db in databases:
                if db in ["PostgreSQL", "MySQL"]:
                    # Small RDS db.t4g.micro instance = $15.00/mo
                    # 20 GB GP3 storage volume = $2.30/mo
                    database += 17.30
                elif db == "Redis":
                    # ElastiCache cache.t4g.micro node = $11.00/mo
                    database += 11.00
                elif db == "MongoDB":
                    # Amazon DocumentDB basic t3.medium instance = $28.00/mo
                    database += 28.00
                elif db == "SQLite":
                    # SQLite is serverless, runs inside compute local disk
                    database += 0.0
        
        # 3. Storage costs (S3 assets + ECR container repository storage)
        if target == "AWS Amplify":
            storage = 1.50  # Web static asset hosting
        else:
            # ECR Image storage (2 GB) = $0.20
            # S3 file storage (10 GB) = $0.23
            # S3 Request charges = $0.50
            storage = 0.93 * mult

        # 4. Network Data Transfer
        # Inbound is free, outbound data transfer estimated at 50 GB/month = $4.50
        data_transfer = 4.50 * mult

        total = round(compute + database + storage + data_transfer, 2)
        
        breakdown = CostBreakdown(
            compute=round(compute, 2),
            database=round(database, 2),
            storage=round(storage, 2),
            data_transfer=round(data_transfer, 2)
        )
        
        return total, breakdown

    @staticmethod
    def generate_assumptions_text(
        target: str, 
        databases: List[str], 
        complexity: str, 
        total_cost: float,
        breakdown: CostBreakdown
    ) -> str:
        """
        Generates a clear explanation of assumptions and details behind the cost estimation.
        """
        db_text = ", ".join(databases) if databases else "None detected"
        
        assumptions = (
            f"### Estimated AWS Monthly Cost: ${total_cost:.2f}/mo (USD)\n\n"
            f"> [!NOTE]\n"
            f"> This is a simulated operational cost estimate for high-availability cloud routing. "
            f"It represents architectural assumptions and is not an exact AWS pricing quote.\n\n"
            f"#### Cost Breakdown:\n"
            f"- **Compute & Routing:** ${breakdown.compute:.2f}/mo\n"
            f"- **Databases & Cache:** ${breakdown.database:.2f}/mo\n"
            f"- **File Storage & ECR:** ${breakdown.storage:.2f}/mo\n"
            f"- **Data Transfer (Outbound):** ${breakdown.data_transfer:.2f}/mo\n\n"
            f"#### Architectural Cost Assumptions:\n"
            f"1. **Traffic Tier:** Assumes a base load of approximately 50,000 HTTP requests per month with 50 GB network transfer.\n"
            f"2. **Compute Sizing:** \n"
        )

        if target == "AWS Amplify":
            assumptions += (
                "   - Amplify hosting rates: $0.15 per GB served, $0.01 per build minute.\n"
                "   - Includes S3 file storage bandwidth allocations.\n"
            )
        elif target == "AWS App Runner":
            assumptions += (
                "   - 1 active instance configuration (0.25 vCPU, 0.5 GB RAM) billed continuously at $0.007/hour.\n"
                "   - Auto-scaling limits capped at 2 instances to control monthly billing caps.\n"
            )
        elif target in ["AWS ECS", "AWS ECS on Fargate"]:
            assumptions += (
                "   - Multi-AZ Deployment: 2 tasks running concurrently on AWS Fargate (0.25 vCPU, 0.5 GB RAM each) for high availability.\n"
                "   - Ingress Routing: Includes base hourly cost for 1 Application Load Balancer (ALB) (~$22.26/mo) and LCU scaling metrics.\n"
            )
        elif target == "AWS Lambda":
            assumptions += (
                "   - Serverless Execution: 100,000 execution requests per month (256MB RAM size, 300ms execution duration).\n"
                "   - HTTP Gateway: Amazon API Gateway routing integrations ($1.00 per million requests).\n"
            )

        if databases:
            assumptions += "3. **Database Sizing:** \n"
            for db in databases:
                if db in ["PostgreSQL", "MySQL"]:
                    assumptions += "   - Amazon RDS: 1 single-AZ db.t4g.micro instance with 20 GB GP3 SSD storage volume.\n"
                elif db == "Redis":
                    assumptions += "   - Amazon ElastiCache: 1 cache.t4g.micro Redis node running continuously.\n"
                elif db == "MongoDB":
                    assumptions += "   - Amazon DocumentDB: 1 basic t3.medium instance running MongoDB compatible APIs.\n"

        assumptions += (
            f"4. **Expected Scaling Factor:** Adjusted for `{complexity}` project complexity. "
            f"Auto-scaling is configured to increase container tasks or memory limits during traffic surges, which may increase actual monthly costs."
        )

        return assumptions
