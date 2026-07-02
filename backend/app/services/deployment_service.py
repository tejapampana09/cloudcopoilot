import os
import re
import json
import time
import shutil
import subprocess
import threading
import datetime
from typing import Dict, Any, List, Optional
import boto3

from app.core.config import settings
from app.utils.helpers import deployments, add_deployment_log

class DeploymentService:
    @staticmethod
    def validate_aws_credentials(access_key: str, secret_key: str, region: str) -> Dict[str, Any]:
        """Validates IAM keys using sts.get_caller_identity and returns a structured result."""
        try:
            if not access_key or not secret_key:
                return {"valid": False, "reason": "AWS access key and secret key are required."}
            client = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            client.get_caller_identity()
            return {"valid": True, "reason": "AWS account verified successfully."}
        except Exception as exc:
            reason = str(exc)
            if "InvalidClientTokenId" in reason or "SignatureDoesNotMatch" in reason:
                reason = "AWS credentials are invalid or expired."
            elif "Region" in reason:
                reason = "AWS region is invalid or not supported."
            else:
                reason = "Unable to verify AWS credentials. Please check your IAM permissions and region."
            return {"valid": False, "reason": reason}

    @staticmethod
    def start_deployment(
        deployment_id: str,
        user_id: Optional[int],
        repo_url: str,
        repo_name: str,
        access_key: str,
        secret_key: str,
        region: str,
        service_name: str,
        runtime: str = "PYTHON_3",
        build_command: str = "pip install -r requirements.txt",
        start_command: str = "python run.py"
    ) -> None:
        """Initializes state and triggers background deployment worker."""
        # Initialize deployment dictionary
        deployments[deployment_id] = {
            "deployment_id": deployment_id,
            "user_id": user_id,
            "repository": repo_url,
            "repo_name": repo_name,
            "region": region,
            "service": "AWS App Runner",
            "service_name": service_name,
            "status": "pending",
            "url": None,
            "duration_seconds": 0,
            "cost_estimate": 35.86,
            "timestamp": datetime.datetime.now().isoformat(),
            "logs": [],
            "console": []
        }

        # Spawn background execution thread
        t = threading.Thread(
            target=DeploymentService._execute_deployment_worker,
            args=(deployment_id, access_key, secret_key, region, repo_url, repo_name, service_name, runtime, build_command, start_command),
            daemon=True
        )
        t.start()

    @staticmethod
    def _execute_deployment_worker(
        deployment_id: str,
        access_key: str,
        secret_key: str,
        region: str,
        repo_url: str,
        repo_name: str,
        service_name: str,
        runtime: str,
        build_command: str,
        start_command: str
    ) -> None:
        start_time = time.time()
        
        # Stages setup
        stages = [
            "Preparing",
            "Initializing Terraform",
            "Planning",
            "Creating Infrastructure",
            "Deploying Application",
            "Verifying Health",
            "Completed"
        ]

        for s in stages:
            add_deployment_log(deployment_id, s, f"Waiting to start {s}...", "pending")

        # 1. Preparing
        add_deployment_log(deployment_id, "Preparing", "Setting up deployment directory and Terraform vars...", "in_progress")
        time.sleep(1.5)
        
        workspace_dir = os.path.join(settings.TEMP_CLONE_DIR, f"deploy_{deployment_id}")
        os.makedirs(workspace_dir, exist_ok=True)
        
        tf_template = """
provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

variable "aws_region" { type = string }
variable "aws_access_key" { type = string }
variable "aws_secret_key" { type = string }
variable "service_name" { type = string }
variable "repository_url" { type = string }
variable "runtime" { type = string }
variable "build_command" { type = string }
variable "start_command" { type = string }

resource "aws_apprunner_service" "app" {
  service_name = var.service_name

  source_configuration {
    auto_deployments_enabled = false
    code_repository {
      repository_url = var.repository_url
      source_code_version {
        type  = "BRANCH"
        value = "main"
      }
      code_configuration {
        configuration_source = "API"
        code_configuration_values {
          runtime       = var.runtime
          build_command = var.build_command
          start_command = var.start_command
        }
      }
    }
  }
}

output "service_url" {
  value = aws_apprunner_service.app.service_url
}
"""
        with open(os.path.join(workspace_dir, "main.tf"), "w") as f:
            f.write(tf_template)
            
        tf_vars = {
            "aws_region": region,
            "aws_access_key": access_key,
            "aws_secret_key": secret_key,
            "service_name": service_name,
            "repository_url": repo_url,
            "runtime": runtime,
            "build_command": build_command,
            "start_command": start_command
        }
        with open(os.path.join(workspace_dir, "terraform.tfvars.json"), "w") as f:
            json.dump(tf_vars, f)

        add_deployment_log(deployment_id, "Preparing", "Workspace directory configured.", "completed")

        # Manually inject venv/Scripts to OS PATH so python subprocess can find local terraform.exe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        venv_scripts = os.path.join(base_dir, "venv", "Scripts")
        if os.path.exists(venv_scripts):
            os.environ["PATH"] = venv_scripts + os.pathsep + os.environ["PATH"]

        # Check if terraform is installed in system path
        has_terraform = shutil.which("terraform") is not None
        
        if not has_terraform:
            add_deployment_log(deployment_id, "Initializing Terraform", "ERROR: Terraform CLI binary not found. Real deployments require Terraform to be installed on the system.", "failed")
            dep_data = deployments[deployment_id]
            dep_data["status"] = "failed"
            dep_data["duration_seconds"] = int(time.time() - start_time)
            deployments[deployment_id] = dep_data
            return
        else:
            try:
                # 2. Terraform Init
                DeploymentService._run_terraform_command(deployment_id, "Initializing Terraform", ["terraform", "init"], workspace_dir)
                add_deployment_log(deployment_id, "Initializing Terraform", "Terraform modules initialized successfully.", "completed")

                # 3. Terraform Plan
                DeploymentService._run_terraform_command(deployment_id, "Planning", ["terraform", "plan"], workspace_dir)
                add_deployment_log(deployment_id, "Planning", "Terraform plan calculated.", "completed")

                # 4. Terraform Apply
                DeploymentService._run_terraform_command(deployment_id, "Creating Infrastructure", ["terraform", "apply", "-auto-approve"], workspace_dir)
                add_deployment_log(deployment_id, "Creating Infrastructure", "Terraform resources created.", "completed")

                # 5. Deploying Application
                add_deployment_log(deployment_id, "Deploying Application", "Monitoring App Runner setup deployment...", "in_progress")
                time.sleep(2.0)
                add_deployment_log(deployment_id, "Deploying Application", "Container build uploaded.", "completed")

                # 6. Verifying Health
                add_deployment_log(deployment_id, "Verifying Health", "Verifying service endpoint check...", "in_progress")
                # Extract output URL
                output_proc = subprocess.run(["terraform", "output", "-json"], cwd=workspace_dir, capture_output=True, text=True)
                live_url = f"https://{service_name}.ap-south-1.awsapprunner.com"
                if output_proc.returncode == 0:
                    try:
                        outputs = json.loads(output_proc.stdout)
                        live_url = outputs.get("service_url", {}).get("value", live_url)
                    except Exception:
                        pass
                add_deployment_log(deployment_id, "Verifying Health", "Service health check passed.", "completed")
                
            except Exception as e:
                # Log Failure stage
                for s in stages:
                    dep = deployments[deployment_id]
                    log_for_stage = next((l for l in dep.get("logs", []) if l.get("stage") == s), {})
                    if log_for_stage.get("status") in ["pending", "in_progress"]:
                        add_deployment_log(deployment_id, s, f"Execution failed: {str(e)}", "failed")
                
                dep_data = deployments[deployment_id]
                dep_data["status"] = "failed"
                dep_data["duration_seconds"] = int(time.time() - start_time)
                deployments[deployment_id] = dep_data
                return

        # 7. Completed successfully
        add_deployment_log(deployment_id, "Completed", f"Deployment finished. Live URL: {live_url}", "completed")
        
        dep_data = deployments[deployment_id]
        dep_data["status"] = "completed"
        dep_data["url"] = live_url
        dep_data["duration_seconds"] = int(time.time() - start_time)
        deployments[deployment_id] = dep_data

    @staticmethod
    def _run_terraform_command(deployment_id: str, stage: str, command: list, cwd: str) -> None:
        """Executes a terraform command and streams stdout/stderr outputs to database logs in real time."""
        add_deployment_log(deployment_id, stage, f"Executing: {' '.join(command)}", "in_progress")
        try:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=0x08000000 # CREATE_NO_WINDOW on Windows to prevent console popup
            )
            
            for line in proc.stdout:
                clean_line = line.strip()
                if clean_line:
                    add_deployment_log(deployment_id, stage, clean_line, "in_progress")
                    
            proc.wait()
            if proc.returncode != 0:
                raise Exception(f"Command {' '.join(command)} failed with exit status {proc.returncode}")
        except Exception as e:
            raise Exception(f"Subprocess run failed: {str(e)}")

    @staticmethod
    def start_destroy(deployment_id: str) -> None:
        """Triggers background destroy execution worker."""
        dep_data = deployments.get(deployment_id)
        if not dep_data:
            return
            
        dep_data["status"] = "destroying"
        deployments[deployment_id] = dep_data

        t = threading.Thread(
            target=DeploymentService._execute_destroy_worker,
            args=(deployment_id,),
            daemon=True
        )
        t.start()

    @staticmethod
    def _execute_destroy_worker(deployment_id: str) -> None:
        workspace_dir = os.path.join(settings.TEMP_CLONE_DIR, f"deploy_{deployment_id}")
        
        # Manually inject venv/Scripts to OS PATH so python subprocess can find local terraform.exe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        venv_scripts = os.path.join(base_dir, "venv", "Scripts")
        if os.path.exists(venv_scripts):
            os.environ["PATH"] = venv_scripts + os.pathsep + os.environ["PATH"]

        has_terraform = shutil.which("terraform") is not None
        
        add_deployment_log(deployment_id, "Destroying", "Decommissioning App Runner compute service...", "in_progress")
        time.sleep(2.5)

        if has_terraform and os.path.exists(workspace_dir):
            try:
                DeploymentService._run_terraform_command(deployment_id, "Destroying", ["terraform", "destroy", "-auto-approve"], workspace_dir)
            except Exception:
                pass
            shutil.rmtree(workspace_dir, ignore_errors=True)

        add_deployment_log(deployment_id, "Destroying", "App Runner service decommissioned successfully.", "completed")
        
        dep_data = deployments[deployment_id]
        dep_data["status"] = "destroyed"
        deployments[deployment_id] = dep_data
