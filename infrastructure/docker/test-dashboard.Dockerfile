# Test Dockerfile to debug npm install issue
FROM node:25-alpine

WORKDIR /app

# Copy the dashboard source
COPY apps/dashboard/ ./

# Show what we have
RUN echo "=== Contents before npm install ===" && \
    ls -la && \
    echo "=== node_modules before install ===" && \
    ls -la node_modules 2>&1 || echo "No node_modules directory" && \
    echo "=== package.json check ===" && \
    test -f package.json && echo "package.json exists" || echo "package.json MISSING" && \
    echo "=== Running npm install ===" && \
    npm install --no-audit --no-fund && \
    echo "=== After npm install ===" && \
    ls -la node_modules/.bin/ | head -20 && \
    echo "=== Checking for vite ===" && \
    test -f node_modules/.bin/vite && echo "✓ vite binary exists" || echo "✗ vite binary MISSING" && \
    test -d node_modules/vite && echo "✓ vite package exists" || echo "✗ vite package MISSING" && \
    echo "=== Checking vite in package.json ===" && \
    grep '"vite"' package.json || echo "vite not in dependencies"
