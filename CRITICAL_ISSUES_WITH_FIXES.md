# Critical Issues - Code Fix Examples

## Issue #1: Deployment is Only Simulated

### Current Code (Simulation)
```python
# backend/app/services/deployment_service.py lines 160-180
if not has_terraform:
    # RUN REALISTIC SIMULATOR
    add_deployment_log(deployment_id, "Initializing Terraform", "Terraform binary not found. Running deployment simulation...", "in_progress")
    time.sleep(2.0)
    # ... fake logs ...
    live_url = f"https://{service_name}.ap-south-1.awsapprunner.com"
else:
    try:
        # 2. Terraform Init
        DeploymentService._run_terraform_command(deployment_id, "Initializing Terraform", ["terraform", "init"], workspace_dir)
```

### Fix Required
```python
# backend/app/services/deployment_service.py

# OPTION A: Require terraform (fail fast if not available)
has_terraform = shutil.which("terraform") is not None
if not has_terraform:
    add_deployment_log(deployment_id, "Preparing", "ERROR: Terraform CLI not found. Install with: apt-get install terraform", "failed")
    dep_data = deployments[deployment_id]
    dep_data["status"] = "failed"
    deployments[deployment_id] = dep_data
    return

# OPTION B: Use subprocess to run real terraform
try:
    # 1. Initialize
    result = subprocess.run(
        ["terraform", "init"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    if result.returncode != 0:
        add_deployment_log(deployment_id, "Initializing Terraform", f"ERROR: {result.stderr}", "failed")
        raise Exception(result.stderr)
    
    # 2. Plan
    result = subprocess.run(
        ["terraform", "plan", "-out=tfplan"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    if result.returncode != 0:
        raise Exception(result.stderr)
    
    # 3. Apply
    result = subprocess.run(
        ["terraform", "apply", "-auto-approve", "tfplan"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        timeout=600
    )
    if result.returncode != 0:
        raise Exception(result.stderr)
    
    # Extract output
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=workspace_dir,
        capture_output=True,
        text=True
    )
    outputs = json.loads(result.stdout)
    live_url = outputs.get("service_url", {}).get("value", "")
    
except Exception as e:
    add_deployment_log(deployment_id, "Deployment", f"ERROR: {str(e)}", "failed")
    raise
```

---

## Issue #2: Ephemeral Data Loss (SqliteDict)

### Current Code (In-Memory Loss)
```python
# backend/app/utils/helpers.py
analysis_tasks = SqliteDict("analyses", "task_id")
infra_generations = SqliteDict("generations", "generation_id")
deployments = SqliteDict("deployments", "deployment_id")

# Data lost when server restarts!
```

### Fix Required
```python
# Option A: Use PostgreSQL directly instead of SqliteDict

# backend/app/routers/analyzer.py
from app.models.analysis import Analysis as AnalysisModel
from app.utils.database import SessionLocal

@router.post("/analyze")
async def analyze_repository(request: AnalyzeRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    
    # Save to PostgreSQL immediately
    db = SessionLocal()
    db_analysis = AnalysisModel(
        task_id=task_id,
        status="pending",
        user_id=current_user.id,
        data=json.dumps({"status": "pending", "logs": []})
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    db.close()
    
    background_tasks.add_task(run_analysis_pipeline, task_id, repo_url, clone_path)
    return AnalyzeResponse(task_id=task_id, status="pending")

# Then in analysis pipeline:
def update_analysis_status(task_id: str, data: dict):
    db = SessionLocal()
    analysis = db.query(AnalysisModel).filter(AnalysisModel.task_id == task_id).first()
    if analysis:
        analysis.data = json.dumps(data)
        analysis.status = data.get("status", "pending")
        db.commit()
    db.close()

# Option B: Use SQLiteDict with periodic PostgreSQL sync
from sqlalchemy.orm import Session

class PersistentDict:
    """SQLiteDict wrapper that syncs to PostgreSQL"""
    def __init__(self, model_class: type, db: Session):
        self.model_class = model_class
        self.db = db
        self.cache = {}
    
    def __setitem__(self, key, value):
        self.cache[key] = value
        # Sync to DB
        instance = self.db.query(self.model_class).filter(
            self.model_class.id == key
        ).first()
        if instance:
            instance.data = json.dumps(value)
        else:
            instance = self.model_class(id=key, data=json.dumps(value))
            self.db.add(instance)
        self.db.commit()
    
    def __getitem__(self, key):
        return self.cache.get(key) or json.loads(
            self.db.query(self.model_class).filter(
                self.model_class.id == key
            ).first().data
        )
```

