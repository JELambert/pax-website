#!/bin/bash
# fetch-artifacts.sh — Download latest registry artifacts from pax-market releases
#
# Downloads registry.json, constructs.json, full-catalog.json, and pack archives
# from the latest GitHub Release on JELambert/pax-market.
#
# Usage:
#   scripts/fetch-artifacts.sh
#
# Requires: gh CLI (authenticated) OR curl + jq

set -euo pipefail

REPO="JELambert/pax-market"
ARTIFACTS_DIR="${PAX_ARTIFACTS_DIR:-artifacts}"
STATIC_PAX_DIR="static/pax"

echo "Fetching latest registry artifacts from $REPO..."

mkdir -p "$ARTIFACTS_DIR" "$STATIC_PAX_DIR"

# Try gh CLI first, fall back to curl
if command -v gh &>/dev/null; then
    gh release download latest -R "$REPO" -D "$ARTIFACTS_DIR" --clobber
else
    echo "gh CLI not found, using curl..."
    RELEASE_URL=$(curl -sL "https://api.github.com/repos/$REPO/releases/latest" | jq -r '.assets[] | .browser_download_url' 2>/dev/null)
    if [ -z "$RELEASE_URL" ]; then
        echo "ERROR: Could not fetch release URL"
        exit 1
    fi
    for url in $RELEASE_URL; do
        filename=$(basename "$url")
        echo "  Downloading $filename..."
        curl -sL "$url" -o "$ARTIFACTS_DIR/$filename"
    done
fi

# Verify required files
for f in registry.json constructs.json full-catalog.json pax-archives.tar; do
    if [ ! -f "$ARTIFACTS_DIR/$f" ]; then
        echo "ERROR: Missing $ARTIFACTS_DIR/$f"
        exit 1
    fi
done

# Unpack pack archives into static/pax/
echo "Unpacking pack archives..."
tar -xf "$ARTIFACTS_DIR/pax-archives.tar" -C "$STATIC_PAX_DIR" --strip-components=1

# Copy data files
mkdir -p data
cp "$ARTIFACTS_DIR/registry.json" data/registry.json
cp "$ARTIFACTS_DIR/registry.json" static/registry.json
cp "$ARTIFACTS_DIR/constructs.json" data/constructs.json

PACK_COUNT=$(find "$STATIC_PAX_DIR" -name '*.pax.tar.gz' | wc -l)
echo "Done: $PACK_COUNT pack archives ready"
