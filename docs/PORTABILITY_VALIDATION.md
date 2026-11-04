# Portability update validation — 2026-11-03

This `main` update adds a Linux preflight/setup entry point and migration
instructions. It does not modify the CAD core, skills, UI, pinned fixture/font,
existing launcher/runtime setup, package manifest or release tag.

The working-source manifest and public package were compared locally. The
current core, skills and five-file/export implementation already match the
public alpha. The private transfer also contains project-specific model files
and supplemental checks; those private assets are not part of this update.

Current matching-code evidence from a relocated copy on the existing Mac:

| Check | Result |
| --- | --- |
| Python workflow tests | 32 pass |
| Node/server tests | 17 pass |
| Native unchanged Basil build | Required checks pass; 48 × 100.05 × 2.6 mm |
| Compact revision | Exactly five files; no full ZIP created |
| Native fixture source SHA-256 | c4a60cf4b5a093bbc0a0b1162b03608d7101027e495cccc394cc965d8a67f1e9 |
| Current core SHA-256 | b59dca528ce286bfa74ce472aa8b83116e2e801c5ec35a63a5ee8f52e7e5e057 |

The actual-STL fixture preview was inspected and its run integrity verified.
Existing Mac Python/development dependencies were reused for those relocation
tests; no clean Linux installation is implied. The transferred built JavaScript
runtime needs no `node_modules` for ordinary use.

For the new entry point, shell syntax, documented help/invalid-argument behavior,
wrong-OS rejection before installation and the existing plugin manifest were
checked. Full native Linux dependency/graphics/engine execution and embedded
host UI are unverified until the new-machine smoke test succeeds. Bambu Studio
compatibility and all physical outcomes remain separate.

The historical `v0.4.0-alpha.1` release receipt in RELEASE.json and its tag remain
unchanged. See [original alpha validation](ALPHA_VALIDATION.md). This update does
not publish a new release archive, upgrade an installed plugin, expose private
projects, add paid hosting/model APIs or operate a printer.
