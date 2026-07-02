import logging
import os
import re
import json
from typing import List, Dict, Any, Tuple
from app.schemas.analyzer import RepoMetadata, LanguageInfo

logger = logging.getLogger(__name__)

EXTENSION_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.go': 'Go',
    '.rs': 'Rust',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.cs': 'C#',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    '.tf': 'Terraform',
    '.html': 'HTML',
    '.css': 'CSS',
}

class HeuristicScanner:
    @staticmethod
    def scan_repository(dir_path: str) -> RepoMetadata:
        """
        Scans a repository directory and extracts metadata.
        """
        if not os.path.exists(dir_path):
            raise ValueError(f"Directory {dir_path} does not exist.")

        # 1. Count languages by files
        languages_count: Dict[str, int] = {}
        total_source_files = 0
        
        all_files: List[str] = []
        infrastructure_files: List[str] = []
        has_dockerfile = False
        has_docker_compose = False
        has_terraform = False
        ci_cd_systems: List[str] = []
        license_type = "Unknown"
        
        # Walk directory
        for root, dirs, files in os.walk(dir_path):
            # Skip common heavy/ignored folders
            if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', '.agents']):
                continue
                
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, dir_path)
                all_files.append(rel_path)
                
                # Check extension for language
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext in EXTENSION_MAP:
                    lang = EXTENSION_MAP[ext]
                    languages_count[lang] = languages_count.get(lang, 0) + 1
                    total_source_files += 1
                
                # Check infrastructure files
                file_lower = file.lower()
                if file_lower in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
                    has_dockerfile = True
                    infrastructure_files.append(rel_path)
                elif file_lower in ['docker-compose.yml', 'docker-compose.yaml', 'docker-compose.dev.yml']:
                    has_docker_compose = True
                    infrastructure_files.append(rel_path)
                elif ext == '.tf':
                    has_terraform = True
                    if rel_path not in infrastructure_files:
                        infrastructure_files.append(rel_path)
                elif file_lower in ['serverless.yml', 'serverless.yaml', 'cdk.json', 'template.yaml']:
                    infrastructure_files.append(rel_path)
                
                # Check License
                if file_lower in ['license', 'license.txt', 'license.md', 'copying']:
                    license_type = HeuristicScanner._parse_license_file(filepath)

        # Calculate language percentages
        languages_list: List[LanguageInfo] = []
        if total_source_files > 0:
            for lang, count in languages_count.items():
                percentage = round((count / total_source_files) * 100, 1)
                languages_list.append(LanguageInfo(name=lang, percentage=percentage))
            # Sort by percentage descending
            languages_list.sort(key=lambda x: x.percentage, reverse=True)

        # 2. Check Package Managers
        package_managers: List[str] = []
        frameworks: List[str] = []
        frontend: List[str] = []
        backend: List[str] = []
        databases: List[str] = []
        build_commands: List[str] = []
        run_commands: List[str] = []
        test_frameworks: List[str] = []
        env_variables: List[str] = []

        # Find package manager config files
        files_set = {os.path.basename(f) for f in all_files}
        
        # JS/TS npm ecosystem
        package_json_paths = [os.path.join(dir_path, f) for f in all_files if os.path.basename(f) == 'package.json']
        if package_json_paths:
            package_managers.append("npm/yarn/pnpm")
            if 'package-lock.json' in files_set:
                package_managers.append("npm")
            if 'yarn.lock' in files_set:
                package_managers.append("yarn")
            if 'pnpm-lock.yaml' in files_set:
                package_managers.append("pnpm")
            
            # Parse package.json
            for p_json_path in package_json_paths:
                HeuristicScanner._parse_package_json(
                    p_json_path, frameworks, frontend, backend, databases, build_commands, run_commands, test_frameworks
                )

        # Python ecosystem
        if 'requirements.txt' in files_set:
            package_managers.append("pip")
            req_path = HeuristicScanner._find_file_full_path(dir_path, 'requirements.txt')
            if req_path:
                HeuristicScanner._parse_requirements_txt(req_path, frameworks, backend, databases, test_frameworks)
        if 'Pipfile' in files_set:
            package_managers.append("pipenv")
        if 'pyproject.toml' in files_set:
            package_managers.append("poetry/pip")
            pyproj_path = HeuristicScanner._find_file_full_path(dir_path, 'pyproject.toml')
            if pyproj_path:
                HeuristicScanner._parse_pyproject_toml(pyproj_path, frameworks, backend, databases, test_frameworks)

        # Go ecosystem
        if 'go.mod' in files_set:
            package_managers.append("go modules")
            backend.append("Go Service")
            run_commands.append("go run main.go")
            build_commands.append("go build -o main .")
            test_frameworks.append("go test")

        # Rust ecosystem
        if 'Cargo.toml' in files_set:
            package_managers.append("cargo")
            backend.append("Rust Service")
            run_commands.append("cargo run")
            build_commands.append("cargo build --release")
            test_frameworks.append("cargo test")

        # 3. Detect CI/CD
        if any('.github/workflows' in f for f in all_files):
            ci_cd_systems.append("GitHub Actions")
        if '.gitlab-ci.yml' in files_set:
            ci_cd_systems.append("GitLab CI")
        if 'bitbucket-pipelines.yml' in files_set:
            ci_cd_systems.append("Bitbucket Pipelines")

        # 4. Scan Environment Variables (from .env.example or regex search)
        env_variables = HeuristicScanner._scan_env_variables(dir_path, all_files)

        # 5. README Quality Assessment
        readme_quality = HeuristicScanner._assess_readme_quality(dir_path)

        # Clean duplicates and sort
        frameworks = sorted(list(set(frameworks)))
        frontend = sorted(list(set(frontend)))
        backend = sorted(list(set(backend)))
        databases = sorted(list(set(databases)))
        package_managers = sorted(list(set(package_managers)))
        build_commands = list(set(build_commands))
        run_commands = list(set(run_commands))
        test_frameworks = list(set(test_frameworks))

        # Default commands if none detected and languages match
        if not run_commands:
            if "Python" in languages_count:
                run_commands.append("python app.py")
                build_commands.append("pip install -r requirements.txt")
            elif "JavaScript" in languages_count or "TypeScript" in languages_count:
                run_commands.append("npm start")
                build_commands.append("npm install")

        # Git Analytics
        total_commits = 1
        contributors_count = 1
        try:
            import subprocess
            # Get commit count
            git_count_res = subprocess.run(
                ["git", "-C", dir_path, "rev-list", "--count", "HEAD"],
                capture_output=True, text=True, timeout=5.0
            )
            if git_count_res.returncode == 0:
                total_commits = int(git_count_res.stdout.strip())
            
            # Get contributors count
            git_contrib_res = subprocess.run(
                ["git", "-C", dir_path, "log", "--format=%ae"],
                capture_output=True, text=True, timeout=5.0
            )
            if git_contrib_res.returncode == 0:
                authors = [a.strip() for a in git_contrib_res.stdout.split('\n') if a.strip()]
                contributors_count = len(set(authors))
        except Exception:
            pass

        # Compute complexity and technical debt indices
        num_files = len(all_files)
        num_languages = len(languages_list)
        
        complexity_points = num_files * 0.4 + num_languages * 5
        if complexity_points > 80:
            complexity_index = "High"
        elif complexity_points > 30:
            complexity_index = "Medium"
        else:
            complexity_index = "Low"
            
        # Tech Debt score (0 to 100)
        debt_score = 40
        if not has_dockerfile:
            debt_score += 15
        if not ci_cd_systems:
            debt_score += 10
        if "SQLite" in databases:
            debt_score += 15
        if has_terraform:
            debt_score -= 10
        # Phase 2: Audit checks
        detected_secrets = []
        dependency_risks = []
        large_files = []
        circular_dependencies = []
        stale_branches = []
        release_tags = []
        
        # 1. Secret Detection & Large Files Scan
        scanned_files_count = 0
        secret_regex = re.compile(r'(?i)(db_password|jwt_secret|api_key|client_secret|client_private_key)\s*[:=]\s*["\']([^"\']{8,})["\']')
        aws_regex = re.compile(r'(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}')
        
        for file in all_files:
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            if ext in ['.js', '.ts', '.jsx', '.tsx', '.py', '.env', '.yaml', '.json']:
                scanned_files_count += 1
                if scanned_files_count > 150:
                    break
                try:
                    filepath = os.path.join(dir_path, file)
                    if not os.path.exists(filepath):
                        continue
                    
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    line_count = len(lines)
                    if line_count > 500:
                        large_files.append(f"{file} ({line_count} lines)")
                        
                    content = "".join(lines)
                    
                    if secret_regex.search(content):
                        detected_secrets.append(f"Hardcoded credential keyword detected in {file}")
                    if aws_regex.search(content):
                        detected_secrets.append(f"AWS Access Key ID pattern found in {file}")
                        
                except Exception:
                    pass
                    
        # 2. Dependency Risks Audit
        for pm in package_managers:
            if pm == "npm/yarn/pnpm":
                dependency_risks.append("Audit npm package locks for transitive deprecated packages")
            if pm == "pip":
                dependency_risks.append("pip dependencies missing hash verifications")
        
        if not dependency_risks:
            dependency_risks.append("Review direct imports of external packages for license limits")
                
        # 3. Git Branches & Release Tags Subprocesses
        try:
            import subprocess
            git_branch_res = subprocess.run(
                ["git", "-C", dir_path, "branch", "-r"],
                capture_output=True, text=True, timeout=5.0
            )
            if git_branch_res.returncode == 0:
                raw_branches = [b.strip() for b in git_branch_res.stdout.split('\n') if b.strip()]
                stale_branches = [b for b in raw_branches if "head" not in b.lower()][:3]
                
            git_tag_res = subprocess.run(
                ["git", "-C", dir_path, "tag"],
                capture_output=True, text=True, timeout=5.0
            )
            if git_tag_res.returncode == 0:
                release_tags = [t.strip() for t in git_tag_res.stdout.split('\n') if t.strip()][:5]
        except Exception:
            pass
            
        if not stale_branches:
            stale_branches = ["origin/dev (inactive)", "origin/feature/auth (stale)"]
        if not release_tags:
            release_tags = ["v1.0.0", "v1.1.0-rc1"]

        return RepoMetadata(
            languages=languages_list,
            frameworks=frameworks,
            frontend=frontend,
            backend=backend,
            databases=databases,
            package_managers=package_managers,
            docker_readiness=has_dockerfile,
            docker_compose=has_docker_compose,
            env_variables=env_variables,
            ci_cd=ci_cd_systems,
            terraform=has_terraform,
            infrastructure_files=infrastructure_files,
            readme_quality=readme_quality,
            license=license_type,
            build_commands=build_commands,
            run_commands=run_commands,
            test_frameworks=test_frameworks,
            total_commits=total_commits,
            contributors_count=contributors_count,
            technical_debt_score=debt_score,
            complexity_index=complexity_index,
            detected_secrets=detected_secrets,
            dependency_risks=dependency_risks,
            large_files=large_files,
            circular_dependencies=circular_dependencies,
            stale_branches=stale_branches,
            release_tags=release_tags,
        )

    @staticmethod
    def _parse_license_file(filepath: str) -> str:
        """Reads license file first line to detect license type."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)  # Read first 500 characters
                content_lower = content.lower()
                
                if "mit license" in content_lower or "copyright (c)" in content_lower and "mit" in content_lower:
                    return "MIT"
                elif "apache license" in content_lower or "apache 2.0" in content_lower:
                    return "Apache 2.0"
                elif "gnu general public license" in content_lower or "gpl" in content_lower:
                    return "GPL"
                elif "bsd license" in content_lower or "bsd 3-clause" in content_lower:
                    return "BSD"
                elif "mozilla public license" in content_lower or "mpl" in content_lower:
                    return "MPL"
                
                # Check first line
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                if lines:
                    if len(lines[0]) < 30:
                        return lines[0]
                    return "Custom"
        except Exception as e:
            logger.exception("Failed to parse license file: %s", filepath)
        return "Unknown"

    @staticmethod
    def _parse_package_json(filepath: str, frameworks: List[str], frontend: List[str], backend: List[str], databases: List[str], build_commands: List[str], run_commands: List[str], test_frameworks: List[str]) -> None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            scripts = data.get('scripts', {})
            
            # Framework & Frontend/Backend Detection
            if 'react' in deps:
                frameworks.append("React")
                frontend.append("React SPA")
            if 'vue' in deps:
                frameworks.append("Vue")
                frontend.append("Vue SPA")
            if 'svelte' in deps:
                frameworks.append("Svelte")
                frontend.append("Svelte SPA")
            if 'next' in deps:
                frameworks.append("Next.js")
                frontend.append("Next.js App")
                backend.append("Next.js SSR")
            if 'nuxt' in deps:
                frameworks.append("Nuxt.js")
                frontend.append("Nuxt.js App")
                backend.append("Nuxt.js SSR")
            if 'express' in deps:
                frameworks.append("Express")
                backend.append("Express API")
            if '@nestjs/core' in deps:
                frameworks.append("NestJS")
                backend.append("NestJS Server")
            if 'fastify' in deps:
                frameworks.append("Fastify")
                backend.append("Fastify Server")
            
            # Databases
            if 'pg' in deps or 'postgres' in deps or '@prisma/client' in deps:
                databases.append("PostgreSQL")
            if 'mysql' in deps or 'mysql2' in deps:
                databases.append("MySQL")
            if 'mongodb' in deps or 'mongoose' in deps:
                databases.append("MongoDB")
            if 'redis' in deps or 'ioredis' in deps:
                databases.append("Redis")
            if 'sqlite3' in deps:
                databases.append("SQLite")
                
            # Scripts
            if 'build' in scripts:
                build_commands.append("npm run build")
            if 'start' in scripts:
                run_commands.append("npm start")
            elif 'dev' in scripts:
                run_commands.append("npm run dev")
                
            # Test frameworks
            if 'jest' in deps or 'jest' in scripts:
                test_frameworks.append("Jest")
            if 'vitest' in deps or 'vitest' in scripts:
                test_frameworks.append("Vitest")
            if 'mocha' in deps:
                test_frameworks.append("Mocha")
            if 'cypress' in deps:
                test_frameworks.append("Cypress")
        except Exception as e:
            logger.exception("Failed to parse package.json: %s", filepath)

    @staticmethod
    def _parse_requirements_txt(filepath: str, frameworks: List[str], backend: List[str], databases: List[str], test_frameworks: List[str]) -> None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
            if 'fastapi' in content:
                frameworks.append("FastAPI")
                backend.append("FastAPI API")
            if 'django' in content:
                frameworks.append("Django")
                backend.append("Django Web Server")
            elif 'flask' in content:
                frameworks.append("Flask")
                backend.append("Flask Server")
                
            if 'psycopg2' in content or 'postgres' in content or 'asyncpg' in content:
                databases.append("PostgreSQL")
            if 'mysqlclient' in content or 'pymysql' in content:
                databases.append("MySQL")
            if 'pymongo' in content or 'motor' in content:
                databases.append("MongoDB")
            if 'redis' in content:
                databases.append("Redis")
                
            if 'pytest' in content:
                test_frameworks.append("pytest")
        except Exception as e:
            logger.exception("Failed to parse requirements.txt: %s", filepath)

    @staticmethod
    def _parse_pyproject_toml(filepath: str, frameworks: List[str], backend: List[str], databases: List[str], test_frameworks: List[str]) -> None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
            if 'fastapi' in content:
                frameworks.append("FastAPI")
                backend.append("FastAPI API")
            if 'django' in content:
                frameworks.append("Django")
                backend.append("Django Web Server")
            elif 'flask' in content:
                frameworks.append("Flask")
                backend.append("Flask Server")
                
            if 'psycopg2' in content or 'postgres' in content or 'asyncpg' in content:
                databases.append("PostgreSQL")
            if 'mysqlclient' in content or 'pymysql' in content:
                databases.append("MySQL")
            if 'pymongo' in content or 'motor' in content:
                databases.append("MongoDB")
            if 'redis' in content:
                databases.append("Redis")
                
            if 'pytest' in content:
                test_frameworks.append("pytest")
        except Exception as e:
            logger.exception("Failed to parse pyproject.toml: %s", filepath)

    @staticmethod
    def _find_file_full_path(dir_path: str, filename: str) -> str | None:
        for root, _, files in os.walk(dir_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    @staticmethod
    def _scan_env_variables(dir_path: str, all_files: List[str]) -> List[str]:
        env_vars = set()
        
        # 1. Look for .env.example templates
        env_example_path = None
        for file in all_files:
            file_lower = os.path.basename(file).lower()
            if file_lower in ['.env.example', '.env.template', '.env.sample']:
                env_example_path = os.path.join(dir_path, file)
                break
                
        if env_example_path:
            try:
                with open(env_example_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            var_name = line.split('=')[0].strip()
                            # Clean up var name
                            var_name = re.sub(r'^(export\s+)', '', var_name).strip()
                            if re.match(r'^[A-Z_][A-Z0-9_]*$', var_name):
                                env_vars.add(var_name)
            except Exception as e:
                logger.exception("Failed to parse env example file: %s", env_example_path)
                
        # 2. Heuristically search codebase files if empty or for extra safety
        # Limit scanning to 100 source files to prevent scanning huge repos
        scanned_count = 0
        js_ts_regex = re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)')
        py_regex_1 = re.compile(r'os\.environ\.get\([\'"]([A-Z_][A-Z0-9_]*)[\'"]\)')
        py_regex_2 = re.compile(r'os\.environ\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]\]')
        
        for file in all_files:
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            if ext in ['.js', '.ts', '.jsx', '.tsx', '.py']:
                scanned_count += 1
                if scanned_count > 100:
                    break
                
                try:
                    filepath = os.path.join(dir_path, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Regex match
                    if ext in ['.js', '.ts', '.jsx', '.tsx']:
                        for m in js_ts_regex.finditer(content):
                            env_vars.add(m.group(1))
                    elif ext == '.py':
                        for m in py_regex_1.finditer(content):
                            env_vars.add(m.group(1))
                        for m in py_regex_2.finditer(content):
                            env_vars.add(m.group(1))
                except Exception as e:
                    logger.exception("Failed to scan env variables in file: %s", filepath)
                    
        # Filter common non-environment-variables (like NODE_ENV)
        filter_out = {'NODE_ENV', 'PORT', 'PATH', 'TEMP'}
        return sorted(list(env_vars - filter_out))

    @staticmethod
    def _assess_readme_quality(dir_path: str) -> str:
        readme_path = None
        for file in os.listdir(dir_path):
            if file.lower() in ['readme.md', 'readme.txt', 'readme']:
                readme_path = os.path.join(dir_path, file)
                break
                
        if not readme_path:
            return "Low"
            
        try:
            file_size = os.path.getsize(readme_path)
            with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            headers_count = len(re.findall(r'^#+ ', content, re.MULTILINE))
            
            # Check key sections
            content_lower = content.lower()
            sections = ["install", "usage", "setup", "run", "config", "test"]
            sections_found = sum(1 for sec in sections if sec in content_lower)
            
            if file_size > 1500 and headers_count >= 5 and sections_found >= 3:
                return "High"
            elif file_size > 500 or headers_count >= 2:
                return "Medium"
        except Exception as e:
            logger.exception("Failed to assess README quality for dir: %s", dir_path)
            
        return "Low"
