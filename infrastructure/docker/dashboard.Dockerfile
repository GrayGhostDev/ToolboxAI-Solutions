# Dashboard Frontend Dockerfile - Multi-stage build for production
FROM node:20-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY apps/dashboard/package*.json ./

# Install dependencies with legacy peer deps to resolve conflicts
# Need all dependencies (including dev) for the build step
RUN npm install --legacy-peer-deps && \
    npm cache clean --force

# Copy source code
COPY apps/dashboard/ ./

# Build the application
ARG VITE_API_BASE_URL
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER
ARG VITE_PUSHER_AUTH_ENDPOINT

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_PUSHER_KEY=${VITE_PUSHER_KEY} \
    VITE_PUSHER_CLUSTER=${VITE_PUSHER_CLUSTER} \
    VITE_PUSHER_AUTH_ENDPOINT=${VITE_PUSHER_AUTH_ENDPOINT}

RUN npm run build

# Production stage - Nginx
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY infrastructure/docker/nginx.conf /etc/nginx/nginx.conf
COPY infrastructure/docker/default.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add security headers configuration
RUN echo 'add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\''; style-src '\''self'\'' '\''unsafe-inline'\''; img-src '\''self'\'' data: https:; font-src '\''self'\'' data:; connect-src '\''self'\'' wss: https:;" always;' >> /etc/nginx/conf.d/security.conf

# Create non-root user
RUN adduser -D -u 1000 nginx-user && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginx-user:nginx-user /var/run/nginx.pid

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Switch to non-root user
USER nginx-user

# Start nginx
CMD ["nginx", "-g", "daemon off;"]