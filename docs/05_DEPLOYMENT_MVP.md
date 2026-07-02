# CloudPilot Deploy MVP Architecture

This document describes the design, database models, and API interfaces for the CloudPilot Deploy MVP.

## 1. Scope & Capabilities
The Deploy MVP allows users to deploy analyzed repositories directly to AWS App Runner using safe, auditable IAM credentials.

- **Target Compute Service**: AWS App Runner
- **IaC Tool**: Terraform (`main.tf`, `terraform.tfvars.json`)
- **Execution Mode**: Background thread calling Terraform CLI sub-processes, with fallback simulations when CLI or AWS access permissions are absent.
- **Log Streaming**: Server-Sent Events (SSE) `/api/v1/deploy/stream/{deployment_id}`

## 2. API Endpoints Reference

### AWS Account Connection
- **POST** `/api/v1/deploy/connect`
  - Validates AWS IAM access keys using `sts.get_caller_identity`.
  - Body: `{ access_key, secret_key, region }`

### Trigger Deployment
- **POST** `/api/v1/deploy/trigger`
  - Spawns a background thread to generate configuration and execute deployment.
  - Body: `{ repository_url, repository_name, access_key, secret_key, region, service_name }`
  - Returns: `{ deployment_id, status }`

### SSE Event Stream
- **GET** `/api/v1/deploy/stream/{deployment_id}`
  - Delivers real-time status and logs of deployment stages:
    1. Preparing
    2. Initializing Terraform
    3. Planning
    4. Creating Infrastructure
    5. Deploying Application
    6. Verifying Health
    7. Completed

### Destroy Infrastructure
- **POST** `/api/v1/deploy/destroy/{deployment_id}`
  - Triggers decommission of the App Runner infrastructure.

### History Fetch
- **GET** `/api/v1/deploy/history`
  - Returns all past deployments for the user persisted inside the SQLite database.

## 3. Database Persistence
Deployments are persisted in the `deployments` table, linked to the `users` table via `user_id`.

```sql
CREATE TABLE deployments (
    deployment_id VARCHAR(255) PRIMARY KEY,
    data TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    user_id INTEGER FOREIGN KEY REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
