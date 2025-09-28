/*
 * ============================================
 * TEAMCITY KOTLIN DSL CONFIGURATION
 * ============================================
 * ToolBoxAI Solutions - Complete CI/CD Pipeline
 * Version: 2025.03
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
import jetbrains.buildServer.configs.kotlin.vcs.GitVcsRoot

version = "2025.03"

project {
    description = "ToolBoxAI Solutions - Educational Platform with AI Integration"

    // ============================================
    // VCS Roots
    // ============================================
    vcsRoot(MainRepository)

    // ============================================
    // Build Configurations
    // ============================================
    buildType(DashboardBuild)
    buildType(BackendBuild)
    buildType(MCPServerBuild)
    buildType(AgentCoordinatorBuild)
    buildType(IntegrationTests)
    buildType(DeploymentPipeline)

    // ============================================
    // Build Templates
    // ============================================
    template(DockerBuildTemplate)
    template(PythonTestTemplate)
    template(NodeTestTemplate)

    // ============================================
    // Project Features
    // ============================================
    features {
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

        feature {
            type = "pusher-notifications"
            param("app_id", "%env.PUSHER_APP_ID%")
            param("key", "%env.PUSHER_KEY%")
            param("secret", "%env.PUSHER_SECRET%")
            param("cluster", "%env.PUSHER_CLUSTER%")
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
    url = "https://github.com/ToolBoxAI-Solutions/toolboxai.git"
    branch = "refs/heads/main"
    branchSpec = """
        +:refs/heads/*
        +:refs/tags/*
        +:refs/pull/*/head
    """.trimIndent()
    authMethod = uploadedKey {
        uploadedKey = "GitHub Deploy Key"
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

    // Use TeamCity Cloud builder
    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    steps {
        nodeJS {
            name = "Setup Node.js"
            shellScript = """
                nvm install %env.NODE_VERSION%
                nvm use %env.NODE_VERSION%
                node --version
                npm --version
            """.trimIndent()
        }

        script {
            name = "Install Dependencies"
            workingDir = "apps/dashboard"
            scriptContent = """
                npm ci --legacy-peer-deps
                echo "✅ Dependencies installed"
            """.trimIndent()
        }

        parallel {
            script {
                name = "TypeScript Check"
                workingDir = "apps/dashboard"
                scriptContent = "npm run typecheck"
            }

            script {
                name = "Lint Check"
                workingDir = "apps/dashboard"
                scriptContent = "npm run lint"
            }

            script {
                name = "Unit Tests"
                workingDir = "apps/dashboard"
                scriptContent = "npm test -- --run --coverage"
            }
        }

        script {
            name = "Build Production"
            workingDir = "apps/dashboard"
            scriptContent = """
                npm run build
                echo "Build size: $(du -sh dist/)"
            """.trimIndent()
        }

        dockerCommand {
            name = "Build Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/dashboard-fixed.Dockerfile"
                }
                contextDir = "."
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-dashboard:latest
                """.trimIndent()
                commandArgs = "--cache-from type=local,src=/tmp/docker-cache"
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
        }
    }

    failureConditions {
        testFailure = false
        buildFailureOnMetric {
            metric = BuildFailureOnMetric.MetricType.COVERAGE_PERCENTAGE
            threshold = 80
            stopBuildOnFailure = true
        }
        executionTimeoutMin = 30
    }
})

