# Private prototype validation — 2026-10-25

This record covers the package and local CAD workflow, not installed phone/cloud access.

## Observed results

- **19 automated tests passed**, 0 failed: mesh dimensions/sections, scale mismatch, missing sections, insufficient envelope without resizing, open/inverted/degenerate/nonfinite/empty meshes, intent-dependent component counts, unsupported contracts, changed source/external dependencies, timeout termination, stale artifacts, export/render failures, checksum/ZIP mismatch, stale review evidence, and manifest path traversal.
- **Skill validation passed** using the Skill Creator validator.
- **Portable plugin manifest schema validation passed**, against `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. This does not validate host-specific extension semantics or installation.
- **Native OpenSCAD export passed** for the unchanged plant-label source and verified Work Sans Bold. The exported STL has 1,400 triangles, one connected component, consistent winding, positive volume, no detected degenerate triangles, and watertight edge incidence.
- **Four actual-mesh previews rendered and were visually inspected**: face, back, edge and oblique. Basil is legible on the face, the back is plain, and embossing is visible at the edge and oblique angles. Geometric crease outlines improve readability without changing the mesh.
- **Portable draft ZIP verified and rebuilt successfully after extraction to a different folder**, using only its bundled runner/source/contract/font plus installed runtime dependencies. All 24 manifest-listed files verified. Original and rebuilt STL bytes were identical in this same-machine trial; bounds, extents, volume, triangles and component count also matched.
- **No paid model/API calls, extra credits, cloud deployment, plugin installation, publication, slicing or printing** were performed.
- **Preservation passed:** 1,555 pre-existing entries remained unchanged; only an append to the root project's `AGENTS.md` changed an existing file. No unexpected added files were found outside the new prototype and its dated preservation folder; Git HEAD and existing tracked edits were retained. Inventory excludes Git internals and named cache/environment directories.

| Required dimension | Measured (mm, rounded) | Expected (mm) | Tolerance (mm) | Result |
| --- | ---: | ---: | ---: | --- |
| Whole-mesh X / head width | 48.000 | 48 | 0.1 | Pass |
| Whole-mesh Y / total length | 100.050 | 100.05 | 0.1 | Pass |
| Whole-mesh Z / body plus embossing | 2.600 | 2.6 | 0.1 | Pass |
| Stake X span at Y=40 | 10.000 | 10 | 0.1 | Pass |
| Stake Z span at Y=40 | 2.000 | 2 | 0.1 | Pass |

Volume: **3,776.6294385 mm³**. Bounds: X `[-24, 24]`, Y `[-0.05, 100]`, Z `[-1, 1.6]` mm, rounded. The source's coordinate frame is preserved; the part has not been moved onto a slicer bed.

## Runtime and revision

- macOS 27.0.1, arm64; Python 3.11.15.
- OpenSCAD 2026.06.12, native execution outside the agent sandbox.
- NumPy 2.4.6, SciPy 1.17.1, trimesh 4.12.2, VTK 9.6.1, Pillow 12.3.0.
- Font: Work Sans Bold, upstream commit `b35c81086186162164947bd39574683073d9b268`, SHA-256 `e32ca4477095e3b259915d3db0b2acd1091e9d142706a54ba3eb2dcc54184c41`. Verified both by isolated fontconfig lookup and OpenSCAD's actual font-match trace.
- Original SCAD SHA-256: `c4a60cf4b5a093bbc0a0b1162b03608d7101027e495cccc394cc965d8a67f1e9`.
- Tested runner SHA-256: `708035ead518507535c6c517c7058c27aa2993dd83836815470864b15b0e0e88`.
- Review candidate: `20261025T222153Z-e4d92893`; relocated rebuild: `20261025T222251Z-5ee65b29`.

Local evidence is under `output/runs/plant-label-20261025T222153Z-e4d92893/`, `output/relocation-test/`, and `output/validation-record.json`. The source package intentionally excludes these generated files. The candidate's own draft bundle includes its reports, logs and previews.

## Failures encountered and retained

The first attempt stopped before OpenSCAD export because setting `FC_DEBUG=0` caused diagnostic lines in the fontconfig response. The runner now removes that environment variable for the probe and enables it only for export evidence. No font fallback was accepted. The failed run remains in the local output folder.

An earlier successful render made face-on embossing hard to see because the text tops and body had the same shading. Preview rendering now draws actual mesh creases and lights each view. Source and dimensions were not changed; the earlier run is retained separately.

## Limits and next gate

User acceptance is **pending** for the stated candidate. Agent visual review is recorded separately; the automatic bundle retains pending user/agent review fields so it is not rewritten after packaging.

No fresh dependency installation, Linux runtime, actual plugin loader, iPhone download/cleanup, cloud execution, Bambu Studio import/slicing, printer profile, or physical print/fit was tested in this increment. The intended next gate is an authenticated private installation and iPhone-to-cloud run within the existing plan allowance. No account setup was inferred from desktop success.

General minimum wall thickness, self-intersection freedom, hole/clearance semantics, material strength, printability and physical fit remain unassessed. The checker and generator are not independently protected from modification. Hashes detect mismatches against the recorded manifest, not adversarial forgery. Same-machine byte equality is not a cross-platform reproducibility guarantee.

## DeepSeek Harness (DSH) port — 2026-10-26

- Skill linked at `<repo>/.dsh/skills/capture-to-print` (relative symlink into this folder). DSH listed it in the session skill catalog without a restart.
- Resolution tested as written in `SKILL.md`: `readlink -f` on the skill base directory, two levels up, `scripts/capture_to_print.py` present. The link path alone (`.dsh/skills/capture-to-print`) does not resolve to the plugin root; the resolved path does.
- Build through that path: `plant-label-20261026T163403Z-6697d826`, `awaiting_user_review`, required checks passed, 48 × 100.05 × 2.6 mm, 1,400 triangles, one component, 24 manifest files verified, 19 tests pass.
- STL SHA-256 `abdaea072a97e7841495dc4da8f3a82c9d9ebc3e7a8e350100e34551bc8d5a8c`, identical to the 2026-10-25 candidate and to a second run today (`plant-label-20261026T163315Z-ce13e21b`) on this machine.
- Agent visual review of all four views: face shows the "Basil" emboss outlines, back is flat, edge shows the single step of the emboss, no floating or missing geometry. User acceptance remains pending.
- `install-dsh.sh` links the skill into `${DSH_HOME:-$HOME/.dsh}/skills` or `--dir`. Link, duplicate refusal and `--force` replacement were tested in a temporary directory. No install into the real `~/.dsh/skills` was performed; the project-level link was used instead.

Not tested here: DSH on Linux or another Mac, a published npm plugin bundle, the global installer path, and any phone surface. DSH has no phone client, so a photo arrives as a file rather than from a live camera.

## Publishable bundle — 2026-10-26

- Built this folder from `prototypes/capture-to-print-plugin/` (0.1 core, unchanged runner SHA-256 `708035ead518507535c6c517c7058c27aa2993dd83836815470864b15b0e0e88`) and added the DSH bundle layer: `package.json` with `dsh.bundle.patch`, `cordis.patch.yml`, and `lib/index.mjs`, which links the bundled skill into `$DSH_HOME/skills` and the package root into `$CAPTURE_TO_PRINT_HOME/app` on load, removing only its own links on dispose.
- Added `scripts/doctor.py` (Python, OpenSCAD, fontconfig, pinned wheels, bundled font) and `scripts/bootstrap.sh` (venv outside the package, pinned wheels, optional `--smoke` fixture build).
- Verified on macOS arm64, Node 24 / Python 3.11.7: 4 Node link tests pass (idempotent re-apply, foreign link/directory refusal, explicit roots, dispose); 19 Python workflow tests pass; `bootstrap.sh --smoke` created a fresh venv, installed the pinned wheels, ran the doctor (all PASS; the `fc-match` WARN is expected because Work Sans is not installed system-wide and runs pin the bundled file), and built the fixture to `awaiting_user_review` with 48 × 100.05 × 2.6 mm and all required checks passing.
- Not tested: installation through `dsh plugin add` into a real profile, a second machine or Linux, private-repository authentication for another user, uninstall through the plugin manager, and any phone or hosted route. The package declares `engines.node >= 22.19.0`; only Node 24 was exercised.
