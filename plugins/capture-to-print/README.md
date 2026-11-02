# capture-to-print Codex alpha 0.4.0-alpha.1

Embedded photo/measurement briefs, editable parametric SCAD, checked STL previews
and review downloads. Uses the host model and a local MCP server with OpenSCAD;
no separate model API or Bambu account connection is included.

## Runtime setup

Install Node.js 22+, Python 3.11, OpenSCAD and fontconfig. From this folder:

```sh
sh scripts/setup-runtime.sh --smoke
```

The setup installs pinned Python wheels into a versioned runtime outside the
package, under `${XDG_DATA_HOME:-$HOME/.local/share}/capture-to-print-codex/0.4.0-alpha.1/`.
It does not install OS packages. The optional smoke test builds the unchanged
plant label. Existing model/project files and DSH's runtime are not changed.

The MCP launcher uses `node` on PATH or common system installation locations,
and the setup-created Python interpreter. Overrides: `CAPTURE_TO_PRINT_NODE`,
`CAPTURE_TO_PRINT_PYTHON`, `CAPTURE_TO_PRINT_OPENSCAD`,
`CAPTURE_TO_PRINT_FC_MATCH`, `CAPTURE_TO_PRINT_RUNTIME_HOME`. To choose Python for
setup, set `CAPTURE_TO_PRINT_SETUP_PYTHON`. The host supplies `PLUGIN_ROOT` and
`PLUGIN_DATA`; private projects use `${PLUGIN_DATA}/projects`.

For a GitHub marketplace install, follow the repository's root README. For a
manual local marketplace install, point `source.path` at this folder, then add
the marketplace through Codex and explicitly install capture-to-print. Start a
fresh chat and ask to open the panel. The JavaScript bundles in `dist/` run
without `node_modules`; build dependencies are only for development/tests.

## Use

Save a brief with photos and measured dimensions, discuss missing details with
the host, confirm the brief, then generate. Review the actual-STL views/checks
and download editable SCAD/STL. A successful revision has exactly five files;
create a full ZIP only through the explicit export action. User acceptance is
separate from computational checks. Import the STL into Bambu Studio and slice
manually after review.

Only one self-contained SCAD part and declared extents/section spans/basic mesh
checks are supported. General fit, minimum walls, strength, motion and physical
printing are unassessed. Preview framing can crop broad models; inspect the STL
in a CAD/slicer viewer if the preview is incomplete.

**Ordinary ChatGPT iPhone chat is not implemented.** This is a desktop alpha;
the repository's `docs/PHONE.md` describes the remote-backend and directory gates.
Linux and clean-machine CAD execution remain unverified. Current release tests
are recorded in the repository's `docs/ALPHA_VALIDATION.md`.

MIT code; keep Work Sans OFL and bundled JS notices. No original user projects,
reference photos, machine-specific overlays or private benchmark recreations
are included. Existing local installation data is not migrated or deleted.
