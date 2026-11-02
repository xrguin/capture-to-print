# Parametric source and MakerWorld preparation

Use this path for editable controls or a MakerWorld-customizable design. Keep the existing CAD engine, checking and exact-revision review workflow. A source file with variables is editable; a usable Customizer additionally needs clear literal controls, units, bounds and deliberate separation of internal interfaces.

Ask which controls are useful. Put bounded numeric literals at the top in named groups with descriptions and `// [minimum:step:maximum]`. Put dependent values, thread/fit constants and resolution settings under `/* [Hidden] */`. Keep the source self-contained; this initial packager rejects external assets and supports numeric sliders only. Other Customizer control types need separate implementation/testing rather than a false pass.

Make parameters drive the geometry. Do not rescale an entire assembly when appearance changes must preserve holes or threads. Put explicit assertions in SCAD for meaningful limits and coupled constraints; slider annotations alone do not enforce correctness for command-line edits. Select the printer envelope deliberately. Preserve the original model when adding controls, and tie the default contract to the exact new source bytes.

After a successful default build:

```sh
python scripts/package_parametric.py inspect --source /path/to/design.scad --parameters /path/to/parameters.json
python scripts/package_parametric.py package --run /path/to/verified/run --parameters /path/to/parameters.json --output /path/to/new/customizer-package
```

The schema has `schema_version: 1`, the `source_sha256`, a `parameters` list and complete named `presets`. Each parameter has `name`, `label`, `default`, `minimum`, `maximum`, `step`. Optional `fixed_dimensions` is a list of descriptions. All presets specify exactly those parameters. The packager verifies the core run, source annotations/defaults/bounds and presets, then writes model.scad, an OpenSCAD model.json preset file, default STL, controls/reference notes and a hash manifest/ZIP. It preserves the run and never uploads.

Render/export representative minimum, maximum and interacting combinations and measure actual geometry for each. Include at least one invalid input to demonstrate assertion failure. Record which combinations were executed and which manufacturing/functional properties remain unassessed. Passing syntax or a few presets does not validate the full range. A parameter change invalidates the old STL checks, previews, acceptance and slice; obtain a new source/parameter binding and build/check/slice it again.

For MakerWorld, trial the self-contained .scad in Parametric Model Maker and inspect the intended controls before claiming hosted compatibility. Its live Sample code demonstrates OpenSCAD Customizer conventions. A default Bambu Studio 3MF is tied to its specific geometry and settings; it does not automatically configure arbitrary customized output. Prepare the source for upload, but publication and platform rights/settings require their own user request.

References checked 2026-10-29: [MakerWorld Parametric Model Maker](https://makerworld.com/en/makerlab/parametricModelMaker) and the [OpenSCAD manual](https://files.openscad.org/documentation/manual/OpenSCAD_User_Manual.pdf). These sources do not establish which backend/version the hosted service will use for this design.
