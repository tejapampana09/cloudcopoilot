# Critical Production Issues & Code Fixes

This document outlines five critical production blockers identified in the CloudPilot AI codebase, along with proposed options and working code samples to resolve them.

---

## Issue #1: Deployment is Simulated (Fake/Demo Fallback)

### Problem
When `terraform` is not found on the system path, the backend falls back to a simulated deployment worker (`DeploymentService._execute_deployment_worker` simulation path) that logs fake progress steps and returns a mock live URL. This is acceptable for a hackathon demo but is a major blocker for production.

### Proposed Fixes

#### Option A: Fail Fast (Production Enforcement)
Enforce that Terraform is present and raise an error immediately if it is missing, preventing simulated deployments.

```python
# app/services/deployment_service.py

import shutil
from fastapi import HTTPException, status

class DeploymentService:
    @staticmethod
    def verify_terraform_installed():
        if shutil.which("terraform") is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Terraform binary is not installed or not found on the system PATH."
            )
```

#### Option B: Real Terraform Execution Engine
Ensure the backend runs real Terraform apply and handles real errors:

```python
# app/services/deployment_service.py

import subprocess
import os
from app.utils.helpers import add_deployment_log

class DeploymentService:
    @staticmethod
    def _run_terraform_apply(deployment_id: str, workspace_dir: str):
        command = ["terraform", "apply", "-auto-approve"]
        add_deployment_log(deployment_id, "Creating Infrastructure", "Applying Terraform changes...", "in_progress")
        
        try:
            proc = subprocess.Popen(
                command,
                cwd=workspace_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
            
            for line in proc.stdout:
                clean_line = line.strip()
                if clean_line:
                    add_deployment_log(deployment_id, "Creating Infrastructure", clean_line, "in_progress")
                    
            proc.wait()
            if proc.returncode != 0:
                raise Exception(f"Terraform apply failed with exit code {proc.returncode}")
                
            add_deployment_log(deployment_id, "Creating Infrastructure", "Terraform resources created successfully.", "completed")
        except Exception as e:
            add_deployment_log(deployment_id, "Creating Infrastructure", f"Failed: {str(e)}", "failed")
            raise e
```

---

## Issue #2: Data Loss on Restart (SqliteDict / PostgresDict Ephemeral Persistence)

### Problem
The application uses a custom `SqliteDict` (which wraps `PostgresDict` or SQLite depending on the environment string) to manage task states. When the backend container restarts, if it falls back to SQLite, the local database file `cloudpilot.db` is destroyed since container storage is ephemeral. Under high load, opening/closing connections per dictionary operation creates significant latency.

### Proposed Fixes

#### Option A: PostgreSQL Direct ORM Integration
Move away from raw stringified JSON storage in the dict wrapper and use robust SQLAlchemy schemas with connection pooling.

```python
# app/services/task_persistence.py

from sqlalchemy.orm import Session
from app.models.analysis import Analysis
import json

class TaskPersistenceService:
    @staticmethod
    def update_task_data(db: Session, task_id: str, status: str, updated_fields: dict):
        task = db.query(Analysis).filter(Analysis.task_id == task_id).first()
        if not task:
            return None
            
        # Parse current data
        data = json.loads(task.data) if task.data else {}
        data.update(updated_fields)
        
        # Save back
        task.data = json.dumps(data)
        task.status = status
        db.commit()
        db.refresh(task)
        return task
```

#### Option B: Redis Synchronization Pattern
Use Redis as a fast, transient status cache and pub/sub layer for SSE streaming, syncing to PostgreSQL only on milestone completions.

```python
# app/utils/redis_cache.py

import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_deployment_status(deployment_id: str, status_data: dict, ttl: int = 86400):
    redis_key = f"deployment:{deployment_id}"
    redis_client.setex(redis_key, ttl, json.dumps(status_data))
    # Publish update to SSE stream channel
    redis_client.publish(f"stream:{deployment_id}", json.dumps(status_data))
```

---

## Issue #3: No IAM Permission Validation

### Problem
The backend accepts IAM keys and connects to AWS, but does not verify if the credentials possess the minimal permissions required to create App Runner services, IAM roles, or subnets, leading to late failures during the Terraform apply stage.

### Proposed Fixes

