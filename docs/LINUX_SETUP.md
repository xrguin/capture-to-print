# Continue on Linux x86-64

This guide applies to the current `main` branch. The published
`v0.4.0-alpha.1` tag remains unchanged. The Codex runtime is still 0.4.0;
five-file revisions and explicit full-bundle export were already included.

## Install prerequisites

Install Node.js 22+, Python 3.11 with venv/pip support, OpenSCAD with binary STL
export, and fontconfig (`fc-match`) through your distribution or the vendors.
The project does not install OS packages. Preview rendering needs working
graphics libraries; a headless machine may require a display/Xvfb setup.

Use the [official Codex CLI instructions](https://developers.openai.com/codex/cli)
and sign in with your existing ChatGPT account. No separate model API key is
required by this plugin. Embedded-panel availability needs an actual test in a
supported graphical host; CLI/MCP execution alone does not establish that UI.

## Clone and set up

```sh
git clone --branch main https://github.com/xrguin/capture-to-print.git
cd capture-to-print
sh scripts/setup-linux.sh --smoke
codex plugin marketplace add "$PWD"
codex plugin add capture-to-print@capture-to-print-alpha
```

If you already have this checkout on `main`, preserve local changes and pull
with `git pull --ff-only` instead of cloning again. A detached tagged checkout
must deliberately switch to `main`; pulling does not upgrade a pinned tag.

The explicit setup first checks the OS/architecture, Python, Node, OpenSCAD,
fontconfig and the plugin's source manifest. It then calls the existing runtime
setup to install pinned Python dependencies. It creates no model/API calls,
account connection or printer job. Downloading dependencies requires internet.

The default runtime is outside the checkout:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/capture-to-print-codex/0.4.0-alpha.1/
```

Overrides: `CAPTURE_TO_PRINT_SETUP_PYTHON`, `CAPTURE_TO_PRINT_RUNTIME_HOME`,
`CAPTURE_TO_PRINT_PYTHON`, `CAPTURE_TO_PRINT_NODE`,
`CAPTURE_TO_PRINT_OPENSCAD`, and `CAPTURE_TO_PRINT_FC_MATCH`.
See the [adapter README](../plugins/capture-to-print/README.md).

The smoke builds the unchanged Basil label: expect
**48 × 100.05 × 2.6 mm**, required checks passing, exactly five files and
`awaiting_user_review`. Runs and shared resources are retained in the external
runtime's `smoke-runs/`. No full ZIP is created automatically. If rendering fails
on a headless system, preserve the failure and configure graphics/Xvfb before
retrying; a failed preview must not count as readiness.

Refresh/start a new host chat and enable capture-to-print. Ask to build the
unchanged plant label or open the panel. Follow the current host's
[local marketplace instructions](https://developers.openai.com/plugins/build/plugins)
if its install interface differs. Keep this checkout at its selected path or
update the marketplace location after moving it. Refresh/reinstall cached plugin
copies after later source changes; source edits do not automatically update the
installed copy.

## Bring existing work

Follow [Moving projects](MOVING_PROJECTS.md). The public repository contains code,
rules, tests and a sanitized fixture. Private photos, generated CAD, slicer jobs,
project databases, environments and credentials must be transferred separately.
Do not commit them to obtain a convenient backup.

The generic core checks declared extents, section spans and basic mesh integrity.
Project-specific wall, negative-space, fit, motion and slicer checks need their
own tools/references and fresh validation. Do not assume old Mac engine settings,
profiles or physical claims apply on Linux. Manual Bambu Studio slicing is a
separate step; no Bambu account or printer integration is added.

## Evidence boundary

The portable source was relocated and checked on macOS Apple Silicon. Native
Linux dependencies, graphics, CAD output, Bambu Studio and host UI remain
unverified until the destination tests pass. See
[portability validation](PORTABILITY_VALIDATION.md). Ordinary ChatGPT iPhone
execution remains a separate [unimplemented hosted-backend track](PHONE.md).
