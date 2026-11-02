#!/usr/bin/env python3
"""Local/hosted OpenSCAD execution tools. No model API client or network calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from xml.sax.saxutils import escape
import zipfile

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
FONT_ASSETS = ROOT / "assets/fonts" if (ROOT / "assets/fonts").is_dir() else ROOT / "fonts"
VIEWS = ("face", "back", "edge", "oblique")
SOURCE_LIMIT = 1024 * 1024
MESH_LIMIT = 64 * 1024 * 1024


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))


def exact_keys(obj, required, optional=()):
    if not isinstance(obj, dict):
        raise ValueError("Expected a JSON object")
    missing, extra = set(required) - obj.keys(), obj.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f"Contract fields: missing={sorted(missing)}, unknown={sorted(extra)}")


def validate_contract(c):
    exact_keys(c, ("schema_version", "name", "units", "source_sha256", "font_pattern",
                   "expected_components", "dimensions"), ("build_envelope_mm", "notes"))
    if type(c["schema_version"]) is not int or c["schema_version"] != 1 or c["units"] != "mm":
        raise ValueError("Only contract version 1 in millimeters is supported")
    if not isinstance(c["name"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", c["name"]):
        raise ValueError("Invalid contract name")
    if not isinstance(c["source_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", c["source_sha256"]):
        raise ValueError("Pin the approved source SHA-256 before building")
    if c["font_pattern"] not in (None, "Work Sans:style=Bold"):
        raise ValueError("Use null for no text or the bundled Work Sans Bold font")
    if type(c["expected_components"]) is not int or c["expected_components"] < 1:
        raise ValueError("Declare the intended number of connected components")
    if not isinstance(c["dimensions"], list) or not c["dimensions"]:
        raise ValueError("Declare at least one dimension check")
    ids = {"watertight", "winding", "positive_volume", "nondegenerate", "components", "envelope",
           "self_intersections", "global_minimum_wall", "strength", "physical_fit",
           "slicer_printability", "glyph_readability", "independent_checker_isolation", "printer_envelope"}
    for d in c["dimensions"]:
        if not isinstance(d, dict):
            raise ValueError("Dimension check must be an object")
        method = d.get("method")
        keys = ("id", "method", "axis", "expected_mm", "tolerance_mm")
        if method == "plane_span":
            keys += ("plane_axis", "plane_offset_mm")
        elif method != "bbox_extent":
            raise ValueError(f"Unsupported required measurement method: {method}")
        exact_keys(d, keys)
        if not isinstance(d["id"], str) or not re.fullmatch(r"[a-z0-9_-]+", d["id"]) or d["id"] in ids:
            raise ValueError("Dimension IDs must be unique lowercase identifiers")
        ids.add(d["id"])
        if type(d["axis"]) is not int or d["axis"] not in (0, 1, 2):
            raise ValueError("Measurement axis must be 0, 1, or 2")
        for key in ("expected_mm", "tolerance_mm"):
            number(d[key], key, positive=True)
        if method == "plane_span":
            if type(d["plane_axis"]) is not int or d["plane_axis"] not in (0, 1, 2) or d["plane_axis"] == d["axis"]:
                raise ValueError("Section plane must be perpendicular to another axis")
            number(d["plane_offset_mm"], "plane_offset_mm")
    if "build_envelope_mm" in c:
        envelope = c["build_envelope_mm"]
        if not isinstance(envelope, list) or len(envelope) != 3:
            raise ValueError("Envelope must contain three dimensions")
        for value in envelope:
            number(value, "build_envelope_mm", positive=True)
    return c


def preflight_source(source, contract):
    source = Path(source)
    if source.suffix.lower() != ".scad" or source.stat().st_size > SOURCE_LIMIT:
        raise ValueError("Expected a self-contained SCAD file no larger than 1 MiB")
    if sha256(source) != contract["source_sha256"]:
        raise ValueError("Source hash differs from the confirmed contract; preserve and review the new revision")
    text = source.read_text()
    # This dependency screen is NOT a sandbox or a complete SCAD parser.
    tokens = re.sub(r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*', "", text, flags=re.S)
    if re.search(r"\b(include|use|import|surface)\b", tokens):
        raise ValueError("Pilot requires self-contained SCAD; external assets/includes are unsupported")


def run_tool(argv, cwd, env, timeout, log):
    """Use explicit argv and stop the process group on timeout; retain diagnostics."""
    with Path(log).open("wb") as output:
        process = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env,
                                   stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError(f"Process exceeded {timeout}s; see {Path(log).name}")
    if code != 0:
        raise RuntimeError(f"Process exited {code}; see {Path(log).name}")


def executable(value, fallback):
    found = shutil.which(value or fallback)
    if not found:
        raise ValueError(f"Executable not found: {value or fallback}")
    return str(Path(found).resolve())


def prepare_font(run, fc_match, pattern):
    font_dir = run / "fonts"
    font_dir.mkdir()
    provenance = read_json(FONT_ASSETS / "provenance.json")
    for item in provenance["files"]:
        src = FONT_ASSETS / item["path"]
        if src.parent != FONT_ASSETS or sha256(src) != item["sha256"]:
            raise ValueError("Pinned font/license checksum mismatch")
        shutil.copy2(src, font_dir / src.name)
    shutil.copy2(FONT_ASSETS / "provenance.json", font_dir / "provenance.json")
    cache = run / ".font-cache"
    cache.mkdir()
    config = run / "fontconfig.xml"
    config.write_text('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                      f"<fontconfig><dir>{escape(str(font_dir))}</dir>"
                      f"<cachedir>{escape(str(cache))}</cachedir></fontconfig>\n")
    env = os.environ.copy()
    env.pop("FC_DEBUG", None)
    env.update(FONTCONFIG_FILE=str(config), FONTCONFIG_PATH=str(run),
               XDG_CACHE_HOME=str(cache), QT_QPA_PLATFORM="offscreen")
    log = run / "font-match.log"
    run_tool([fc_match, "-f", "%{file}\n%{family}\n%{style}\n", "Work Sans:style=Bold"], run, env, 20, log)
    lines = log.read_text().splitlines()
    font = font_dir / "WorkSans-Bold.ttf"
    if len(lines) != 3 or Path(lines[0]).resolve() != font.resolve() or lines[1:] != ["Work Sans", "Bold"]:
        raise ValueError("Requested font resolved to an unexpected file/family/style; see font-match.log")
    return env, {"pattern": pattern, "file": "fonts/WorkSans-Bold.ttf", "sha256": sha256(font),
                 "family": lines[1], "style": lines[2], "upstream_commit": provenance["upstream_commit"]}


def measure_mesh(path, contract):
    import numpy as np
    import trimesh

    validate_contract(contract)
    path = Path(path)
    if path.stat().st_size == 0 or path.stat().st_size > MESH_LIMIT:
        raise ValueError("STL is empty or exceeds the 64 MiB pilot limit")
    # STL only, one explicitly selected artifact. Vertex welding enables topology checks;
    # no hole filling, surface repair, scaling, or export of the processed mesh occurs.
    mesh = trimesh.load_mesh(path, file_type="stl", process=False)
    if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces):
        raise ValueError("Expected a nonempty triangle mesh")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("Mesh has non-finite coordinates")
    # Preserve all input faces, including defects; only weld duplicate vertices.
    mesh.merge_vertices(digits_vertex=8)
    rows = []

    def flag(key, passed, measured, expected, method):
        rows.append({"id": key, "status": "pass" if passed else "fail", "required": True,
                     "measured": measured, "expected": expected, "method": method})

    components = len(trimesh.graph.connected_components(mesh.face_adjacency, nodes=np.arange(len(mesh.faces))))
    flag("watertight", bool(mesh.is_watertight), bool(mesh.is_watertight), True, "edge incidence after vertex welding")
    flag("winding", bool(mesh.is_winding_consistent), bool(mesh.is_winding_consistent), True, "adjacent face winding")
    volume = float(mesh.volume)
    flag("positive_volume", math.isfinite(volume) and volume > 0, volume, "> 0 mm^3", "signed triangle volume")
    degenerate = int(np.count_nonzero(mesh.area_faces <= 1e-12))
    flag("nondegenerate", degenerate == 0, degenerate, 0, "triangle area <= 1e-12 mm^2")
    flag("components", components == contract["expected_components"], components,
         contract["expected_components"], "connected face components, including open components")
    extents = mesh.extents
    for dimension in contract["dimensions"]:
        measured = None
        if dimension["method"] == "bbox_extent":
            measured = float(extents[dimension["axis"]])
        else:
            normal, origin = np.zeros(3), np.zeros(3)
            normal[dimension["plane_axis"]] = 1
            origin[dimension["plane_axis"]] = dimension["plane_offset_mm"]
            segments = trimesh.intersections.mesh_plane(mesh, normal, origin)
            if len(segments):
                measured = float(np.ptp(segments[:, :, dimension["axis"]]))
        passed = measured is not None and abs(measured - dimension["expected_mm"]) <= dimension["tolerance_mm"]
        rows.append({**dimension, "required": True, "measured_mm": measured,
                     "status": "pass" if passed else "fail",
                     "coverage": "whole-mesh axis extent" if dimension["method"] == "bbox_extent"
                     else "span of all mesh-plane intersections, not a general local wall/diameter measurement"})
    if "build_envelope_mm" in contract:
        envelope = contract["build_envelope_mm"]
        flag("envelope", bool(np.all(extents <= np.array(envelope))), extents.tolist(), envelope,
             "unrotated extents only; no placement, brim, purge, or slicer reservation check")
    unassessed = ["self_intersections", "global_minimum_wall", "strength", "physical_fit",
                  "slicer_printability", "glyph_readability", "independent_checker_isolation"]
    if "build_envelope_mm" not in contract:
        unassessed.append("printer_envelope")
    rows.extend({"id": x, "status": "unassessed", "required": False} for x in unassessed)
    return {"schema_version": 1, "mesh_sha256": sha256(path), "contract_sha256": None,
            "units": "mm", "bounds_mm": mesh.bounds.tolist(), "extents_mm": extents.tolist(),
            "volume_mm3": volume, "triangles": len(mesh.faces), "components": components,
            "euler_number_informational": int(mesh.euler_number), "checks": rows,
            "required_checks_passed": all(x["status"] == "pass" for x in rows if x["required"]),
            "method_limits": "Feature checks cover only declared extents/sections; no universal printability claim."}


def render_views(stl, destination):
    """Render the actual exported mesh. No image generation model or CAD re-export."""
    import numpy as np
    import vtk
    from PIL import Image

    destination = Path(destination)
    destination.mkdir(exist_ok=True)
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(stl))
    reader.Update()
    poly = reader.GetOutput()
    if poly.GetNumberOfCells() == 0:
        raise ValueError("Renderer received an empty STL")
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    # Draw only geometric creases/boundaries, not triangle tessellation. This makes
    # embossing legible in a face-on view without recoloring or altering the mesh.
    edges = vtk.vtkFeatureEdges()
    edges.SetInputConnection(reader.GetOutputPort())
    edges.BoundaryEdgesOn()
    edges.FeatureEdgesOn()
    edges.SetFeatureAngle(30)
    edges.ManifoldEdgesOff()
    edges.NonManifoldEdgesOn()
    edges.ColoringOff()
    edge_mapper = vtk.vtkPolyDataMapper()
    edge_mapper.SetInputConnection(edges.GetOutputPort())
    edge_mapper.SetResolveCoincidentTopologyToPolygonOffset()
    edge_mapper.SetRelativeCoincidentTopologyLineOffsetParameters(0, -1)
    bounds = poly.GetBounds()
    center = np.array([(bounds[2*i] + bounds[2*i+1])/2 for i in range(3)])
    span = max(bounds[2*i+1] - bounds[2*i] for i in range(3))
    views = {"face": ((0, 0, 1), (0, 1, 0)), "back": ((0, 0, -1), (0, 1, 0)),
             "edge": ((1, 0, 0), (0, 1, 0)), "oblique": ((1, -1, 1.8), (0, 1, 0))}
    for name, (direction, up) in views.items():
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.24, 0.60, 0.40)
        actor.GetProperty().SetAmbient(0.25)
        actor.GetProperty().SetDiffuse(0.75)
        actor.GetProperty().SetSpecular(0.15)
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.97, 0.98, 0.97)
        renderer.AddActor(actor)
        edge_actor = vtk.vtkActor()
        edge_actor.SetMapper(edge_mapper)
        edge_actor.GetProperty().SetColor(0.08, 0.22, 0.14)
        edge_actor.GetProperty().SetLineWidth(1)
        renderer.AddActor(edge_actor)
        camera = renderer.GetActiveCamera()
        camera.SetFocalPoint(*center)
        vector = np.array(direction) / np.linalg.norm(direction)
        camera.SetPosition(*(center + vector * span * 3))
        camera.SetViewUp(*up)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(span * 0.58)
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*(center + (vector * 2.5 + np.array([-0.6, -0.2, 0.3])) * span))
        light.SetFocalPoint(*center)
        light.SetIntensity(0.9)
        renderer.AddLight(light)
        renderer.ResetCameraClippingRange()
        window = vtk.vtkRenderWindow()
        window.SetOffScreenRendering(True)
        window.SetSize(720, 1000)
        window.AddRenderer(renderer)
        try:
            window.Render()
            capture = vtk.vtkWindowToImageFilter()
            capture.SetInput(window)
            capture.SetInputBufferTypeToRGB()
            capture.ReadFrontBufferOff()
            capture.Update()
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(str(destination / f"{name}.png"))
            writer.SetInputConnection(capture.GetOutputPort())
            writer.Write()
        finally:
            window.Finalize()
        with Image.open(destination / f"{name}.png") as picture:
            pixels = np.asarray(picture.convert("RGB"))
            if picture.size != (720, 1000) or np.ptp(pixels.astype(float), axis=(0, 1)).max() < 10:
                raise ValueError(f"Unusable {name} preview")
    # A contact sheet of actual renders, not a replacement for individually inspectable views.
    canvas = Image.new("RGB", (1440, 2000), "white")
    for i, name in enumerate(VIEWS):
        with Image.open(destination / f"{name}.png") as p:
            canvas.paste(p, ((i % 2)*720, (i // 2)*1000))
    canvas.save(destination / "contact-sheet.png")


def artifact_rows(run, paths):
    rows = []
    for relative in paths:
        path = run / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or linked artifact: {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return rows


REVISION_FILES = {"design.scad", "design-contract.json", "part.stl", "preview.png", "revision.json"}
RESOURCE_FILES = {"capture_to_print.py", "requirements.txt", "LICENSE",
                  "fonts/WorkSans-Bold.ttf", "fonts/OFL.txt", "fonts/provenance.json"}


def verify_revision_data(record, read_bytes):
    """Verify the same evidence in a directory or ZIP, without executing it."""
    if record.get("schema_version") != 2 or record.get("status") != "awaiting_user_review":
        raise ValueError("Not a supported completed revision")
    if record.get("user_acceptance") != "pending" or record.get("agent_visual_review") != "pending":
        raise ValueError("Automatic revision must retain pending user acceptance and review")
    rows = record.get("files", [])
    if len(rows) != 4 or {x["path"] for x in rows} != REVISION_FILES - {"revision.json"}:
        raise ValueError("Revision must bind exactly four artifacts")
    for row in rows:
        data = read_bytes(row["path"])
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"Artifact checksum mismatch: {row['path']}")
    hashes = {r["path"]: r["sha256"] for r in rows}
    contract = validate_contract(json.loads(read_bytes("design-contract.json")))
    if contract["source_sha256"] != hashes["design.scad"] or record["source_sha256"] != hashes["design.scad"]:
        raise ValueError("Source hash differs from the contract/revision")
    checks = record["checks"]
    if (checks.get("required_checks_passed") is not True or
            any(c.get("required") and c.get("status") != "pass" for c in checks["checks"]) or
            checks["mesh_sha256"] != hashes["part.stl"] or
            checks["contract_sha256"] != hashes["design-contract.json"]):
        raise ValueError("Checks are not bound to this mesh/contract")
    if record.get("part") != {"path": "part.stl", "quantity": 1, "name": contract["name"]}:
        raise ValueError("Part differs from the contract")
    resources = record["resources"]
    if not re.fullmatch(r"\.\./\.resources/[0-9a-f]{64}", resources.get("path", "")):
        raise ValueError("Invalid resource path")
    resource_rows = resources["files"]
    if len(resource_rows) != len(RESOURCE_FILES) or {r["path"] for r in resource_rows} != RESOURCE_FILES:
        raise ValueError("Invalid resource inventory")
    fingerprint = hashlib.sha256(json.dumps(resource_rows, sort_keys=True).encode()).hexdigest()
    if resources["path"] != "../.resources/" + fingerprint:
        raise ValueError("Resource inventory fingerprint mismatch")
    resource_hashes = {r["path"]: r["sha256"] for r in resource_rows}
    if (record["build"]["checker_sha256"] != resource_hashes["capture_to_print.py"] or
            record["build"]["font"]["sha256"] != resource_hashes["fonts/WorkSans-Bold.ttf"]):
        raise ValueError("Build record differs from pinned resources")
    return {"verified_files": 5, "revision": record["revision"], "status": record["status"],
            "limits": "Recorded integrity, not adversarial authenticity or independent validation."}


def verify_run(run):
    run = Path(run).resolve()
    if run.is_file():
        return verify_bundle(run)
    if (run / "revision.json").exists():
        if {p.name for p in run.iterdir()} != REVISION_FILES:
            raise ValueError("Completed revision must contain exactly five files")
        for p in run.iterdir():
            if p.is_symlink() or not p.is_file():
                raise ValueError("Linked or non-file revision artifact")
        result = verify_revision_data(read_json(run / "revision.json"), lambda name: (run / name).read_bytes())
        preflight_source(run / "design.scad", read_json(run / "design-contract.json"))
        return result
    return verify_legacy_run(run)


def pin_resources(work, output_root):
    rows = artifact_rows(work, sorted(RESOURCE_FILES))
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    parent = output_root / ".resources"
    parent.mkdir(exist_ok=True)
    target = parent / fingerprint
    if not target.exists():
        temporary = Path(tempfile.mkdtemp(prefix=".new-", dir=parent))
        try:
            for row in rows:
                dst = temporary / row["path"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(work / row["path"], dst)
            try:
                temporary.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    if target.is_symlink() or artifact_rows(target, sorted(RESOURCE_FILES)) != rows:
        raise ValueError("Shared rebuild resources changed")
    return {"path": "../.resources/" + fingerprint, "files": rows}


def export_bundle(run, output):
    """Explicit export; never append files to, rebuild, or approve a revision."""
    run, output = Path(run).resolve(), Path(output).resolve()
    verify_run(run)
    if output.is_relative_to(run) or ".resources" in output.parts:
        raise ValueError("Export outside the immutable revision and resource directories")
    if output.exists():
        raise ValueError("Export destination already exists; choose a new filename")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not (run / "revision.json").exists():
        # Legacy artifacts are exported as-is. No migration or cleanup.
        names = [r["path"] for r in read_json(run / "manifest.json")["files"]] + ["manifest.json"]
        with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
            for name in names:
                archive.write(run / name, name)
        return {"bundle": str(output), "revision": read_json(run / "manifest.json")["revision"],
                "sha256": sha256(output), "bytes": output.stat().st_size}
    record = read_json(run / "revision.json")
    resource_root = (run / record["resources"]["path"]).resolve()
    if resource_root != run.parent / ".resources" / Path(record["resources"]["path"]).name:
        raise ValueError("Shared resource directory escaped its root")
    if artifact_rows(resource_root, sorted(RESOURCE_FILES)) != record["resources"]["files"]:
        raise ValueError("Pinned rebuild resources are missing or changed")
    prefix = ".resources/" + resource_root.name
    instructions = ("# Rebuild this revision\n\nInstall OpenSCAD, fontconfig and Python 3.11.\n\n"
        f"Install Python dependencies: `python -m pip install -r {prefix}/requirements.txt`.\n\n"
        f"Verify: `python {prefix}/capture_to_print.py verify revision`.\n\n"
        f"Rebuild: `python {prefix}/capture_to_print.py build --source revision/design.scad "
        "--contract revision/design-contract.json --output-root rebuilt`.\n\n"
        "Match engine/dependency versions in revision/revision.json for comparable results. "
        "Engine binaries and graphics drivers are external. Each rebuild is a new unapproved revision. "
        "The four original views are combined in preview.png. Successful-run logs were summarized; "
        "this export does not recreate discarded logs or rerun CAD. No printing or fit is certified.\n").encode()
    paths = [("revision/" + name, run / name) for name in sorted(REVISION_FILES)]
    paths += [(prefix + "/" + name, resource_root / name) for name in sorted(RESOURCE_FILES)]
    fd, temp = tempfile.mkstemp(prefix=".export-", suffix=".zip", dir=output.parent)
    os.close(fd)
    temp = Path(temp)
    try:
        rows = []
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, path in paths:
                data = path.read_bytes()
                archive.writestr(name, data)
                rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            archive.writestr("REBUILD.md", instructions)
            rows.append({"path": "REBUILD.md", "bytes": len(instructions), "sha256": hashlib.sha256(instructions).hexdigest()})
            archive.writestr("manifest.json", json.dumps({"schema_version": 2, "revision": record["revision"],
                "status": record["status"], "files": rows}, indent=2) + "\n")
        verify_bundle(temp)
        # Exclusive publication: do not overwrite another export racing this one.
        os.link(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    return {"bundle": str(output), "revision": record["revision"], "sha256": sha256(output),
            "bytes": output.stat().st_size}


def verify_bundle(bundle):
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("schema_version") != 2:
            raise ValueError("Use extracted-directory verification for a legacy bundle")
        rows = manifest["files"]
        names = archive.namelist()
        if len(names) != len(set(names)) or len(rows) != len({r["path"] for r in rows}):
            raise ValueError("Duplicate bundle membership")
        if set(names) != {r["path"] for r in rows} | {"manifest.json"}:
            raise ValueError("Bundle membership differs from manifest")
        for row in rows:
            name = row["path"]
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("Invalid bundle path")
            data = archive.read(name)
            if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Bundle checksum mismatch: " + name)
        record = json.loads(archive.read("revision/revision.json"))
        result = verify_revision_data(record, lambda name: archive.read("revision/" + name))
        prefix = record["resources"]["path"][3:] + "/"
        expected = {"revision/" + name for name in REVISION_FILES} | {prefix + name for name in RESOURCE_FILES} | {"REBUILD.md"}
        if {r["path"] for r in rows} != expected or manifest["revision"] != record["revision"] or manifest["status"] != record["status"]:
            raise ValueError("Bundle membership or revision mismatch")
        for row in record["resources"]["files"]:
            data = archive.read(prefix + row["path"])
            if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Bundle resource mismatch")
        return {**result, "verified_files": len(names)}


def verify_legacy_run(run):
    run = Path(run).resolve()
    manifest = read_json(run / "manifest.json")
    if manifest.get("schema_version") != 1 or manifest.get("status") != "awaiting_user_review":
        raise ValueError("Not a supported draft manifest")
    parts = manifest.get("parts", [])
    if len(parts) != 1 or parts[0].get("quantity") != 1:
        raise ValueError("Pilot expects one named part")
    seen = set()
    for item in manifest["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or item["path"] in seen:
            raise ValueError("Invalid or duplicate manifest path")
        seen.add(item["path"])
        path = run / relative
        if path.is_symlink() or not path.resolve().is_relative_to(run) or not path.is_file():
            raise ValueError(f"Missing or escaped artifact: {relative}")
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Artifact checksum mismatch: {relative}")
    required = {"design.scad", "design-contract.json", "capture_to_print.py", "requirements.txt",
                "LICENSE", "checks.json", "build-record.json", "review.json", "state.json",
                "fonts/WorkSans-Bold.ttf", "fonts/OFL.txt", "fonts/provenance.json", parts[0]["path"]}
    required.update(f"previews/{name}.png" for name in (*VIEWS, "contact-sheet"))
    if not required <= seen:
        raise ValueError("Manifest omits required artifacts")
    contract = validate_contract(read_json(run / "design-contract.json"))
    preflight_source(run / "design.scad", contract)
    checks, state, review = (read_json(run / name) for name in ("checks.json", "state.json", "review.json"))
    if not checks.get("required_checks_passed") or checks["mesh_sha256"] != sha256(run / parts[0]["path"]) or checks["contract_sha256"] != sha256(run / "design-contract.json"):
        raise ValueError("Checks are not bound to this mesh/contract")
    if any(x.get("revision") != manifest["revision"] for x in (state, review)) or state["status"] != manifest["status"]:
        raise ValueError("Revision/status mismatch")
    if state["user_acceptance"] != "pending" or review["user_acceptance"] != "pending":
        raise ValueError("Automatic bundle must retain pending user acceptance")
    expected_evidence = {"design.scad", "design-contract.json", parts[0]["path"], "checks.json",
                         "build-record.json", "fonts/WorkSans-Bold.ttf"} | {f"previews/{name}.png" for name in VIEWS}
    if {x["path"] for x in review["evidence"]} != expected_evidence:
        raise ValueError("Review omits required evidence")
    by_path = {x["path"]: x for x in manifest["files"]}
    if any(item != by_path.get(item["path"]) for item in review["evidence"]):
        raise ValueError("Review evidence differs from the manifest")
    bundle = run / "draft-bundle.zip"
    if bundle.exists():
        with zipfile.ZipFile(bundle) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != seen | {"manifest.json"}:
                raise ValueError("Bundle membership differs from the manifest")
            for name in names:
                if hashlib.sha256(archive.read(name)).hexdigest() != sha256(run / name):
                    raise ValueError(f"Bundle bytes differ: {name}")
    return {"verified_files": len(seen), "revision": manifest["revision"],
            "status": manifest["status"], "limits": "Integrity against this manifest, not adversarial authenticity or independent validation."}


def build(source, contract_path, output_root, openscad=None, fc_match=None, timeout=180):
    number(timeout, "timeout", positive=True)
    if timeout > 600:
        raise ValueError("Pilot timeout must be at most 600 seconds")
    contract = validate_contract(read_json(contract_path))
    preflight_source(source, contract)
    engine = executable(openscad, "openscad")
    font_tool = executable(fc_match, "fc-match")
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    revision = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    final_run = output_root / (contract["name"] + "-" + revision)
    run = output_root / (".building-" + revision)
    run.mkdir()
    state = {"schema_version": 1, "revision": revision, "created_at": utc_now(), "status": "preflight",
             "user_acceptance": "pending", "agent_visual_review": "pending", "units": "mm",
             "source_sha256": contract["source_sha256"], "paid_api_calls": 0}
    save_json(run / "state.json", state)
    try:
        shutil.copy2(source, run / "design.scad")
        shutil.copy2(contract_path, run / "design-contract.json")
        shutil.copy2(Path(__file__), run / "capture_to_print.py")
        shutil.copy2(SCRIPT_DIR / "requirements.txt", run / "requirements.txt")
        shutil.copy2(ROOT / "LICENSE", run / "LICENSE")
        (run / "parts").mkdir()
        env, font_record = prepare_font(run, font_tool, contract["font_pattern"])
        run_tool([engine, "--version"], run, env, 20, run / "engine-version.log")
        state["status"] = "building"
        save_json(run / "state.json", state)
        env["FC_DEBUG"] = "1"
        part = f"parts/{contract['name']}.stl"
        command = [engine, "--export-format", "binstl", "-o", part, "design.scad"]
        run_tool(command, run, env, timeout, run / "build.log")
        log = (run / "build.log").read_text(errors="replace")
        resolved_fonts = sorted(set(re.findall(r'file:\s*"([^"\n]+)"', log)))
        expected_font = str(run / font_record["file"])
        if (contract["font_pattern"] and expected_font not in resolved_fonts) or any(Path(p).resolve() != Path(expected_font).resolve() for p in resolved_fonts):
            raise ValueError("OpenSCAD runtime font match was not exclusively the pinned font; see build.log")
        if contract["font_pattern"] is None and resolved_fonts:
            raise ValueError("A font was used despite a no-text contract")
        if re.search(r"\b(?:WARNING|ERROR):", log):
            raise ValueError("OpenSCAD emitted warnings/errors; review build.log before continuing")
        if sha256(run / "design.scad") != contract["source_sha256"]:
            raise ValueError("Source changed during the build")
        versions = {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "trimesh", "vtk", "Pillow")}
        record = {"engine": engine, "engine_version": (run / "engine-version.log").read_text().strip(),
                  "argv": command, "python": sys.version, "platform": platform.platform(),
                  "dependencies": versions, "font": font_record,
                  "font_runtime_match_verified": bool(contract["font_pattern"]), "font_resolution_method": "isolated fontconfig plus OpenSCAD FC_DEBUG match trace; null font means no text",
                  "checker_sha256": sha256(run / "capture_to_print.py"), "timeout_seconds": timeout,
                  "source_transforms": "none", "scope": "Local process execution; not a hostile-code sandbox"}
        save_json(run / "build-record.json", record)
        state["status"] = "checking"
        save_json(run / "state.json", state)
        run_tool([sys.executable, str(run / "capture_to_print.py"), "check", "--mesh", str(run / part),
                  "--contract", str(run / "design-contract.json"), "--report", str(run / "checks.json")],
                 run, env, timeout, run / "check.log")
        checks = read_json(run / "checks.json")
        if not checks["required_checks_passed"]:
            raise ValueError("Required geometry checks failed; see checks.json")
        state["status"] = "rendering"
        save_json(run / "state.json", state)
        env.pop("FC_DEBUG", None)
        run_tool([sys.executable, str(run / "capture_to_print.py"), "render", "--mesh", str(run / part),
                  "--output", str(run / "previews")], run, env, timeout, run / "render.log")
        from PIL import Image
        for name in (*VIEWS, "contact-sheet"):
            with Image.open(run / "previews" / f"{name}.png") as picture:
                picture.verify()
        if sha256(run / "design.scad") != contract["source_sha256"] or checks["mesh_sha256"] != sha256(run / part):
            raise ValueError("Source or mesh changed after measurement")
        if checks["contract_sha256"] != sha256(run / "design-contract.json"):
            raise ValueError("Contract changed after measurement")
        resources = pin_resources(run, output_root)
        state.update(schema_version=2, status="awaiting_user_review", completed_at=utc_now())
        compact = run / "completed"
        compact.mkdir()
        for src, dst in [("design.scad", "design.scad"), ("design-contract.json", "design-contract.json"),
                         (part, "part.stl"), ("previews/contact-sheet.png", "preview.png")]:
            shutil.copy2(run / src, compact / dst)
        record = {**state, "part": {"path": "part.stl", "quantity": 1, "name": contract["name"]},
                  "checks": checks, "build": record, "resources": resources,
                  "preview": {"path": "preview.png", "layout": [["face", "back"], ["edge", "oblique"]]},
                  "logs": [{**row, "status": "completed", "retention": "summary only"} for row in
                           artifact_rows(run, ["engine-version.log", "font-match.log", "build.log", "check.log", "render.log"])],
                  "files": artifact_rows(compact, sorted(REVISION_FILES - {"revision.json"})),
                  "review_instruction": "Inspect measurements and all four views in preview.png. Record explicit acceptance separately; checks never approve a revision."}
        save_json(compact / "revision.json", record)
        verify_run(compact)
        compact.rename(final_run)
        shutil.rmtree(run)
        return {"run": str(final_run), "status": state["status"], "extents_mm": checks["extents_mm"],
                "required_checks_passed": True, "file_count": 5, "bundle": None}

    except Exception as exc:
        state.update(status="failed", failed_stage=state["status"], error=str(exc), completed_at=utc_now())
        save_json(run / "state.json", state)
        failed = output_root / ("failed-" + revision)
        run.rename(failed)
        run = failed
        raise RuntimeError(f"{exc}\nRetained run: {run}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build", help="Build one immutable candidate; never auto-approve")
    b.add_argument("--source", type=Path, default=ROOT / "fixtures/plant-label/design.scad")
    b.add_argument("--contract", type=Path, default=ROOT / "fixtures/plant-label/contract.json")
    b.add_argument("--output-root", type=Path, default=ROOT / "output/runs")
    b.add_argument("--openscad")
    b.add_argument("--fc-match")
    b.add_argument("--timeout", type=float, default=180)
    r = commands.add_parser("render", help="Render one exact STL; no generation/re-export")
    r.add_argument("--mesh", type=Path, required=True)
    r.add_argument("--output", type=Path, required=True)
    e = commands.add_parser("export", help="Explicitly create a full rebuild ZIP without changing the revision")
    e.add_argument("run", type=Path)
    e.add_argument("--output", type=Path, required=True)
    v = commands.add_parser("verify", help="Verify a five-file revision, legacy run, or full ZIP")
    v.add_argument("run", type=Path)
    c = commands.add_parser("check", help="Measure an explicit STL against a contract")
    c.add_argument("--mesh", type=Path, required=True)
    c.add_argument("--contract", type=Path, required=True)
    c.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.source, args.contract, args.output_root, args.openscad, args.fc_match, args.timeout)
        elif args.command == "render":
            render_views(args.mesh, args.output)
            result = {"previews": str(args.output), "mesh_sha256": sha256(args.mesh)}
        elif args.command == "export":
            result = export_bundle(args.run, args.output)
        elif args.command == "verify":
            result = verify_run(args.run)
        else:
            result = measure_mesh(args.mesh, read_json(args.contract))
            result["contract_sha256"] = sha256(args.contract)
            if args.report:
                save_json(args.report, result)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 1 if result.get("required_checks_passed") is False else 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
