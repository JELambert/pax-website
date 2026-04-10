#!/bin/bash
# ct105-autodeploy.sh — PAX Website auto-deploy from CT 105
#
# Run via systemd timer every 5 minutes.
# Checks for:
#   1. New commits on pax-website (website changes)
#   2. New releases on pax-market (registry artifacts)
# If either changed: fetch artifacts → generate content → hugo build → rsync to CT 110
#
# Logs to /var/log/pax-autodeploy.log

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_DIR="/opt/pax-website"
REGISTRY_REPO="JELambert/pax-market"
CT110_WEBROOT="root@192.168.68.110:/var/www/marketplace/"
STAGING_DIR="/tmp/pax-marketplace-staging"
LOG_FILE="/var/log/pax-autodeploy.log"
PYTHON_BIN="/opt/pax-website/.venv/bin/python"
HUGO_BIN="/opt/praxis/bin/hugo"
LOCK_FILE="/var/run/pax-autodeploy.lock"
RELEASE_TAG_FILE="/opt/pax-website/.last-registry-release"

# Fall back to system python3 if venv not present
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ---------------------------------------------------------------------------
# Lock: prevent overlapping runs
# ---------------------------------------------------------------------------
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log "Already running (lock held). Skipping this cycle."
    exit 0
fi

# ---------------------------------------------------------------------------
# Check for changes
# ---------------------------------------------------------------------------
cd "$REPO_DIR"
NEEDS_BUILD=false

# Check 1: website repo commits
log "Checking website repo..."
git fetch origin main --quiet 2>>"$LOG_FILE"
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)
if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    log "Website repo has new commits: ${LOCAL_HASH:0:8} → ${REMOTE_HASH:0:8}"
    git pull --ff-only origin main >>"$LOG_FILE" 2>&1
    NEEDS_BUILD=true
fi

# Check 2: registry releases
log "Checking registry releases..."
CURRENT_TAG=""
if [ -f "$RELEASE_TAG_FILE" ]; then
    CURRENT_TAG=$(cat "$RELEASE_TAG_FILE")
fi
LATEST_TAG=$(curl -sL "https://api.github.com/repos/$REGISTRY_REPO/releases/latest" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tag_name',''))" 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ] && [ "$LATEST_TAG" != "$CURRENT_TAG" ]; then
    log "Registry has new release: $CURRENT_TAG → $LATEST_TAG"
    NEEDS_BUILD=true
fi

if [ "$NEEDS_BUILD" = false ]; then
    log "No changes detected. Nothing to do."
    exit 0
fi

# ---------------------------------------------------------------------------
# Fetch registry artifacts
# ---------------------------------------------------------------------------
log "Fetching registry artifacts..."
if ! bash scripts/fetch-artifacts.sh >>"$LOG_FILE" 2>&1; then
    log "ERROR: fetch-artifacts.sh failed. Aborting."
    exit 1
fi

# ---------------------------------------------------------------------------
# Generate Hugo content
# ---------------------------------------------------------------------------
log "Generating content from catalog..."
if ! "$PYTHON_BIN" scripts/generate-content.py >>"$LOG_FILE" 2>&1; then
    log "ERROR: generate-content.py failed. Aborting — CT 110 unchanged."
    exit 1
fi

# ---------------------------------------------------------------------------
# Hugo build into staging dir
# ---------------------------------------------------------------------------
log "Building Hugo site..."
rm -rf "$STAGING_DIR"

if ! "$HUGO_BIN" --minify --destination "$STAGING_DIR" >>"$LOG_FILE" 2>&1; then
    log "ERROR: Hugo build failed. Aborting — CT 110 unchanged."
    exit 1
fi

# ---------------------------------------------------------------------------
# Verify build output
# ---------------------------------------------------------------------------
if [ ! -f "$STAGING_DIR/index.html" ]; then
    log "ERROR: No index.html in staging. Aborting."
    exit 1
fi

if [ ! -f "$STAGING_DIR/registry.json" ]; then
    log "ERROR: registry.json missing from staging. Aborting."
    exit 1
fi

HTML_COUNT=$(find "$STAGING_DIR" -name '*.html' | wc -l)
PACK_COUNT=$(find "$STAGING_DIR/pax" -name '*.pax.tar.gz' 2>/dev/null | wc -l)
log "Build verified: ${HTML_COUNT} HTML files, ${PACK_COUNT} pack archives"

if [ "$HTML_COUNT" -lt 10 ]; then
    log "ERROR: Suspiciously few HTML files (${HTML_COUNT}). Refusing to deploy."
    exit 1
fi

# ---------------------------------------------------------------------------
# rsync to CT 110
# ---------------------------------------------------------------------------
log "Deploying to CT 110 via rsync..."
if ! rsync -a --delete "$STAGING_DIR/" "$CT110_WEBROOT" >>"$LOG_FILE" 2>&1; then
    log "ERROR: rsync to CT 110 failed."
    exit 1
fi

# Save release tag
if [ -n "$LATEST_TAG" ]; then
    echo "$LATEST_TAG" > "$RELEASE_TAG_FILE"
fi

log "Deploy complete. ${HTML_COUNT} pages, ${PACK_COUNT} packs live."
