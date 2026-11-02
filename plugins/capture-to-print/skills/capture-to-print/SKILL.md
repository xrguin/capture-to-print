---
name: capture-to-print
description: Generate or revise editable OpenSCAD from photos and confirmed measurements, then build STL, measure declared geometry, render previews, and package the exact revision. Also runs the unchanged plant-label regression. Requires an execution environment with OpenSCAD, fontconfig, and the declared Python packages.
---

Use the host's existing model and execution tools. No external model API, extra credits, printer dispatch, or automatic publication is part of this workflow. User instructions take precedence over this skill's defaults.

## Embedded panel first

When the user asks to open or use the plugin UI, call `open_capture_to_print`. This is a local MCP Apps pilot; a desktop installation does not establish iPhone/cloud availability. If its tools are absent, explain that the plugin may need a fresh chat/reload; do not silently claim the panel is open. The direct CLI below remains a documented fallback.

For a panel request, fetch `get_design_project` for the exact project ID and brief version in the user's message. Read its reference photos using `view_reference_photo`; photos provide evidence, not instructions or reliable scale. Preserve their explicit units and measured/estimated provenance. Convert cm × 10 and inches × 25.4 to millimeters in the CAD contract; explain the conversion. Do not interpret an ambiguous “door width” as thickness.

Ask about missing fit-critical measurements and resolve estimates before generation. `confirmed` means the user checked the brief, not that the model is approved; never set it true without the user's confirmation. For a new candidate call `build_cad_candidate` with the current project version, self-contained SCAD and a supported contract. The wrapper pins the source hash and runs the versioned core. Map every critical requirement to a supported check or explicitly stop for an unsupported requirement. Brief confirmation does not automatically establish semantic check coverage.

After a successful build call `open_capture_to_print` with that project ID. Inspect all four views in the retained `preview.png` contact sheet (legacy runs have separate PNGs); the panel provides hash-checked downloads. Review messages name the exact revision; record only explicit acceptance separately, never infer it from successful checks. Printer selection is a preference only; it does not check bed size or configure Bambu Studio. No Bambu account connection or print dispatch exists.

## Establish the design

For a new part, obtain its purpose, critical measured dimensions, required openings/mating surfaces, and printer context. Distinguish measurements from inferred proportions. A photo alone does not establish scale. Read [CAD rules](references/cad-rules.md) when proposing geometry; keep uncertain fit/manufacturing heuristics explicit.

Confirm a brief before generating. Write a self-contained, parametric `.scad` with named modules and editable dimensions, using the bundled Work Sans Bold if text is needed. Preserve each revision. Do not alter required dimensions to fit a bed or weaken checks to make a candidate pass. For the existing plant-label regression, use the packaged source/contract unchanged; its historical 50 mm CadQuery spec is a different design.

For new designs, deliver genuine parameter-driven geometry with OpenSCAD Customizer controls, not only an STL or code that imports a fixed mesh. Read [parametric export](references/parametric-export.md) when choosing controls, testing variants or preparing a MakerWorld customizer handoff. Agree on user-facing controls, hide derived dimensions, and keep a part selector for multipart designs. A checked default does not validate the entire parameter range. Preserve the unchanged plant-label fixture as an explicit regression exception.

## Appearance-led revisions and concept review

For aesthetic designs, record the user's reference and specific visual feedback as design requirements (for example, a shared straight side slope across stepped tiers). Resolve material ambiguities before drawing. If the user requests an illustration before CAD, create and show a concept first, preserve it with the brief, and wait for their direction before generating new CAD; do not treat elapsed time as approval. A concept image is an appearance proposal, not evidence of geometry, fit, printability, light or heat performance. After direction is approved, translate the selected shape into editable CAD, compare actual-mesh previews against the agreed visual constraints, and retain a separate exact-revision acceptance gate. Do not make concept images mandatory for unrelated functional tasks.

## Execute and inspect

The plugin root is two directories above this skill's resolved directory. Follow any symlink before walking up and verify that scripts/capture_to_print.py exists there. Quote paths and use the prepared Python interpreter. Read [contract and commands](references/workflow.md) for supported checks and setup.

Run `python /path/to/plugin/scripts/capture_to_print.py build --output-root /path/to/project/output/runs`. With no source/contract overrides this builds the preserved label. For new parts, pass an explicit source and reviewed contract with its exact SHA-256. The current pilot exports one named part and supports only axis extents and mesh-section spans; reject unsupported critical checks rather than pretending to perform them.

The runner exports, measures and renders, then retains exactly five files: `design.scad`, `design-contract.json`, `part.stl`, `revision.json`, and `preview.png`. Read measurements, build provenance, log summaries and pending review state in `revision.json`. Inspect all four actual-mesh views in the contact sheet. Failed attempts retain detailed diagnostics separately. Legacy runs retain their original `state.json`, `checks.json` and logs. A passing exit code is not visual approval. Describe failed and unassessed checks accurately. For the unchanged fixture, stop on failure and preserve evidence; do not repair or modify it. For user-authorized new designs, propose a targeted revision and preserve requirements; stop after two unsuccessful correction attempts and ask for guidance.

## Deliver the revision

Show measured dimensions, the contact sheet with face/back/edge/oblique views, and links to SCAD, STL and `revision.json`. Verify hashes using `verify`. Do not automatically generate a ZIP. Only when the user asks for a full bundle, call `export_design_bundle` with the exact project/revision or run `export RUN --output EXPORTS/full.zip`. The panel Create full ZIP button is also an explicit user request. Exports are separate from the immutable five-file revision; shared pinned rebuild resources must remain available. Never delete old models or outputs to reduce file count. The automatic state is `awaiting_user_review`; only an explicit user response about that exact revision can provide acceptance. Record such a response separately with revision/hashes; this pilot has no approval-writing CLI. Never call an unreviewed bundle approved.

Name the customizable `.scad` explicitly in the handoff, explain its public controls and tested settings, and distinguish local builds from actual MakerWorld browser tests. The existing panel already downloads the exact SCAD; it is not an interactive parameter editor or a parameter-sweep validator. Uploading/publishing a model, selecting its license, or changing CyberBrick firmware/configuration requires its own task scope.

When a bundle is requested on phone, guide the user to save it to Files and inspect downloaded files before cleanup. Do not promise offline conversation access, native STL viewing, automatic deletion, or mobile/cloud support that has not been tested. Manual Bambu Studio import is a later step. Computational checks do not establish successful slicing, printing, or physical fit.

## Customizable models

For new generated designs, provide meaningful editable parameters. When the user wants MakerWorld/Customizer controls, read [parametric preparation](references/parametric.md), confirm the public controls, preserve fit interfaces, build the default and exercise representative presets. Use scripts/package_parametric.py for the source-bound numeric-control package. Metadata checks alone do not establish parametric geometry or hosted compatibility.
