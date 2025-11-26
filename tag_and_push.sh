#!/usr/bin/env bash
set -euo pipefail

# -------- helpers --------
err() {
  echo "ERROR: $*" >&2
}

die() {
  err "$@"
  exit 1
}

run() {
  echo "+ $*"
  "$@"
}

# -------- locate repo root / pyproject.toml --------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYPROJECT="pyproject.toml"
[[ -f "$PYPROJECT" ]] || die "Cannot find $PYPROJECT in $SCRIPT_DIR"

# -------- extract version from pyproject.toml --------
VERSION="$(
python - <<'PY'
import re, sys, pathlib

p = pathlib.Path("pyproject.toml")
text = p.read_text(encoding="utf-8")

# Try tomllib/tomli first for correctness
data = None
try:
    import tomllib  # py>=3.11
    data = tomllib.loads(text)
except Exception:
    try:
        import tomli  # optional backport
        data = tomli.loads(text)
    except Exception:
        data = None

if data is not None:
    v = data.get("project", {}).get("version")
    if v:
        print(v)
        sys.exit(0)

# Fallback: regex parse [project] version line
m = re.search(r'(?ms)^\[project\]\s.*?^\s*version\s*=\s*["\']([^"\']+)["\']', text)
if not m:
    print("", end="")
    sys.exit(0)
print(m.group(1))
PY
)"

[[ -n "$VERSION" ]] || die "Could not read [project].version from pyproject.toml"

echo "Detected version: $VERSION"

# -------- git sanity checks --------
run git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repository."

# Ensure origin remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
  die "Remote 'origin' not configured."
fi

# Optional: ensure main branch exists locally
if ! git show-ref --verify --quiet refs/heads/main; then
  die "Local branch 'main' not found. Check your branch name."
fi

# Check if tag already exists locally or remotely
if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
  die "Tag '$VERSION' already exists locally."
fi

if git ls-remote --tags origin | grep -q "refs/tags/$VERSION$"; then
  die "Tag '$VERSION' already exists on origin."
fi

# -------- tag + push --------
echo "Tagging current commit with '$VERSION'..."
run git tag "$VERSION"

echo "Pushing main to origin..."
run git push origin main

echo "Pushing tags to origin..."
run git push origin --tags

echo "✅ Done. Tagged and pushed version '$VERSION'."
