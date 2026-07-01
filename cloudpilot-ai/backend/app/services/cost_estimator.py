from typing import List, Tuple
from app.schemas.analyzer import CostBreakdown

class CostEstimator:
    @staticmethod
    def estimate_cost(target: str, databases: List[str]) -> Tuple[float, CostBreakdown]:
        """
        Estimates monthly AWS cost in USD based on target and databases.
        """
        compute = 0.0
        database = 0.0
        storage = 0.0
        data_transfer = 0.0
        
        # Determine base compute cost
        if target == "AWS Amplify":
            compute = 3.0  # Hosting + build minutes
            storage = 1.0  # S3 assets
            data_transfer = 1.0
        elif target == "AWS App Runner":
            compute = 5.0  # Minimal resource / paused compute
            storage = 1.0  # S3 assets
            data_transfer = 0.4
        elif target == "AWS ECS":
            compute = 25.0  # Base ECS Fargate task + Load Balancer share
            storage = 2.0
            data_transfer = 3.0
        elif target == "AWS Lambda":
            compute = 1.0  # Serverless execution pricing (base tier)
            storage = 0.5
            data_transfer = 0.5
            
        # Determine database costs if applicable
        if databases:
            for db in databases:
                if db in ["PostgreSQL", "MySQL"]:
                    # Small db.t4g.micro RDS instance
                    database += 15.0
                elif db == "Redis":
                    # ElastiCache cache.t4g.micro
                    database += 10.0
                elif db == "MongoDB":
                    # DocumentDB / Atlas (assume basic tier)
                    database += 8.0
                    
        total = round(compute + database + storage + data_transfer, 2)
        
        breakdown = CostBreakdown(
            compute=round(compute, 2),
            database=round(database, 2),
            storage=round(storage, 2),
            data_transfer=round(data_transfer, 2)
        )
        
        return total, breakdown
