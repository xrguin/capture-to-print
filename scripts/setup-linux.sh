#!/bin/sh
# Explicit Linux setup for the Codex adapter; never run during MCP startup.
# Installs no OS packages and makes no model API requests.
set -eu
ctp_repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
case ${1:-} in
    ''|--smoke) ;;
    -h|--help) echo 'Usage: sh scripts/setup-linux.sh [--smoke]'; exit 0 ;;
    *) echo 'Usage: sh scripts/setup-linux.sh [--smoke]' >&2; exit 2 ;;
esac
if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
    echo 'This setup targets Linux x86-64. It has not installed anything.' >&2
    exit 1
fi
ctp_setup_python=${CAPTURE_TO_PRINT_SETUP_PYTHON:-python3.11}
"$ctp_setup_python" -c 'import sys; assert sys.version_info[:2] == (3,11)' || {
    echo 'Python 3.11 with venv/pip support is required.' >&2; exit 1;
}
command -v "${CAPTURE_TO_PRINT_OPENSCAD:-openscad}" >/dev/null || {
    echo 'Install OpenSCAD or set CAPTURE_TO_PRINT_OPENSCAD.' >&2; exit 1;
}
command -v "${CAPTURE_TO_PRINT_FC_MATCH:-fc-match}" >/dev/null || {
    echo 'Install fontconfig or set CAPTURE_TO_PRINT_FC_MATCH.' >&2; exit 1;
}
"${CAPTURE_TO_PRINT_NODE:-node}" -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)' || {
    echo 'Node.js 22+ is required.' >&2; exit 1;
}
"$ctp_setup_python" "$ctp_repo_root/plugins/capture-to-print/scripts/verify-source.py"
CAPTURE_TO_PRINT_SETUP_PYTHON="$ctp_setup_python" \
    sh "$ctp_repo_root/plugins/capture-to-print/scripts/setup-runtime.sh" "$@"
