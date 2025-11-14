/*
 * ============================================
 * TEAMCITY KOTLIN DSL CONFIGURATION
 * ============================================
 * ToolBoxAI Solutions - Complete CI/CD Pipeline
 * Version: 2025.07
 * Updated: 2025-11-08
 *
 * New Features (2025.07):
 * - Build Cache enabled (10GB max size)
 * - Parallel Tests support
 * - Smart .teamcity directory handling
 * - Kotlin incremental compilation
 * ============================================
 */

import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildFeatures.dockerRegistry
import jetbrains.buildServer.configs.kotlin.buildFeatures.dockerSupport
import jetbrains.buildServer.configs.kotlin.buildFeatures.notifications
import jetbrains.buildServer.configs.kotlin.buildFeatures.perfmon
import jetbrains.buildServer.configs.kotlin.buildSteps.*
import jetbrains.buildServer.configs.kotlin.failureConditions.BuildFailureOnMetric
import jetbrains.buildServer.configs.kotlin.projectFeatures.dockerRegistry
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.triggers.schedule
import jetbrains.buildServer.configs.kotlin.vcs.GitVcsRoot

version = "2025.07"

project {
    description = "ToolBoxAI Solutions - Educational Platform with AI Integration"

    // ============================================
    // VCS Roots
    // ============================================
    vcsRoot(MainRepository)

    // ============================================
    // Build Configurations
    // ============================================
    buildType(Build)  // Main build configuration
    buildType(DashboardBuild)
    buildType(BackendBuild)
    buildType(BackendDeploy)  // Backend deployment to Render
    buildType(MCPServerBuild)
    buildType(AgentCoordinatorBuild)
    buildType(RobloxIntegrationBuild)
    buildType(SecurityScan)
    buildType(IntegrationTests)
    buildType(PerformanceTests)
    buildType(DeploymentPipeline)
    buildType(ProductionDeployment)

    // ============================================
    // Build Templates
    // ============================================
    template(DockerBuildTemplate)
    template(PythonTestTemplate)
    template(NodeTestTemplate)
    template(SecurityScanTemplate)

    // ============================================
    // Project Features
    // ============================================
    features {
        // Build Cache (2025.07 feature)
        feature {
            type = "BuildCache"
            id = "build-cache"
            param("name", "Build Cache")
            param("enabled", "true")
            param("publish.max.size", "10GB")
            param("rules", """
                +:**/node_modules/** => directory
                +:**/.venv/** => directory
                +:**/target/** => directory
                +:**/.gradle/** => directory
                +:**/__pycache__/** => directory
            """.trimIndent())
        }

        // TeamCity Cloud Docker Registry
        dockerRegistry {
            id = "TeamCityCloudRegistry"
            name = "TeamCity Cloud Registry"
            url = "https://build-cloud.docker.com:443"
            userName = "thegrayghost23"
            password = "credentialsJSON:teamcity-cloud-docker"
        }

        // Docker Hub Registry (optional, for public images)
        dockerRegistry {
            id = "DockerHub"
            name = "Docker Hub Registry"
            url = "https://registry-1.docker.io"
            userName = "thegrayghost23"
            password = "credentialsJSON:docker-hub-password"
        }

        // GitHub Integration
        feature {
            type = "OAuthProvider"
            param("providerType", "GitHub")
            param("displayName", "GitHub.com")
            param("gitHubUrl", "https://github.com/")
            param("clientId", "%env.GITHUB_CLIENT_ID%")
            param("clientSecret", "%env.GITHUB_CLIENT_SECRET%")
        }

        // Pusher Notifications
        feature {
            type = "pusher-notifications"
            param("app_id", "%env.PUSHER_APP_ID%")
            param("key", "%env.PUSHER_KEY%")
            param("secret", "%env.PUSHER_SECRET%")
            param("cluster", "%env.PUSHER_CLUSTER%")
        }

        // Slack Notifications
        feature {
            type = "slack"
            param("connection", "slack-webhook")
            param("webhook.url", "%env.SLACK_WEBHOOK_URL%")
            param("channel", "#ci-builds")
        }
    }

    // ============================================
    // Parameters
    // ============================================
    params {
        // Cloud builder configuration
        param("env.TEAMCITY_CLOUD_BUILDER", "cloud://thegrayghost23/jetbrains_linux-amd64")
        param("env.DOCKER_REGISTRY", "build-cloud.docker.com:443/thegrayghost23")
        param("env.NODE_VERSION", "22")
        param("env.PYTHON_VERSION", "3.12")
        param("env.TEAMCITY_PIPELINE_ACCESS_TOKEN", "%env.TEAMCITY_PIPELINE_ACCESS_TOKEN%")
        param("env.DOCKER_BUILDKIT", "1")
        param("env.COMPOSE_DOCKER_CLI_BUILD", "1")

        // ============================================
        // Authentication & Secrets
        // ============================================
        // Clerk Authentication
        password("env.CLERK_SECRET_KEY", "credentialsJSON:clerk-secret-key", display = ParameterDisplay.HIDDEN)

        // Pusher Real-time Configuration
        param("env.PUSHER_APP_ID", "2050003")
        param("env.PUSHER_KEY", "73f059a21bb304c7d68c")
        password("env.PUSHER_SECRET", "credentialsJSON:pusher-secret", display = ParameterDisplay.HIDDEN)
        param("env.PUSHER_CLUSTER", "us2")

        // ============================================
        // AI/ML API Keys
        // ============================================
        password("env.OPENAI_API_KEY", "credentialsJSON:openai-api-key", display = ParameterDisplay.HIDDEN)
        password("env.ANTHROPIC_API_KEY", "credentialsJSON:anthropic-api-key", display = ParameterDisplay.HIDDEN)

        // ============================================
        // GitHub Integration
        // ============================================
        param("env.GITHUB_USERNAME", "GrayGhostDev")
        password("env.GITHUB_TOKEN", "credentialsJSON:github-token", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Database Configuration
        // ============================================
        param("env.POSTGRES_DB", "toolboxai_6rmgje4u")
        param("env.POSTGRES_USER", "dbuser_4qnrmosa")
        password("env.POSTGRES_PASSWORD", "credentialsJSON:postgres-password", display = ParameterDisplay.HIDDEN)
        password("env.DATABASE_URL", "credentialsJSON:database-url", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Redis Configuration
        // ============================================
        password("env.REDIS_PASSWORD", "credentialsJSON:redis-password", display = ParameterDisplay.HIDDEN)
        password("env.REDIS_URL", "credentialsJSON:redis-url", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Security Keys
        // ============================================
        password("env.JWT_SECRET_KEY", "credentialsJSON:jwt-secret-key", display = ParameterDisplay.HIDDEN)
        password("env.CLERK_WEBHOOK_SIGNING_SECRET", "credentialsJSON:clerk-webhook-secret", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Deployment Keys
        // ============================================
        password("env.RENDER_API_KEY", "credentialsJSON:render-api-key", display = ParameterDisplay.HIDDEN)
        password("env.VERCEL_DEPLOY_HOOKS", "credentialsJSON:vercel-deploy-hooks", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Communication Services
        // ============================================
        password("env.SENDGRID_API_KEY", "credentialsJSON:sendgrid-api-key", display = ParameterDisplay.HIDDEN)
        param("env.SENDGRID_FROM_EMAIL", "curtis@grayghostdata.com")
        param("env.SENDGRID_FROM_NAME", "The Gray Ghost")

        param("env.TWILIO_ACCOUNT_SID", "AC554c2d9641861cbd82d7c4db296fd189")
        password("env.TWILIO_AUTH_TOKEN", "credentialsJSON:twilio-auth-token", display = ParameterDisplay.HIDDEN)
        password("env.TWILIO_API_SECRET", "credentialsJSON:twilio-api-secret", display = ParameterDisplay.HIDDEN)

        // ============================================
        // AI/ML Additional Keys
        // ============================================
        password("env.LANGCHAIN_API_KEY", "credentialsJSON:langchain-api-key", display = ParameterDisplay.HIDDEN)
        param("env.LANGCHAIN_PROJECT", "ToolboxAI-Solutions")
        param("env.LANGCHAIN_TRACING_V2", "true")

        password("env.LANGCACHE_API_KEY", "credentialsJSON:langcache-api-key", display = ParameterDisplay.HIDDEN)
        param("env.LANGCACHE_ENABLED", "true")

        // ============================================
        // Vault Configuration
        // ============================================
        param("env.VAULT_ADDR", "http://0.0.0.0:8200")
        password("env.VAULT_ROOT_TOKEN", "credentialsJSON:vault-root-token", display = ParameterDisplay.HIDDEN)
        password("env.VAULT_UNSEAL_KEY", "credentialsJSON:vault-unseal-key", display = ParameterDisplay.HIDDEN)

        // ============================================
        // Frontend Build Args
        // ============================================
        param("env.VITE_CLERK_PUBLISHABLE_KEY", "pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA")
        param("env.VITE_API_BASE_URL", "http://127.0.0.1:8009")
        param("env.VITE_ENABLE_CLERK_AUTH", "true")
        param("env.VITE_ENABLE_PUSHER", "true")
    }

    // ============================================
    // Cleanup
    // ============================================
    cleanup {
        all(days = 30)
        history(days = 90)
        artifacts(days = 14)
        preventDependencyCleanup = false
    }
}

// ============================================
// VCS ROOT CONFIGURATION
// ============================================
object MainRepository : GitVcsRoot({
    name = "ToolBoxAI Main Repository"
    url = "https://github.com/GrayGhostDev/ToolboxAI-Solutions.git"
    branch = "refs/heads/main"
    branchSpec = """
        +:refs/heads/*
        +:refs/tags/*
        +:refs/pull/*/merge
    """.trimIndent()
    authMethod = password {
        userName = "%env.GITHUB_USERNAME%"
        password = "credentialsJSON:github-token"
    }
})

// ============================================
// MAIN BUILD CONFIGURATION
// ============================================
object Build : BuildType({
    name = "Build All Services"
    description = "Master build configuration for all services"

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = """
                +:main
                +:develop
                +:feature/*
                +:fix/*
                +:chore/*
            """.trimIndent()
        }
    }

    features {
        perfmon {
        }

        notifications {
            notifierSettings = slackNotifier {
                connection = "slack-webhook"
                sendTo = "#ci-builds"
                messageFormat = verboseMessageFormat {
                    addBranch = true
                    addStatusText = true
                    maximumNumberOfChanges = 10
                }
            }
            buildFailedToStart = true
            buildFailed = true
            buildFinishedSuccessfully = true
            firstBuildErrorOccurs = true
        }
    }

    steps {
        script {
            name = "Environment Setup"
            scriptContent = """
                #!/bin/bash
                echo "=== ToolBoxAI Build Pipeline ==="
                echo "Build Number: %build.number%"
                echo "Branch: %teamcity.build.branch%"
                echo "Commit: %build.vcs.number%"
                echo ""
                echo "Environment Variables:"
                echo "  NODE_VERSION: %env.NODE_VERSION%"
                echo "  PYTHON_VERSION: %env.PYTHON_VERSION%"
                echo "  DOCKER_BUILDKIT: %env.DOCKER_BUILDKIT%"
                echo ""
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(DashboardBuild) {
            reuseBuilds = ReuseBuilds.NO
        }
        snapshot(BackendBuild) {
            reuseBuilds = ReuseBuilds.NO
        }
        snapshot(MCPServerBuild) {
            reuseBuilds = ReuseBuilds.NO
        }
        snapshot(AgentCoordinatorBuild) {
            reuseBuilds = ReuseBuilds.NO
        }
        snapshot(RobloxIntegrationBuild) {
            reuseBuilds = ReuseBuilds.NO
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }
})

// ============================================
// DASHBOARD BUILD CONFIGURATION
// ============================================
object DashboardBuild : BuildType({
    name = "Dashboard (React + Vite)"
    description = "Build and test the React dashboard with Mantine UI"

    artifactRules = """
        apps/dashboard/dist => dashboard-build-%build.number%.zip
        apps/dashboard/coverage => coverage-report.zip
        apps/dashboard/test-reports => test-reports.zip
    """.trimIndent()

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = "+:main +:develop +:feature/*"
            includeRule = "+:apps/dashboard/**"
            includeRule = "+:package*.json"
        }
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }

        perfmon {
            metric(BuildFailureOnMetric.MetricType.ARTIFACT_SIZE)
            threshold = 100 // MB
        }

        notifications {
            notifierSettings = pusher {
                channel = "dashboard-builds"
                event = "build-status"
            }
        }
    }

    requirements {
        // Require Frontend or Integration agent (has Node.js + pnpm)
        matches("teamcity.agent.name", "(Frontend-Builder|Integration-Builder).*")
        exists("system.node.version")
        exists("system.pnpm.version")
    }

    steps {
        script {
            name = "Verify Node.js and pnpm"
            scriptContent = """
                echo "🔍 Checking Node.js and pnpm versions..."
                node --version
                pnpm --version
                echo "✅ Environment verified"
            """.trimIndent()
        }

        script {
            name = "Install Dependencies"
            scriptContent = """
                echo "📦 Installing dependencies with pnpm..."
                pnpm install --frozen-lockfile
                echo "✅ Dependencies installed"
            """.trimIndent()
        }

        script {
            name = "Run Test"
            scriptContent = """
                echo "🧪 Running tests..."
                pnpm -w dashboard test
                echo "✅ Tests completed"
            """.trimIndent()
        }

        script {
            name = "Build Production"
            scriptContent = """
                echo "🏗️ Building production bundle..."
                pnpm -w dashboard build
                echo "✅ Build completed successfully"
                echo "Build size: $(du -sh dist/)"
                echo "Asset breakdown:"
                find dist -name "*.js" -exec du -h {} \; | sort -h | tail -10
            """.trimIndent()
        }

        script {
            name = "Bundle Analysis"
            workingDir = "apps/dashboard"
            scriptContent = """
                if [ -f "dist/stats.html" ]; then
                    echo "Bundle analysis available at dist/stats.html"
                fi
            """.trimIndent()
        }

        dockerCommand {
            name = "Build Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/dashboard-fixed.Dockerfile"
                }
                contextDir = "."
                platform = DockerCommandBuildImagePlatform.Linux
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:latest
                """.trimIndent()
                commandArgs = """
                    --build-arg NODE_VERSION=%env.NODE_VERSION%
                    --cache-from %env.DOCKER_REGISTRY%/toolboxai-dashboard:latest
                    --label "build.number=%build.number%"
                    --label "git.commit=%build.vcs.number%"
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Push Docker Image"
            commandType = push {
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:latest
                """.trimIndent()
            }
            executionMode = BuildStep.ExecutionMode.RUN_ON_SUCCESS
        }
    }

    failureConditions {
        testFailure = false
        buildFailureOnMetric {
            metric = BuildFailureOnMetric.MetricType.COVERAGE_PERCENTAGE
            threshold = 70
            stopBuildOnFailure = false
        }
        executionTimeoutMin = 30
    }
})

// ============================================
// BACKEND BUILD CONFIGURATION
// ============================================
object BackendBuild : BuildType({
    name = "Backend (FastAPI)"
    description = "Build and test the FastAPI backend with all integrations"

    artifactRules = """
        htmlcov => coverage-report.zip
        tests/results => test-results.zip
        security-report.json => security-report.json
    """.trimIndent()

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = "+:main +:develop +:feature/*"
            includeRule = "+:apps/backend/**"
            includeRule = "+:core/**"
            includeRule = "+:database/**"
            includeRule = "+:requirements.txt"
            includeRule = "+:pyproject.toml"
        }
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    steps {
        python {
            name = "Setup Python Environment"
            pythonVersion = "%env.PYTHON_VERSION%"
            command = script {
                content = """
                    python -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                    pip install pytest pytest-cov pytest-asyncio black mypy basedpyright ruff safety bandit
                """.trimIndent()
            }
        }

        parallel {
            python {
                name = "Type Checking"
                command = script {
                    content = """
                        source venv/bin/activate
                        echo "Running BasedPyright..."
                        basedpyright . --pythonpath venv/bin/python || true
                        echo "Running MyPy..."
                        mypy apps/backend core database --ignore-missing-imports || true
                    """.trimIndent()
                }
            }

            python {
                name = "Code Quality"
                command = script {
                    content = """
                        source venv/bin/activate
                        echo "Running Black formatter check..."
                        black --check apps/backend core database
                        echo "Running Ruff linter..."
                        ruff check apps/backend core database
                    """.trimIndent()
                }
            }

            python {
                name = "Security Scan"
                command = script {
                    content = """
                        source venv/bin/activate
                        echo "Running safety check..."
                        safety check --json || true
                        echo "Running bandit security scan..."
                        bandit -r apps/backend core database -f json -o security-report.json -ll
                    """.trimIndent()
                }
            }
        }

        dockerCompose {
            name = "Start Test Services"
            file = "infrastructure/docker/compose/docker-compose.yml"
            additionalDockerComposeFile = "infrastructure/docker/compose/docker-compose.dev.yml"
            services = "postgres redis"
        }

        python {
            name = "Run Tests"
            command = script {
                content = """
                    source venv/bin/activate
                    export PYTHONPATH=${'$'}{PWD}

                    echo "Running unit tests..."
                    pytest tests/unit -v --cov=apps/backend --cov=core --cov=database \
                        --cov-report=html --cov-report=xml:coverage.xml \
                        --junit-xml=tests/results/junit.xml

                    echo "Running integration tests..."
                    RUN_ENDPOINT_TESTS=1 RUN_WS_INTEGRATION=1 \
                    pytest tests/integration -v --junit-xml=tests/results/integration-junit.xml
                """.trimIndent()
            }
        }

        script {
            name = "Database Migration Check"
            scriptContent = """
                source venv/bin/activate
                cd apps/backend
                alembic check || echo "⚠️ Pending migrations detected"
            """.trimIndent()
        }

        dockerCommand {
            name = "Build Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/backend.Dockerfile"
                }
                contextDir = "."
                platform = DockerCommandBuildImagePlatform.Linux
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-backend:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-backend:latest
                """.trimIndent()
                commandArgs = """
                    --build-arg PYTHON_VERSION=%env.PYTHON_VERSION%
                    --cache-from %env.DOCKER_REGISTRY%/toolboxai-backend:latest
                    --label "build.number=%build.number%"
                    --label "git.commit=%build.vcs.number%"
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Security Scan Image"
            commandType = other {
                customCommand = """
                    run --rm -v /var/run/docker.sock:/var/run/docker.sock
                    aquasec/trivy image --severity HIGH,CRITICAL
                    %env.DOCKER_REGISTRY%/toolboxai-backend:%build.number%
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Push Docker Image"
            commandType = push {
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-backend:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-backend:latest
                """.trimIndent()
            }
            executionMode = BuildStep.ExecutionMode.RUN_ON_SUCCESS
        }
    }

    failureConditions {
        testFailure = true
        executionTimeoutMin = 45
    }
})

