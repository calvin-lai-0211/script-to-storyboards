#!/bin/bash

# Convenience wrapper for docker-compose up
# Starts services using compose configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting services with Docker Compose..."
echo ""

cd "$SCRIPT_DIR/compose"

# Pass all arguments to docker-compose
docker-compose up -d "$@"
