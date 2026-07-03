# AWS Production Deployment Guide for CloudPilot AI

This guide contains the architecture design, configuration settings, parameters, and deployment scripts to deploy CloudPilot AI to AWS in a secure, scalable, and highly available configuration.

## 1. Compute & Network Architecture

We recommend deploying CloudPilot AI on **AWS ECS (Fargate)** or **AWS App Runner** with a PostgreSQL database on **AWS RDS (Aurora Serverless v2)**.

### Target Resources:
1. **AWS ECS Fargate Service**: For running the FastAPI backend.
2. **AWS App Runner / Amplify**: For serving the React static frontend.
3. **Amazon RDS Aurora PostgreSQL**: High performance database cluster.
4. **AWS ElastiCache Redis**: For rate limiting and session storage.
5. **AWS Secrets Manager**: For managing JWT Secrets and OpenAI API keys.

---

## 2. Infrastructure Parameters

| Parameter Key | Suggested Value | Description |
|---|---|---|
| `VpcCIDR` | `10.0.0.0/16` | VPC Network Address Block |
| `EcsTaskCpu` | `1024` (1 vCPU) | CPU resources allocated to FastAPI container |
| `EcsTaskMemory` | `2048` (2 GB) | Memory resources allocated to FastAPI container |
| `MinCapacity` | `2` | Minimum auto-scaling task count |
| `MaxCapacity` | `10` | Maximum auto-scaling task count |
| `RdsInstanceClass` | `db.serverless` | Aurora Serverless DB instance class |

---

## 3. Deployment via AWS Copilot CLI

The simplest and most robust way to deploy multi-container projects to AWS ECS is via the **AWS Copilot CLI**.

### Step 1: Initialize the Application
```bash
copilot app init cloudpilot
```

### Step 2: Deploy the Backend Service (FastAPI)
```bash
copilot svc init --name backend --svc-type "Load Balanced Web Service" --dockerfile ./backend/Dockerfile
```

### Step 3: Configure Environment Settings
Add these to `./copilot/backend/manifest.yml`:
```yaml
image:
  build: ./backend/Dockerfile
  port: 8000

cpu: 1024
memory: 2048

count:
  range: 2-10
  cpu_percentage: 70

variables:
  OPENAI_MODEL: "gpt-4o-mini"
  BACKEND_CORS_ORIGINS: '["*"]'

secrets:
  DATABASE_URL: /copilot/cloudpilot/secrets/DATABASE_URL
  OPENAI_API_KEY: /copilot/cloudpilot/secrets/OPENAI_API_KEY
  JWT_SECRET: /copilot/cloudpilot/secrets/JWT_SECRET
  JWT_REFRESH_SECRET: /copilot/cloudpilot/secrets/JWT_REFRESH_SECRET
```

### Step 4: Deploy the App to ECS Fargate
```bash
copilot deploy --env prod
```
