# Move the pipeline and keep project history

The repository is the reusable pipeline. Private project data and OS-installed
tools are separate. Copying this checkout does not move an installed plugin's
database, sign-in state, Python environment or CAD engine.

## Source and dependencies

Clone/pull the desired branch, keep its pinned fonts/licenses and install the
destination dependencies. The current Codex implementation is under
`plugins/capture-to-print`; the older DSH adapter remains at the repository root.
Do not silently substitute their versions/capabilities. On Linux, use
[the setup guide](LINUX_SETUP.md).

## Private projects

Stop active builds before copying project data. Locate the source host's actual
`CAPTURE_TO_PRINT_DATA_DIR` or host-provided plugin data directory; do not assume
it is inside the checkout. Copy the complete private project directory to a
private destination. Preserve briefs, photos, candidate history and relative
run paths. Keep the original until the destination copy is complete and checked.
Do not copy login tokens, global host configuration or the Mac virtualenv.

A successful current revision has exactly:

```text
design.scad
design-contract.json
part.stl
preview.png
revision.json
```

Its shared **`.resources/<fingerprint>/` directory beside the run root is also
required for reproducible export**. Copying only the five visible files can
lose that dependency. Preserve older-format runs unchanged. A loose SCAD/STL
folder is not automatically imported into the panel database; use those files
directly or create a new brief/candidate in the panel.

For a standalone project kept outside the panel, copy its source, contracts,
exact runs/resources, fonts, custom validators/reference parts, previews and
required slice evidence. Keep project-specific scripts distinct from generic
plugin guarantees. Use the owner's private transfer/archive for unpublished
designs; they are intentionally not included in this public repository.

## Verify after moving

With the destination CAD Python interpreter:

```sh
python /path/to/capture-to-print/plugins/capture-to-print/scripts/capture_to_print.py \
  verify /path/to/private/run
```

Verify the copied source/mesh/report hashes before changing them. Preserve any
historical absolute paths in provenance; they do not need to be normalized by
rewriting an immutable run. Configure destination runtime paths and actual
private data location in the host, then confirm it can read the project. Do not
delete the only complete copy or treat a successful hash check as an operational
test.

Build the unchanged fixture on the destination, inspect its actual-STL preview,
then rebuild the target model into a new revision and rerun its applicable
checks. Changes to geometry, fonts, engine or slicer profiles need new evidence.
Physical fit, support removal, strength and light/heat behavior remain separate.

Full ZIP export is available when explicitly requested. It does not replace a
backup of the private project database or grant approval. No automatic project
upload, publication, paid API or printer dispatch is part of migration.
