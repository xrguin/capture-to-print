---
name: capture-to-print
description: Generate or revise editable OpenSCAD from photos and confirmed measurements, then build STL, measure declared geometry, render previews, and package the exact revision. Also runs the unchanged plant-label regression. Requires an execution environment with OpenSCAD, fontconfig, and the declared Python packages.
---

Use the host's existing model and execution tools. No external model API, extra credits, printer dispatch, or automatic publication is part of this workflow. User instructions take precedence over this skill's defaults.

## Establish the design

For a new part, obtain its purpose, critical measured dimensions, required openings/mating surfaces, and printer context. Distinguish measurements from inferred proportions. A photo alone does not establish scale. Read [CAD rules](references/cad-rules.md) when proposing geometry; keep uncertain fit/manufacturing heuristics explicit.

Confirm a brief before generating. Write a self-contained, parametric `.scad` with named modules and editable dimensions, using the bundled Work Sans Bold if text is needed. Preserve each revision. Do not alter required dimensions to fit a bed or weaken checks to make a candidate pass. For the existing plant-label regression, use the packaged source/contract unchanged; its historical 50 mm CadQuery spec is a different design.

## Execute and inspect

The plugin root is two directories above this skill's **resolved** directory (follow symlinks first, e.g. `readlink -f`); it must contain `scripts/capture_to_print.py`. A host that links the skill into a skills root (DeepSeek Harness) makes the link path shorter than the real one, so resolve before going up. Quote paths and use the prepared Python interpreter. Read [contract and commands](references/workflow.md) for supported checks and setup.

Run `python /path/to/plugin/scripts/capture_to_print.py build --output-root /path/to/project/output/runs`. With no source/contract overrides this builds the preserved label. For new parts, pass an explicit source and reviewed contract with its exact SHA-256. The current pilot exports one named part and supports only axis extents and mesh-section spans; reject unsupported critical checks rather than pretending to perform them.

The runner exports, measures, renders, and packages. Read `state.json`, `checks.json`, and build logs. Inspect all four actual-mesh PNG views. A passing exit code is not visual approval. Describe failed and unassessed checks accurately. For the unchanged fixture, stop on failure and preserve evidence; do not repair or modify it. For user-authorized new designs, propose a targeted revision and preserve requirements; stop after two unsuccessful correction attempts and ask for guidance.

## Deliver the revision

Show measured dimensions, face/back/edge/oblique previews, and links to SCAD, STL, report, and draft bundle. Verify manifest hashes using `verify`. The automatic state is `awaiting_user_review`; only an explicit user response about that exact revision can provide acceptance. Record such a response separately with revision/hashes; this pilot has no approval-writing CLI. Never call an unreviewed bundle approved.

On phone, guide the user to save the complete bundle to Files and inspect downloaded files before cleanup. Do not promise offline conversation access, native STL viewing, automatic deletion, or mobile/cloud support that has not been tested. Manual Bambu Studio import is a later step. Computational checks do not establish successful slicing, printing, or physical fit.
