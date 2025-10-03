#!/bin/bash

# Script to start the application with Docker

set -e

echo "🚀 Starting Script-to-Storyboards Application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if frontend dist directory exists
if [ ! -d "frontend/dist" ]; then
    echo "📦 Building frontend..."
    cd frontend

    # Check for package manager
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm install
        pnpm build
    elif [ -f "package-lock.json" ]; then
        npm install
        npm run build
    else
        npm install
        npm run build
    fi

    cd ..
    echo "✅ Frontend built successfully"
else
    echo "✅ Frontend dist directory already exists"
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🏃 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📍 Access URLs:"
echo "   Frontend: http://localhost:8866"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""
