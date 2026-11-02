# Parametric OpenSCAD deliverable

Use for new designs and revisions that will be customized by other makers.
This is an authoring and review workflow over the existing SCAD export. The
runtime does not independently enforce Customizer syntax or validate a complete
family of models. Do not modify the preserved plant-label fixture to add controls.

## Choose the public controls

Agree on useful dimensions, discrete options and proposed limits before modeling.
Use literal defaults before the first module, readable descriptions and units,
Customizer groups (`/* [Group] */`), sliders (`// [minimum:step:maximum]`) or
enumerations. Put derived quantities and hardware constants in `/* [Hidden] */`.
Build geometry from the parameters. Scaling an imported STL is not the requested
editable parametric design. Prefer self-contained source; declare any necessary
font/library dependency and verify it on the target platform.

Use coupled formulas and `assert()` to reject inconsistent values, such as a
compartment smaller than its wall allowance or a part exceeding its selected
printer envelope. Do not clamp requested sizes or silently change manufacturing
clearances. Slider limits are interface hints; assertions and geometry checks
still matter. Keep functional contact surfaces smooth where ribs would interfere.

For hardware designs, distinguish measured interfaces, manufacturer reference
dimensions and chosen fit allowances. New fit allowances need physical coupons.
Do not expose a motor mount, gear ratio, pivot or movement limit as an unrestricted
control before it has an explicit validation plan. Geometry controls do not update
servo firmware automatically. Controller settings, power and load tests are separate.

## Validate declared settings

Keep the customizable source unchanged. To test a setting through the current
one-part runner, create a separate materialized SCAD revision with only the
declared parameter assignments changed; record the canonical source hash,
parameter values, materialized source hash and its own reviewed contract. Do not
pass a different source under the default source hash or reuse default reports.
No new parameter CLI flag or sweep tool exists in this pilot.

At minimum build the default, useful smaller/larger presets and combinations that
stress fit, wall allowance or bed placement. Include an intentionally invalid
combination to verify the relevant rejection. Pick tests based on the geometry,
not a universal number of samples. Measure requirements from final meshes;
preserve every revision and retain failed outputs. Label unsampled settings and
unsupported feature checks accurately. Sampling does not prove a continuous range,
strength, fit, collision-free motion or successful physical prints.

Every customized output is a new candidate with new measurements, previews and
pending user acceptance. Record physical outcomes against the exact parameter set.

## Multipart and MakerWorld handoff

Provide a one-part selector for ordinary OpenSCAD/STL export; package every named
part and quantity separately. An assembled preview is not the print layout.
The current core builds one part per run, so use separate runs and a family index.

For a separately requested MakerWorld multi-plate source, the manufacturer documents
`mw_plate_1()`, `mw_plate_2()` and optional `mw_assembly_view()` modules. The cited
announcement says multi-plate mode disables STL download, so retain a separate
ordinary part-selector SCAD. Do not assume that native STL exports prove the
MakerWorld path; verify controls, representative settings and downloads in its
current browser implementation before claiming platform compatibility. Do not
upload or publish automatically. Model licensing is separate from the MIT tools.

Current deliverables: customizable SCAD, checked default STL(s), dimension/check
reports, actual-STL previews and exact revision bundle, with a clear record of
tested presets and platform-test status. A future in-panel parameter editor and
automatic sweep runner are additional implementation work, not current features.

Sources checked 2026-10-29:

- [OpenSCAD Customizer manual](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Customizer)
- [Bambu Lab multi-plate announcement](https://forum.bambulab.com/t/parametric-model-maker-v0-10-0-multi-plate-3mf-generation/144618)