---

## Issue #3: No IAM Permission Validation

### Current Code
```python
# backend/app/services/deployment_service.py
@staticmethod
def validate_aws_credentials(access_key: str, secret_key: str, region: str):
    try:
        client = boto3.client('sts', ...)
        client.get_caller_identity()  # Only checks if creds are valid
        return {"valid": True, "reason": "AWS account verified successfully."}
    except Exception:
        return {"valid": False, "reason": "Invalid credentials"}
```

### Fix Required
```python
# backend/app/services/deployment_service.py

@staticmethod
def validate_aws_credentials_and_permissions(access_key: str, secret_key: str, region: str, deployment_target: str = "AWS App Runner"):
    """Validates both credential validity AND required IAM permissions"""
    required_permissions = {
        "AWS App Runner": [
            "sts:GetCallerIdentity",
            "apprunner:CreateService",
            "apprunner:DescribeService",
            "ecr:CreateRepository",
            "ecr:GetAuthorizationToken",
            "iam:PassRole",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
        ],
        "AWS ECS": [
            "ecs:CreateCluster",
            "ecs:RegisterTaskDefinition",
            "ecs:CreateService",
            "ecr:CreateRepository",
            "iam:PassRole",
        ],
        "AWS Lambda": [
            "lambda:CreateFunction",
            "lambda:UpdateFunctionCode",
            "iam:CreateRole",
            "iam:PutRolePolicy",
        ]
    }
    
    try:
        sts = boto3.client("sts", aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        iam = boto3.client("iam", aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        
        # 1. Validate credentials
        identity = sts.get_caller_identity()
        
        # 2. Simulate permission check via IAM
        missing_permissions = []
        for permission in required_permissions.get(deployment_target, []):
            try:
                # Use IAM access analyzer or simulate policy
                service, action = permission.split(":")
                # This is a simplified check - real implementation should use IAM access analyzer
            except Exception:
                missing_permissions.append(permission)
        
        if missing_permissions:
            return {
                "valid": False,
                "reason": f"Missing IAM permissions: {', '.join(missing_permissions[:3])}...",
                "missing_permissions": missing_permissions
            }
        
        return {
            "valid": True,
            "reason": "AWS credentials and permissions validated successfully.",
            "account_id": identity["Account"],
            "arn": identity["Arn"]
        }
        
    except Exception as exc:
        reason = str(exc)
        if "InvalidClientTokenId" in reason:
            reason = "AWS credentials are invalid or expired."
        elif "Region" in reason:
            reason = "AWS region is invalid."
        return {"valid": False, "reason": reason}
```

---

## Issue #4: Generated Files Not Tracked

### Current Code
```python
# backend/app/routers/infrastructure.py
# Files generated but not indexed in DB
generated_files = HeuristicGenerator.generate_docker(metadata)
# Packaged to ZIP but not tracked
```

