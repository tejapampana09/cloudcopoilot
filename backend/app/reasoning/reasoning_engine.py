from typing import List
from app.schemas.architecture import AWSRecommendationDetail
from app.schemas.analyzer import RepoMetadata


class ReasoningEngine:
    @staticmethod
    def generate_reasons(metadata: RepoMetadata, target: str) -> List[str]:
        reasons = []
        if target == 'AWS Amplify':
            reasons.append('Best fit for static frontend hosting with automated build and CDN distribution.')
            reasons.append('Suits SPAs or static sites with minimal backend requirements.')
        elif target == 'AWS App Runner':
            reasons.append('Fits containerized web applications while minimizing operational overhead.')
            reasons.append('Supports managed scaling and deployment from source or containers.')
        elif target == 'AWS ECS':
            reasons.append('Ideal for multi-service container applications with greater networking control.')
            reasons.append('Provides Fargate-managed compute without managing servers.')
        elif target == 'AWS Lambda':
            reasons.append('Works well for event-driven microservices and low-traffic API usage.')
            reasons.append('Reduces cost by scaling to zero when idle.')

        if metadata.databases:
            reasons.append('Detected database dependencies indicate stateful components that should be isolated from frontend.')

        return reasons
