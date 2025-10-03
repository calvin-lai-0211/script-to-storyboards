#!/bin/bash

# Convenience wrapper for docker-compose up
# Starts services using compose configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting services with Docker Compose..."
echo ""

# Check if --build flag is passed or images don't exist
BUILD_FLAG=""
if [[ "$*" == *"--build"* ]] || ! docker images | grep -q "script-to-storyboards-api"; then
    echo "📦 Building Docker images..."
    BUILD_FLAG="--build"
fi

cd "$SCRIPT_DIR/compose"

# Start services with optional build
docker-compose up -d $BUILD_FLAG "$@"

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access URLs:"
echo "   Frontend: http://localhost:8866"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Quick commands:"
echo "   Rebuild & restart: ./docker/local-run.sh --build"
echo "   View logs: docker-compose -f docker/compose/docker-compose.yml logs -f"
echo "   Stop: docker-compose -f docker/compose/docker-compose.yml down"
echo ""
