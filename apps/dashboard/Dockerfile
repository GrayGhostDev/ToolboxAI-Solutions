# Multi-stage production Dockerfile for ToolBoxAI Dashboard
# Node 22 Alpine for optimized performance
# Created: September 21, 2025

# ========================================
# Stage 1: Dependencies
# ========================================
FROM node:22-alpine AS deps

# Install system dependencies
RUN apk add --no-cache libc6-compat python3 make g++

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Install production dependencies with clean install
# Use npm ci for reproducible builds
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# ========================================
# Stage 2: Builder
# ========================================
FROM node:22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache libc6-compat python3 make g++

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Set build-time environment variables
ARG NODE_ENV=production
ARG VITE_API_BASE_URL=http://backend:8009
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER=us2
ARG VITE_ENABLE_WEBSOCKET=true
ARG VITE_ENABLE_GAMIFICATION=true
ARG VITE_ENABLE_ANALYTICS=true

ENV NODE_ENV=${NODE_ENV}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_PUSHER_KEY=${VITE_PUSHER_KEY}
ENV VITE_PUSHER_CLUSTER=${VITE_PUSHER_CLUSTER}
ENV VITE_ENABLE_WEBSOCKET=${VITE_ENABLE_WEBSOCKET}
ENV VITE_ENABLE_GAMIFICATION=${VITE_ENABLE_GAMIFICATION}
ENV VITE_ENABLE_ANALYTICS=${VITE_ENABLE_ANALYTICS}

# Build the application
RUN npm run build && \
    # Remove dev dependencies after build
    npm prune --production && \
    # Clean npm cache
    npm cache clean --force

# ========================================
# Stage 3: Production Runtime
# ========================================
FROM node:22-alpine AS runner

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    tini

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

WORKDIR /app

# Copy production dependencies from deps stage
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

# Copy server configuration if exists
COPY --chown=nextjs:nodejs server.js* ./
COPY --chown=nextjs:nodejs vite.config.ts* ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/tmp && \
    chown -R nextjs:nodejs /app/logs /app/tmp

# Set runtime environment variables
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=5179 \
    # Node.js 22 optimizations
    NODE_OPTIONS="--max-old-space-size=2048 --enable-source-maps" \
    # Security headers
    NODE_TLS_REJECT_UNAUTHORIZED=1

# Switch to non-root user
USER nextjs

# Expose dashboard port
EXPOSE 5179

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5179/health || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application
# Use preview mode for production serving of Vite build
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5179"]