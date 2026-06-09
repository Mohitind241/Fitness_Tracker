#!/bin/bash
# ──────────────────────────────────────────────────────────
# ArgoCD Installation Script on EKS
# ──────────────────────────────────────────────────────────
set -euo pipefail

echo "📦 Installing ArgoCD on EKS …"

# Create ArgoCD namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "⏳ Waiting for ArgoCD pods to be ready …"
kubectl wait --for=condition=Ready pods \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd \
  --timeout=120s

# Get initial admin password
echo ""
echo "═══════════════════════════════════════"
echo "ArgoCD Initial Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo ""
echo "═══════════════════════════════════════"

# Patch argocd-server to use LoadBalancer (to access UI)
kubectl patch svc argocd-server -n argocd \
  -p '{"spec": {"type": "LoadBalancer"}}'

echo "⏳ Waiting for LoadBalancer IP …"
sleep 30

ARGOCD_IP=$(kubectl get svc argocd-server -n argocd \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo ""
echo "✅ ArgoCD UI: https://$ARGOCD_IP"
echo "   Username: admin"
echo "   Password: (shown above)"
echo ""

# Apply ArgoCD project and applications
echo "📋 Applying ArgoCD manifests …"
kubectl apply -f argocd/project.yaml
kubectl apply -f argocd/application-prod.yaml
kubectl apply -f argocd/application-staging.yaml

echo "✅ ArgoCD setup complete!"
