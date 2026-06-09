#!/bin/bash
# ──────────────────────────────────────────────────────────
# EKS Cluster Bootstrap Script
# Creates a free-tier compatible EKS cluster with eksctl
# Region: us-east-1 (N. Virginia)
# ──────────────────────────────────────────────────────────
set -euo pipefail

CLUSTER_NAME="fitness-tracker-cluster"
REGION="us-east-1"
K8S_VERSION="1.29"
NODE_TYPE="t3.medium"    # Free-tier-like (cheapest viable for EKS)
MIN_NODES=1
MAX_NODES=3
DESIRED_NODES=2

echo "═══════════════════════════════════════════════════════"
echo "  🚀 Creating EKS Cluster: $CLUSTER_NAME"
echo "  Region    : $REGION"
echo "  Node type : $NODE_TYPE"
echo "  Nodes     : $MIN_NODES – $MAX_NODES"
echo "═══════════════════════════════════════════════════════"

# Step 1: Create cluster
eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$REGION" \
  --version "$K8S_VERSION" \
  --nodegroup-name fitness-nodes \
  --node-type "$NODE_TYPE" \
  --nodes "$DESIRED_NODES" \
  --nodes-min "$MIN_NODES" \
  --nodes-max "$MAX_NODES" \
  --managed \
  --with-oidc \
  --alb-ingress-access

echo "✅ Cluster created: $CLUSTER_NAME"

# Step 2: Update kubeconfig
aws eks update-kubeconfig \
  --region "$REGION" \
  --name "$CLUSTER_NAME"

echo "✅ kubeconfig updated"

# Step 3: Install AWS Load Balancer Controller
echo "📦 Installing AWS Load Balancer Controller …"

# Create IAM policy
curl -o /tmp/iam_policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file:///tmp/iam_policy.json 2>/dev/null || echo "Policy already exists"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

eksctl create iamserviceaccount \
  --cluster="$CLUSTER_NAME" \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn="arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy" \
  --approve

helm repo add eks https://aws.github.io/eks-charts
helm repo update

VPC_ID=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" \
  --query 'cluster.resourcesVpcConfig.vpcId' --output text)

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region="$REGION" \
  --set vpcId="$VPC_ID"

echo "✅ AWS Load Balancer Controller installed"

# Step 4: Install Gateway API CRDs
echo "📦 Installing Kubernetes Gateway API CRDs …"
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
echo "✅ Gateway API CRDs installed"

# Step 5: Create namespace
kubectl create namespace fitness-app --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace fitness-app ready"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ EKS Bootstrap Complete!"
echo "  Next: kubectl apply -f k8s/"
echo "═══════════════════════════════════════════════════════"
