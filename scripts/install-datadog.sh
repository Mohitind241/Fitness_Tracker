#!/bin/bash
# ──────────────────────────────────────────────────────────
# Datadog Agent Installation on EKS
# Uses Datadog Helm chart (free trial available)
# ──────────────────────────────────────────────────────────
set -euo pipefail

DD_API_KEY="${DD_API_KEY:-17f70c28759e381392e0f9efd594582b}"
DD_SITE="datadoghq.com"
CLUSTER_NAME="fitness-tracker-cluster"

echo "📦 Installing Datadog Agent on EKS …"

# Add Datadog Helm repo
helm repo add datadog https://helm.datadoghq.com
helm repo update

# Create Datadog namespace
kubectl create namespace datadog --dry-run=client -o yaml | kubectl apply -f -

# Create API key secret
kubectl create secret generic datadog-secret \
  --from-literal api-key="$DD_API_KEY" \
  -n datadog \
  --dry-run=client -o yaml | kubectl apply -f -

# Install Datadog Agent
helm upgrade --install datadog-agent datadog/datadog \
  --namespace datadog \
  --set datadog.apiKeyExistingSecret=datadog-secret \
  --set datadog.site="$DD_SITE" \
  --set datadog.clusterName="$CLUSTER_NAME" \
  --set datadog.logs.enabled=true \
  --set datadog.logs.containerCollectAll=true \
  --set datadog.apm.portEnabled=true \
  --set datadog.processAgent.enabled=true \
  --set datadog.processAgent.processCollection=true \
  --set datadog.kubelet.tlsVerify=false \
  --set clusterAgent.enabled=true \
  --set clusterAgent.metricsProvider.enabled=true \
  --set datadog.tags[0]="env:production" \
  --set datadog.tags[1]="app:fitness-tracker" \
  --set datadog.tags[2]="cluster:$CLUSTER_NAME"

echo "⏳ Waiting for Datadog agent pods …"
kubectl wait --for=condition=Ready pods \
  -l app=datadog-agent \
  -n datadog \
  --timeout=120s

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Datadog Agent Installed!"
echo "  → View metrics at: https://app.datadoghq.com"
echo "  → Go to: Infrastructure > Kubernetes"
echo "  → Create dashboard for: fitness-tracker"
echo "═══════════════════════════════════════════════════════"
