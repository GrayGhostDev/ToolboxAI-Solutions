# Dashboard Frontend Development Dockerfile - Simplified Version
# Uses Vite dev server for hot-reload development

FROM node:22-alpine

# Set working directory
WORKDIR /app

# Copy the entire dashboard application
COPY apps/dashboard/ ./

# Install dependencies - use npm ci for faster, more reliable installs
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Clear any existing Vite cache to force re-optimization
RUN rm -rf node_modules/.vite

# Expose Vite dev server port
EXPOSE 5179

# Set environment variables for development
ENV NODE_ENV=development
# Use Docker service name for backend communication
ENV VITE_API_BASE_URL=http://fastapi-main:8009
ENV VITE_FASTAPI_URL=http://fastapi-main:8009
ENV VITE_PROXY_TARGET=http://fastapi-main:8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:5179', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => { process.exit(1); });"

# Start Vite dev server with force optimization flag
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5179", "--force"]