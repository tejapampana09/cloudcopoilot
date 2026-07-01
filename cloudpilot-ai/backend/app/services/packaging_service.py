import os
import shutil
import zipfile
from typing import Dict

class PackagingService:
    @staticmethod
    def redact_secrets(content: str) -> str:
        """Defense-in-depth scanner to redact secret key patterns from LLM outputs."""
        import re
        # Redact OpenAI sk- keys
        content = re.sub(r'sk-[a-zA-Z0-9]{48}', '[REDACTED_OPENAI_KEY]', content)
        # Redact AWS Access Key IDs
        content = re.sub(r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY_ID]', content)
        return content

    @staticmethod
    def package_files(generation_id: str, generated_files: Dict[str, str], temp_dir_base: str, downloads_dir_base: str) -> str:
        """
        Writes files locally, packages them into a ZIP archive, cleans up staging,
        and returns the absolute path to the ZIP archive.
        """
        # Create unique temp staging directory
        staging_path = os.path.join(temp_dir_base, generation_id)
        os.makedirs(staging_path, exist_ok=True)

        try:
            # 1. Write all generated files
            for rel_path, content in generated_files.items():
                # Redact any accidentally output secret patterns
                cleaned_content = PackagingService.redact_secrets(content)
                
                file_path = os.path.join(staging_path, rel_path)
                # Create directories if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Write file content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)

            # Write static README deployment notes
            readme_path = os.path.join(staging_path, "deploy_notes.md")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(PackagingService._generate_deployment_notes(generated_files))

            # 2. Package into a ZIP file
            os.makedirs(downloads_dir_base, exist_ok=True)
            zip_filename = f"cloudpilot-infra-{generation_id}.zip"
            zip_path = os.path.join(downloads_dir_base, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(staging_path):
                    for file in files:
                        full_filepath = os.path.join(root, file)
                        # Relative path inside the zip file
                        archive_name = os.path.relpath(full_filepath, staging_path)
                        zip_file.write(full_filepath, archive_name)

            return zip_path
        finally:
            # 3. Clean up staging directory
            if os.path.exists(staging_path):
                shutil.rmtree(staging_path, ignore_errors=True)

    @staticmethod
    def _generate_deployment_notes(generated_files: Dict[str, str]) -> str:
        """Generates static instructions on how to use these files."""
        has_docker = "Dockerfile" in generated_files
        has_compose = "docker-compose.yml" in generated_files
        has_terraform = any("terraform/" in k for k in generated_files.keys())
        has_gha = any(".github/" in k for k in generated_files.keys())

        notes = """# CloudPilot AI - Generated Deployment Infrastructure

This archive contains the infrastructure configurations generated for your repository.

## Contents
"""
        if has_docker:
            notes += "- `Dockerfile` & `.dockerignore`: For containerizing your application.\n"
        if has_compose:
            notes += "- `docker-compose.yml`: For running multi-container stacks locally.\n"
        if has_terraform:
            notes += "- `terraform/`: Modular configuration files to provision compute/VPC/ECR on AWS.\n"
        if has_gha:
            notes += "- `.github/workflows/deploy.yml`: CI/CD actions to build, test, and deploy to AWS.\n"

        notes += "\n## Quick Start\n"
        if has_compose:
            notes += """
### Run Locally
To spin up your application stack locally including databases:
```bash
docker compose up -d --build
```
"""
        if has_terraform:
            notes += """
### Deploy to AWS (Terraform)
1. Configure your AWS credentials CLI.
2. Initialize and deploy the Terraform files:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```
"""
        return notes
