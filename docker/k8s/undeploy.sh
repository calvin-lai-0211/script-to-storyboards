#!/bin/bash

# K3s Undeploy Script for Script-to-Storyboards

set -e

echo "🗑️  Removing deployments from K3s..."

# Delete all resources
kubectl delete -f docker/k8s/ingress.yaml --ignore-not-found=true
kubectl delete -f docker/k8s/frontend-deployment.yaml --ignore-not-found=true
kubectl delete -f docker/k8s/api-deployment.yaml --ignore-not-found=true
kubectl delete -f docker/k8s/nginx-configmap.yaml --ignore-not-found=true

echo "✅ All resources removed successfully!"
