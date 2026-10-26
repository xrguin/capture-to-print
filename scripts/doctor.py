#!/usr/bin/env python3
"""Check the local runtime capture-to-print needs, and print fixes for what is missing.

Run with the interpreter that will execute the runner (the bootstrap venv):
    python scripts/doctor.py
Optional:
    python scripts/doctor.py --openscad /path/to/OpenSCAD --fc-match /path/to/fc-match
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

REQUIRED_MODULES = ("numpy", "scipy", "trimesh", "vtk", "PIL")
DIST_NAMES = {"PIL": "Pillow"}
ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts" / "WorkSans-Bold.ttf"
REQUIREMENTS = ROOT / "scripts" / "requirements.txt"
MAC_OPENSCAD = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")

results: list[tuple[str, str, str]] = []


def record(state: str, name: str, detail: str) -> None:
    results.append((state, name, detail))


def pinned() -> dict[str, str]:
    """Exact versions from requirements.txt, keyed by import name."""
    names = {"Pillow": "PIL"}
    versions: dict[str, str] = {}
    if not REQUIREMENTS.is_file():
        return versions
    for line in REQUIREMENTS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        package, version = (part.strip() for part in line.split("==", 1))
        versions[names.get(package, package)] = version
    return versions


def check_python(minimum: tuple[int, int]) -> None:
    version = sys.version_info
    label = f"{version.major}.{version.minor}.{version.micro}"
    if version[:2] >= minimum:
        record("PASS", "python", f"{label} ({sys.executable})")
    else:
        record("FAIL", "python", f"{label}; need {minimum[0]}.{minimum[1]}+")


def check_modules() -> None:
    expected = pinned()
    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            record("FAIL", f"module:{module}", "not installed in this interpreter")
            continue
        try:
            version = importlib.metadata.version(DIST_NAMES.get(module, module))
        except Exception:
            version = "unknown"
        want = expected.get(module)
        if want and version != "unknown" and version != want:
            record("WARN", f"module:{module}", f"{version}; pinned {want}")
        else:
            record("PASS", f"module:{module}", version)


def check_openscad(explicit: str | None) -> None:
    candidates = [explicit, os.environ.get("OPENSCAD"), shutil.which("openscad"), str(MAC_OPENSCAD)]
    found = next((item for item in candidates if item and Path(item).is_file()), None)
    if not found:
        record("FAIL", "openscad", "not found; install it or pass --openscad")
        return
    try:
        run = subprocess.run([found, "--version"], capture_output=True, text=True, timeout=30)
        text = (run.stdout or run.stderr).strip().splitlines()
        detail = text[0] if text else f"exit {run.returncode}"
    except Exception as error:  # noqa: BLE001 - report, never crash the doctor
        detail = f"could not run --version: {error}"
    record("PASS", "openscad", f"{found} ({detail})")


def check_fc_match(explicit: str | None) -> None:
    found = explicit or os.environ.get("FC_MATCH") or shutil.which("fc-match")
    if not found:
        record("FAIL", "fc-match", "fontconfig not found; install fontconfig")
        return
    try:
        run = subprocess.run(
            [found, "-f", "%{file}\n", "Work Sans:style=Bold"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        matched = (run.stdout or "").strip()
    except Exception as error:  # noqa: BLE001
        record("FAIL", "fc-match", f"could not run: {error}")
        return
    if matched and FONT.is_file() and Path(matched).resolve() == FONT.resolve():
        record("PASS", "fc-match", "Work Sans Bold resolves to the bundled file")
    elif matched and FONT.is_file():
        record("WARN", "fc-match", f"system match is {matched}; runs still pin the bundled font")
    elif FONT.is_file():
        record("WARN", "fc-match", "no Work Sans match; runs still pin the bundled font")
    else:
        record("FAIL", "fc-match", "no usable Work Sans font")


def check_font_file() -> None:
    if FONT.is_file():
        record("PASS", "font:bundled", f"{FONT} ({FONT.stat().st_size} bytes)")
    else:
        record("FAIL", "font:bundled", f"missing {FONT}")


def fix_advice() -> list[str]:
    failed = {name for state, name, _ in results if state == "FAIL"}
    warned = {name for state, name, _ in results if state == "WARN"}
    advice: list[str] = []
    system = platform.system()
    if "python" in failed:
        advice.append(
            "Python 3.11: brew install python@3.11" if system == "Darwin"
            else "Python 3.11: sudo apt install python3.11 python3.11-venv" if system == "Linux"
            else "install Python 3.11"
        )
    if "openscad" in failed:
        advice.append(
            "OpenSCAD: brew install openscad (or https://openscad.org/downloads)" if system == "Darwin"
            else "OpenSCAD: sudo apt install openscad" if system == "Linux"
            else "install OpenSCAD"
        )
    if "fc-match" in failed:
        advice.append(
            "fontconfig: brew install fontconfig" if system == "Darwin"
            else "fontconfig: sudo apt install fontconfig" if system == "Linux"
            else "install fontconfig"
        )
    if any(name.startswith("module:") for name in failed | warned):
        advice.append("Python wheels: bash scripts/bootstrap.sh")
    return advice


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openscad", default=None, help="path to the OpenSCAD executable")
    parser.add_argument("--fc-match", dest="fc_match", default=None, help="path to fc-match")
    parser.add_argument("--skip-modules", action="store_true", help="do not check Python packages")
    args = parser.parse_args()

    check_python((3, 11))
    if not args.skip_modules:
        check_modules()
    check_font_file()
    check_openscad(args.openscad)
    check_fc_match(args.fc_match)

    failed = False
    for state, name, detail in results:
        print(f"{state:4} {name:16} {detail}")
        failed = failed or state == "FAIL"

    advice = fix_advice()
    if advice:
        print("\nFixes:")
        for line in advice:
            print(f"  - {line}")
    if failed:
        print("\nNot ready. Fix the FAIL lines, then run: bash scripts/bootstrap.sh")
    else:
        print("\nReady. Ask a DSH session to use the capture-to-print skill.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
