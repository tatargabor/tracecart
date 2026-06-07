#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

die() { echo "Error: $1" >&2; exit 1; }
info() { echo "-> $1"; }

current_version() {
  grep -o '"version": *"[^"]*"' "$ROOT/package.json" | grep -o '[0-9][^"]*'
}

bump_version() {
  local ver="$1" type="$2"
  local major minor patch
  IFS='.' read -r major minor patch <<< "$ver"
  case "$type" in
    major) echo "$((major + 1)).0.0" ;;
    minor) echo "$major.$((minor + 1)).0" ;;
    patch) echo "$major.$minor.$((patch + 1))" ;;
    *) die "Invalid bump type: $type (use major|minor|patch)" ;;
  esac
}

# --- Parse args ---

DRY_RUN=false
BUMP_TYPE=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    major|minor|patch) BUMP_TYPE="$arg" ;;
    *) die "Unknown argument: $arg" ;;
  esac
done

if [[ -z "$BUMP_TYPE" ]]; then
  echo "Usage: ./scripts/publish.sh [--dry-run] <major|minor|patch>"
  echo ""
  echo "Current version: $(current_version)"
  exit 1
fi

# --- Preflight checks ---

cd "$ROOT"

[[ -z "$(git status --porcelain)" ]] || die "Working tree not clean. Commit or stash first."
command -v gh &>/dev/null || die "gh CLI not found. Install: https://cli.github.com"

OLD_VERSION="$(current_version)"
NEW_VERSION="$(bump_version "$OLD_VERSION" "$BUMP_TYPE")"

info "Bumping $OLD_VERSION -> $NEW_VERSION"

if [[ "$DRY_RUN" == true ]]; then
  info "[DRY RUN] Would: bump version, build, publish, tag v$NEW_VERSION, create GitHub release."
  exit 0
fi

# --- Bump version ---

sed -i "s/\"version\": \"$OLD_VERSION\"/\"version\": \"$NEW_VERSION\"/" package.json
info "Version bumped in package.json"

# --- Build ---

npm run build
info "Build complete"

# --- Test ---

npm test
info "Tests passed"

# --- Publish ---

npm publish --access public
info "Published @set-trace/cli@$NEW_VERSION to npm"

# --- Git tag + commit ---

git add package.json
git commit -m "v$NEW_VERSION"
git tag "v$NEW_VERSION"
git push && git push --tags
info "Tagged v$NEW_VERSION and pushed"

# --- GitHub release ---

gh release create "v$NEW_VERSION" \
  --title "v$NEW_VERSION" \
  --generate-notes
info "GitHub release created"

echo ""
echo "Published @set-trace/cli@$NEW_VERSION"
echo "  npm: https://www.npmjs.com/package/@set-trace/cli"
echo "  gh:  https://github.com/tatargabor/set-trace/releases/tag/v$NEW_VERSION"
