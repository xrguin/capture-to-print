#!/bin/sh
# Create the runtime for capture-to-print outside the installed package, install
# the pinned Python wheels, and check the CAD engine.
#
#   bash scripts/bootstrap.sh             # venv + doctor
#   bash scripts/bootstrap.sh --smoke     # also build the unchanged plant label
#
# OpenSCAD and fontconfig come from the OS package manager; this script does not
# install system software.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
runtime_home=${CAPTURE_TO_PRINT_HOME:-$HOME/.local/share/capture-to-print}
venv=$runtime_home/venv
python=${PYTHON:-python3.11}
smoke=0
openscad_args=

for arg in "$@"; do
    case $arg in
        --smoke) smoke=1 ;;
        --openscad=*) openscad_args="--openscad ${arg#--openscad=}" ;;
        -h|--help)
            sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

if ! command -v "$python" >/dev/null 2>&1; then
    echo "error: $python not found on PATH (set PYTHON=/path/to/python3.11)" >&2
    exit 1
fi

if [ ! -f "$root/scripts/capture_to_print.py" ]; then
    echo "error: not a capture-to-print folder: $root" >&2
    exit 1
fi

mkdir -p "$runtime_home"
if [ ! -x "$venv/bin/python" ]; then
    echo "==> creating venv at $venv"
    "$python" -m venv "$venv"
fi

echo "==> installing pinned wheels"
"$venv/bin/python" -m pip install --quiet --upgrade pip
"$venv/bin/python" -m pip install --quiet -r "$root/scripts/requirements.txt"

echo "==> checking the runtime"
# shellcheck disable=SC2086
"$venv/bin/python" "$root/scripts/doctor.py" $openscad_args

if [ "$smoke" -eq 1 ]; then
    runs=$runtime_home/runs
    mkdir -p "$runs"
    echo "==> building the unchanged plant-label fixture"
    "$venv/bin/python" "$root/scripts/capture_to_print.py" build --output-root "$runs"
fi

cat <<EOF

Runtime: $venv/bin/python
Runner:  "$venv/bin/python" "$root/scripts/capture_to_print.py" build --output-root "$runtime_home/runs"
Skill:   ask a DSH session to "build and check the unchanged plant-label fixture".
EOF
