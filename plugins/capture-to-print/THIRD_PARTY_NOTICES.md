# Third-party notices

## Work Sans Bold

`assets/fonts/WorkSans-Bold.ttf` is unmodified upstream Work Sans Bold, by the Work Sans project contributors, distributed under SIL Open Font License 1.1. The complete copyright and license are in `assets/fonts/OFL.txt`. Do not apply this project's MIT license to the font.

Upstream: https://github.com/weiweihuanghuang/Work-Sans

Pinned commit: `b35c81086186162164947bd39574683073d9b268`. Exact download URLs, sizes and SHA-256 checksums are in `assets/fonts/provenance.json`. Both the font and its license are included in every successful draft bundle. There is no global font installation.

## Runtime dependencies

OpenSCAD, fontconfig, Python, NumPy, SciPy, trimesh, VTK and Pillow are external runtime dependencies under their respective licenses. Their binaries are not redistributed in the source package. Python versions are pinned in `scripts/requirements.txt`; an actual build records versions in `build-record.json`.

## Source fixture and rules

The plant-label source is copied unchanged from the owner's `automatic-cad/models/wip/plant_label_parametric.scad`, SHA-256 `c4a60cf4b5a093bbc0a0b1162b03608d7101027e495cccc394cc965d8a67f1e9`. Original code in this package uses the user-selected MIT license. The rules are distilled from the owner's CAD project; no personal reference photos or unrelated project assets are included.

## Bundled JavaScript dependencies

The distribution includes bundled JavaScript from the MCP SDK, MCP Apps SDK, Zod and their used transitive dependencies. Exact dependency resolution is in package-lock.json. The build gathers each contributing package's copyright and license files into [dist/THIRD_PARTY_LICENSES.txt](dist/THIRD_PARTY_LICENSES.txt). Keep that file with the bundles. Node.js and the build tool esbuild are external dependencies; their executables are not redistributed.
