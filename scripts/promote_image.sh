#!/bin/bash
# ──────────────────────────────────────────────────────────────
# Docker Image Promotion Script (Shell version)
# Usage: ./promote_image.sh <source_tag> <target_tag>
# Example: ./promote_image.sh mohitdocker241/fitness:v1 mohitdocker241/fitness:v2-staging
# ──────────────────────────────────────────────────────────────
set -euo pipefail

# ─── Colours ────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

# ─── Log file ────────────────────────────────────────────────
LOG_FILE="image_promotion_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

log()  { echo -e "${BLUE}[$(date +%T)]${NC} $*"; }
ok()   { echo -e "${GREEN}[$(date +%T)] ✅ $*${NC}"; }
warn() { echo -e "${YELLOW}[$(date +%T)] ⚠️  $*${NC}"; }
err()  { echo -e "${RED}[$(date +%T)] ❌ $*${NC}"; exit 1; }

# ─── Args ─────────────────────────────────────────────────────
SOURCE="${1:-}"
TARGET="${2:-}"
DOCKER_USER="${DOCKER_USERNAME:-mohitdocker241}"
DOCKER_PASS="${DOCKER_PASSWORD:-}"

[[ -z "$SOURCE" ]] && err "Usage: $0 <source_image:tag> <target_image:tag>"
[[ -z "$TARGET" ]] && err "Usage: $0 <source_image:tag> <target_image:tag>"
[[ -z "$DOCKER_PASS" ]] && err "Set DOCKER_PASSWORD environment variable"

log "═══════════════════════════════════════════"
log "  Docker Image Promotion Starting"
log "  Source : $SOURCE"
log "  Target : $TARGET"
log "═══════════════════════════════════════════"

# Step 1 – Docker Login
log "🔐 Logging in to Docker Hub …"
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin \
  && ok "Docker login successful" \
  || err "Docker login failed"

# Step 2 – Pull
log "📥 Pulling source image: $SOURCE"
docker pull "$SOURCE" && ok "Pulled: $SOURCE" || err "Pull failed"

# Step 3 – Tag
log "🏷️  Tagging $SOURCE → $TARGET"
docker tag "$SOURCE" "$TARGET" && ok "Tagged: $TARGET" || err "Tag failed"

# Step 4 – Push
log "📤 Pushing image: $TARGET"
docker push "$TARGET" && ok "Pushed: $TARGET" || err "Push failed"

# Step 5 – Validate
log "🔍 Validating pushed image …"
docker pull "$TARGET" && ok "Validation passed: $TARGET" || err "Validation failed"

# Step 6 – Cleanup
log "🗑️  Cleaning up local copies …"
docker rmi -f "$SOURCE" "$TARGET" 2>/dev/null || warn "Cleanup skipped (images may still be in use)"

log "═══════════════════════════════════════════"
ok "Image promotion complete! Log: $LOG_FILE"
log "═══════════════════════════════════════════"
