/*
 * ============================================
 * TEAMCITY - VERCEL & SENTRY DEPLOYMENT
 * ============================================
 * Additional build configurations for Vercel and Sentry
 * Updated: 2025-11-02
 * ============================================
 */

import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.*
import jetbrains.buildServer.configs.kotlin.triggers.*

// ============================================
// VERCEL FRONTEND DEPLOYMENT
// ============================================
object VercelDeployment : BuildType({
    name = "Deploy Frontend to Vercel"
    description = "Deploy React dashboard to Vercel with Sentry sourcemap upload"

    params {
        param("env.VERCEL_ORG_ID", "%env.VERCEL_ORG_ID%")
        param("env.VERCEL_PROJECT_ID", "%env.VERCEL_PROJECT_ID%")
        param("env.VERCEL_TOKEN", "%env.VERCEL_TOKEN%")
        param("env.SENTRY_AUTH_TOKEN", "%env.SENTRY_AUTH_TOKEN%")
        param("env.SENTRY_ORG", "toolboxai")
        param("env.SENTRY_PROJECT", "frontend")
    }

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = "+:main"
        }
    }

    steps {
        script {
            name = "Setup Environment"
            workingDir = "apps/dashboard"
            scriptContent = """
                echo "Setting up Vercel deployment..."
                npm install -g vercel@latest
                npm install -g @sentry/cli
                
                echo "Vercel CLI version: $(vercel --version)"
                echo "Sentry CLI version: $(sentry-cli --version)"
            """.trimIndent()
        }

        script {
            name = "Install Dependencies"
            workingDir = "apps/dashboard"
            scriptContent = """
                npm ci --legacy-peer-deps
            """.trimIndent()
        }

        script {
            name = "Build Production"
            workingDir = "apps/dashboard"
            scriptContent = """
                export VITE_API_URL=https://toolboxai-backend.onrender.com
                export VITE_SENTRY_DSN=%env.VITE_SENTRY_DSN%
                export VITE_COMMIT_SHA=%build.vcs.number%
                export VITE_ENVIRONMENT=production
                
                npm run build
                
                echo "✅ Build completed"
                echo "Build size: $(du -sh dist/)"
            """.trimIndent()
        }

        script {
            name = "Deploy to Vercel"
            workingDir = "apps/dashboard"
            scriptContent = """
                vercel --prod \
                    --token=%env.VERCEL_TOKEN% \
                    --yes \
                    --build-env VITE_API_URL=https://toolboxai-backend.onrender.com \
                    --build-env VITE_SENTRY_DSN=%env.VITE_SENTRY_DSN% \
                    --build-env VITE_COMMIT_SHA=%build.vcs.number% \
                    --build-env VITE_ENVIRONMENT=production
                
                echo "✅ Deployed to Vercel"
            """.trimIndent()
        }

        script {
            name = "Upload Sourcemaps to Sentry"
            workingDir = "apps/dashboard"
            scriptContent = """
                export SENTRY_AUTH_TOKEN=%env.SENTRY_AUTH_TOKEN%
                export SENTRY_ORG=%env.SENTRY_ORG%
                export SENTRY_PROJECT=%env.SENTRY_PROJECT%
                
                # Create release
                sentry-cli releases new %build.vcs.number%
                
                # Upload sourcemaps
                sentry-cli releases files %build.vcs.number% upload-sourcemaps ./dist \
                    --url-prefix '~/' \
                    --validate \
                    --strip-common-prefix
                
                # Finalize release
                sentry-cli releases finalize %build.vcs.number%
                
                # Create deployment
                sentry-cli releases deploys %build.vcs.number% new -e production
                
                echo "✅ Sourcemaps uploaded to Sentry"
            """.trimIndent()
        }

        script {
            name = "Verify Deployment"
            scriptContent = """
                echo "Verifying deployment..."
                sleep 10
                
                # Get Vercel deployment URL
                DEPLOYMENT_URL="https://toolboxai.vercel.app"
                
                # Health check
                for i in {1..10}; do
                    if curl -f "${'$'}DEPLOYMENT_URL" > /dev/null 2>&1; then
                        echo "✅ Deployment verified: ${'$'}DEPLOYMENT_URL"
                        exit 0
                    fi
                    echo "Waiting for deployment... attempt ${'$'}i/10"
                    sleep 5
                done
                
                echo "⚠️ Deployment verification timeout"
                exit 1
            """.trimIndent()
        }

        script {
            name = "Notify Deployment"
            scriptContent = """
                curl -X POST %env.SLACK_WEBHOOK_URL% \
                    -H 'Content-Type: application/json' \
                    -d '{
                        "text": "🚀 Frontend deployed to Vercel!",
                        "attachments": [{
                            "color": "good",
                            "fields": [
                                {"title": "Environment", "value": "Production", "short": true},
                                {"title": "Version", "value": "%build.vcs.number%", "short": true},
                                {"title": "URL", "value": "https://toolboxai.vercel.app", "short": false}
                            ]
                        }]
                    }'
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(DashboardBuild) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    failureConditions {
        executionTimeoutMin = 20
    }
})

// ============================================
// RENDER BACKEND DEPLOYMENT
// ============================================
object RenderDeployment : BuildType({
    name = "Deploy Backend to Render"
    description = "Deploy Python backend to Render with Docker"

    params {
        param("env.RENDER_API_KEY", "%env.RENDER_API_KEY%")
        param("env.RENDER_SERVICE_ID", "%env.RENDER_SERVICE_ID%")
    }

    vcs {
        root(MainRepository)
    }

    triggers {
        vcs {
            branchFilter = "+:main"
        }
    }

    steps {
        script {
            name = "Build Docker Image"
            scriptContent = """
                echo "Building backend Docker image..."
                docker build \
                    -f infrastructure/docker/Dockerfile.backend \
                    -t toolboxai-backend:%build.number% \
                    --build-arg COMMIT_SHA=%build.vcs.number% \
                    .
                
                echo "✅ Docker image built"
            """.trimIndent()
        }

        script {
            name = "Deploy to Render"
            scriptContent = """
                echo "Triggering Render deployment..."
                
                curl -X POST \
                    -H "Authorization: Bearer %env.RENDER_API_KEY%" \
                    -H "Content-Type: application/json" \
                    "https://api.render.com/v1/services/%env.RENDER_SERVICE_ID%/deploys" \
                    -d '{
                        "clearCache": false
                    }'
                
                echo "✅ Render deployment triggered"
            """.trimIndent()
        }

        script {
            name = "Wait for Deployment"
            scriptContent = """
                echo "Waiting for deployment to complete..."
                
                for i in {1..30}; do
                    STATUS=$(curl -s \
                        -H "Authorization: Bearer %env.RENDER_API_KEY%" \
                        "https://api.render.com/v1/services/%env.RENDER_SERVICE_ID%" \
                        | jq -r '.service.state')
                    
                    if [ "${'$'}STATUS" = "running" ]; then
                        echo "✅ Deployment completed successfully"
                        exit 0
                    fi
                    
                    echo "Current status: ${'$'}STATUS (attempt ${'$'}i/30)"
                    sleep 20
                done
                
                echo "⚠️ Deployment timeout"
                exit 1
            """.trimIndent()
        }

        script {
            name = "Health Check"
            scriptContent = """
                echo "Performing health check..."
                
                BACKEND_URL="https://toolboxai-backend.onrender.com"
                
                for i in {1..10}; do
                    if curl -f "${'$'}BACKEND_URL/health" > /dev/null 2>&1; then
                        echo "✅ Backend is healthy"
                        exit 0
                    fi
                    echo "Waiting for backend... attempt ${'$'}i/10"
                    sleep 5
                done
                
                echo "❌ Health check failed"
                exit 1
            """.trimIndent()
        }

        script {
            name = "Notify Sentry"
            scriptContent = """
                export SENTRY_AUTH_TOKEN=%env.SENTRY_AUTH_TOKEN%
                export SENTRY_ORG=toolboxai
                export SENTRY_PROJECT=backend
                
                # Create release
                sentry-cli releases new %build.vcs.number%
                
                # Create deployment
                sentry-cli releases deploys %build.vcs.number% new -e production
                
                # Finalize
                sentry-cli releases finalize %build.vcs.number%
                
                echo "✅ Sentry notified"
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(BackendBuild) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    failureConditions {
        executionTimeoutMin = 30
    }
})

