#!/bin/bash

# Convenience wrapper for K8s deployment
# Provides easy access to K8s deployment scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚢 K8s Deployment Options"
echo ""
echo "Choose deployment target:"
echo "  1) Local k3d (Mac)"
echo "  2) Remote K3s (Linux server)"
echo "  3) Package for manual deployment"
echo ""

read -p "Enter choice [1-3]: " choice

case $choice in
  1)
    echo ""
    echo "📦 Deploying to local k3d..."
    cd "$SCRIPT_DIR/k8s"
    ./local-deploy.sh
    ;;
  2)
    echo ""
    echo "🌐 Deploying to remote K3s server..."
    cd "$SCRIPT_DIR/k8s"
    ./deploy-to-remote.sh
    ;;
  3)
    echo ""
    echo "📦 Creating deployment package..."
    cd "$SCRIPT_DIR/k8s"
    ./package.sh
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac
