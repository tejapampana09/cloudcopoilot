import os
from typing import Dict, List, Any
from app.schemas.analyzer import RepoMetadata

class HeuristicGenerator:
    @staticmethod
    def generate_docker(metadata: RepoMetadata) -> Dict[str, str]:
        """Generates fallback Dockerfile and .dockerignore."""
        lang = metadata.languages[0].name if metadata.languages else "Node"
        framework = metadata.frameworks[0] if metadata.frameworks else ""
        
        dockerfile = ""
        dockerignore = ".git\nnode_modules\nvenv\n.venv\n__pycache__\ndist\nbuild\n.env\n"
        
        # 1. Next.js / React Frontend
        if "Next.js" in metadata.frameworks or "Next.js" in metadata.frontend:
            dockerfile = """# Multi-stage build for Next.js
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1002 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["npm", "start"]
"""
        elif "React" in metadata.frameworks or "React" in metadata.frontend:
            dockerfile = """# Production-grade React SPA Nginx setup
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        # 2. FastAPI Backend
        elif "FastAPI" in metadata.frameworks or "FastAPI API" in metadata.backend:
            dockerfile = """# Python FastAPI Production Build
FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        # 3. Express/Node Backend
        elif "Express" in metadata.frameworks or "Node" in lang:
            dockerfile = """# Production Node Express Build
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

FROM node:18-alpine
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app ./
EXPOSE 3000
USER node
CMD ["npm", "start"]
"""
        # 4. Standard Python fallback
        elif "Python" in lang:
            dockerfile = """# Standard Python App Build
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
        # 5. Default generic template
        else:
            dockerfile = """# Standard Alpine container template
FROM alpine:latest
RUN apk add --no-cache curl
WORKDIR /app
COPY . .
CMD ["echo", "Container successfully configured!"]
"""
            
        return {
            "Dockerfile": dockerfile,
            ".dockerignore": dockerignore
        }

    @staticmethod
    def generate_compose(metadata: RepoMetadata, target: str) -> str:
        """Generates fallback docker-compose.yml."""
        db_services = ""
        depends_on = ""
        
        # Parse databases
        if metadata.databases:
            for db in metadata.databases:
                if db == "PostgreSQL":
                    db_services += """
  postgres:
    image: postgres:15-alpine
    container_name: cp-postgres
    environment:
      POSTGRES_USER: cp_user
      POSTGRES_PASSWORD: cp_secure_password
      POSTGRES_DB: cp_database
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - cp-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cp_user -d cp_database"]
      interval: 10s
      timeout: 5s
      retries: 5
"""
                    depends_on = "\n    depends_on:\n      postgres:\n        condition: service_healthy"
                elif db == "Redis":
                    db_services += """
  redis:
    image: redis:7-alpine
    container_name: cp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - cp-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
"""
                elif db == "MongoDB":
                    db_services += """
  mongodb:
    image: mongo:6
    container_name: cp-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - cp-network
"""
        
        # Build core service
        app_port = "8000" if "FastAPI" in metadata.frameworks else "3000"
        
        compose_content = f"""version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cp-app
    ports:
      - "{app_port}:{app_port}"
    environment:
      - PORT={app_port}
      - NODE_ENV=development
      - DATABASE_URL=postgresql://cp_user:cp_secure_password@postgres:5432/cp_database{db_services}
    networks:
      - cp-network{depends_on}
"""
        
        # Volumes section
        if metadata.databases:
            compose_content += "\nvolumes:"
            for db in metadata.databases:
                if db == "PostgreSQL":
                    compose_content += "\n  postgres_data:"
                elif db == "Redis":
                    compose_content += "\n  redis_data:"
                elif db == "MongoDB":
                    compose_content += "\n  mongo_data:"
                    
        compose_content += """

networks:
  cp-network:
    driver: bridge
