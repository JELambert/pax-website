#!/bin/bash
# deploy.sh — Emergency local build and deploy of PAX Marketplace to CT 110
#
# Use this when you need to force an immediate deploy from your local machine
# without waiting for the CT 105 autodeploy timer.
#
# Usage:
#   ./scripts/deploy.sh         # generate + build + deploy
#   ./scripts/deploy.sh --url   # show the current tunnel URL
#
# Prerequisites: hugo, python3, python3-yaml (pyyaml), sshpass
# Environment:  PX_PW — Proxmox root password

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PX_HOST="192.168.68.70"
PX_PW="${PX_PW:?Set PX_PW environment variable (Proxmox root password)}"
CT_ID="110"
DOMAIN="https://pax-market.com"

ssh_cmd() {
  sshpass -p "$PX_PW" ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR "root@$PX_HOST" "$@"
}

if [ "${1:-}" = "--url" ]; then
  echo "Marketplace URL: $DOMAIN"
  echo "  LAN: http://192.168.68.110"
  exit 0
fi

cd "$PROJECT_DIR"

# Step 1: Generate Hugo content from pax/
echo "==> Generating marketplace content from pax/..."
python3 scripts/generate-from-git.py
echo

# Step 2: Build Hugo
echo "==> Building Hugo site..."
hugo --minify
echo

# Verify build before touching CT 110
if [ ! -f public/index.html ]; then
  echo "ERROR: Hugo build produced no index.html — aborting"
  exit 1
fi
if [ ! -f public/registry.json ]; then
  echo "ERROR: registry.json missing from public/ — aborting"
  exit 1
fi
echo "  Build OK: $(find public -name '*.html' | wc -l | tr -d ' ') HTML files"

# Step 3: Deploy to container via Proxmox host (atomic swap)
echo "==> Deploying to CT $CT_ID (192.168.68.110) via Proxmox host..."
ssh_cmd "pct exec $CT_ID -- rm -rf /var/www/marketplace-deploy-tmp && mkdir -p /var/www/marketplace-deploy-tmp"
tar czf - -C public . | ssh_cmd "pct exec $CT_ID -- tar xzf - -C /var/www/marketplace-deploy-tmp"
ssh_cmd "pct exec $CT_ID -- bash -c 'rm -rf /var/www/marketplace-backup; mv /var/www/marketplace /var/www/marketplace-backup 2>/dev/null || true; mv /var/www/marketplace-deploy-tmp /var/www/marketplace'"
echo "  Deployed $(du -sh public | cut -f1) to /var/www/marketplace"

echo
echo "==> Deployment complete!"
echo "  LAN:    http://192.168.68.110"
echo "  Public: $DOMAIN"
