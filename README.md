# 🏋️ Fitness Tracker — Enterprise DevOps Pipeline

A production-grade 10-phase DevOps pipeline built on Amazon EKS

## 🏗️ Architecture
Developer → GitHub Actions → Docker Hub → ArgoCD → EKS → Datadog → AI Agent

## 🛠️ Tech Stack
| Tool | Purpose |
|------|---------|
| GitHub Actions | CI/CD Pipeline |
| SonarQube | Code Quality |
| Docker | Containerization |
| Kubernetes (EKS) | Orchestration |
| Helm | Package Management |
| ArgoCD | GitOps Deployment |
| Datadog | Monitoring |
| Google Gemini AI | AI Operations |

## ✅ 10 Phases Completed
- Phase 1  → Jira Agile Planning
- Phase 2  → GitHub Source Control  
- Phase 3  → CI/CD with SonarQube
- Phase 4  → Docker & Image Promotion
- Phase 5  → Kubernetes on EKS
- Phase 6  → NGINX Gateway API
- Phase 7  → Helm Charts
- Phase 8  → ArgoCD GitOps
- Phase 9  → Datadog Monitoring
- Phase 10 → AI Agent (Gemini)

## 🚀 How to Deploy
# Install dependencies
npm install

# Run locally
npm start

# Deploy to Kubernetes
kubectl apply -f k8s/

# Deploy with Helm
helm install fitness-app helm/fitness-app-chart/ -n fitness-app

# Run AI Agent
export GEMINI_API_KEY="my-key"
python3 ai-agent/ai_agent.py --mode analyze-pods
