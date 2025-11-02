FROM node:22-alpine
WORKDIR /app

# Copy package files
COPY apps/dashboard/package.json apps/dashboard/package-lock.json ./

# Test 1: Install with NODE_ENV=production (should skip devDependencies)
RUN echo "=== Test 1: NODE_ENV=production ===" && \
    NODE_ENV=production npm install --no-audit --no-fund && \
    echo "Packages installed: $(ls node_modules | wc -l)" && \
    test -f node_modules/.bin/vite && echo "✓ vite found" || echo "✗ vite NOT found (expected)"

# Clean for test 2
RUN rm -rf node_modules

# Test 2: Install with NODE_ENV=development (should include devDependencies)
RUN echo "=== Test 2: NODE_ENV=development ===" && \
    NODE_ENV=development npm install --no-audit --no-fund && \
    echo "Packages installed: $(ls node_modules | wc -l)" && \
    test -f node_modules/.bin/vite && echo "✓ vite found (SUCCESS!)" || echo "✗ vite NOT found (FAIL)"
