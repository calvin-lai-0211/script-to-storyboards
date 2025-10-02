#!/bin/bash
set -e

echo "🔄 Updating API code in K8s..."

# 1. Rebuild Docker image
echo "📦 Step 1/3: Rebuilding Docker image..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
docker-compose -f docker/compose/docker-compose.yml build api

# 2. Import to k3d
echo "📥 Step 2/3: Importing to k3d..."
CLUSTER_NAME=$(kubectl config current-context | sed 's/k3d-//')
if [ -z "$CLUSTER_NAME" ]; then
    CLUSTER_NAME="calvin"
fi
k3d image import script-to-storyboards-api:latest -c "$CLUSTER_NAME"

# 3. Restart deployment
echo "🔄 Step 3/3: Restarting deployment..."
kubectl rollout restart deployment/storyboard-api
kubectl rollout status deployment/storyboard-api --timeout=60s

echo "✅ API updated successfully!"
