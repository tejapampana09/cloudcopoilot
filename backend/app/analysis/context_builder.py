import os
import re
import json
import logging
from typing import Dict, List, Optional
from app.schemas.architecture import RepositoryContext
from app.schemas.analyzer import RepoMetadata

logger = logging.getLogger(__name__)


class RepositoryContextBuilder:
    @staticmethod
    def build(metadata: RepoMetadata, repo_name: str, owner: str, clone_path: Optional[str] = None) -> RepositoryContext:
        project_type = "Unknown"
        if metadata.frontend and metadata.backend:
            project_type = "Fullstack"
        elif metadata.frontend:
            project_type = "Frontend"
        elif metadata.backend:
            project_type = "Backend"

        # Initialize collections
        dependencies = []
        orm = []
        authentication = []
        storage = []
        caching = []
        queues = []
        third_party_apis = []
        has_local_uploads = False
        has_sqlite = False
        detected_bottlenecks = []

        if clone_path and os.path.exists(clone_path):
            # Scan dependency files
            for root, dirs, files in os.walk(clone_path):
                # Skip build, temp and git folders
                if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next']):
                    continue
                
                for file in files:
                    filepath = os.path.join(root, file)
                    file_lower = file.lower()
                    
                    # 1. Parse dependencies
                    if file_lower == "package.json":
                        dependencies.extend(RepositoryContextBuilder._parse_package_json(filepath))
                    elif file_lower == "requirements.txt":
                        dependencies.extend(RepositoryContextBuilder._parse_requirements_txt(filepath))
                    elif file_lower == "pyproject.toml":
                        dependencies.extend(RepositoryContextBuilder._parse_toml_dependencies(filepath))
                    elif file_lower == "pipfile":
                        dependencies.extend(RepositoryContextBuilder._parse_toml_dependencies(filepath))
                    elif file_lower == "cargo.toml":
                        dependencies.extend(RepositoryContextBuilder._parse_toml_dependencies(filepath))
                    elif file_lower == "go.mod":
                        dependencies.extend(RepositoryContextBuilder._parse_go_mod(filepath))

                    # 2. Check for local upload directories heuristically
                    if any(upload_dir in root.lower() for upload_dir in ["/uploads", "\\uploads", "/media", "\\media", "/public/uploads"]):
                        has_local_uploads = True

            # Deduplicate dependencies
            dependencies = sorted(list(set(dependencies)))

            # Categorize dependencies
            orm = RepositoryContextBuilder._detect_orm(dependencies)
            authentication = RepositoryContextBuilder._detect_auth(dependencies, metadata.env_variables)
            storage = RepositoryContextBuilder._detect_storage(dependencies, metadata.infrastructure_files)
            caching = RepositoryContextBuilder._detect_caching(dependencies)
            queues = RepositoryContextBuilder._detect_queues(dependencies)
            third_party_apis = RepositoryContextBuilder._detect_apis(dependencies)

            # Extract SQLite database presence
            if "sqlite" in [db.lower() for db in metadata.databases] or any("sqlite" in dep.lower() for dep in dependencies):
                has_sqlite = True
                if "SQLite" not in metadata.databases:
                    metadata.databases.append("SQLite")

            # Identify Bottlenecks
            detected_bottlenecks = RepositoryContextBuilder._detect_bottlenecks(
                metadata=metadata,
                dependencies=dependencies,
                authentication=authentication,
                storage=storage,
                caching=caching,
                queues=queues,
                has_local_uploads=has_local_uploads,
                has_sqlite=has_sqlite
            )

        # Estimate complexity and scalability
        project_complexity = RepositoryContextBuilder._estimate_complexity(metadata, dependencies, queues)
        expected_scalability = RepositoryContextBuilder._estimate_scalability(metadata, caching, queues, has_local_uploads, has_sqlite)
        repository_structure = RepositoryContextBuilder._analyze_repository_structure(metadata)

        # Ensure database is in list if not empty
        db_list = metadata.databases
        if not db_list and any(db in orm for db in ["Mongoose", "Sequelize", "Prisma"]):
            # Inferred database
            db_list = ["PostgreSQL"]

        # If there are bottleneck descriptions, we store them somewhere.
        # Note: We can attach them to repository_structure metadata or pass them as part of custom context fields.
        # We can write these bottlenecks into repository_structure under a special key for retrieval.
        repository_structure["bottlenecks_count"] = len(detected_bottlenecks)
        # Store raw bottlenecks list in dependencies if needed, or we will read them in ArchitectureAnalyzer.

        return RepositoryContext(
            project_name=repo_name,
            project_type=project_type,
            frontend_framework=metadata.frontend[0] if metadata.frontend else None,
            backend_framework=metadata.backend[0] if metadata.backend else None,
            programming_languages=[lang.name for lang in metadata.languages],
            package_managers=metadata.package_managers,
            databases=db_list,
            orm=orm,
            authentication=authentication,
            storage=storage,
            caching=caching,
            queues=queues,
            third_party_apis=third_party_apis,
            environment_variables=metadata.env_variables,
            deployment_requirements=metadata.run_commands + metadata.build_commands,
            docker_availability=metadata.docker_readiness,
            infrastructure_files=metadata.infrastructure_files,
            build_commands=metadata.build_commands,
            run_commands=metadata.run_commands,
            project_complexity=project_complexity,
            expected_scalability=expected_scalability,
            repository_structure=repository_structure,
            dependencies=dependencies,
        )

    @staticmethod
    def _parse_package_json(filepath: str) -> List[str]:
        deps = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in ["dependencies", "devDependencies"]:
                if s in data and isinstance(data[s], dict):
                    deps.extend(data[s].keys())
        except Exception as e:
            logger.warning(f"Error parsing package.json dependency file: {e}")
        return deps

    @staticmethod
    def _parse_requirements_txt(filepath: str) -> List[str]:
        deps = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        name = re.split(r"==|>=|<=|>|<|@|;", line)[0].strip()
                        if name:
                            deps.append(name)
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt dependency file: {e}")
        return deps

    @staticmethod
    def _parse_toml_dependencies(filepath: str) -> List[str]:
        deps = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("["):
                    sec = line.lower()
                    if "dependencies" in sec or "packages" in sec:
                        in_deps = True
                    else:
                        in_deps = False
                    continue
                if in_deps:
                    if "=" in line and not line.startswith("#"):
                        name = line.split("=")[0].strip().strip('"').strip("'")
                        if name:
                            deps.append(name)
        except Exception as e:
            logger.warning(f"Error parsing toml dependency file: {e}")
        return deps

    @staticmethod
    def _parse_go_mod(filepath: str) -> List[str]:
        deps = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    if line.startswith("require ("):
                        in_require = True
                        continue
                    elif line.startswith(")") and in_require:
                        in_require = False
                        continue
                    
                    if in_require:
                        parts = line.split()
                        if parts:
                            deps.append(parts[0])
                    elif line.startswith("require "):
                        parts = line.split()
                        if len(parts) >= 2:
                            deps.append(parts[1])
        except Exception as e:
            logger.warning(f"Error parsing go.mod dependency file: {e}")
        return deps

    @staticmethod
    def _detect_orm(dependencies: List[str]) -> List[str]:
        orm_map = {
            "sqlalchemy": "SQLAlchemy",
            "peewee": "Peewee",
            "tortoise": "Tortoise ORM",
            "django": "Django ORM",
            "prisma": "Prisma",
            "mongoose": "Mongoose",
            "sequelize": "Sequelize",
            "typeorm": "TypeORM",
            "objection": "Objection.js",
            "knex": "Knex.js",
            "gorm": "Gorm",
            "diesel": "Diesel",
            "sea-orm": "SeaORM"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in orm_map.items():
                if key in dep_lower:
                    detected.append(val)
        return sorted(list(set(detected)))

    @staticmethod
    def _detect_auth(dependencies: List[str], env_vars: List[str]) -> List[str]:
        auth_map = {
            "passport": "PassportJS",
            "jsonwebtoken": "JWT (jsonwebtoken)",
            "next-auth": "NextAuth",
            "auth0": "Auth0 SDK",
            "firebase-admin": "Firebase Authentication",
            "cognito": "AWS Cognito SDK",
            "pyjwt": "PyJWT",
            "passlib": "Passlib (bcrypt)",
            "bcrypt": "Bcrypt",
            "argon2": "Argon2",
            "jose": "JOSE Token SDK"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in auth_map.items():
                if key in dep_lower:
                    detected.append(val)
        
        # Check env variables for auth configs
        env_auth_triggers = ["JWT", "AUTH", "COGNITO", "CLERK", "FIREBASE_AUTH", "SESSION_SECRET"]
        for env in env_vars:
            for trig in env_auth_triggers:
                if trig in env.upper():
                    if trig == "JWT":
                        detected.append("Token-based / JWT")
                    elif trig == "COGNITO":
                        detected.append("AWS Cognito")
                    elif trig == "CLERK":
                        detected.append("Clerk Auth")
                    else:
                        detected.append("Environment-configured Secrets")
        
        return sorted(list(set(detected)))

    @staticmethod
    def _detect_storage(dependencies: List[str], infra_files: List[str]) -> List[str]:
        storage_map = {
            "boto3": "AWS SDK (Boto3)",
            "aws-sdk": "AWS SDK",
            "client-s3": "Amazon S3 Client",
            "multer": "Multer File Upload",
            "cloudinary": "Cloudinary Storage",
            "google-cloud-storage": "Google Cloud Storage",
            "azure-storage": "Azure Blob Storage"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in storage_map.items():
                if key in dep_lower:
                    detected.append(val)
        
        if any("s3" in f.lower() for f in infra_files):
            detected.append("Amazon S3 (inferred from IaC)")

        return sorted(list(set(detected)))

    @staticmethod
    def _detect_caching(dependencies: List[str]) -> List[str]:
        cache_map = {
            "redis": "Redis",
            "ioredis": "Redis (ioredis)",
            "memcached": "Memcached",
            "pymemcache": "Memcached (pymemcache)",
            "cache-manager": "NestJS Cache Manager"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in cache_map.items():
                if key in dep_lower:
                    detected.append(val)
        return sorted(list(set(detected)))

    @staticmethod
    def _detect_queues(dependencies: List[str]) -> List[str]:
        queue_map = {
            "celery": "Celery",
            "bull": "Bull MQ",
            "bullmq": "BullMQ",
            "amqp": "AMQP (RabbitMQ)",
            "pika": "Pika (RabbitMQ)",
            "client-sqs": "Amazon SQS Client",
            "kafkajs": "KafkaJS",
            "kafka-python": "Kafka Python",
            "rq": "Redis Queue (RQ)"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in queue_map.items():
                if key in dep_lower:
                    detected.append(val)
        return sorted(list(set(detected)))

    @staticmethod
    def _detect_apis(dependencies: List[str]) -> List[str]:
        api_map = {
            "stripe": "Stripe Payments",
            "twilio": "Twilio API",
            "sendgrid": "SendGrid Email",
            "mailchimp": "Mailchimp Marketing",
            "sentry": "Sentry Monitoring",
            "datadog": "Datadog Observability",
            "firebase": "Firebase Platform"
        }
        detected = []
        for dep in dependencies:
            dep_lower = dep.lower()
            for key, val in api_map.items():
                if key in dep_lower:
                    detected.append(val)
        return sorted(list(set(detected)))

    @staticmethod
    def _detect_bottlenecks(
        metadata: RepoMetadata,
        dependencies: List[str],
        authentication: List[str],
        storage: List[str],
        caching: List[str],
        queues: List[str],
        has_local_uploads: bool,
        has_sqlite: bool
    ) -> List[str]:
        bottlenecks = []
        
        # 1. SQLite database
        if has_sqlite:
            bottlenecks.append(
                "Uses SQLite as database, which is file-based and blocks write operations "
                "under concurrency, restricting the application to single-instance stateless scaling."
            )
        
        # 2. Local uploads
        if has_local_uploads or "Multer File Upload" in storage:
            bottlenecks.append(
                "Detected local disk file storage upload patterns (e.g. uploads/ or Multer). "
                "Files uploaded to a local container will be lost during scaling/redeployment. "
                "Recommend migration to Amazon S3."
            )
            
        # 3. Stateless scalability database reads bottleneck
        if metadata.databases and not caching:
            bottlenecks.append(
                "App uses a persistent database but no caching tier (like Redis) was detected. "
                "High read traffic volumes could saturate database IOPS."
            )

        # 4. Long running processes or CPU work without queue
        if metadata.backend and not queues:
            bottlenecks.append(
                "No asynchronous worker/task queue detected in backend dependencies. "
                "Running long-running or resource-intensive tasks synchronously inside request handlers "
                "will bottleneck API throughput and response times."
            )

        # 5. Missing environment template
        if not any(f in "".join(metadata.infrastructure_files).lower() for f in [".env.example", ".env.template", ".env.sample"]):
            if len(metadata.env_variables) > 0:
                bottlenecks.append(
                    "No environment configuration template (.env.example) found despite the "
                    "presence of environment variable references. This complicates config management."
                )
                
        # 6. Lack of containerization
        if not metadata.docker_readiness:
            bottlenecks.append(
                "No Dockerfile found in the repository. Modern scalable deployment configurations "
                "rely on containerization; deploying directly from code source requires specific platform runtimes."
            )

        return bottlenecks

    @staticmethod
    def _estimate_complexity(metadata: RepoMetadata, dependencies: List[str], queues: List[str]) -> str:
        score = 0
        score += len(metadata.languages) * 2
        score += len(metadata.frameworks) * 3
        score += len(metadata.infrastructure_files) * 2
        score += len(metadata.package_managers)
        score += len(queues) * 4
        score += 5 if metadata.docker_compose else 0
        score += 3 if metadata.terraform else 0
        score += len(metadata.databases) * 3
        
        if score >= 16:
            return "High"
        if score >= 8:
            return "Medium"
        return "Low"

    @staticmethod
    def _estimate_scalability(metadata: RepoMetadata, caching: List[str], queues: List[str], has_local_uploads: bool, has_sqlite: bool) -> str:
        if has_sqlite or has_local_uploads:
            return "Limited"
        
        score = 0
        if metadata.docker_readiness:
            score += 3
        if metadata.terraform:
            score += 2
        if caching:
            score += 2
        if queues:
            score += 3
        if metadata.ci_cd:
            score += 1

        if score >= 7:
            return "Excellent"
        if score >= 4:
            return "Good"
        return "Moderate"

    @staticmethod
    def _analyze_repository_structure(metadata: RepoMetadata) -> Dict[str, int]:
        return {
            "languages": len(metadata.languages),
            "frameworks": len(metadata.frameworks),
            "frontend_components": len(metadata.frontend),
            "backend_components": len(metadata.backend),
            "databases": len(metadata.databases),
            "infrastructure_files": len(metadata.infrastructure_files)
        }
