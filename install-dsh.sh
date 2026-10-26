#!/bin/sh
# Link this skill into a DeepSeek Harness skills root so DSH discovers it.
# The folder must stay where it is; DSH reads the skill through this link.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
skills=${DSH_SKILLS_DIR:-${DSH_HOME:-$HOME/.dsh}/skills}
force=0

for arg in "$@"; do
    case $arg in
        --force) force=1 ;;
        --dir=*) skills=${arg#--dir=} ;;
        -h|--help)
            printf '%s\n' \
                "usage: $0 [--dir=SKILLS_DIR] [--force]" \
                "" \
                "  --dir=DIR   skills root to install into (default: \${DSH_HOME:-\$HOME/.dsh}/skills)" \
                "  --force     replace an existing capture-to-print symlink" \
                "" \
                "DSH also scans <project>/.dsh/skills and <project>/.agents/skills." \
                "DSH refreshed the catalog without a restart in testing; restart if it is not listed."
            exit 0
            ;;
        *)
            echo "unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

if [ ! -f "$root/scripts/capture_to_print.py" ]; then
    echo "not a capture-to-print folder: $root" >&2
    exit 1
fi

mkdir -p "$skills"
dest=$skills/capture-to-print

if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$force" -ne 1 ]; then
        echo "already exists: $dest (pass --force to replace a link)" >&2
        exit 1
    fi
    if [ -L "$dest" ]; then
        rm -f "$dest"
    else
        echo "refusing to replace a real directory: $dest" >&2
        exit 1
    fi
fi

ln -s "$root/skills/capture-to-print" "$dest"
echo "linked: $dest -> $root/skills/capture-to-print"

missing=
for tool in python3.11 openscad fc-match; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        missing="$missing $tool"
    fi
done
if [ -n "$missing" ]; then
    echo "warning: not on PATH:$missing" >&2
    echo "OpenSCAD may also live at /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD." >&2
fi

cat <<EOF

Next:
  cd "$root"
  python3.11 -m venv .venv
  .venv/bin/python -m pip install -r scripts/requirements.txt

Open a DSH session and ask (the catalog refreshed live in testing):
  "Build and check the unchanged plant-label fixture."

Uninstall: rm "$dest"
EOF
