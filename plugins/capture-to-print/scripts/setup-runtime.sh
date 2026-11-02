#!/bin/sh
# Explicit setup only. Never run during MCP startup; never install OS packages.
set -eu
plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
runtime_home=${CAPTURE_TO_PRINT_RUNTIME_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/capture-to-print-codex/0.4.0-alpha.1}
python_bin=${CAPTURE_TO_PRINT_SETUP_PYTHON:-python3.11}
case ${1:-} in
    ''|--smoke) ;;
    *) echo "Usage: sh scripts/setup-runtime.sh [--smoke]" >&2; exit 2 ;;
esac
if ! "$python_bin" -c 'import sys; assert sys.version_info[:2] == (3,11)' 2>/dev/null; then
    echo 'Python 3.11 is required. Set CAPTURE_TO_PRINT_SETUP_PYTHON to its executable.' >&2
    exit 1
fi
mkdir -p "$runtime_home"
if [ ! -x "$runtime_home/venv/bin/python" ]; then
    "$python_bin" -m venv "$runtime_home/venv"
fi
"$runtime_home/venv/bin/python" -m pip install -r "$plugin_root/scripts/requirements.txt"
if [ "${1:-}" = --smoke ]; then
    "$runtime_home/venv/bin/python" "$plugin_root/scripts/capture_to_print.py" build --output-root "$runtime_home/smoke-runs"
fi
echo "Runtime ready: $runtime_home/venv/bin/python"
