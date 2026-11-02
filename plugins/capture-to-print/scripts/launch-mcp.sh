#!/bin/sh
# Keep setup outside the installed plugin and stdout reserved for MCP messages.
set -eu
plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
runtime_home=${CAPTURE_TO_PRINT_RUNTIME_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/capture-to-print-codex/0.4.0-alpha.1}
node_bin=${CAPTURE_TO_PRINT_NODE:-}
if [ -z "$node_bin" ]; then
    node_bin=$(command -v node || true)
fi
if [ -z "$node_bin" ]; then
    for candidate in /opt/homebrew/bin/node /usr/local/bin/node /usr/bin/node; do
        if [ -x "$candidate" ]; then node_bin=$candidate; break; fi
    done
fi
if [ -z "$node_bin" ] || ! "$node_bin" -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)' 2>/dev/null; then
    echo 'capture-to-print requires Node.js 22+. Set CAPTURE_TO_PRINT_NODE to its executable if it is not on PATH.' >&2
    exit 1
fi
if [ -z "${CAPTURE_TO_PRINT_PYTHON:-}" ]; then
    CAPTURE_TO_PRINT_PYTHON=$runtime_home/venv/bin/python
fi
if [ ! -x "$CAPTURE_TO_PRINT_PYTHON" ]; then
    echo "capture-to-print runtime missing. Run: sh $plugin_root/scripts/setup-runtime.sh" >&2
    exit 1
fi
export CAPTURE_TO_PRINT_PYTHON
if [ -z "${CAPTURE_TO_PRINT_OPENSCAD:-}" ] && [ -x /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD ]; then
    CAPTURE_TO_PRINT_OPENSCAD=/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD
    export CAPTURE_TO_PRINT_OPENSCAD
fi
if [ -z "${CAPTURE_TO_PRINT_FC_MATCH:-}" ] && [ -x /opt/homebrew/bin/fc-match ]; then
    CAPTURE_TO_PRINT_FC_MATCH=/opt/homebrew/bin/fc-match
    export CAPTURE_TO_PRINT_FC_MATCH
fi
exec "$node_bin" "$plugin_root/dist/server.mjs"
