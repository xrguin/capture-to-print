# Historical core 0.1: Private prototype validation — 2026-10-25

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

For the embedded UI increment, see [UI validation](UI_VALIDATION.md).
