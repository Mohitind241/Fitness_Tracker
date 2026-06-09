#!/usr/bin/env python3
"""
AI Agent for EKS Operations - Fitness Tracker
Analyzes Kubernetes logs, identifies issues, recommends fixes,
and generates automation scripts using Google Gemini AI.

Usage:
  python ai_agent.py --mode analyze-pods
  python ai_agent.py --mode analyze-logs --namespace fitness-app
  python ai_agent.py --mode troubleshoot --pod fitness-app-deployment-xxx
  python ai_agent.py --mode generate-fix --issue "OOMKilled"
"""

import argparse
import subprocess
import sys
import os
import json
import re
from datetime import datetime

# ─── Try to import Google Generative AI (free tier) ─────────────────
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

NAMESPACE = os.getenv("K8S_NAMESPACE", "fitness-app")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Free at aistudio.google.com
GEMINI_MODEL = "gemini-2.0-flash"  # Free tier model


# ─── Helpers ──────────────────────────────────────────────────────────
def run_kubectl(args: list[str]) -> str:
    """Run kubectl and return stdout."""
    cmd = ["kubectl"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr


def banner(title: str) -> None:
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")


# ─── Data Collection ─────────────────────────────────────────────────
def collect_pod_status(namespace: str) -> str:
    return run_kubectl(["get", "pods", "-n", namespace, "-o", "wide"])


def collect_pod_logs(namespace: str, pod_name: str = None, tail: int = 100) -> str:
    if pod_name:
        return run_kubectl(["logs", pod_name, "-n", namespace, f"--tail={tail}"])
    # Get logs from all pods with the app label
    return run_kubectl(["logs", "-l", "app=fitness-tracker",
                        "-n", namespace, f"--tail={tail}", "--prefix=true"])


def collect_events(namespace: str) -> str:
    return run_kubectl(["get", "events", "-n", namespace,
                        "--sort-by=.lastTimestamp"])


def collect_describe(namespace: str, resource_type: str, name: str) -> str:
    return run_kubectl(["describe", resource_type, name, "-n", namespace])


def collect_cluster_info() -> dict:
    """Collect comprehensive cluster state."""
    return {
        "pods": collect_pod_status(NAMESPACE),
        "events": collect_events(NAMESPACE),
        "nodes": run_kubectl(["get", "nodes", "-o", "wide"]),
        "hpa": run_kubectl(["get", "hpa", "-n", NAMESPACE]),
    }


# ─── AI Analysis ──────────────────────────────────────────────────────
def analyze_with_gemini(context: str, question: str) -> str:
    """Send cluster context to Gemini for AI analysis."""
    if not HAS_GEMINI:
        return ("⚠️  google-generativeai not installed.\n"
                "Run: pip install google-generativeai\n"
                "Get free API key at: https://aistudio.google.com/")

    if not GEMINI_API_KEY:
        return ("⚠️  GEMINI_API_KEY not set.\n"
                "export GEMINI_API_KEY='your-key-here'\n"
                "Get free key at: https://aistudio.google.com/")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = f"""You are an expert SRE (Site Reliability Engineer) and Kubernetes DevOps engineer.
Analyze the following Kubernetes cluster data for the Fitness Tracker application and answer the question.

CLUSTER DATA:
{context}

QUESTION: {question}

Provide:
1. 📊 DIAGNOSIS: What is the issue?
2. 🔍 ROOT CAUSE: Why is it happening?
3. 🛠️ FIX STEPS: Exact kubectl commands to resolve the issue
4. 📝 PREVENTION: How to prevent this in the future
5. 🤖 AUTOMATION SCRIPT: A bash/kubectl script that automates the fix

Format your response clearly with these sections."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini API error: {e}"


# ─── Rule-based Analysis (fallback without AI) ─────────────────────
KNOWN_ISSUES = {
    "OOMKilled": {
        "diagnosis": "Container ran out of memory",
        "cause": "Memory limit too low or memory leak",
        "fix": [
            "kubectl top pods -n fitness-app",
            "kubectl patch deployment fitness-app-deployment -n fitness-app -p '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"fitness-app\",\"resources\":{\"limits\":{\"memory\":\"512Mi\"}}}]}}}}'",
        ],
    },
    "CrashLoopBackOff": {
        "diagnosis": "Container keeps crashing and restarting",
        "cause": "Application error, wrong config, or failing health checks",
        "fix": [
            "kubectl logs <pod-name> -n fitness-app --previous",
            "kubectl describe pod <pod-name> -n fitness-app",
        ],
    },
    "ImagePullBackOff": {
        "diagnosis": "Cannot pull Docker image from registry",
        "cause": "Wrong image name/tag or missing Docker Hub credentials",
        "fix": [
            "kubectl describe pod <pod-name> -n fitness-app",
            "kubectl create secret docker-registry regcred --docker-server=docker.io --docker-username=mohitdocker241 --docker-password=<token> -n fitness-app",
        ],
    },
    "Pending": {
        "diagnosis": "Pod cannot be scheduled onto a node",
        "cause": "Insufficient CPU/Memory on nodes or missing PVC",
        "fix": [
            "kubectl describe pod <pod-name> -n fitness-app",
            "kubectl get nodes -o wide",
            "kubectl describe nodes",
        ],
    },
}


def rule_based_analysis(data: str) -> str:
    """Simple pattern matching when AI is not available."""
    findings = []
    for issue, info in KNOWN_ISSUES.items():
        if issue in data:
            findings.append(f"\n⚠️  DETECTED: {issue}")
            findings.append(f"   Diagnosis : {info['diagnosis']}")
            findings.append(f"   Cause     : {info['cause']}")
            findings.append(f"   Fix steps :")
            for step in info['fix']:
                findings.append(f"     $ {step}")
    return "\n".join(findings) if findings else "✅ No common issues detected."


# ─── Modes ───────────────────────────────────────────────────────────
def mode_analyze_pods(namespace: str) -> None:
    banner("Pod Health Analysis")
    info = collect_cluster_info()
    combined = "\n".join(info.values())

    print("📋 Current Pod Status:")
    print(info["pods"])

    print("\n📋 Recent Events:")
    print(info["events"])

    # AI or rule-based
    if HAS_GEMINI and GEMINI_API_KEY:
        print("\n🤖 AI Analysis:")
        answer = analyze_with_gemini(
            combined,
            "Analyze these pods and events. Are there any issues? "
            "What immediate actions should the SRE take?"
        )
        print(answer)
    else:
        print("\n🔍 Rule-based Analysis:")
        print(rule_based_analysis(combined))


def mode_analyze_logs(namespace: str) -> None:
    banner("Log Analysis")
    logs = collect_pod_logs(namespace)
    events = collect_events(namespace)
    context = f"LOGS:\n{logs}\n\nEVENTS:\n{events}"

    print("📋 Recent Logs:")
    print(logs[:2000])

    if HAS_GEMINI and GEMINI_API_KEY:
        print("\n🤖 AI Log Analysis:")
        answer = analyze_with_gemini(
            context,
            "Analyze these application logs and Kubernetes events. "
            "Identify errors, warnings, or anomalies and suggest fixes."
        )
        print(answer)
    else:
        print("\n🔍 Rule-based Analysis:")
        print(rule_based_analysis(context))


def mode_troubleshoot(pod_name: str, namespace: str) -> None:
    banner(f"Troubleshooting Pod: {pod_name}")
    describe = collect_describe(namespace, "pod", pod_name)
    logs = collect_pod_logs(namespace, pod_name)
    context = f"DESCRIBE:\n{describe}\n\nLOGS:\n{logs}"

    print(describe)

    if HAS_GEMINI and GEMINI_API_KEY:
        print("\n🤖 AI Troubleshooting:")
        answer = analyze_with_gemini(
            context,
            f"Troubleshoot pod '{pod_name}'. What is wrong and how to fix it?"
        )
        print(answer)
    else:
        print("\n🔍 Rule-based Troubleshooting:")
        print(rule_based_analysis(context))


def mode_generate_fix(issue: str) -> None:
    banner(f"Generating Fix for: {issue}")
    info = collect_cluster_info()
    context = "\n".join(info.values())

    if HAS_GEMINI and GEMINI_API_KEY:
        print("\n🤖 AI-Generated Fix Script:")
        answer = analyze_with_gemini(
            context,
            f"Generate a complete bash automation script to fix: '{issue}' "
            "in the fitness-tracker namespace on EKS. "
            "Include error handling and logging."
        )
        print(answer)

        # Save script
        filename = f"fix_{issue.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.sh"
        with open(f"scripts/{filename}", "w") as f:
            # Extract bash code blocks
            code = re.findall(r"```bash\n(.*?)```", answer, re.DOTALL)
            f.write("#!/bin/bash\nset -euo pipefail\n\n")
            f.write("\n".join(code) if code else answer)
        print(f"\n✅ Fix script saved: scripts/{filename}")
    else:
        if issue in KNOWN_ISSUES:
            info_data = KNOWN_ISSUES[issue]
            print(f"Fix for {issue}:")
            for step in info_data['fix']:
                print(f"  $ {step}")
        else:
            print(f"No rule-based fix for: {issue}")
            print("Set GEMINI_API_KEY for AI-powered fixes.")


def mode_health_report(namespace: str) -> None:
    banner("Cluster Health Report")
    info = collect_cluster_info()
    report = {
        "timestamp": datetime.now().isoformat(),
        "namespace": namespace,
        "pods": info["pods"],
        "nodes": info["nodes"],
        "hpa": info["hpa"],
        "events": info["events"],
    }

    filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Health report saved: {filename}")
    print("\n📊 Summary:")
    print(info["pods"])
    print("\n⚡ HPA Status:")
    print(info["hpa"])


# ─── CLI ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Agent for EKS/Kubernetes Operations"
    )
    parser.add_argument(
        "--mode",
        choices=["analyze-pods", "analyze-logs", "troubleshoot",
                 "generate-fix", "health-report"],
        required=True,
        help="Operation mode"
    )
    parser.add_argument("--namespace", default=NAMESPACE,
                        help="Kubernetes namespace (default: fitness-app)")
    parser.add_argument("--pod", default=None,
                        help="Pod name (for troubleshoot mode)")
    parser.add_argument("--issue", default=None,
                        help="Issue description (for generate-fix mode)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    MODE_MAP = {
        "analyze-pods": lambda: mode_analyze_pods(args.namespace),
        "analyze-logs": lambda: mode_analyze_logs(args.namespace),
        "troubleshoot": lambda: mode_troubleshoot(args.pod or "fitness-app-pod", args.namespace),
        "generate-fix": lambda: mode_generate_fix(args.issue or "CrashLoopBackOff"),
        "health-report": lambda: mode_health_report(args.namespace),
    }

    print(f"🤖 Fitness Tracker AI Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode      : {args.mode}")
    print(f"   Namespace : {args.namespace}")
    print(f"   AI Engine : {'Gemini (enabled)' if HAS_GEMINI and GEMINI_API_KEY else 'Rule-based (no API key)'}")

    MODE_MAP[args.mode]()
