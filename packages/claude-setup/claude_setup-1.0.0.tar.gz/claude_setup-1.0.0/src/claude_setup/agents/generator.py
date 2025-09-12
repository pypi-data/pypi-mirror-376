"""Configuration generator that creates optimal Claude setups."""

from typing import Any

from claude_setup.config import ClaudeConfig, ProjectConfig


class ConfigGenerator:
    """Generates optimal Claude Code configurations based on project analysis."""

    def generate(self, config: ProjectConfig) -> ClaudeConfig:
        """Generate complete Claude configuration for project.

        Args:
            config: Project configuration data

        Returns:
            Generated Claude configuration
        """
        return ClaudeConfig(
            settings=self._generate_settings(config),
            claude_md=self._generate_claude_md(config),
            commands=self._generate_commands(config),
            agents=self._generate_agents(config),
            hooks=self._generate_hooks(config),
            mcp_servers=self._generate_mcp_servers(config),
        )

    def _generate_settings(self, config: ProjectConfig) -> dict[str, Any]:
        """Generate optimized settings.json."""
        settings = {
            "model": config.model,
            "permissions": {
                "allow": [],
                "deny": [
                    "Read(.env*)",
                    "Read(**/*.key)",
                    "Read(**/*.pem)",
                    "Delete(**)",
                    "Bash(sudo:*)",
                ],
            },
            "env": {
                "PROJECT_TYPE": config.project_type,
                "PRIMARY_LANGUAGE": config.language,
                "TEAM_SIZE": config.team_size,
            },
        }

        # Language-specific permissions
        if config.language == "Python":
            settings["permissions"]["allow"].extend(
                [
                    "Read(**/*.py)",
                    "Write(**/*.py)",
                    "Bash(python:*)",
                    "Bash(pip:*)",
                    "Bash(uv:*)",
                    "Bash(pytest:*)",
                    "Bash(ruff:*)",
                    "Bash(black:*)",
                ]
            )
        elif config.language == "JavaScript/TypeScript":
            settings["permissions"]["allow"].extend(
                [
                    "Read(**/*.js)",
                    "Read(**/*.ts)",
                    "Read(**/*.jsx)",
                    "Read(**/*.tsx)",
                    "Write(**/*.js)",
                    "Write(**/*.ts)",
                    "Write(**/*.jsx)",
                    "Write(**/*.tsx)",
                    "Bash(npm:*)",
                    "Bash(yarn:*)",
                    "Bash(pnpm:*)",
                    "Bash(node:*)",
                    "Bash(jest:*)",
                    "Bash(vitest:*)",
                ]
            )
        elif config.language == "Go":
            settings["permissions"]["allow"].extend(
                ["Read(**/*.go)", "Write(**/*.go)", "Bash(go:*)", "Bash(gofmt:*)", "Bash(golint:*)"]
            )
        elif config.language == "Rust":
            settings["permissions"]["allow"].extend(
                [
                    "Read(**/*.rs)",
                    "Write(**/*.rs)",
                    "Bash(cargo:*)",
                    "Bash(rustc:*)",
                    "Bash(rustfmt:*)",
                ]
            )

        # Framework-specific permissions
        if "Docker" in config.tools or "Docker" in config.frameworks:
            settings["permissions"]["allow"].extend(
                [
                    "Read(Dockerfile*)",
                    "Write(Dockerfile*)",
                    "Read(docker-compose*.yml)",
                    "Write(docker-compose*.yml)",
                    "Bash(docker:*)",
                    "Bash(docker-compose:*)",
                ]
            )

        if "Git" in config.tools:
            settings["permissions"]["allow"].extend(["Bash(git:*)", "Bash(gh:*)"])

        if "Kubernetes" in config.tools:
            settings["permissions"]["allow"].extend(
                ["Read(**/*.yaml)", "Write(**/*.yaml)", "Bash(kubectl:*)", "Bash(helm:*)"]
            )

        # Database permissions
        db_tools = ["PostgreSQL", "MongoDB", "MySQL", "Redis"]
        for db in db_tools:
            if db in config.frameworks:
                if db == "PostgreSQL":
                    settings["permissions"]["allow"].append("Bash(psql:*)")
                elif db == "MongoDB":
                    settings["permissions"]["allow"].append("Bash(mongosh:*)")
                elif db == "MySQL":
                    settings["permissions"]["allow"].append("Bash(mysql:*)")
                elif db == "Redis":
                    settings["permissions"]["allow"].append("Bash(redis-cli:*)")

        # Add general permissions
        settings["permissions"]["allow"].extend(
            [
                "Read(**/*)",
                "Write(**/*)",
                "Bash(ls:*)",
                "Bash(cat:*)",
                "Bash(grep:*)",
                "Bash(find:*)",
                "Bash(curl:*)",
                "Bash(wget:*)",
                "Bash(make:*)",
            ]
        )

        # Remove duplicates
        settings["permissions"]["allow"] = list(set(settings["permissions"]["allow"]))

        return settings

    def _generate_claude_md(self, config: ProjectConfig) -> str:
        """Generate optimized CLAUDE.md content."""
        sections = [
            f"# {config.project_type} Project",
            "",
            "## Project Overview",
            f"- **Primary Language**: {config.language}",
            f"- **Frameworks**: {', '.join(config.frameworks) if config.frameworks else 'None specified'}",
            f"- **Team Size**: {config.team_size}",
            f"- **Tools**: {', '.join(config.tools) if config.tools else 'Standard development tools'}",
            "",
            "## Development Focus",
            "",
        ]

        if config.needs:
            for need in config.needs:
                sections.append(f"- {need}")
            sections.append("")

        sections.extend(["## Coding Standards", ""])

        # Language-specific standards
        standards = self._get_language_standards(config.language)
        sections.extend(standards)

        sections.extend(
            [
                "",
                "## Project Structure",
                "",
                "```",
                ".",
                "├── .claude/          # Claude Code configuration",
                "│   ├── settings.json # Permissions and environment",
                "│   ├── commands/     # Custom slash commands",
                "│   └── agents/       # Specialized AI agents",
            ]
        )

        # Add language-specific structure
        if config.language == "Python":
            sections.extend(
                [
                    "├── src/              # Source code",
                    "├── tests/            # Test files",
                    "├── docs/             # Documentation",
                    "└── pyproject.toml    # Project configuration",
                ]
            )
        elif config.language == "JavaScript/TypeScript":
            sections.extend(
                [
                    "├── src/              # Source code",
                    "├── tests/            # Test files",
                    "├── public/           # Static assets",
                    "└── package.json      # Project configuration",
                ]
            )

        sections.extend(
            [
                "```",
                "",
                "## Available Commands",
                "",
                "Use `/help` to see all available commands. Key commands include:",
                "",
            ]
        )

        # List key commands based on needs
        if "Writing tests" in config.needs:
            sections.append("- `/test` - Run tests with coverage")
        if "Writing new features" in config.needs:
            sections.append("- `/plan` - Plan implementation approach")
        if "Code review" in config.needs:
            sections.append("- `/review` - Review recent changes")
        if "Documentation" in config.needs:
            sections.append("- `/docs` - Generate or update documentation")
        if "Performance optimization" in config.needs:
            sections.append("- `/optimize` - Analyze and optimize performance")

        sections.extend(
            [
                "",
                "## Workflow",
                "",
                "1. Use `/plan` before implementing features",
                "2. Write tests alongside code",
                "3. Run `/test` to verify changes",
                "4. Use `/review` for code review",
                "5. Document changes appropriately",
                "",
                "## Quick Start",
                "",
                "```bash",
                "# Start Claude Code",
                "claude",
                "",
                "# In Claude, run:",
                "/help  # See all commands",
                "/plan  # Plan your implementation",
                "/test  # Run tests",
                "```",
                "",
                "---",
                "*Configuration generated by claude-setup v1.0.0*",
            ]
        )

        return "\n".join(sections)

    def _generate_commands(self, config: ProjectConfig) -> dict[str, str]:
        """Generate project-specific commands."""
        commands = {}

        # Universal commands
        commands["help"] = """---
description: Show available commands and usage
---

# Available Commands

Show all available commands with descriptions and usage examples.

List all:
- Built-in Claude commands
- Project-specific commands
- Custom agent commands

Provide usage examples for common workflows."""

        commands["plan"] = """---
description: Plan implementation approach
argument-hint: [feature description]
---

Create a detailed implementation plan for: $ARGUMENTS

1. Analyze requirements and constraints
2. Identify affected files and components
3. Design solution architecture
4. List implementation steps in order
5. Identify potential issues and edge cases
6. Suggest tests needed
7. Estimate complexity and time"""

        commands["review"] = """---
description: Review recent code changes
---

Review recent code changes:

1. Check for bugs and logic errors
2. Verify coding standards compliance
3. Assess performance implications
4. Check test coverage
5. Identify security concerns
6. Suggest improvements
7. Validate documentation"""

        # Testing commands based on language
        if config.language == "Python":
            commands["test"] = """---
description: Run Python tests with coverage
argument-hint: [test file or pattern]
---

Run Python tests:

1. Execute pytest with coverage: `pytest --cov --cov-report=term-missing $ARGUMENTS`
2. Show test results with details
3. Highlight any failures or errors
4. Display coverage report
5. Identify untested code paths
6. Suggest additional test cases if coverage is low"""

        elif config.language == "JavaScript/TypeScript":
            if "Jest" in config.frameworks or "jest" in str(config.tools).lower():
                test_runner = "jest"
            elif "Vitest" in config.frameworks:
                test_runner = "vitest"
            else:
                test_runner = "npm test"

            commands["test"] = f"""---
description: Run JavaScript tests with coverage
argument-hint: [test file or pattern]
---

Run JavaScript tests:

1. Execute {test_runner} with coverage
2. Show test results with details
3. Highlight any failures or errors
4. Display coverage report
5. Identify untested code paths
6. Suggest additional test cases if coverage is low"""

        # Framework-specific commands
        if "React" in config.frameworks:
            commands["component"] = """---
description: Create React component
argument-hint: [component name]
---

Create a new React component: $ARGUMENTS

1. Generate component file with TypeScript interfaces
2. Create component implementation with hooks
3. Add prop types and default props
4. Create test file with initial tests
5. Add Storybook story if configured
6. Update barrel exports
7. Add to relevant module"""

        if "FastAPI" in config.frameworks:
            commands["endpoint"] = """---
description: Create API endpoint
argument-hint: [endpoint path and method]
---

Create new FastAPI endpoint: $ARGUMENTS

1. Define endpoint function with type hints
2. Add request/response Pydantic models
3. Implement business logic with error handling
4. Add input validation
5. Create comprehensive tests
6. Update OpenAPI documentation
7. Add to router if applicable"""

        if "Django" in config.frameworks:
            commands["model"] = """---
description: Create Django model
argument-hint: [model name]
---

Create new Django model: $ARGUMENTS

1. Define model class with fields
2. Add Meta options and methods
3. Create and run migrations
4. Add admin configuration
5. Create serializers if using DRF
6. Write model tests
7. Update documentation"""

        # Need-specific commands
        if "Documentation" in config.needs:
            commands["docs"] = """---
description: Generate or update documentation
argument-hint: [component or module]
---

Generate documentation for: $ARGUMENTS

1. Extract docstrings and type hints
2. Generate API documentation
3. Create usage examples
4. Update README if needed
5. Generate diagrams if applicable
6. Check for missing documentation
7. Validate links and references"""

        if "Performance optimization" in config.needs:
            commands["optimize"] = """---
description: Analyze and optimize performance
argument-hint: [module or function]
---

Optimize performance for: $ARGUMENTS

1. Profile current performance
2. Identify bottlenecks and hot paths
3. Analyze time and space complexity
4. Suggest algorithmic improvements
5. Implement optimizations
6. Measure performance impact
7. Document changes and trade-offs"""

        if "Security review" in config.needs:
            commands["security"] = """---
description: Security audit and review
---

Perform security review:

1. Check for common vulnerabilities (OWASP Top 10)
2. Audit dependencies for known CVEs
3. Review authentication and authorization
4. Check for sensitive data exposure
5. Validate input sanitization
6. Review cryptographic implementations
7. Generate security report"""

        # DevOps commands
        if "Docker" in config.tools:
            commands["docker"] = """---
description: Docker operations
argument-hint: [build|run|push]
---

Docker operations for: $ARGUMENTS

Handle Docker workflows including building images, running containers, and managing compose stacks."""

        if "CI/CD setup" in config.needs:
            commands["deploy"] = """---
description: Deployment operations
argument-hint: [environment]
---

Deploy to environment: $ARGUMENTS

1. Run pre-deployment checks
2. Execute tests
3. Build artifacts
4. Deploy to target environment
5. Run smoke tests
6. Monitor deployment
7. Rollback if needed"""

        return commands

    def _generate_agents(self, config: ProjectConfig) -> dict[str, str]:
        """Generate specialized agents."""
        agents = {}

        # Code reviewer agent
        agents["code-reviewer"] = f"""---
name: code-reviewer
description: Expert code review for {config.language}
tools: Read, Grep, Bash
---

You are an expert {config.language} code reviewer with deep knowledge of best practices, design patterns, and common pitfalls.

## Review Priorities

1. **Correctness**: Logic errors, bugs, edge cases
2. **Security**: Vulnerabilities, input validation, authentication
3. **Performance**: Time/space complexity, database queries, caching
4. **Maintainability**: Code clarity, modularity, documentation
5. **Standards**: Style guide compliance, naming conventions
6. **Testing**: Coverage, test quality, edge cases

## Language-Specific Focus

{self._get_language_review_focus(config.language)}

## Process

1. Analyze changes with git diff
2. Check against coding standards
3. Run static analysis tools
4. Identify potential issues
5. Suggest improvements with examples
6. Verify test coverage
7. Provide actionable feedback"""

        # Test engineer agent
        if "Writing tests" in config.needs:
            agents["test-engineer"] = f"""---
name: test-engineer
description: Test creation and validation specialist
tools: Read, Write, Edit, Bash
---

You are a test engineering specialist for {config.language} projects.

## Responsibilities

1. Write comprehensive unit tests
2. Create integration tests
3. Design end-to-end tests
4. Ensure edge case coverage
5. Maintain test documentation
6. Monitor coverage metrics
7. Optimize test performance

## Testing Framework

{self._get_test_framework_details(config)}

## Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths
- All edge cases tested
- Error conditions handled
- Performance benchmarks met

## Test Types

- Unit tests for individual functions
- Integration tests for components
- E2E tests for user flows
- Performance tests for bottlenecks
- Security tests for vulnerabilities"""

        # Performance analyst
        if "Performance optimization" in config.needs:
            agents["performance-analyst"] = """---
name: performance-analyst
description: Performance analysis and optimization expert
tools: Read, Write, Bash
---

You are a performance optimization specialist.

## Analysis Areas

1. **Algorithm Complexity**: Time and space analysis
2. **Database Performance**: Query optimization, indexing
3. **Network Optimization**: Request batching, caching
4. **Memory Management**: Leak detection, optimization
5. **Concurrency**: Parallelization, async operations

## Tools & Techniques

- Profilers for hotspot identification
- Benchmarking for measurements
- Load testing for scalability
- Memory analysis for leaks
- APM tools for monitoring

## Optimization Strategies

1. Algorithm improvements
2. Caching implementation
3. Database query optimization
4. Lazy loading and pagination
5. CDN and edge caching
6. Code splitting and bundling
7. Resource pooling"""

        # Architecture expert
        if config.team_size != "Solo" or "Architecture design" in config.needs:
            agents["architect"] = f"""---
name: architect
description: Software architecture and design expert
tools: Read, Write, Bash
---

You are a software architect specializing in {config.project_type} systems.

## Focus Areas

1. **System Design**: Scalable, maintainable architectures
2. **Design Patterns**: Apply appropriate patterns
3. **API Design**: RESTful, GraphQL, gRPC
4. **Data Modeling**: Database schema, relationships
5. **Security Architecture**: Defense in depth
6. **Performance Architecture**: Caching, scaling
7. **Integration Patterns**: Microservices, event-driven

## Architectural Principles

- SOLID principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple)
- YAGNI (You Aren't Gonna Need It)
- Separation of Concerns
- Single Source of Truth

## Deliverables

- Architecture diagrams
- Design documents
- API specifications
- Data models
- Security assessments
- Performance plans"""

        # Custom agents based on selections
        for agent_type in config.custom_agents:
            if agent_type == "Database Expert":
                agents["database-expert"] = self._generate_database_expert(config)
            elif agent_type == "Security Auditor":
                agents["security-auditor"] = self._generate_security_auditor(config)
            elif agent_type == "DevOps Engineer":
                agents["devops-engineer"] = self._generate_devops_engineer(config)

        # The master scaffolding agent
        agents["scaffolder"] = """---
name: scaffolder
description: Generate optimal Claude configurations for any project
tools: Read, Write, Bash
---

You are the Claude Configuration Scaffolder, an expert at analyzing projects and generating optimal Claude Code setups.

## Your Mission

Analyze the current project and generate the PERFECT Claude Code configuration.

## Analysis Process

### 1. Project Discovery

- Primary programming language(s)
- Frameworks and libraries
- Project structure and patterns
- Development tools and workflows
- Team size and collaboration needs

### 2. Configuration Generation

Based on analysis, create:

#### Settings.json
- Model selection based on complexity
- Granular permissions for safety
- Environment variables
- Tool allowlists

#### CLAUDE.md
- Project-specific context
- Coding standards
- Workflow documentation
- Architecture overview

#### Commands
- Language-specific utilities
- Framework generators
- Workflow automation
- Testing and deployment

#### Agents
- Domain experts
- Code reviewers
- Test engineers
- Performance specialists

## Quality Criteria

- Every configuration choice must be justified
- Security by default
- Optimized for the tech stack
- Follows best practices
- Enables efficient workflows

Remember: You're crafting a bespoke configuration that perfectly fits this project's needs!"""

        return agents

    def _generate_hooks(self, config: ProjectConfig) -> dict[str, Any]:
        """Generate hook configurations."""
        hooks = {}

        # Auto-format on save for Python
        if config.language == "Python":
            hooks["PostToolUse"] = [
                {
                    "matcher": "Write(*.py)|Edit(*.py)",
                    "hooks": [
                        {"type": "command", "command": "black --quiet $file || true"},
                        {"type": "command", "command": "ruff check --fix $file || true"},
                    ],
                }
            ]

        # Auto-format for JavaScript/TypeScript
        elif config.language == "JavaScript/TypeScript":
            hooks["PostToolUse"] = [
                {
                    "matcher": "Write(*.js|*.ts|*.jsx|*.tsx)|Edit(*.js|*.ts|*.jsx|*.tsx)",
                    "hooks": [
                        {"type": "command", "command": "prettier --write $file || true"},
                        {"type": "command", "command": "eslint --fix $file || true"},
                    ],
                }
            ]

        # Go formatting
        elif config.language == "Go":
            hooks["PostToolUse"] = [
                {
                    "matcher": "Write(*.go)|Edit(*.go)",
                    "hooks": [{"type": "command", "command": "gofmt -w $file"}],
                }
            ]

        # Rust formatting
        elif config.language == "Rust":
            hooks["PostToolUse"] = [
                {
                    "matcher": "Write(*.rs)|Edit(*.rs)",
                    "hooks": [{"type": "command", "command": "rustfmt $file"}],
                }
            ]

        # Git hooks
        if "Git" in config.tools:
            if "PreToolUse" not in hooks:
                hooks["PreToolUse"] = []

            hooks["PreToolUse"].append(
                {
                    "matcher": "Bash(git commit:*)",
                    "hooks": [
                        {"type": "command", "command": "echo 'Running pre-commit checks...'"}
                    ],
                }
            )

        return hooks

    def _generate_mcp_servers(self, config: ProjectConfig) -> list[dict[str, Any]]:
        """Generate MCP server configurations."""
        servers = []

        # GitHub MCP for projects using Git
        if "Git" in config.tools or "GitHub Actions" in config.tools:
            servers.append(
                {
                    "name": "github",
                    "description": "GitHub integration for issues, PRs, and workflows",
                    "config": {
                        "owner": "${GITHUB_OWNER}",
                        "repo": "${GITHUB_REPO}",
                        "token": "${GITHUB_TOKEN}",
                    },
                }
            )

        # Database MCP servers
        if "PostgreSQL" in config.frameworks:
            servers.append(
                {
                    "name": "postgres",
                    "description": "PostgreSQL database access",
                    "config": {"connection_string": "${DATABASE_URL}"},
                }
            )
        elif "MongoDB" in config.frameworks:
            servers.append(
                {
                    "name": "mongodb",
                    "description": "MongoDB database access",
                    "config": {"connection_string": "${MONGODB_URI}"},
                }
            )
        elif "MySQL" in config.frameworks:
            servers.append(
                {
                    "name": "mysql",
                    "description": "MySQL database access",
                    "config": {"connection_string": "${MYSQL_URL}"},
                }
            )

        # Communication tools for teams
        if config.team_size != "Solo":
            servers.append(
                {
                    "name": "slack",
                    "description": "Team communication via Slack",
                    "config": {"token": "${SLACK_TOKEN}", "channel": "${SLACK_DEFAULT_CHANNEL}"},
                }
            )

        # Cloud providers
        if "AWS" in str(config.tools) or "aws" in str(config.frameworks).lower():
            servers.append(
                {
                    "name": "aws",
                    "description": "AWS services integration",
                    "config": {"region": "${AWS_REGION}", "profile": "${AWS_PROFILE}"},
                }
            )

        return servers

    def _get_language_standards(self, language: str) -> list[str]:
        """Get language-specific coding standards."""
        standards = {
            "Python": [
                "- Follow PEP 8 style guide",
                "- Use type hints for all function signatures",
                "- Write docstrings for all public functions and classes",
                "- Prefer f-strings for string formatting",
                "- Use pathlib for file operations",
                "- Keep functions under 20 lines when possible",
                "- Use meaningful variable names",
            ],
            "JavaScript/TypeScript": [
                "- Use ES6+ syntax (const/let, arrow functions, destructuring)",
                "- Prefer const over let, never use var",
                "- Use async/await over promise chains",
                "- Follow Airbnb or Standard style guide",
                "- Use TypeScript strict mode",
                "- Avoid 'any' type in TypeScript",
                "- Keep components small and focused",
            ],
            "Go": [
                "- Follow Effective Go guidelines",
                "- Use gofmt for formatting",
                "- Handle all errors explicitly",
                "- Keep interfaces small",
                "- Use meaningful package names",
                "- Prefer composition over inheritance",
                "- Document exported functions",
            ],
            "Rust": [
                "- Follow Rust API guidelines",
                "- Use rustfmt for formatting",
                "- Prefer Result over panic",
                "- Use meaningful lifetime names",
                "- Keep unsafe blocks minimal",
                "- Document public APIs",
                "- Follow ownership principles",
            ],
        }

        return standards.get(
            language,
            [
                "- Follow language best practices",
                "- Write clean, readable code",
                "- Document complex logic",
                "- Keep functions focused",
                "- Use meaningful names",
            ],
        )

    def _get_language_review_focus(self, language: str) -> str:
        """Get language-specific review focus."""
        focus = {
            "Python": """- Type hints completeness and correctness
- Exception handling patterns
- Resource management (context managers)
- List comprehensions vs loops
- Generator usage for memory efficiency
- Proper use of decorators
- Module organization""",
            "JavaScript/TypeScript": """- Type safety and inference
- Promise handling and async patterns
- Memory leaks in closures
- Event listener cleanup
- Bundle size impact
- React hooks dependencies
- State management patterns""",
            "Go": """- Error handling completeness
- Goroutine leaks
- Channel usage patterns
- Interface design
- Package organization
- Mutex usage and deadlocks
- Context propagation""",
            "Rust": """- Lifetime correctness
- Ownership and borrowing
- Error handling with Result
- Unsafe block justification
- Trait implementation
- Memory safety
- Performance implications""",
        }

        return focus.get(
            language, "- Language-specific best practices\n- Common pitfalls and anti-patterns"
        )

    def _get_test_framework_details(self, config: ProjectConfig) -> str:
        """Get test framework details for the project."""
        if config.language == "Python":
            return """pytest with:
- Fixtures for test setup
- Parametrize for test cases
- Mock/patch for dependencies
- Coverage.py for metrics
- pytest-asyncio for async tests"""

        elif config.language == "JavaScript/TypeScript":
            if "Jest" in config.frameworks:
                return """Jest with:
- describe/it blocks
- beforeEach/afterEach hooks
- jest.mock for mocking
- expect assertions
- Coverage reports"""
            else:
                return """JavaScript testing with:
- Test runner (Jest/Vitest/Mocha)
- Assertion library
- Mocking capabilities
- Coverage tools"""

        elif config.language == "Go":
            return """Go testing with:
- testing package
- testify for assertions
- gomock for mocking
- benchmarks for performance
- coverage with go test -cover"""

        elif config.language == "Rust":
            return """Rust testing with:
- #[test] attributes
- assert macros
- mockall for mocking
- criterion for benchmarks
- cargo test with coverage"""

        return "Language-appropriate testing framework"

    def _generate_database_expert(self, config: ProjectConfig) -> str:
        """Generate database expert agent."""
        return """---
name: database-expert
description: Database design and optimization specialist
tools: Read, Write, Bash
---

You are a database expert specializing in design, optimization, and management.

## Expertise Areas

1. **Schema Design**: Normalization, relationships, constraints
2. **Query Optimization**: Indexes, execution plans, statistics
3. **Performance Tuning**: Configuration, caching, partitioning
4. **Data Migration**: Schema changes, data transformation
5. **Backup/Recovery**: Strategies, testing, automation
6. **Replication**: Master-slave, clustering, sharding
7. **Security**: Encryption, access control, auditing

## Best Practices

- Design for scalability
- Optimize for read/write patterns
- Implement proper indexing
- Use transactions appropriately
- Monitor performance metrics
- Plan for disaster recovery
- Document schema changes"""

    def _generate_security_auditor(self, config: ProjectConfig) -> str:
        """Generate security auditor agent."""
        return f"""---
name: security-auditor
description: Security analysis and vulnerability assessment
tools: Read, Grep, Bash
---

You are a security auditor specializing in {config.project_type} applications.

## Security Focus

1. **OWASP Top 10**: Common vulnerabilities
2. **Authentication**: OAuth, JWT, sessions
3. **Authorization**: RBAC, permissions
4. **Data Protection**: Encryption, hashing
5. **Input Validation**: Sanitization, escaping
6. **Dependencies**: CVE scanning, updates
7. **Secrets Management**: Environment variables, vaults

## Audit Process

1. Static code analysis
2. Dependency vulnerability scan
3. Configuration review
4. Authentication flow analysis
5. Data flow mapping
6. Penetration testing recommendations
7. Compliance verification

## Deliverables

- Security assessment report
- Vulnerability remediation plan
- Best practices guide
- Security checklist"""

    def _generate_devops_engineer(self, config: ProjectConfig) -> str:
        """Generate DevOps engineer agent."""
        return """---
name: devops-engineer
description: CI/CD, infrastructure, and deployment specialist
tools: Read, Write, Bash
---

You are a DevOps engineer specializing in automation and infrastructure.

## Expertise Areas

1. **CI/CD**: Pipeline design, automation
2. **Containerization**: Docker, Kubernetes
3. **Infrastructure as Code**: Terraform, CloudFormation
4. **Monitoring**: Metrics, logs, alerts
5. **Cloud Platforms**: AWS, GCP, Azure
6. **Configuration Management**: Ansible, Chef
7. **Security**: DevSecOps practices

## Responsibilities

- Design deployment pipelines
- Automate build processes
- Manage infrastructure
- Implement monitoring
- Optimize costs
- Ensure reliability
- Document procedures

## Best Practices

- GitOps workflows
- Blue-green deployments
- Canary releases
- Automated rollbacks
- Infrastructure testing
- Disaster recovery
- Cost optimization"""