// ============================================
// FULL PRODUCTION DEPLOYMENT PIPELINE
// ============================================
object FullProductionDeploy : BuildType({
    name = "🚀 Deploy All Services to Production"
    description = "Complete production deployment: Backend (Render) + Frontend (Vercel)"

    steps {
        script {
            name = "Pre-deployment Validation"
            scriptContent = """
                echo "========================================"
                echo "PRODUCTION DEPLOYMENT VALIDATION"
                echo "========================================"
                echo "Build Number: %build.number%"
                echo "Git Commit: %build.vcs.number%"
                echo "Branch: %teamcity.build.branch%"
                echo ""
                echo "This will deploy:"
                echo "  - Backend to Render"
                echo "  - Frontend to Vercel"
                echo "  - Upload sourcemaps to Sentry"
                echo ""
                echo "✅ Pre-deployment checks passed"
            """.trimIndent()
        }
    }

    dependencies {
        snapshot(RenderDeployment) {
            reuseBuilds = ReuseBuilds.NO
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
        snapshot(VercelDeployment) {
            reuseBuilds = ReuseBuilds.NO
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    triggers {
        vcs {
            branchFilter = "+:main"
            triggerRules = """
                +:apps/**
                +:core/**
                +:infrastructure/**
            """.trimIndent()
        }
    }
})

