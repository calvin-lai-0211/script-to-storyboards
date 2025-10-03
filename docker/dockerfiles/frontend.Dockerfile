# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files from frontend directory
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source code
COPY frontend/ .

# Accept build argument for API URL
ARG VITE_API_BASE_URL=http://localhost:8000

# Create .env file with build argument
RUN echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}" > .env

# Build the application
RUN pnpm run build

# Documentation build stage
FROM python:3.12-alpine AS docs-builder

WORKDIR /docs-build

# Install mkdocs-material
RUN pip install --no-cache-dir mkdocs-material

# Copy documentation files from project root context
COPY docs ./docs
COPY mkdocs.yml .

# Build documentation
RUN mkdocs build

# Production stage
FROM nginx:alpine

# Copy built dist from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy documentation from docs-builder stage
COPY --from=docs-builder /docs-build/site /usr/share/nginx/html/docs

# Copy nginx configuration from frontend directory
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
