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
CT110_HOST="root@192.168.68.110"
CT110_WEBROOT="${CT110_HOST}:/var/www/marketplace/"
CT110_BACKUP_WEBROOT="${CT110_HOST}:/var/www/marketplace-backup/"
STAGING_DIR="/tmp/pax-marketplace-staging"
LOG_FILE="/var/log/pax-autodeploy.log"
PYTHON_BIN="/opt/pax-website/.venv/bin/python"
HUGO_BIN="/opt/praxis/bin/hugo"
LOCK_FILE="/var/run/pax-autodeploy.lock"
RELEASE_TAG_FILE="/opt/pax-website/.last-registry-release"
# Optional: set PAX_ALERT_WEBHOOK to a URL to receive failure POSTs
PAX_ALERT_WEBHOOK="${PAX_ALERT_WEBHOOK:-}"

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
# Failure notification + trap
# ---------------------------------------------------------------------------
notify_failure() {
    local msg="pax-autodeploy FAILED on $(hostname) at $(date '+%Y-%m-%d %H:%M:%S'): $*"
    log "ALERT: $msg"
    if [ -n "$PAX_ALERT_WEBHOOK" ]; then
        curl -sS -X POST "$PAX_ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$msg\"}" \
            >> "$LOG_FILE" 2>&1 || true
    fi
}

on_error() {
    notify_failure "script exited with error on line $1"
}
trap 'on_error $LINENO' ERR

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
UPLOAD_SERVICE_CHANGED=false
if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    log "Website repo has new commits: ${LOCAL_HASH:0:8} → ${REMOTE_HASH:0:8}"
    # Capture path-scoped diff BEFORE the pull so we know what to restart.
    if git diff --name-only "$LOCAL_HASH" "$REMOTE_HASH" 2>/dev/null | grep -qE '^upload-service/'; then
        UPLOAD_SERVICE_CHANGED=true
        log "  upload-service/ files changed in this update."
    fi
    git pull --ff-only origin main >>"$LOG_FILE" 2>&1
    NEEDS_BUILD=true
fi

# ---------------------------------------------------------------------------
# Restart pax-upload.service if its source changed.
# Done independently of the static-site build: upload-service runs locally on
# CT 105 and a restart is unrelated to whether the Hugo build/rsync succeeds.
# Only restart when files actually changed — even a sub-second restart drops
# any in-flight upload, so we don't want to do it on every cycle.
# ---------------------------------------------------------------------------
if [ "$UPLOAD_SERVICE_CHANGED" = true ]; then
    log "Restarting pax-upload.service (source changed)..."
    if systemctl restart pax-upload.service >>"$LOG_FILE" 2>&1; then
        sleep 1
        if systemctl is-active --quiet pax-upload.service; then
            log "pax-upload.service restarted successfully."
        else
            log "ERROR: pax-upload.service inactive after restart."
            notify_failure "pax-upload.service inactive after restart"
        fi
    else
        log "ERROR: systemctl restart pax-upload.service failed."
        notify_failure "pax-upload.service restart command failed"
    fi
fi

# Check 2: registry releases
# Compare updated_at timestamp — tag_name is always "latest" (rolling tag) so it
# never changes. updated_at reflects when artifacts were last uploaded.
log "Checking registry releases..."
CURRENT_TS=""
if [ -f "$RELEASE_TAG_FILE" ]; then
    CURRENT_TS=$(cat "$RELEASE_TAG_FILE")
fi
RELEASE_JSON=$(curl -sL "https://api.github.com/repos/$REGISTRY_REPO/releases/latest" 2>/dev/null || echo "")
LATEST_TAG=$(echo "$RELEASE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tag_name',''))" 2>/dev/null || echo "")
LATEST_TS=$(echo "$RELEASE_JSON"  | python3 -c "import sys,json; print(json.load(sys.stdin).get('updated_at',''))" 2>/dev/null || echo "")

if [ -n "$LATEST_TS" ] && [ "$LATEST_TS" != "$CURRENT_TS" ]; then
    log "Registry has new artifacts: ${CURRENT_TS:-none} → $LATEST_TS (tag: $LATEST_TAG)"
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
# Snapshot current CT 110 webroot for rollback
# ---------------------------------------------------------------------------
log "Snapshotting current CT 110 webroot for rollback..."
if ssh "${CT110_HOST}" "test -d /var/www/marketplace && cp -a /var/www/marketplace/. /var/www/marketplace-backup/" >>"$LOG_FILE" 2>&1; then
    log "Snapshot saved to ${CT110_HOST}:/var/www/marketplace-backup/"
else
    log "WARNING: Could not snapshot CT 110 webroot — continuing without rollback capability"
fi

# ---------------------------------------------------------------------------
# rsync to CT 110
# ---------------------------------------------------------------------------
log "Deploying to CT 110 via rsync..."
if ! rsync -a --delete "$STAGING_DIR/" "$CT110_WEBROOT" >>"$LOG_FILE" 2>&1; then
    log "ERROR: rsync to CT 110 failed. Attempting rollback..."
    if ssh "${CT110_HOST}" "test -d /var/www/marketplace-backup && rsync -a --delete /var/www/marketplace-backup/. /var/www/marketplace/" >>"$LOG_FILE" 2>&1; then
        log "Rollback succeeded — CT 110 restored to last-good state."
    else
        log "ERROR: Rollback also failed. CT 110 may be in a degraded state. Manual intervention required."
    fi
    notify_failure "rsync to CT 110 failed"
    exit 1
fi

# Save release timestamp so next run knows we're current
if [ -n "$LATEST_TS" ]; then
    echo "$LATEST_TS" > "$RELEASE_TAG_FILE"
fi

log "Deploy complete. ${HTML_COUNT} pages, ${PACK_COUNT} packs live."
