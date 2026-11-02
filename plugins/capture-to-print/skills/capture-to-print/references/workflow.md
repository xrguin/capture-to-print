# Execution contract and commands

Run the packaged tools in a prepared local or hosted environment. Use the host model and existing allowance only. Installing a plugin does not install its CAD engine or establish phone/cloud execution. If the host cannot execute the tools within the current allowance, stop and report that capability gap; do not add a paid API or rented server.

## Setup

Python 3.11 with `scripts/requirements.txt`, OpenSCAD, and `fc-match` from fontconfig are required. Work Sans Bold is included and isolated per run. The setup uses the normal OpenSCAD command line, with no GUI interaction required.

On macOS, the app executable is commonly `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`. Pass `--openscad` and `--fc-match` if those executables are not on PATH. On the test Mac, running this OpenSCAD inside the agent sandbox caused Qt CPU-feature startup crashes in earlier work; use the approved native execution route, not repeated sandbox probes. This is a runtime issue, not a change to the CAD design.

On Linux, install a compatible OpenSCAD and fontconfig through the environment's normal setup, then install the pinned Python packages. VTK offscreen rendering needs working EGL/OSMesa or an X display (for example an environment with Xvfb). `QT_QPA_PLATFORM=offscreen` configures OpenSCAD, not the VTK graphics backend. Linux dependency/runtime compatibility must be tested on the actual host; this package does not claim that test has occurred.

## Commands

From the plugin root:

```sh
python scripts/capture_to_print.py build --output-root ./output/runs
python scripts/capture_to_print.py build --source /path/to/design.scad --contract /path/to/contract.json --output-root ./output/runs --timeout 180
python scripts/capture_to_print.py check --mesh /path/to/part.stl --contract /path/to/contract.json --report /path/to/checks.json
python scripts/capture_to_print.py render --mesh /path/to/part.stl --output /path/to/previews
python scripts/capture_to_print.py verify /path/to/run
# Only when the user requests a complete rebuild bundle:
python scripts/capture_to_print.py export /path/to/run --output /path/to/exports/full.zip
python scripts/capture_to_print.py verify /path/to/exports/full.zip
```

Use unique destinations for standalone `check`/`render`; these low-level commands do not manage revisions. Prefer `build`, which always creates a unique run. Do not edit a completed run. The standalone `verify` command checks exact five-file membership, hashes and report bindings, and also supports unchanged legacy run directories. Pass a new full ZIP to verify its membership, resource hashes and revision binding. It does not rerun CAD or establish a protected trust boundary.

`build` accepts self-contained SCAD up to 1 MiB and STL up to 64 MiB. Export, checking and rendering each have their own timeout (default 180 seconds; maximum 600). Setup probes use shorter limits. Timeouts kill the child process group and retain logs. These are time/file limits, not memory quotas or hostile-code isolation.

The runner has no model calls, shell command construction, automatic mesh repair, source scaling, slicing or printer dispatch. Failed stages retain an error state; they cannot produce an approved result. The latest successful automatic state is `awaiting_user_review`.

## Contract version 1

Use `fixtures/plant-label/contract.json` as the complete working example. Required top-level keys:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer 1 |
| `name` | Lowercase letters/digits/hyphens; becomes the STL filename |
| `units` | `mm` only |
| `source_sha256` | SHA-256 of the exact confirmed SCAD bytes |
| `font_pattern` | `Work Sans:style=Bold`, or JSON null for a part with no text |
| `expected_components` | Positive integer; preserved label uses 1 |
| `dimensions` | Nonempty list of explicit measurement checks |

Optional: `notes`, and `build_envelope_mm` containing three positive axis lengths. Unknown fields/methods fail instead of being silently ignored.

Each dimension has a unique `id`, `method`, integer `axis` (0=X, 1=Y, 2=Z), positive `expected_mm`, and positive `tolerance_mm`. Methods:

- `bbox_extent`: max minus min on the stated axis for the complete mesh.
- `plane_span`: also provide `plane_axis` and `plane_offset_mm`. Measures the span of all mesh-plane intersections on another axis. This is appropriate for the straight label stake; it does not measure a general local wall, arbitrary hole or hidden clearance.

Do not rename an unsupported required hole/wall check as an extent just to fit this schema. Extend and test the checker in a separately authorized increment, or report that the part cannot yet be validated.

Topology checks weld identical STL vertices to eight decimal places without filling holes, removing faces, scaling or re-exporting. Reported degeneracies remain failures. Positive signed volume and consistent winding do not prove self-intersection freedom. The report lists unassessed properties explicitly.

## Revision and delivery

A successful revision contains only `design.scad`, `design-contract.json`, `part.stl`, `revision.json` and `preview.png`. The PNG retains all four 720×1000 views in a 2×2 contact sheet; the panel crops views in memory. The JSON combines measurements, hashes, build versions, log summaries and pending review state. Detailed successful-run logs and transient render/font-cache files are removed only from the new attempt. Failed attempts remain separate with diagnostics and are not successful five-file revisions.

Rebuild resources (runner, requirements, software license, pinned font/license/provenance) are stored once per content hash under the run root's `.resources/`. Keep that shared directory: moving only a revision still permits integrity checks, but full export requires its pinned resources. Project briefs/photos and project metadata remain outside revisions. Existing runs are never migrated or cleaned up automatically.

`export` is explicit and writes a new ZIP outside the revision. It does not rebuild geometry or modify any revision file. A compact-format bundle contains `revision/` (five files), `.resources/<hash>/` (six resources), `REBUILD.md`, and `manifest.json` — 13 entries. Extract it elsewhere and follow `REBUILD.md`; both verification and rebuilding work without the original plugin source. Old-format runs can also be exported without modifying their files. Successful logs are summaries, not reconstructed original logs. OpenSCAD binaries/graphics drivers remain external dependencies; cross-machine byte identity is not promised.

Do not alter `revision.json` (or legacy `review.json`) to simulate user acceptance. Record explicit feedback separately with revision and evidence hashes. On iPhone, verify the entire ZIP is downloaded to Files and opens before any permitted cleanup. Platform retention may remain beyond manual deletion; automatic cloud cleanup is not implemented. STL import, slicer orientation and A1 mini/P1P profiles are manual follow-up work, not completed checks.
