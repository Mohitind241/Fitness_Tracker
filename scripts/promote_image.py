#!/usr/bin/env python3
"""
Docker Image Promotion Script
Promotes a Docker image from one repository/tag to another
without rebuilding the image.

Usage:
  python promote_image.py --source mohitdocker241/fitness:v1 \
                          --target mohitdocker241/fitness:v2-staging \
                          --username mohitdocker241 \
                          --password <token>
"""

import argparse
import subprocess
import sys
import logging
from datetime import datetime

# ─── Logging Setup ───────────────────────────────────────────────
LOG_FILE = f"image_promotion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return result."""
    log.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        log.info(result.stdout.strip())
    if result.returncode != 0:
        log.error(result.stderr.strip())
        if check:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def docker_login(username: str, password: str) -> None:
    """Login to Docker Hub."""
    log.info("🔐 Logging in to Docker Hub …")
    run(["docker", "login", "-u", username, "--password-stdin"],
        check=False)
    # Use stdin to avoid password in process list
    proc = subprocess.run(
        ["docker", "login", "-u", username, "--password-stdin"],
        input=password,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Docker login failed: {proc.stderr.strip()}")
    log.info("✅ Docker login successful")


def pull_image(source: str) -> None:
    """Pull source image from registry."""
    log.info(f"📥 Pulling source image: {source}")
    run(["docker", "pull", source])
    log.info(f"✅ Pulled: {source}")


def tag_image(source: str, target: str) -> None:
    """Tag the source image as the target."""
    log.info(f"🏷️  Tagging {source} → {target}")
    run(["docker", "tag", source, target])
    log.info(f"✅ Tagged: {target}")


def push_image(target: str) -> None:
    """Push the tagged image to registry."""
    log.info(f"📤 Pushing image: {target}")
    run(["docker", "push", target])
    log.info(f"✅ Pushed: {target}")


def validate_image(target: str) -> None:
    """Validate the pushed image by pulling it and checking metadata."""
    log.info(f"🔍 Validating image: {target}")
    run(["docker", "pull", target])
    result = run(["docker", "inspect", target])
    if '"Id"' in result.stdout:
        log.info(f"✅ Validation passed for: {target}")
    else:
        raise RuntimeError(f"Validation failed for: {target}")


def cleanup_local(images: list[str]) -> None:
    """Remove local copies of images to free disk space."""
    for img in images:
        log.info(f"🗑️  Removing local image: {img}")
        run(["docker", "rmi", "-f", img], check=False)


def promote(source: str, target: str, username: str, password: str,
            cleanup: bool = True) -> None:
    """Full promotion workflow."""
    log.info("=" * 60)
    log.info(f"🚀 Starting Image Promotion")
    log.info(f"   Source : {source}")
    log.info(f"   Target : {target}")
    log.info("=" * 60)

    try:
        docker_login(username, password)
        pull_image(source)
        tag_image(source, target)
        push_image(target)
        validate_image(target)

        if cleanup:
            cleanup_local([source, target])

        log.info("=" * 60)
        log.info("✅ Image promotion completed successfully!")
        log.info(f"   Log file: {LOG_FILE}")
        log.info("=" * 60)

    except Exception as exc:
        log.error(f"❌ Promotion failed: {exc}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Docker Image Promotion Tool"
    )
    parser.add_argument("--source", required=True,
                        help="Source image (e.g. mohitdocker241/fitness:v1)")
    parser.add_argument("--target", required=True,
                        help="Target image (e.g. mohitdocker241/fitness:v2-staging)")
    parser.add_argument("--username", default="mohitdocker241",
                        help="Docker Hub username")
    parser.add_argument("--password", required=True,
                        help="Docker Hub password or access token")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Keep local image copies after promotion")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    promote(
        source=args.source,
        target=args.target,
        username=args.username,
        password=args.password,
        cleanup=not args.no_cleanup,
    )
