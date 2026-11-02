"""Mesh and failure-path tests. Fake exporters do not count as CAD integration tests."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np
from PIL import Image
import trimesh

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ctp", ROOT / "scripts/capture_to_print.py")
ctp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctp)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        test_root = ROOT / "output/test-work"
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_root)
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.source = self.work / "design.scad"
        self.source.write_text("cube([10, 20, 2], center=true);\n")
        self.contract = {
            "schema_version": 1, "name": "test-box", "units": "mm",
            "source_sha256": ctp.sha256(self.source), "font_pattern": None,
            "expected_components": 1,
            "dimensions": [
                {"id": "width", "method": "bbox_extent", "axis": 0, "expected_mm": 10, "tolerance_mm": .01},
                {"id": "length", "method": "bbox_extent", "axis": 1, "expected_mm": 20, "tolerance_mm": .01},
                {"id": "thickness", "method": "bbox_extent", "axis": 2, "expected_mm": 2, "tolerance_mm": .01},
                {"id": "section", "method": "plane_span", "axis": 0, "plane_axis": 1,
                 "plane_offset_mm": 0, "expected_mm": 10, "tolerance_mm": .01}
            ]}
        self.contract_path = self.work / "contract.json"
        ctp.save_json(self.contract_path, self.contract)
        self.box = trimesh.creation.box(extents=[10, 20, 2])

    def measure(self, mesh, contract=None):
        path = self.work / "sample.stl"
        mesh.export(path)
        before = ctp.sha256(path)
        result = ctp.measure_mesh(path, contract or self.contract)
        self.assertEqual(before, ctp.sha256(path), "Measurement must not change the artifact")
        return result

    @staticmethod
    def status(report, check):
        return next(x["status"] for x in report["checks"] if x["id"] == check)

    def test_mesh_dimensions_and_section(self):
        report = self.measure(self.box)
        self.assertTrue(report["required_checks_passed"])
        self.assertEqual(report["extents_mm"], [10, 20, 2])
        self.assertEqual(self.status(report, "global_minimum_wall"), "unassessed")

    def test_scaled_mesh_is_rejected(self):
        mesh = self.box.copy()
        mesh.apply_scale(.8)
        report = self.measure(mesh)
        self.assertFalse(report["required_checks_passed"])
        self.assertEqual(self.status(report, "width"), "fail")
        self.assertEqual(self.status(report, "section"), "fail")

    def test_missing_section_is_rejected(self):
        c = deepcopy(self.contract)
        c["dimensions"][-1]["plane_offset_mm"] = 100
        self.assertEqual(self.status(self.measure(self.box, c), "section"), "fail")

    def test_envelope_failure_does_not_resize_mesh(self):
        c = {**self.contract, "build_envelope_mm": [9, 30, 10]}
        report = self.measure(self.box, c)
        self.assertEqual(report["extents_mm"], [10, 20, 2])
        self.assertEqual(self.status(report, "envelope"), "fail")

    def test_open_mesh_is_rejected(self):
        mesh = self.box.copy()
        mesh.update_faces(np.arange(len(mesh.faces) - 1))
        self.assertEqual(self.status(self.measure(mesh), "watertight"), "fail")

    def test_inverted_mesh_is_rejected(self):
        mesh = self.box.copy()
        mesh.invert()
        self.assertEqual(self.status(self.measure(mesh), "positive_volume"), "fail")

    def test_degenerate_face_is_retained_and_rejected(self):
        vertices = np.vstack([self.box.vertices, [[30, 30, 30]] * 3])
        faces = np.vstack([self.box.faces, [[8, 9, 10]]])
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        self.assertEqual(self.status(self.measure(mesh), "nondegenerate"), "fail")

    def test_component_count_follows_intent(self):
        other = self.box.copy()
        other.apply_translation([30, 0, 0])
        mesh = trimesh.util.concatenate([self.box, other])
        c = deepcopy(self.contract)
        c["dimensions"] = [c["dimensions"][2]]
        self.assertEqual(self.status(self.measure(mesh, c), "components"), "fail")
        c["expected_components"] = 2
        self.assertTrue(self.measure(mesh, c)["required_checks_passed"])

    def test_nonfinite_vertex_is_not_silently_removed(self):
        mesh = self.box.copy()
        mesh.vertices[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            self.measure(mesh)

    def test_empty_mesh_is_rejected(self):
        path = self.work / "empty.stl"
        path.write_bytes(b"")
        with self.assertRaises(ValueError):
            ctp.measure_mesh(path, self.contract)

    def test_unsupported_contracts_fail_closed(self):
        edits = [lambda c: c.update(units="in"), lambda c: c.update(unknown=True),
                 lambda c: c.update(expected_components=True),
                 lambda c: c["dimensions"][0].update(method="minimum_wall"),
                 lambda c: c["dimensions"][0].update(axis=True),
                 lambda c: c["dimensions"][0].update(expected_mm=float("nan")),
                 lambda c: c["dimensions"][0].update(tolerance_mm=0),
                 lambda c: c["dimensions"][0].update(id="components"),
                 lambda c: c["dimensions"].append(c["dimensions"][0])]
        for edit in edits:
            with self.subTest(edit=edit):
                c = deepcopy(self.contract)
                edit(c)
                with self.assertRaises(ValueError):
                    ctp.validate_contract(c)

    def test_changed_source_and_external_dependencies_are_rejected(self):
        self.source.write_text("include <other.scad>\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            ctp.preflight_source(self.source, self.contract)
        c = {**self.contract, "source_sha256": ctp.sha256(self.source)}
        with self.assertRaisesRegex(ValueError, "self-contained"):
            ctp.preflight_source(self.source, c)

    def test_timeout_retains_log_and_terminates_process(self):
        with self.assertRaisesRegex(RuntimeError, "exceeded"):
            ctp.run_tool([sys.executable, "-c", "import time; print('started', flush=True); time.sleep(30)"],
                         self.work, os.environ.copy(), .3, self.work / "timeout.log")
        self.assertIn("started", (self.work / "timeout.log").read_text())

    def fake_font(self, run, tool, pattern):
        shutil.copytree(ROOT / "assets/fonts", run / "fonts")
        (run / "font-match.log").write_text("test font probe\n")
        return os.environ.copy(), {"file": "fonts/WorkSans-Bold.ttf", "sha256": ctp.sha256(run / "fonts/WorkSans-Bold.ttf")}

    def fake_tool(self, argv, cwd, env, timeout, log):
        argv = [str(x) for x in argv]
        log = Path(log)
        log.write_text("test exporter/renderer stub\n")
        if "--version" in argv:
            return
        if "--export-format" in argv:
            self.box.export(Path(cwd) / argv[argv.index("-o") + 1])
        elif "check" in argv:
            report = ctp.measure_mesh(Path(argv[argv.index("--mesh") + 1]), self.contract)
            report["contract_sha256"] = ctp.sha256(Path(argv[argv.index("--contract") + 1]))
            ctp.save_json(Path(argv[argv.index("--report") + 1]), report)
        elif "render" in argv:
            destination = Path(argv[argv.index("--output") + 1])
            destination.mkdir()
            # Stub images exercise packaging only; real preview validation is a separate native run.
            for name in (*ctp.VIEWS, "contact-sheet"):
                Image.new("RGB", (4, 4), "green").save(destination / f"{name}.png")

    def mocked_build(self, tool=None):
        with patch.object(ctp, "executable", return_value="test-executable"), \
             patch.object(ctp, "prepare_font", side_effect=self.fake_font), \
             patch.object(ctp, "run_tool", side_effect=tool or self.fake_tool):
            return ctp.build(self.source, self.contract_path, self.work / "runs")

    def test_success_keeps_exactly_five_files_without_zip(self):
        output = self.work / "runs"
        output.mkdir()
        (output / "stale.stl").write_text("not an artifact")
        result = self.mocked_build()
        run = Path(result["run"])
        self.assertEqual(result["status"], "awaiting_user_review")
        self.assertIsNone(result["bundle"])
        self.assertEqual({p.name for p in run.iterdir()}, ctp.REVISION_FILES)
        self.assertEqual(ctp.read_json(run / "revision.json")["user_acceptance"], "pending")
        self.assertFalse(list(output.glob(".building-*")))
        self.assertFalse(list(output.rglob("*.zip")))
        self.assertEqual(ctp.verify_run(run)["verified_files"], 5)

    def test_shared_resources_reused_between_revisions(self):
        first, second = Path(self.mocked_build()["run"]), Path(self.mocked_build()["run"])
        self.assertNotEqual(first, second)
        self.assertEqual(ctp.read_json(first / "revision.json")["resources"], ctp.read_json(second / "revision.json")["resources"])
        self.assertEqual(len(list((first.parent / ".resources").iterdir())), 1)

    def test_explicit_export_is_relocatable_and_leaves_revision_unchanged(self):
        run = Path(self.mocked_build()["run"])
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        bundle = self.work / "exports" / "full.zip"
        ctp.export_bundle(run, bundle)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})
        ctp.verify_bundle(bundle)
        with zipfile.ZipFile(bundle) as archive:
            self.assertEqual(len(archive.namelist()), 13)
            self.assertNotIn("stale.stl", archive.namelist())
            archive.extractall(self.work / "relocated")
        relocated = self.work / "relocated/revision"
        ctp.verify_run(relocated)
        ctp.export_bundle(relocated, self.work / "second.zip")
        with self.assertRaisesRegex(ValueError, "already exists"):
            ctp.export_bundle(run, bundle)
        with self.assertRaisesRegex(ValueError, "outside"):
            ctp.export_bundle(run, run / "full.zip")

    def test_export_rejects_missing_or_changed_resources(self):
        run = Path(self.mocked_build()["run"])
        resources = run / ctp.read_json(run / "revision.json")["resources"]["path"]
        (resources / "requirements.txt").write_text("changed")
        with self.assertRaisesRegex(ValueError, "resources"):
            ctp.export_bundle(run, self.work / "bad.zip")
        self.assertFalse((self.work / "bad.zip").exists())

    def test_failed_render_preserves_failure_without_bundle(self):
        def fail_render(argv, *args):
            if "render" in argv:
                raise RuntimeError("simulated render failure")
            return self.fake_tool(argv, *args)
        with self.assertRaisesRegex(RuntimeError, "simulated render failure"):
            self.mocked_build(fail_render)
        run, = (self.work / "runs").glob("failed-*")
        self.assertEqual(ctp.read_json(run / "state.json")["failed_stage"], "rendering")
        self.assertTrue((run / "build.log").exists())
        self.assertFalse((run / "revision.json").exists())
        self.assertFalse(list(run.glob("*.zip")))

    def test_failed_checks_never_publish_revision(self):
        def fail_checks(argv, *args):
            self.fake_tool(argv, *args)
            if "check" in argv:
                report = Path(argv[argv.index("--report") + 1])
                ctp.save_json(report, {"required_checks_passed": False})
        with self.assertRaisesRegex(RuntimeError, "Required geometry"):
            self.mocked_build(fail_checks)
        self.assertFalse(list((self.work / "runs").glob("*/revision.json")))

    def test_failed_export_does_not_reuse_old_stl(self):
        def fail_export(argv, *args):
            if "--export-format" in argv:
                raise RuntimeError("simulated export failure")
            return self.fake_tool(argv, *args)
        with self.assertRaisesRegex(RuntimeError, "simulated export failure"):
            self.mocked_build(fail_export)
        run, = (self.work / "runs").glob("failed-*")
        self.assertEqual(ctp.read_json(run / "state.json")["status"], "failed")
        self.assertFalse((run / "revision.json").exists())

    def test_integrity_detects_changed_preview_and_zip(self):
        run = Path(self.mocked_build()["run"])
        preview = run / "preview.png"
        original = preview.read_bytes()
        preview.write_bytes(original + b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            ctp.verify_run(run)
        preview.write_bytes(original)
        bundle = self.work / "full.zip"
        ctp.export_bundle(run, bundle)
        with zipfile.ZipFile(bundle, "a") as archive:
            archive.writestr("extra.txt", "unexpected")
        with self.assertRaisesRegex(ValueError, "membership"):
            ctp.verify_bundle(bundle)

    def test_checks_cannot_reference_stale_mesh(self):
        run = Path(self.mocked_build()["run"])
        record = ctp.read_json(run / "revision.json")
        record["checks"]["mesh_sha256"] = "0" * 64
        ctp.save_json(run / "revision.json", record)
        with self.assertRaisesRegex(ValueError, "bound"):
            ctp.verify_run(run)

    def test_unrequested_files_and_path_escapes_are_rejected(self):
        run = Path(self.mocked_build()["run"])
        extra = run / "unrequested.zip"
        extra.write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "five files"):
            ctp.verify_run(run)
        extra.unlink()
        record = ctp.read_json(run / "revision.json")
        record["files"][0]["path"] = "../outside"
        ctp.save_json(run / "revision.json", record)
        with self.assertRaisesRegex(ValueError, "four artifacts"):
            ctp.verify_run(run)

    def test_legacy_reader_retains_original_bundle(self):
        run = Path(self.mocked_build()["run"])
        record = ctp.read_json(run / "revision.json")
        legacy = self.work / "legacy"
        legacy.mkdir()
        resources = run / record["resources"]["path"]
        for name in ctp.RESOURCE_FILES:
            target = legacy / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resources / name, target)
        for name in ["design.scad", "design-contract.json"]:
            shutil.copy2(run / name, legacy / name)
        (legacy / "parts").mkdir()
        part = "parts/test-box.stl"
        shutil.copy2(run / "part.stl", legacy / part)
        (legacy / "previews").mkdir()
        for name in (*ctp.VIEWS, "contact-sheet"):
            shutil.copy2(run / "preview.png", legacy / "previews" / (name + ".png"))
        ctp.save_json(legacy / "checks.json", record["checks"])
        ctp.save_json(legacy / "build-record.json", record["build"])
        ctp.save_json(legacy / "state.json", {"revision": record["revision"], "status": record["status"], "user_acceptance": "pending"})
        evidence = ["design.scad", "design-contract.json", part, "checks.json", "build-record.json", "fonts/WorkSans-Bold.ttf"] + ["previews/" + n + ".png" for n in ctp.VIEWS]
        ctp.save_json(legacy / "review.json", {"revision": record["revision"], "user_acceptance": "pending", "evidence": ctp.artifact_rows(legacy, evidence)})
        files = [p.relative_to(legacy).as_posix() for p in legacy.rglob("*") if p.is_file()]
        ctp.save_json(legacy / "manifest.json", {"schema_version": 1, "revision": record["revision"], "status": record["status"], "parts": [{"path": part, "quantity": 1}], "files": ctp.artifact_rows(legacy, files)})
        original = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        ctp.verify_run(legacy)
        ctp.export_bundle(legacy, self.work / "legacy.zip")
        self.assertEqual(original, {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
