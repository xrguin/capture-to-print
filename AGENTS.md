# capture-to-print — publishable bundle

This folder is the distributable copy of `prototypes/capture-to-print-plugin/` and
is meant to become the public repository. Keep generated runs, venvs and personal
paths out of it.

Rules:

- The fixture SCAD, its contract and the pinned font bytes must not change. A
  release that alters them needs a new contract, new measurements and a fresh
  review.
- `scripts/capture_to_print.py` is the only CAD executor. Do not add model API
  clients, paid services, printer dispatch or automatic approval.
- A passing build is `awaiting_user_review`; never record user acceptance from an
  agent's visual review.
- The DSH layer (`lib/index.mjs`, `cordis.patch.yml`) may only create and remove
  its own symlinks. It must not install system software.
- Run `node --test tests/*.mjs` and the Python workflow tests before tagging a
  release, and rebuild the fixture once with `scripts/bootstrap.sh --smoke`.