// ============================================
// BACKEND BUILD CONFIGURATION
// ============================================
object BackendBuild : BuildType({
    name = "Backend (FastAPI)"
    description = "Build and test the FastAPI backend"

    artifactRules = """
        htmlcov => coverage-report.zip
        tests/results => test-results.zip
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
        }
    }

    features {
        dockerSupport {
            loginToRegistry = on {
                dockerRegistryId = "TeamCityCloudRegistry"
            }
        }
    }

    // Use TeamCity Cloud builder
    requirements {
        contains("teamcity.agent.name", "linux-amd64")
    }

    steps {
        python {
            name = "Setup Python Environment"
            pythonVersion = "%env.PYTHON_VERSION%"
            command = script {
                content = """
                    python -m venv .venv
                    source .venv/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                """.trimIndent()
            }
        }

        parallel {
            python {
                name = "Type Checking"
                command = script {
                    content = """
                        source .venv/bin/activate
                        basedpyright . --pythonpath .venv/bin/python
                    """.trimIndent()
                }
            }

            python {
                name = "Code Quality"
                command = script {
                    content = """
                        source .venv/bin/activate
                        black --check apps/backend core database
                        ruff check apps/backend core database
                    """.trimIndent()
                }
            }

            python {
                name = "Security Scan"
                command = script {
                    content = """
                        source .venv/bin/activate
                        pip install safety bandit
                        safety check
                        bandit -r apps/backend core database -ll
                    """.trimIndent()
                }
            }
        }

        dockerCompose {
            name = "Start Test Services"
            file = "infrastructure/docker/compose/docker-compose.test.yml"
            services = "postgres redis"
        }

        python {
            name = "Run Tests"
            command = script {
                content = """
                    source .venv/bin/activate
                    pytest tests/unit -v --cov=apps/backend --cov-report=html
                    RUN_INTEGRATION_TESTS=1 pytest tests/integration -v
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Build Docker Image"
            commandType = build {
                source = file {
                    path = "infrastructure/docker/dockerfiles/backend.Dockerfile"
                }
                contextDir = "."
                namesAndTags = """
                    %env.DOCKER_REGISTRY%/toolboxai-backend:%build.number%
                    %env.DOCKER_REGISTRY%/toolboxai-backend:latest
                """.trimIndent()
            }
        }

        dockerCommand {
            name = "Security Scan Image"
            commandType = other {
                customCommand = "run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image %env.DOCKER_REGISTRY%/toolboxai-backend:%build.number%"
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
        }
    }

    failureConditions {
        testFailure = true
        executionTimeoutMin = 45
    }

    dependencies {
        artifacts(DashboardBuild) {
            artifactRules = "dashboard-build-*.zip"
        }
    }
})

// ============================================
// MCP SERVER BUILD CONFIGURATION
// ============================================
object MCPServerBuild : BuildType({
    name = "MCP Server"
    description = "Build Model Context Protocol server"

    vcs {
        root(MainRepository)
    }

    // Use TeamCity Cloud builder
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
                    python -m venv .venv-mcp
                    source .venv-mcp/bin/activate
                    pip install -r core/mcp/requirements.txt
                    pytest core/mcp/tests -v
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
                namesAndTags = "%env.DOCKER_REGISTRY%/toolboxai-mcp:%build.number%"
            }
        }
    }
})

// ============================================
// AGENT COORDINATOR BUILD CONFIGURATION
// ============================================
object AgentCoordinatorBuild : BuildType({
    name = "Agent Coordinator"
    description = "Build LangChain/LangGraph agent coordinator"

    vcs {
        root(MainRepository)
    }

    // Use TeamCity Cloud builder
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
                    python -m venv .venv-agent
                    source .venv-agent/bin/activate
                    pip install langchain langchain-openai langgraph langsmith
                    pytest core/agents/tests -v
                """.trimIndent()
            }
        }

        python {
            name = "LangSmith Integration"
            command = script {
                content = """
                    source .venv-agent/bin/activate
                    python scripts/test_langsmith_connection.py
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
                namesAndTags = "%env.DOCKER_REGISTRY%/toolboxai-coordinator:%build.number%"
            }
        }
    }

    dependencies {
        snapshot(MCPServerBuild)
    }
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

    // Use TeamCity Cloud builder
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
            additionalDockerComposeFile = "infrastructure/docker/compose/docker-compose.test.yml"
        }

        script {
            name = "Run Integration Tests"
            scriptContent = """
                # Wait for services
                sleep 60

                # Test endpoints
                curl -f http://localhost:8009/health
                curl -f http://localhost:5179
                curl -f http://localhost:9877/health
                curl -f http://localhost:8888/health

                # Run E2E tests
                cd apps/dashboard && npm run test:e2e
            """.trimIndent()
        }

        dockerCompose {
            name = "Stop Stack"
            file = "infrastructure/docker/compose/docker-compose.yml"
            additionalDockerComposeFile = "infrastructure/docker/compose/docker-compose.test.yml"
            projectName = "toolboxai-test"
        }
    }

    dependencies {
        snapshot(DashboardBuild)
        snapshot(BackendBuild)
        snapshot(MCPServerBuild)
        snapshot(AgentCoordinatorBuild)
    }
})

// ============================================
// DEPLOYMENT PIPELINE
// ============================================
object DeploymentPipeline : BuildType({
    name = "Deploy to Production"
    description = "Deploy all services to production"

    params {
        param("env.DEPLOY_ENVIRONMENT", "production")
    }

    steps {
        script {
            name = "Deploy with Docker Compose"
            scriptContent = """
                docker compose -f infrastructure/docker/compose/docker-compose.yml \
                               -f infrastructure/docker/compose/docker-compose.prod.yml \
                               pull

                docker compose -f infrastructure/docker/compose/docker-compose.yml \
                               -f infrastructure/docker/compose/docker-compose.prod.yml \
                               up -d

                echo "✅ Deployment complete"
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(IntegrationTests) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    // Use TeamCity Cloud builder for deployment
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