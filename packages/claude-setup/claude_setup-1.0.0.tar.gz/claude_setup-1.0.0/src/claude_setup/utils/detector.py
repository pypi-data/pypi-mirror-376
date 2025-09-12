"""Project detection utilities."""

import json
from pathlib import Path
from typing import Any, Optional


class ProjectDetector:
    """Detects project characteristics and configuration."""

    def __init__(self, project_path: Path):
        """Initialize detector with project path.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)

    def detect(self) -> dict[str, Any]:
        """Detect project configuration.

        Returns:
            Dictionary with detected configuration
        """
        config = {}

        # Detect language
        language = self._detect_language()
        if language:
            config["language"] = language

        # Detect frameworks
        frameworks = self._detect_frameworks()
        if frameworks:
            config["frameworks"] = frameworks

        # Detect project type
        project_type = self._detect_project_type()
        if project_type:
            config["project_type"] = project_type

        # Detect tools
        tools = self._detect_tools()
        if tools:
            config["tools"] = tools

        # Detect team size from git history
        team_size = self._detect_team_size()
        if team_size:
            config["team_size"] = team_size

        return config

    def _detect_language(self) -> Optional[str]:
        """Detect primary programming language."""
        language_patterns = {
            "Python": ["*.py", "requirements.txt", "pyproject.toml", "Pipfile", "setup.py"],
            "JavaScript/TypeScript": ["*.js", "*.ts", "*.jsx", "*.tsx", "package.json"],
            "Go": ["*.go", "go.mod", "go.sum"],
            "Rust": ["*.rs", "Cargo.toml", "Cargo.lock"],
            "Java": ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
            "C/C++": ["*.c", "*.cpp", "*.h", "*.hpp", "CMakeLists.txt", "Makefile"],
            "Ruby": ["*.rb", "Gemfile", "Gemfile.lock"],
            "PHP": ["*.php", "composer.json", "composer.lock"],
            "Swift": ["*.swift", "Package.swift"],
            "Kotlin": ["*.kt", "*.kts", "build.gradle.kts"],
        }

        file_counts = {}

        for lang, patterns in language_patterns.items():
            count = 0
            for pattern in patterns:
                if pattern.startswith("*"):
                    # Count files with extension
                    count += len(list(self.project_path.rglob(pattern)))
                else:
                    # Check if specific file exists
                    if (self.project_path / pattern).exists():
                        count += 10  # Weight config files higher

            if count > 0:
                file_counts[lang] = count

        if file_counts:
            # Return language with most files
            return max(file_counts, key=file_counts.get)

        return "Other"

    def _detect_frameworks(self) -> list[str]:
        """Detect frameworks and libraries."""
        frameworks = []

        # Check package.json for JS frameworks
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                framework_map = {
                    "react": "React",
                    "vue": "Vue",
                    "next": "Next.js",
                    "@angular/core": "Angular",
                    "svelte": "Svelte",
                    "express": "Express",
                    "fastify": "Fastify",
                    "nest": "NestJS",
                    "gatsby": "Gatsby",
                    "nuxt": "Nuxt",
                    "vite": "Vite",
                    "webpack": "Webpack",
                    "tailwindcss": "Tailwind CSS",
                    "@mui/material": "Material UI",
                    "bootstrap": "Bootstrap",
                }

                for key, name in framework_map.items():
                    if any(key in dep.lower() for dep in deps):
                        frameworks.append(name)
            except Exception:
                pass

        # Check Python requirements
        python_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
        for req_file in python_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text().lower()

                    framework_map = {
                        "django": "Django",
                        "fastapi": "FastAPI",
                        "flask": "Flask",
                        "pytest": "pytest",
                        "pandas": "pandas",
                        "numpy": "numpy",
                        "tensorflow": "TensorFlow",
                        "pytorch": "PyTorch",
                        "scikit-learn": "scikit-learn",
                        "streamlit": "Streamlit",
                        "dash": "Dash",
                        "sqlalchemy": "SQLAlchemy",
                        "celery": "Celery",
                        "pydantic": "Pydantic",
                    }

                    for key, name in framework_map.items():
                        if key in content:
                            frameworks.append(name)
                except Exception:
                    pass

        # Check for Go frameworks
        go_mod = self.project_path / "go.mod"
        if go_mod.exists():
            try:
                content = go_mod.read_text().lower()

                framework_map = {
                    "gin-gonic/gin": "Gin",
                    "gorilla/mux": "Gorilla",
                    "fiber": "Fiber",
                    "echo": "Echo",
                    "beego": "Beego",
                }

                for key, name in framework_map.items():
                    if key in content:
                        frameworks.append(name)
            except Exception:
                pass

        # Check for databases
        db_indicators = {
            "PostgreSQL": ["postgres", "psycopg2", "pg", "@prisma/client"],
            "MongoDB": ["mongodb", "mongoose", "pymongo"],
            "MySQL": ["mysql", "mysql2", "mysqlclient"],
            "Redis": ["redis", "ioredis"],
            "SQLite": ["sqlite", "sqlite3"],
        }

        for db, indicators in db_indicators.items():
            for file in ["package.json", "requirements.txt", "go.mod", "Cargo.toml"]:
                file_path = self.project_path / file
                if file_path.exists():
                    try:
                        content = file_path.read_text().lower()
                        if any(ind in content for ind in indicators):
                            frameworks.append(db)
                            break
                    except Exception:
                        pass

        return list(set(frameworks))  # Remove duplicates

    def _detect_project_type(self) -> str:
        """Detect project type."""
        # Check for web app indicators
        if (self.project_path / "package.json").exists():
            try:
                with open(self.project_path / "package.json") as f:
                    data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                # Frontend frameworks
                if any(fw in str(deps).lower() for fw in ["react", "vue", "angular", "svelte"]):
                    return "Web Application"

                # Backend frameworks
                if any(fw in str(deps).lower() for fw in ["express", "fastify", "nestjs", "koa"]):
                    return "Backend API"
            except Exception:
                pass

        # Check for API indicators
        api_files = ["openapi.yaml", "swagger.yaml", "api.yaml", "postman.json"]
        if any((self.project_path / f).exists() for f in api_files):
            return "Backend API"

        # Check for CLI indicators
        if (self.project_path / "setup.py").exists():
            try:
                content = (self.project_path / "setup.py").read_text()
                if "console_scripts" in content or "entry_points" in content:
                    return "CLI Tool"
            except Exception:
                pass

        # Check for data science indicators
        notebook_files = list(self.project_path.rglob("*.ipynb"))
        if notebook_files:
            return "Data Science"

        # Check for mobile app indicators
        if (self.project_path / "package.json").exists():
            try:
                with open(self.project_path / "package.json") as f:
                    data = json.load(f)
                deps = str(data.get("dependencies", {})).lower()
                if "react-native" in deps or "expo" in deps:
                    return "Mobile App"
            except Exception:
                pass

        if (self.project_path / "pubspec.yaml").exists():  # Flutter
            return "Mobile App"

        # Check for documentation projects
        doc_files = ["mkdocs.yml", "docs/conf.py", "_config.yml", "book.toml"]
        if any((self.project_path / f).exists() for f in doc_files):
            return "Documentation"

        # Check for library indicators
        if (self.project_path / "setup.py").exists() or (
            self.project_path / "pyproject.toml"
        ).exists():
            return "Library"

        return "Other"

    def _detect_tools(self) -> list[str]:
        """Detect development tools."""
        tools = []

        tool_files = {
            "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
            "GitHub Actions": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
            "GitLab CI": [".gitlab-ci.yml"],
            "CircleCI": [".circleci/config.yml"],
            "Jenkins": ["Jenkinsfile"],
            "Travis CI": [".travis.yml"],
            "pytest": ["pytest.ini", "tox.ini", "conftest.py", ".pytest_cache"],
            "Jest": ["jest.config.js", "jest.config.ts", "jest.config.json"],
            "Mocha": ["mocha.opts", ".mocharc.js", ".mocharc.json"],
            "ESLint": [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml"],
            "Prettier": [".prettierrc", ".prettierrc.js", ".prettierrc.json", ".prettierrc.yml"],
            "Black": ["pyproject.toml", ".black"],
            "Ruff": ["ruff.toml", ".ruff.toml"],
            "Git": [".git", ".gitignore"],
            "Kubernetes": ["k8s/", "kubernetes/", "*.yaml"],
            "Terraform": ["*.tf", "terraform/"],
            "Ansible": ["ansible.cfg", "playbook.yml", "inventory"],
            "Make": ["Makefile", "makefile"],
        }

        for tool, patterns in tool_files.items():
            for pattern in patterns:
                if "*" in pattern:
                    # Handle glob patterns
                    if list(self.project_path.glob(pattern)):
                        tools.append(tool)
                        break
                else:
                    # Check if file/directory exists
                    if (self.project_path / pattern).exists():
                        tools.append(tool)
                        break

        return list(set(tools))  # Remove duplicates

    def _detect_team_size(self) -> str:
        """Detect team size from git history."""
        git_dir = self.project_path / ".git"
        if not git_dir.exists():
            return "Solo"

        try:
            # Try to count unique authors in git history
            import subprocess

            result = subprocess.run(
                ["git", "log", "--format=%ae"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                authors = set(result.stdout.strip().split("\n"))
                num_authors = len(authors)

                if num_authors <= 1:
                    return "Solo"
                elif num_authors <= 5:
                    return "2-5"
                elif num_authors <= 20:
                    return "6-20"
                else:
                    return "20+"
        except Exception:
            pass

        return "Solo"