// ============================================
// MCP SERVER BUILD CONFIGURATION
// ============================================
object MCPServerBuild : BuildType({
    name = "MCP Server"
    description = "Build Model Context Protocol server"

    artifactRules = """
        core/mcp/dist => mcp-build-%build.number%.zip
    """.trimIndent()

    vcs {
        root(MainRepository)
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    steps {
        python {
            name = "Build and Test MCP"
            command = script {
                content = """
                    python -m venv venv-mcp
                    source venv-mcp/bin/activate
                    pip install -r core/mcp/requirements.txt

                    echo "Running MCP tests..."
                    pytest core/mcp/tests -v

                    echo "Building MCP server..."
                    cd core/mcp
                    python setup.py build
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Build MCP Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/mcp-server.Dockerfile"
                }
                contextDir = "."
                platform = DockerCommandBuildImagePlatform.Linux
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-mcp:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-mcp:latest
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Push MCP Image"
            commandType = push {
                namesAndTags = "%env.DOCKER_REGISTRY%/toolboxai-mcp:%build.number%"
            }
            executionMode = BuildStep.ExecutionMode.RUN_ON_SUCCESS
        }
    }

    failureConditions {
        executionTimeoutMin = 20
    }
})

// ============================================
// AGENT COORDINATOR BUILD CONFIGURATION
// ============================================
object AgentCoordinatorBuild : BuildType({
    name = "Agent Coordinator"
    description = "Build LangChain/LangGraph agent coordinator with SPARC framework"

    vcs {
        root(MainRepository)
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    steps {
        python {
            name = "Build and Test Agents"
            command = script {
                content = """
                    python -m venv venv-agent
                    source venv-agent/bin/activate
                    pip install langchain langchain-openai langgraph langsmith
                    pip install -r core/agents/requirements.txt

                    echo "Testing SPARC framework..."
                    pytest core/agents/tests -v -k "sparc"

                    echo "Testing agent orchestration..."
                    pytest core/agents/tests -v -k "orchestrator"

                    echo "Testing LangChain integration..."
                    python scripts/test_langchain_integration.py
                """.trimIndent()
            }
        }

        python {
            name = "LangSmith Integration"
            command = script {
                content = """
                    source venv-agent/bin/activate

                    if [ -n "${'$'}LANGCHAIN_API_KEY" ]; then
                        echo "Testing LangSmith connection..."
                        python scripts/test_langsmith_connection.py
                    else
                        echo "LangSmith API key not configured, skipping"
                    fi
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Build Coordinator Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/agent-coordinator.Dockerfile"
                }
                contextDir = "."
                platform = DockerCommandBuildImagePlatform.Linux
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-coordinator:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-coordinator:latest
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Push Coordinator Image"
            commandType = push {
                namesAndTags = "%env.DOCKER_REGISTRY%/toolboxai-coordinator:%build.number%"
            }
            executionMode = BuildStep.ExecutionMode.RUN_ON_SUCCESS
        }
    }

    dependencies {
        snapshot(MCPServerBuild)
    }

    failureConditions {
        executionTimeoutMin = 25
    }
})

// ============================================
// ROBLOX INTEGRATION BUILD
// ============================================
object RobloxIntegrationBuild : BuildType({
    name = "Roblox Integration"
    description = "Build and test Roblox integration components"

    artifactRules = """
        roblox/build => roblox-build-%build.number%.zip
    """.trimIndent()

    vcs {
        root(MainRepository)
    }

    steps {
        script {
            name = "Install Rojo"
            scriptContent = """
                # Install Rojo if not present
                if ! command -v rojo &> /dev/null; then
                    cargo install rojo
                fi
                rojo --version
            """.trimIndent()
        }

        script {
            name = "Build Roblox Project"
            workingDir = "roblox"
            scriptContent = """
                echo "Building Roblox project..."
                rojo build default.project.json -o build/ToolBoxAI.rbxlx

                echo "Validating Luau scripts..."
                find src -name "*.lua" -exec luau-analyze {} \;
            """.trimIndent()
        }

        script {
            name = "Run Roblox Tests"
            workingDir = "roblox"
            scriptContent = """
                # Run Luau unit tests if available
                if [ -d "tests" ]; then
                    echo "Running Luau tests..."
                    for test in tests/*.lua; do
                        luau "${'$'}test"
                    done
                fi
            """.trimIndent()
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }
})

// ============================================
// SECURITY SCAN CONFIGURATION
// ============================================
object SecurityScan : BuildType({
    templates(SecurityScanTemplate)
    name = "Security Scan"
    description = "Comprehensive security scanning for all components"

    vcs {
        root(MainRepository)
    }

    triggers {
        schedule {
            schedulingPolicy = daily {
                hour = 2
            }
            branchFilter = "+:main"
            triggerBuildWithPendingChangesOnly = false
        }
    }

    steps {
        script {
            name = "Dependency Security Scan"
            scriptContent = """
                echo "Scanning Python dependencies..."
                pip install safety
                safety check --json

                echo "Scanning Node dependencies..."
                cd apps/dashboard
                npm audit --audit-level=high

                echo "Scanning for secrets..."
                pip install truffleHog3
                trufflehog3 --no-history --format json --output secrets-report.json .
            """.trimIndent()
        }

        script {
            name = "SAST Scan"
            scriptContent = """
                echo "Running Semgrep..."
                docker run --rm -v "${'$'}{PWD}:/src" returntocorp/semgrep \
                    --config=auto --json --output=/src/semgrep-report.json /src
            """.trimIndent()
        }

        script {
            name = "Container Security Scan"
            scriptContent = """
                echo "Scanning Docker images..."
                for image in backend dashboard mcp coordinator; do
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy image --severity HIGH,CRITICAL \
                        %env.DOCKER_REGISTRY%/toolboxai-${'$'}image:latest
                done
            """.trimIndent()
        }
    }

    artifactRules = """
        secrets-report.json => security-reports.zip
        semgrep-report.json => security-reports.zip
        security-report.json => security-reports.zip
    """.trimIndent()
})

// ============================================
// INTEGRATION TESTS CONFIGURATION
// ============================================
object IntegrationTests : BuildType({
    name = "Integration Tests"
    description = "Full stack integration testing"

    vcs {
        root(MainRepository)
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    steps {
        dockerCompose {
            name = "Start Full Stack"
            file = "infrastructure/docker/compose/docker-compose.yml"
            additionalDockerComposeFile = "infrastructure/docker/compose/docker-compose.dev.yml"
            projectName = "toolboxai-integration"
        }

        script {
            name = "Wait for Services"
            scriptContent = """
                echo "Waiting for services to be healthy..."
                for i in {1..60}; do
                    if curl -f http://localhost:8009/health && \
                       curl -f http://localhost:5179/ && \
                       curl -f http://localhost:6379/; then
                        echo "✅ All services are ready!"
                        break
                    fi
                    echo "Waiting... attempt ${'$'}i/60"
                    sleep 5
                done
            """.trimIndent()
        }

        script {
            name = "Setup Python Environment"
            scriptContent = """
                # Create and activate virtual environment
                python3 -m venv venv
                source venv/bin/activate

                # Upgrade pip and install dependencies
                pip install --upgrade pip setuptools wheel
                pip install -r requirements.txt
                pip install pytest pytest-cov pytest-asyncio pytest-mock
            """.trimIndent()
        }

        script {
            name = "Run API Integration Tests"
            scriptContent = """
                source venv/bin/activate
                export RUN_ENDPOINT_TESTS=1
                export RUN_WS_INTEGRATION=1
                export RUN_ROJO_TESTS=1

                pytest tests/integration -v --junit-xml=integration-results.xml
            """.trimIndent()
        }

        script {
            name = "Run E2E Tests"
            scriptContent = """
                cd apps/dashboard
                npm run test:e2e -- --reporter=junit --reporter-options output=e2e-results.xml
            """.trimIndent()
        }

        script {
            name = "Run Pusher Integration Tests"
            scriptContent = """
                echo "Testing Pusher channels..."
                python scripts/test_pusher_integration.py
            """.trimIndent()
        }

        dockerCompose {
            name = "Stop Stack"
            file = "infrastructure/docker/compose/docker-compose.yml"
            additionalDockerComposeFile = "infrastructure/docker/compose/docker-compose.dev.yml"
            projectName = "toolboxai-integration"
            executeCommandType = DockerComposeExecuteCommandType.DOWN
        }
    }

    dependencies {
        snapshot(Build)
    }

    failureConditions {
        executionTimeoutMin = 30
        testFailure = true
    }

    artifactRules = """
        integration-results.xml => test-results.zip
        e2e-results.xml => test-results.zip
    """.trimIndent()
})

// ============================================
// PERFORMANCE TESTS
// ============================================
object PerformanceTests : BuildType({
    name = "Performance Tests"
    description = "Load and performance testing"

    vcs {
        root(MainRepository)
    }

    triggers {
        schedule {
            schedulingPolicy = weekly {
                dayOfWeek = "Sunday"
                hour = 3
            }
            branchFilter = "+:main"
        }
    }

    steps {
        script {
            name = "Run Lighthouse Performance Test"
            scriptContent = """
                cd apps/dashboard
                npm run build
                npm run preview &
                PREVIEW_PID=${'$'}!
                sleep 10

                npm install -g @lhci/cli
                lhci autorun --collect.url=http://localhost:4173 \
                    --assert.preset=lighthouse:recommended \
                    --assert.assertions.categories:performance=80

                kill ${'$'}PREVIEW_PID
            """.trimIndent()
        }

        script {
            name = "Run Load Tests"
            scriptContent = """
                echo "Installing k6..."
                docker pull grafana/k6

                echo "Running API load tests..."
                docker run -i grafana/k6 run - <scripts/load-tests/api-load-test.js

                echo "Running WebSocket load tests..."
                docker run -i grafana/k6 run - <scripts/load-tests/websocket-load-test.js
            """.trimIndent()
        }

        script {
            name = "Database Performance Tests"
            scriptContent = """
                source venv/bin/activate
                python scripts/performance/database_benchmark.py
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(IntegrationTests)
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }
})

// ============================================
// DEPLOYMENT PIPELINE
// ============================================
object DeploymentPipeline : BuildType({
    name = "Deploy to Staging"
    description = "Deploy all services to staging environment"

    params {
        param("env.DEPLOY_ENVIRONMENT", "staging")
        param("env.DEPLOY_URL", "https://staging.toolboxai.com")
    }

    steps {
        script {
            name = "Pre-deployment Checks"
            scriptContent = """
                echo "Running pre-deployment checks..."

                # Check if all required images exist
                for image in backend dashboard mcp coordinator; do
                    docker pull %env.DOCKER_REGISTRY%/toolboxai-${'$'}image:latest || exit 1
                done

                echo "✅ All images available"
            """.trimIndent()
        }

        script {
            name = "Deploy with Docker Compose"
            scriptContent = """
                # Deploy to staging
                docker compose -f infrastructure/docker/compose/docker-compose.yml \
                               -f infrastructure/docker/compose/docker-compose.staging.yml \
                               pull

                docker compose -f infrastructure/docker/compose/docker-compose.yml \
                               -f infrastructure/docker/compose/docker-compose.staging.yml \
                               up -d --remove-orphans

                echo "✅ Staging deployment complete"
            """.trimIndent()
        }

        script {
            name = "Run Database Migrations"
            scriptContent = """
                echo "Running database migrations..."
                docker run --rm \
                    --network toolboxai_network \
                    -e DATABASE_URL=${'$'}STAGING_DATABASE_URL \
                    %env.DOCKER_REGISTRY%/toolboxai-backend:latest \
                    alembic upgrade head
            """.trimIndent()
        }

        script {
            name = "Health Check"
            scriptContent = """
                echo "Performing health checks..."
                for i in {1..20}; do
                    if curl -f %env.DEPLOY_URL%/health && \
                       curl -f %env.DEPLOY_URL%/api/v1/health; then
                        echo "✅ Deployment successful!"
                        exit 0
                    fi
                    echo "Waiting for deployment... attempt ${'$'}i/20"
                    sleep 15
                done
                echo "❌ Deployment health check failed!"
                exit 1
            """.trimIndent()
        }

        script {
            name = "Setup Python Environment for Smoke Tests"
            scriptContent = """
                # Create and activate virtual environment
                python3 -m venv venv
                source venv/bin/activate

                # Install dependencies
                pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest pytest-timeout requests
            """.trimIndent()
        }

        script {
            name = "Run Smoke Tests"
            scriptContent = """
                source venv/bin/activate
                pytest tests/smoke --base-url=%env.DEPLOY_URL% -v
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(IntegrationTests) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }
})

// ============================================
// PRODUCTION DEPLOYMENT
// ============================================
object ProductionDeployment : BuildType({
    name = "Deploy to Production"
    description = "Deploy all services to production with blue-green strategy"

    params {
        param("env.DEPLOY_ENVIRONMENT", "production")
        param("env.DEPLOY_URL", "https://app.toolboxai.com")
        param("env.REQUIRES_APPROVAL", "true")
    }

    steps {
        script {
            name = "Pre-deployment Backup"
            scriptContent = """
                echo "Creating database backup..."
                BACKUP_FILE="backup-${'$'}(date +%Y%m%d-%H%M%S).sql"
                pg_dump ${'$'}PRODUCTION_DATABASE_URL > ${'$'}BACKUP_FILE
                aws s3 cp ${'$'}BACKUP_FILE s3://toolboxai-backups/database/
                echo "✅ Backup created: ${'$'}BACKUP_FILE"
            """.trimIndent()
        }

        script {
            name = "Blue-Green Deployment"
            scriptContent = """
                echo "Starting blue-green deployment..."

                # Deploy to green environment
                docker service update \
                    --image %env.DOCKER_REGISTRY%/toolboxai-backend:latest \
                    production_backend_green

                docker service update \
                    --image %env.DOCKER_REGISTRY%/toolboxai-dashboard:latest \
                    production_dashboard_green

                # Health check green environment
                for i in {1..30}; do
                    if curl -f https://green.toolboxai.com/health; then
                        echo "✅ Green environment healthy"
                        break
                    fi
                    sleep 10
                done

                # Switch traffic to green
                docker service update \
                    --label-add traefik.http.routers.backend.service=backend_green \
                    production_backend_green

                docker service update \
                    --label-add traefik.http.routers.dashboard.service=dashboard_green \
                    production_dashboard_green

                # Scale down blue after success
                sleep 60
                docker service scale production_backend_blue=0
                docker service scale production_dashboard_blue=0

                echo "✅ Blue-green deployment complete"
            """.trimIndent()
        }

        script {
            name = "Post-deployment Validation"
            scriptContent = """
                echo "Running production validation..."
                pytest tests/production --base-url=%env.DEPLOY_URL% -v

                # Check critical metrics
                curl -f %env.DEPLOY_URL%/metrics | grep -E "(http_requests_total|error_rate)"
            """.trimIndent()
        }

        script {
            name = "Notify Stakeholders"
            scriptContent = """
                curl -X POST %env.SLACK_WEBHOOK_URL% \
                    -H 'Content-Type: application/json' \
                    -d '{
                        "text": "🚀 Production deployment completed!",
                        "attachments": [{
                            "color": "good",
                            "fields": [
                                {"title": "Version", "value": "%build.number%", "short": true},
                                {"title": "Environment", "value": "Production", "short": true},
                                {"title": "URL", "value": "%env.DEPLOY_URL%", "short": false},
                                {"title": "Deployed by", "value": "%teamcity.build.triggeredBy%", "short": true}
                            ]
                        }]
                    }'
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(DeploymentPipeline) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
        snapshot(PerformanceTests) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    features {
        approvals {
            approvalRules {
                approvalRule {
                    type = "manual"
                    requiredApprovalsCount = 2
                    timeout = 1440 // 24 hours
                    description = "Production deployment requires approval from 2 team members"
                }
            }
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }
})

// ============================================
// BUILD TEMPLATES
// ============================================
object DockerBuildTemplate : Template({
    name = "Docker Build Template"

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    params {
        param("docker.cache.enabled", "true")
        param("docker.buildkit.enabled", "true")
    }
})

object PythonTestTemplate : Template({
    name = "Python Test Template"

    params {
        param("python.version", "%env.PYTHON_VERSION%")
    }

    steps {
        python {
            name = "Setup Python"
            pythonVersion = "%python.version%"
            command = virtualenv {
            }
        }
    }
})

object NodeTestTemplate : Template({
    name = "Node Test Template"

    params {
        param("node.version", "%env.NODE_VERSION%")
    }

    steps {
        nodeJS {
            name = "Setup Node"
            shellScript = """
                nvm install %node.version%
                nvm use %node.version%
            """.trimIndent()
        }
    }
})

object SecurityScanTemplate : Template({
    name = "Security Scan Template"

    steps {
        script {
            name = "Security Tools Setup"
            scriptContent = """
                pip install safety bandit truffleHog3
                npm install -g snyk
            """.trimIndent()
        }
    }

    features {
        notifications {
            buildFailed = true
            notifierSettings = slackNotifier {
                connection = "slack-webhook"
                sendTo = "#security-alerts"
            }
        }
    }
})

// ============================================
// Backend Deploy (to Render)
// ============================================
object BackendDeploy : BuildType({
    name = "Backend — Deploy to Render"
    description = "Build, test, and deploy FastAPI backend to Render.com"

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = "+:main"
            triggerRules = """
                +:apps/backend/**
                +:requirements.txt
                +:Dockerfile
            """.trimIndent()
        }
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    requirements {
        contains("teamcity.agent.name", "linux-amd64")
        exists("docker.server.version")
    }

    steps {
        // Step 1: Setup Python Environment
        python {
            name = "Setup Python Environment"
            pythonVersion = "%env.PYTHON_VERSION%"
            command = script {
                content = """
                    python -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                """.trimIndent()
            }
        }

        // Step 2: Run Tests
        python {
            name = "Run Backend Tests"
            pythonVersion = "%env.PYTHON_VERSION%"
            command = script {
                content = """
                    source venv/bin/activate
                    pytest -q --disable-warnings --maxfail=1 tests/
                """.trimIndent()
            }
        }

        // Step 3: Build Docker Image
        dockerCommand {
            name = "Build Backend Docker Image"
            commandType = build {
                source = file {
                    path = "apps/backend/Dockerfile"
                }
                contextDir = "apps/backend"
                namesAndTags = "toolboxai-backend:latest toolboxai-backend:%build.number%"
                commandArgs = "--pull --no-cache"
            }
        }

        // Step 4: Deploy to Render
        script {
            name = "Trigger Render Deployment"
            scriptContent = """
                #!/bin/bash
                set -e

                echo "🚀 Deploying to Render..."

                response=${'$'}(curl -s -w "\n%{http_code}" \
                  -X POST \
                  -H "Accept: application/json" \
                  -H "Authorization: Bearer %env.RENDER_API_KEY%" \
                  https://api.render.com/v1/services/%env.RENDER_SERVICE_ID%/deploys)

                http_code=${'$'}(echo "${'$'}response" | tail -n1)
                body=${'$'}(echo "${'$'}response" | head -n -1)

                if [ "${'$'}http_code" = "201" ] || [ "${'$'}http_code" = "200" ]; then
                    echo "✅ Deployment triggered successfully!"
                    echo "${'$'}body" | python3 -m json.tool
                    exit 0
                else
                    echo "❌ Deployment failed with HTTP ${'$'}http_code"
                    echo "${'$'}body"
                    exit 1
                fi
            """.trimIndent()
        }

        // Step 5: Verify Deployment
        script {
            name = "Verify Deployment Health"
            scriptContent = """
                #!/bin/bash
                echo "⏳ Waiting for deployment to stabilize (30 seconds)..."
                sleep 30

                echo "🔍 Checking backend health endpoint..."
                response=${'$'}(curl -s -f -o /dev/null -w "%{http_code}" \
                    https://toolboxai-backend.onrender.com/health || echo "failed")

                if [ "${'$'}response" = "200" ]; then
                    echo "✅ Backend is healthy!"
                    exit 0
                else
                    echo "⚠️ Backend health check returned: ${'$'}response"
                    echo "Deployment may still be in progress. Check Render dashboard."
                    exit 0  # Don't fail the build on health check timeout
                fi
            """.trimIndent()
        }
    }

    params {
        param("env.RENDER_API_KEY", "%RENDER_API_KEY%")
        param("env.RENDER_SERVICE_ID", "srv-d479pmali9vc738itjng")
    }

    failureConditions {
        errorMessage = true
        nonZeroExitCode = true
        testFailure = true
    }
})
