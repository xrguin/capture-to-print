# capture-to-print repository instructions

- This alpha contains a legacy DSH adapter at the root and the Codex 0.4.0 adapter
  under plugins/capture-to-print. Preserve their explicit version distinction.
- Never modify the unchanged plant-label source/contract/font without recording
  a new fixture revision and checking the new geometry. Preserve model outputs.
- Use the host model. Do not add paid model APIs, buy credits, publish updates,
  deploy hosting or operate printers without a user request covering the action.
- Keep project data, photos, machine overlays and environments out of releases.
- A passing build awaits review; user print/fit outcomes need explicit evidence.
- Run the relevant Node/Python tests and an actual unchanged-fixture regression
  for a release. The DSH adapter's smoke test uses scripts/bootstrap.sh --smoke;
  the Codex adapter uses tests/native-regression.mjs with declared runtime paths.
- New model revisions retain exactly five files; full bundles require explicit
  export. Do not rewrite existing revisions to fit the new layout.
- Ordinary ChatGPT mobile execution is not implemented; do not market local MCP
  or a GitHub release as phone support. See docs/PHONE.md.
- Read known issues before changing requirements. Corrections may not weaken
  declared geometry checks or silently repair a reference mesh.

## Portability continuation — 2026-11-03

The current main branch adds scripts/setup-linux.sh and docs/LINUX_SETUP.md,
MOVING_PROJECTS.md and PORTABILITY_VALIDATION.md. Preserve five-file revisions
and their shared resources during migration; private model/project data stays
outside this repository. Core, skills, UI and published tag remain unchanged.
The source has relocated-Mac evidence; run the destination fixture smoke before
claiming native Linux or embedded-panel operation. Keep this progress record
current when implementation changes.
