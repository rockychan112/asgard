#!/usr/bin/env bash
# Build the Claude Desktop extension (.mcpb).
#
# An MCPB has to carry its own dependencies — the user's machine supplies only
# a Python interpreter — so this vendors Asgard and everything it imports into
# mcpb/server/lib, then packs the directory.
#
# Usage: scripts/build_mcpb.sh        (from the repository root)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$ROOT/mcpb"
LIB="$BUNDLE/server/lib"
DIST="$ROOT/dist"

command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
command -v npx >/dev/null || { echo "npx not found — needed for @anthropic-ai/mcpb"; exit 1; }

echo "[1/4] vendoring dependencies into server/lib"
rm -rf "$LIB"
mkdir -p "$LIB"
# --no-compile keeps .pyc out of the bundle; they'd be rebuilt on the user's
# interpreter anyway and only inflate the download.
python3 -m pip install --quiet --no-compile --target "$LIB" "$ROOT[mcp]"

echo "[2/4] trimming"
find "$LIB" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$LIB" -type d -name "tests" -prune -exec rm -rf {} + 2>/dev/null || true
# rich (and its pygments dependency) only back the terminal renderer in
# render.py, which the MCP server never calls — ~7MB of the bundle for code
# that can't run here. Verified removable by the import check below.
# cryptography stays: the MCP SDK pulls it in eagerly through mcp.server.auth,
# so the server won't import without it even though this transport never
# performs OAuth.
shopt -s nullglob
for pkg in rich pygments; do
  rm -rf "$LIB/$pkg" "$LIB/$pkg"-*.dist-info
done
shopt -u nullglob

echo "[3/4] sanity-checking the vendored server"
# Import it exactly the way the manifest will: no venv, just the lib directory.
PYTHONPATH="$LIB" python3 -c "
import asgard.mcp_server as m
names = [t.name for t in m._TOOLS]
assert names == ['asgard_status', 'asgard_brief', 'asgard_daily'], names
assert all(t.annotations for t in m._TOOLS), 'every tool needs annotations for directory submission'
from asgard.persona import PERSONA_DIR
from asgard.sources import FIXTURE_DIR
assert PERSONA_DIR.is_dir() and FIXTURE_DIR.is_dir(), 'demo data did not make it into the bundle'
print('    tools:', ', '.join(names))
print('    demo identities:', len(list(PERSONA_DIR.glob('*.yaml'))), '| fixtures:', len(list(FIXTURE_DIR.glob('*.json'))))
"

echo "[4/4] packing"
mkdir -p "$DIST"
VERSION="$(python3 -c "import json,sys; print(json.load(open('$BUNDLE/manifest.json'))['version'])")"
OUT="$DIST/asgard-$VERSION.mcpb"          # pack wants a file path, not a directory
npx --yes @anthropic-ai/mcpb pack "$BUNDLE" "$OUT"

echo
ls -lh "$OUT"
