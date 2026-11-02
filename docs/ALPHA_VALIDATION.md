# Public alpha validation — 2026-11-02

Release: **0.4.0-alpha.1**. Code copied to a new release workspace; original
prototypes, installed plugins, private CAD projects and old DSH tag are preserved.

| Component | Result |
|---|---|
| Codex Python tests | 32 pass |
| Codex Node/server tests | 17 pass after a lockfile-based npm install/build |
| DSH Python tests | 19 pass |
| DSH bundle-link tests | 4 pass |
| Codex setup script | Fresh isolated Python 3.11 venv, pinned direct dependencies, unchanged-label smoke build passes |
| DSH bootstrap | Separate fresh venv, doctor and unchanged-label build pass |
| Release shell launcher | Real SDK stdio client exercises the packaged launcher and fresh runtime |
| Compact artifacts/export | Five files retained; reads hash-bound; ZIP refused before explicit export; export leaves revision bytes unchanged |
| Export relocation | Independently extracted explicit bundle verifies |

Current actual MCP regression: **20261102T220838Z-c10f5cf0**. Ten required checks pass;
plant label measures **48 × 100.05 × 2.6 mm**, including the source tip/embossing.
Source fixture SHA-256 remains
`c4a60cf4b5a093bbc0a0b1162b03608d7101027e495cccc394cc965d8a67f1e9`.
STL SHA-256: `abdaea072a97e7841495dc4da8f3a82c9d9ebc3e7a8e350100e34551bc8d5a8c`.

Work Sans Bold's exact bundled file and engine match trace are verified. The
system-wide fontconfig fallback remains Verdana, but it is not used in these
isolated builds. The smoke-build face/back/edge/oblique actual-mesh contact sheet
was visually inspected. The MCP run's STL matches that inspected geometry.

Mac environment: Apple Silicon, Python 3.11.15, OpenSCAD 2026.06.12, NumPy 2.4.6,
SciPy 1.17.1, trimesh 4.12.2, VTK 9.6.1 and Pillow 12.3.0. Top-level requirements
are pinned; transitive Python resolution is not a complete multi-platform lock.
The actual fresh environment is recorded in TESTED_PYTHON_ENVIRONMENT.txt.

No new machine or Linux/Windows CAD execution is claimed. These are fresh Python
environments on the existing Mac with existing OS CAD tools. Actual public-Git
installation inside a different user's Codex host, actual host download saves,
ordinary ChatGPT mobile, hosted execution and directory review remain untested.
No physical print/fit or new model acceptance occurred.

The test used the host allowance and local tools. No model API, paid hosting,
GitHub Actions workflow, printer dispatch or silent installed-plugin upgrade was
introduced. Historical adapter validation files are retained for provenance;
this file describes the current release checks.