#### IAM Validation Service
Use `boto3` to evaluate permission policies or perform a dry-run check of the required AWS Actions.

```python
# app/services/iam_validator.py

import boto3
from typing import List, Dict

class IAMValidator:
    REQUIRED_ACTIONS = [
        "apprunner:CreateService",
        "apprunner:DescribeService",
        "apprunner:DeleteService",
        "iam:CreateRole",
        "iam:AttachRolePolicy"
    ]

    @staticmethod
    def validate_permissions(access_key: str, secret_key: str, region: str) -> Dict[str, any]:
        try:
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            client = session.client("clientauthorization" or "iam")
            
            # Retrieve IAM username/ARN
            sts = session.client("sts")
            caller = sts.get_caller_identity()
            arn = caller["Arn"]
            
            # Simulate policy actions
            sim = session.client("iam")
            response = sim.simulate_principal_policy(
                PolicySourceArn=arn,
                ActionNames=IAMValidator.REQUIRED_ACTIONS
            )
            
            evaluation_results = response.get("EvaluationResults", [])
            failed_permissions = [
                res["EvalActionName"] for res in evaluation_results 
                if res["EvalDecision"] != "allowed"
            ]
            
            if failed_permissions:
                return {"valid": False, "missing": failed_permissions}
            return {"valid": True, "missing": []}
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
```

---

## Issue #4: Generated Files Not Tracked in DB

### Problem
FastAPI generates infrastructure files and writes them directly to `temp_clones/`. These files are deleted after 1 hour or when the server cleans up, and they are never stored in the database. If a user returns later, they cannot download their files unless they re-run the entire pipeline.

### Proposed Fixes

#### Database Migration & API Endpoints
Create a `GeneratedFile` database model and persist file contents to PostgreSQL.

```python
# app/models/generated_file.py

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.sql import func
from app.utils.database import Base

class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(String(255), ForeignKey("generations.generation_id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False) # e.g. "main.tf" or "Dockerfile"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

And expose the retrieval API endpoint:

```python
# app/routers/infrastructure.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import SessionLocal
from app.models.generated_file import GeneratedFile

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/files/{generation_id}")
def get_generated_files(generation_id: str, db: Session = Depends(get_db)):
    files = db.query(GeneratedFile).filter(GeneratedFile.generation_id == generation_id).all()
    if not files:
        raise HTTPException(status_code=404, detail="No files found for this generation ID.")
    return {f.file_path: f.content for f in files}
```

---

## Issue #5: No LLM-Based Code Validation

### Problem
AI agents can output malformed Dockerfiles (e.g. missing entrypoints) or incorrect Terraform resources (e.g. circular dependency structures) which are sent straight to the user without verification.

### Proposed Fixes

#### LLM Validation Service
Implement structured validators to check generated outputs prior to saving them.

```python
# app/services/validation_service.py

import json
from langchain_openai import ChatOpenAI
from app.core.config import settings

class ValidationService:
    @staticmethod
    def validate_terraform(tf_code: str) -> dict:
        """Uses LLM to dry-run validate Terraform structure & security guidelines."""
        llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini", temperature=0)
        
        prompt = f"""
        Analyze the following Terraform configuration code for errors, missing values, or security risks.
        Respond STRICTLY in JSON format with two keys:
        - "valid": boolean
        - "errors": list of strings (reasons if invalid)

        Terraform Code:
        {tf_code}
        """
        
        try:
            response = llm.invoke(prompt)
            result = json.loads(response.content.strip())
            return result
        except Exception as e:
            return {"valid": False, "errors": [f"LLM validator unreachable: {str(e)}"]}
            
    @staticmethod
    def validate_dockerfile(dockerfile_content: str) -> dict:
        """Uses LLM to check Dockerfile syntax and best practices."""
        llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini", temperature=0)
        
        prompt = f"""
        Analyze this Dockerfile for missing instructions (e.g., missing FROM, CMD, or EXPOSE).
        Respond STRICTLY in JSON:
        - "valid": boolean
        - "errors": list of strings

        Dockerfile:
        {dockerfile_content}
        """
        
        try:
            response = llm.invoke(prompt)
            return json.loads(response.content.strip())
        except Exception:
            return {"valid": False, "errors": ["Failed to validate Dockerfile."]}
```