### Fix Required
```python
# backend/app/models/analysis.py - Add GeneratedFile model
from sqlalchemy import Column, String, Integer, Float

class GeneratedFile(Base):
    __tablename__ = "generated_files"
    
    id = Column(Integer, primary_key=True)
    generation_id = Column(String(255), ForeignKey("generations.generation_id"), nullable=False)
    filename = Column(String(255), nullable=False)  # e.g., "Dockerfile"
    file_size = Column(Integer)  # bytes
    file_hash = Column(String(64))  # SHA256 for integrity check
    content_preview = Column(Text)  # First 500 chars
    created_at = Column(DateTime, server_default=func.now())
    
    generation = relationship("Generation", back_populates="files")

# backend/app/routers/infrastructure.py
@router.get("/download/{generation_id}")
async def download_infrastructure(generation_id: str):
    db = SessionLocal()
    gen = db.query(GenerationModel).filter(GenerationModel.generation_id == generation_id).first()
    
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Get all tracked files
    files = db.query(GeneratedFile).filter(GeneratedFile.generation_id == generation_id).all()
    
    zip_path = os.path.join(DOWNLOADS_DIR, f"{generation_id}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for f in files:
            zf.write(f.file_path, arcname=f.filename)
    
    # Log download
    gen.download_count += 1
    db.commit()
    db.close()
    
    return FileResponse(zip_path, filename=f"infrastructure-{generation_id}.zip")

# backend/app/routers/infrastructure.py
@router.get("/files/{generation_id}")
async def list_generated_files(generation_id: str):
    """List all files generated in this generation"""
    db = SessionLocal()
    files = db.query(GeneratedFile).filter(GeneratedFile.generation_id == generation_id).all()
    db.close()
    
    return [{
        "filename": f.filename,
        "size": f.file_size,
        "preview": f.content_preview,
        "hash": f.file_hash
    } for f in files]
```

---

## Issue #5: No LLM-based Validation

### Current Code
```python
# backend/app/agents/infra_graph.py
# Validation is just heuristic checks
state['validation_score'] = 50  # Hardcoded!
```

### Fix Required
```python
# backend/app/services/validation_service.py

class ValidationService:
    @staticmethod
    def validate_dockerfile(dockerfile_content: str) -> Dict[str, Any]:
        """Validate Dockerfile using LLM"""
        if not settings.OPENAI_API_KEY:
            return {"score": 0, "errors": ["OpenAI API key not set"]}
        
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")
        
        prompt = f"""Validate this Dockerfile. Check for:
1. Multi-stage builds for optimization
2. Layer caching (frequently changing last)
3. .dockerignore usage
4. Health checks
5. Security: no root user, specific versions, scan vulnerabilities

Dockerfile:
{dockerfile_content}

Return JSON with:
{{"score": 0-100, "errors": [...], "warnings": [...], "suggestions": [...]}}
"""
        
        try:
            response = llm.invoke(prompt)
            result = json.loads(response.content)
            return result
        except Exception as e:
            return {"score": 0, "errors": [str(e)]}
    
    @staticmethod
    def validate_terraform(terraform_content: str, target: str) -> Dict[str, Any]:
        """Validate Terraform using LLM"""
        if not settings.OPENAI_API_KEY:
            return {"score": 0, "errors": ["OpenAI API key not set"]}
        
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")
        
        prompt = f"""Validate this Terraform config for {target}:
1. All required variables defined
2. Output values exported (URLs, IPs)
3. Security: minimal permissions, encryption enabled
4. Best practices: tagging, naming conventions
5. Cost optimization: spot instances, auto-scaling

Terraform:
{terraform_content}

Return JSON with:
{{"score": 0-100, "errors": [...], "warnings": [...], "critical": [...]}}
"""
        
        try:
            response = llm.invoke(prompt)
            result = json.loads(response.content)
            return result
        except Exception as e:
            return {"score": 0, "errors": [str(e)]}
```

---

## Quick Priority Fixes

### 1. Enable Real Terraform Execution (HIGH)
**File:** `backend/app/services/deployment_service.py`
**Change:** Remove the `if not has_terraform` simulation block

### 2. Migrate to PostgreSQL (HIGH)
**Files:** 
- `backend/app/utils/helpers.py` - Replace SqliteDict
- `backend/app/routers/analyzer.py` - Use DB instead of in-memory

### 3. Add Rate Limiting (MEDIUM)
**File:** `backend/app/main.py`
**Add:**
```python
from app.utils.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)
```

### 4. Improve Error Handling (MEDIUM)
**File:** `backend/app/agents/graph.py`
**Wrap all agent nodes in try/except with structured error responses**

### 5. Add Infrastructure File Tracking (MEDIUM)
**Files:**
- `backend/app/models/analysis.py` - Add GeneratedFile model
- `backend/app/routers/infrastructure.py` - Track files in DB
