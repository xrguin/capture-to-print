# CAD generation and evidence rules

These rules distill the owner's automatic-cad experience, reviewed 2026-10-25. They are self-contained guidance. A rule is an automated gate only if a matching implemented check is listed in the report.

## Establish intent

1. Record purpose, part count, measurements with units, openings, mating surfaces and the chosen coordinate frame. Identify which values are measured, inferred or defaults. Photos do not establish missing scale or fit dimensions.
2. Confirm critical dimensions and a suitable numerical tolerance before generating. Preserve locked measurements throughout correction. Report conflicting requirements; do not silently shrink a part to fit a printer.
3. Keep dimensions named and editable, derive shared geometry consistently, and use compact modules. Favor functional geometry and readable labels over decoration.

## Generate geometry

4. Use OpenSCAD for editable parametric source plus STL. Do not call STL a sliced printer job or promise editable STEP feature history.
5. Use robust intended joins and deliberate boolean operations. Cutters should cross intended exits; overlap must not consume a required floor or change a critical dimension. Face-only contact can be fragile. For the preserved plant label, report a problem before altering its joints.
6. Record negative-space intent: a through-hole, open top or drainage path differs from a blind cavity. Watertightness does not verify that intent. If the current checker cannot verify a critical feature, report the missing check rather than marking it passed.
7. Treat fonts as geometry dependencies. The pilot bundles Work Sans Bold; preserve the source request, verify actual file resolution and visually inspect the output. Pinning a file alone does not certify every glyph.
8. Measure final transformed geometry. Scale also changes floors, clearances, text and joints. Overall extents cannot replace local feature measurements.
9. Budget complex operations and tessellation. Limit each export/check/render stage; preserve logs on failure. Do not repeatedly retry unchanged failed geometry.

## Manufacturing guidance is conditional

10. Wall, floor, bridge, overhang and fit values depend on material, nozzle, orientation and function. No universal default proves printability or strength. Use a physical fit coupon where needed.
11. Check full intended print footprint, including auxiliary geometry and slicer reservations. The optional envelope check covers unrotated mesh extents only. Unknown printer setup remains unassessed.
12. Preserve appropriate bed contact and consider support orientation. Do not infer successful slicing or printing from a good-looking render. Historical food-contact, water-resistance or stiffness notes are not certification.

## Validate and deliver

13. Inspect the actual STL: finite geometry, edge topology, winding, positive volume, degenerate faces, components, and declared measurements. Body count depends on intent; Euler characteristic 2 is not a universal rule.
14. Use face/back/edge/oblique previews of the exact output. Missing or failed previews stop the workflow. A nonblank image is only a rendering check; an agent and the user still review it.
15. Preserve each run and declare outputs explicitly. Hash source, contract, font, checker, mesh, previews and reports. Never select an arbitrary STL from a shared folder.
16. Keep build completion, computational checks, visual review, user acceptance, slicing and physical outcomes separate. Record user feedback accurately and bind acceptance to a revision. Never silently repair the baseline or reuse approval after changes.
17. For an authorized new part, preserve requirements and cap correction at two unsuccessful attempts before asking for guidance. Unsupported critical tests cannot become passes by deleting them.

## Examples behind these rules

- The preserved plant-label SCAD is 48 mm wide; a historical 50 mm CadQuery specification describes another design. Its tip extends to Y=-0.05 mm and embossing raises total thickness to 2.6 mm. Measure the selected export.
- In a previous plate/lid model, a final scale of 0.8 also scaled a nominal 2.5 mm floor to 2.0 mm and a 0.4 mm side clearance to 0.32 mm. Checking input parameters alone missed this.
- AprilTag panel faces and joint tongues had different footprints. Six filenames represented nine printed pieces. Part identity, quantity and assembly transforms matter; the present pilot supports only one exported part.

Source lineage: the owner's 30-rule catalog `planning/2026-10-25_iphone-hosted-cad/CAD_RULES.md` (2026-10-25), especially CAD-01–05, 07–17 and 19–30. That catalog preserves the original 24-file evidence map. It is historical provenance, not a runtime dependency or a claim that every proposed check is implemented.
