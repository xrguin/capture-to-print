# Embedded UI validation — 2026-10-26

## Demonstrated locally

- Built the MCP Apps panel and stdio server with pinned dependencies. Fourteen Node tests pass: units/provenance, invalid measurements, stale/concurrent edits, path and linked-metadata rejection, inline-script syntax, photo identity/type/checksums, confirmation gates, retained failed candidates, artifact revision/hash binding, and real stdio tool/resource calls.
- Browser QA used the MCP Apps AppBridge with the real compiled MCP backend. Created and saved a measured test brief, selected P1P, attached an actual PNG and displayed its thumbnail, and captured the correct project/version conversation request.
- Loaded the real plant-label build in the panel, switched preview views, displayed its measurements and captured a complete-ZIP download request. The QA host does not invoke a model or save downloads; host delivery remains a separate test.
- The native MCP build exported the byte-identical plant-label SCAD with pinned Work Sans Bold using OpenSCAD 2026.06.12 on macOS arm64. Revision `20261026T162234Z-bba9cf20`: 10/10 required checks passed; overall 48 × 100.05 × 2.6 mm; stake 10 × 2 mm at Y=40 mm; one component, 1,400 triangles. Automatic status: `awaiting_user_review`.
- The core runner is unchanged from 0.1, whose 19 tests and portable rebuild result are recorded in [historical validation](VALIDATION.md).

Local evidence is under `output/`: `ui-native-regression.json`, `ui-qa/projects/`, screenshots, and packaging/installation verification. These private artifacts are excluded from distribution.

## Bugs addressed during QA

Inline bundle insertion initially corrupted JavaScript dollar sequences; replacement now uses a function and a syntax regression test. Controls are disabled during asynchronous form operations to prevent late responses from overwriting in-flight edits. Linked project metadata is rejected alongside existing containment/hash checks.

## Claims not established

Actual Codex/ChatGPT embedded rendering, host message delivery/download saving, iPhone access, cloud execution, fresh Linux execution, Bambu integration, printer fit, slicing, physical printing and user acceptance remain separate verification steps. The panel's download acknowledgement means requested, not saved. Photos retain metadata. The source screen and file hashes are not an independently isolated validator or adversarial sandbox. User confirmation and numerical dimensions do not establish that every functional requirement has been checked.
