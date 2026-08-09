#!/usr/bin/env sh

set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
REGION="${REGION:-europe-west3}"
PYTHON_REPOSITORY="${PYTHON_REPOSITORY:-solomon-python}"
ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist/plugins"
REPOSITORY_URL="https://${REGION}-python.pkg.dev/${PROJECT_ID}/${PYTHON_REPOSITORY}/"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

docker run --rm -v "$ROOT_DIR:/workspace" -w /workspace python:3.12-slim \
  sh -c 'pip install --quiet build && for plugin in solomon_theme solomon_property solomon_meetings solomon_facilities; do python -m build --wheel --outdir /workspace/dist/plugins "/workspace/plugins/$plugin"; done'

ACCESS_TOKEN="$(gcloud auth print-access-token)"

# Upload each wheel only if that version is not already in Artifact Registry.
uploaded=0
for whl in "$DIST_DIR"/*.whl; do
  # Parse package name and version from filename, e.g. solomon_theme-0.1.0-py3-none-any.whl
  filename="$(basename "$whl")"
  pkg_name="$(echo "$filename" | sed 's/-[0-9].*//')"
  pkg_version="$(echo "$filename" | sed 's/^[^-]*-//' | sed 's/-.*//')"
  # Normalize underscores to hyphens for Artifact Registry package name
  pkg_name_norm="$(echo "$pkg_name" | tr '_' '-')"

  existing="$(gcloud artifacts versions list \
    --package="$pkg_name_norm" \
    --repository="$PYTHON_REPOSITORY" \
    --location="$REGION" \
    --format="value(name)" 2>/dev/null | grep -c "$pkg_version" || true)"

  if [ "$existing" -gt 0 ]; then
    echo "Skipping $filename (version $pkg_version already in Artifact Registry)"
  else
    docker run --rm -v "$DIST_DIR:/dist:ro" \
      -e TWINE_USERNAME=oauth2accesstoken -e TWINE_PASSWORD="$ACCESS_TOKEN" \
      python:3.12-slim sh -c \
      "pip install --quiet twine && twine upload --repository-url '$REPOSITORY_URL' '/dist/$filename'"
    uploaded=$((uploaded + 1))
  fi
done

if [ "$uploaded" -eq 0 ]; then
  echo "All plugin wheels already up to date in $REPOSITORY_URL"
else
  echo "Published $uploaded plugin wheel(s) to $REPOSITORY_URL"
fi