#!/bin/bash
# fetch-artifacts.sh — Download latest registry artifacts from pax-market releases
#
# Downloads registry.json, constructs.json, full-catalog.json, and pack archives
# from the latest GitHub Release on JELambert/pax-market.
#
# Uses curl (no gh CLI auth required — pax-market is a public repo).
#
# Usage:
#   scripts/fetch-artifacts.sh

set -euo pipefail

REPO="JELambert/pax-market"
ARTIFACTS_DIR="${PAX_ARTIFACTS_DIR:-artifacts}"
STATIC_PAX_DIR="static/pax"

echo "Fetching latest registry artifacts from $REPO..."

mkdir -p "$ARTIFACTS_DIR" "$STATIC_PAX_DIR"

# Get download URLs from the latest release
RELEASE_JSON=$(curl -sL "https://api.github.com/repos/$REPO/releases/latest")
if echo "$RELEASE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'assets' in d" 2>/dev/null; then
    URLS=$(echo "$RELEASE_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    print(asset['browser_download_url'])
")
else
    echo "ERROR: Could not fetch release data from $REPO"
    echo "$RELEASE_JSON" | head -5
    exit 1
fi

# Download each asset
for url in $URLS; do
    filename=$(basename "$url")
    echo "  Downloading $filename..."
    curl -sL "$url" -o "$ARTIFACTS_DIR/$filename"
done

# Verify required files
for f in registry.json constructs.json full-catalog.json pax-archives.tar; do
    if [ ! -f "$ARTIFACTS_DIR/$f" ]; then
        echo "ERROR: Missing $ARTIFACTS_DIR/$f"
        exit 1
    fi
done

# Unpack pack archives into static/pax/
# Wipe existing archives first so pruned packs don't linger from prior runs.
echo "Unpacking pack archives..."
find "$STATIC_PAX_DIR" -maxdepth 1 -name '*.pax.tar.gz' -delete
tar -xf "$ARTIFACTS_DIR/pax-archives.tar" -C "$STATIC_PAX_DIR" --strip-components=1

# Copy data files
mkdir -p data
cp "$ARTIFACTS_DIR/registry.json" data/registry.json
cp "$ARTIFACTS_DIR/registry.json" static/registry.json
cp "$ARTIFACTS_DIR/constructs.json" data/constructs.json

# Sync PAX authoring guide from the praxis repo (source of truth).
# The website copy must not drift from praxis/docs/PAX_CREATION_GUIDE.md.
# praxis is private, so we read from the local clone at /opt/praxis (kept
# fresh by praxis-autodeploy.timer). Fail the build if the source is missing —
# better to halt deploy than ship stale content.
PRAXIS_GUIDE_SRC="${PRAXIS_GUIDE_SRC:-/opt/praxis/docs/PAX_CREATION_GUIDE.md}"
GUIDE_DEST="static/PAX_CREATION_GUIDE.md"
echo "Syncing PAX_CREATION_GUIDE.md from $PRAXIS_GUIDE_SRC..."
if [ ! -s "$PRAXIS_GUIDE_SRC" ]; then
    echo "ERROR: $PRAXIS_GUIDE_SRC is missing or empty"
    echo "  Ensure /opt/praxis is cloned and praxis-autodeploy.timer is running."
    exit 1
fi
cp "$PRAXIS_GUIDE_SRC" "$GUIDE_DEST"

PACK_COUNT=$(find "$STATIC_PAX_DIR" -name '*.pax.tar.gz' | wc -l)
echo "Done: $PACK_COUNT pack archives ready"