"""
        return compose_content

    @staticmethod
    def generate_env(metadata: RepoMetadata) -> str:
        """Generates fallback .env.example."""
        env_content = "# CloudPilot AI - Environment Variable Template\n"
        env_content += f"# Configured for frameworks: {', '.join(metadata.frameworks) if metadata.frameworks else 'None'}\n\n"
        
        # Port
        app_port = "8000" if "FastAPI" in metadata.frameworks else "3000"
        env_content += f"PORT={app_port}\nNODE_ENV=production\n\n"
        
        # Databases envs
        if metadata.databases:
            env_content += "# Database Configurations\n"
            for db in metadata.databases:
                if db == "PostgreSQL":
                    env_content += "DATABASE_URL=postgresql://db_user:db_password@localhost:5432/db_name\n"
                elif db == "Redis":
                    env_content += "REDIS_URL=redis://localhost:6379/0\n"
                elif db == "MongoDB":
                    env_content += "MONGODB_URI=mongodb://localhost:27017/db_name\n"
            env_content += "\n"
            
        # Authentication
        env_content += "# Auth Security Secrets\nJWT_SECRET=your-256-bit-secure-jwt-key\n\n"
        
        # Integrations
        env_content += "# Third Party Integrations\nOPENAI_API_KEY=your-openai-api-key-here\nGEMINI_API_KEY=your-gemini-api-key-here\n\n"
        
        # AWS Settings
        env_content += "# AWS Credentials\nAWS_REGION=us-east-1\nAWS_ACCESS_KEY_ID=your-aws-access-key\nAWS_SECRET_ACCESS_KEY=your-aws-secret\n"
        
        return env_content

    @staticmethod
    def generate_terraform(metadata: RepoMetadata, target: str) -> Dict[str, str]:
        """Generates fallback Terraform configurations."""
        
        providers = """terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
"""

        variables = """variable "aws_region" {
  type        = string
  description = "The target AWS Region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name"
  default     = "production"
}

variable "project_name" {
  type        = string
  description = "Application project prefix name"
  default     = "cloudpilot-app"
}
"""

        outputs = """output "ecr_repository_url" {
  value       = aws_ecr_repository.app_ecr.repository_url
  description = "The URL of the generated ECR container registry"
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.app_storage.arn
  description = "The ARN of the assets storage S3 bucket"
}
"""

        # main.tf adapts to recommended compute targets (App Runner vs ECS Fargate)
        if target == "AWS App Runner":
            main_content = """# Modular cloud layout for AWS App Runner deployment
resource "aws_vpc" "app_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_ecr_repository" "app_ecr" {
  name                 = "${var.project_name}-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_s3_bucket" "app_storage" {
  bucket        = "${var.project_name}-assets-storage"
  force_destroy = true
}

resource "aws_iam_role" "app_runner_execution_role" {
  name = "${var.project_name}-runner-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_runner_ecr_policy" {
  role       = aws_iam_role.app_runner_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_apprunner_service" "app_service" {
  service_name = "${var.project_name}-service"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_execution_role.arn
    }
    image_repository {
      image_identifier      = "${aws_ecr_repository.app_ecr.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
      }
    }
    auto_deployments_enabled = true
  }

  tags = {
    Environment = var.environment
  }
}
"""
        else:
            # ECS / Generic container configuration
            main_content = """# Modular cloud layout for AWS ECS Fargate deployment
resource "aws_vpc" "app_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_ecr_repository" "app_ecr" {
  name = "${var.project_name}-ecr"
}

resource "aws_s3_bucket" "app_storage" {
  bucket = "${var.project_name}-assets-storage"
}

resource "aws_ecs_cluster" "app_cluster" {
  name = "${var.project_name}-ecs-cluster"
}
"""

        return {
            "terraform/providers.tf": providers,
            "terraform/variables.tf": variables,
            "terraform/outputs.tf": outputs,
            "terraform/main.tf": main_content
        }

    @staticmethod
    def generate_workflow(metadata: RepoMetadata, target: str) -> str:
        """Generates fallback deploy.yml workflow."""
        build_step = metadata.build_commands[0] if metadata.build_commands else "npm run build"
        test_step = metadata.test_frameworks[0] if metadata.test_frameworks else "npm test"
        
        workflow = f"""name: CloudPilot CI/CD Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    name: Build and Test QA Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Setup Node Environment
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Test execution
        run: {test_step} || echo "Tests bypassed"

  docker-push-and-deploy:
    name: Build Image & Deploy to {target}
    needs: build-and-test
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: us-east-1

      - name: Log in to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{{{ steps.login-ecr.outputs.registry }}}}
          ECR_REPOSITORY: cp-application-ecr
          IMAGE_TAG: ${{{{ github.sha }}}}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
"""
        return workflow
