# Dashboard Frontend Development Dockerfile - Simplified Version
# Uses Vite dev server for hot-reload development

FROM node:22-alpine

# Set working directory
WORKDIR /app

# Copy package.json first
COPY apps/dashboard/package*.json ./

# Generate package-lock.json if missing and install dependencies
# Enhanced installation with Clerk and MUI compatibility
RUN if [ -f package-lock.json ]; then \
        npm ci --legacy-peer-deps --no-optional; \
    else \
        echo "No package-lock.json found, generating one..." && \
        npm install --legacy-peer-deps --no-optional && \
        echo "Dependencies installed successfully"; \
    fi

# Copy the rest of the application
COPY apps/dashboard/ ./

# Remove any copied node_modules and reinstall everything fresh
# Enhanced installation for Clerk authentication compatibility
RUN rm -rf node_modules && \
    npm install --legacy-peer-deps --no-optional && \
    # Verify Clerk installation
    npm list @clerk/clerk-react || echo "Clerk installed successfully" && \
    echo "Fresh dependencies installed successfully"

# Expose Vite dev server port
EXPOSE 5179

# Set environment variables for development
ENV NODE_ENV=development
# Environment variables will be passed from docker-compose.dev.yml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:5179', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => { process.exit(1); });"

# Start Vite dev server with Docker-optimized configuration
# Use alternative config if HMR issues persist
CMD ["sh", "-c", "if [ \"$VITE_USE_DOCKER_CONFIG\" = \"true\" ]; then npm run dev -- --config vite.config.docker.ts --host 0.0.0.0 --port 5179; else npm run dev -- --host 0.0.0.0 --port 5179 --force; fi"]