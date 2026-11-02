from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('parametric',Path(__file__).resolve().parents[1]/'scripts/package_parametric.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class ParametricSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'model.scad'
        self.text='/* [Body] */\n// Height in mm\nheight=100; // [80:10:120]\n/* [Hidden] */\nthread_pitch=4;\ncylinder(h=height,r=20);\n'
        self.schema=dict(schema_version=1,parameters=[dict(name='height',label='Height',default=100,minimum=80,maximum=120,step=10)],presets={'Default':{'height':100},'Small':{'height':80}})
        self.write(self.text)
    def write(self,text):
        self.source.write_text(text);self.schema['source_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
    def inspect(self):return p.inspect_source(self.source,self.schema)
    def test_default_and_boundary_preset(self):
        self.assertTrue(self.inspect()['passed'])
        self.assertEqual(set(self.inspect()['exposed_parameters']),{'height'})
    def test_fit_parameter_accidentally_exposed(self):
        self.write(self.text.replace('/* [Hidden] */\nthread_pitch=4;','thread_pitch=4; // [2:1:8]\n/* [Hidden] */'))
        with self.assertRaisesRegex(ValueError,'Exposed controls'):self.inspect()
    def test_stale_source_binding(self):
        self.source.write_text(self.text+'// Changed\n')
        with self.assertRaisesRegex(ValueError,'exact source'):self.inspect()
    def test_off_step_and_outside_presets(self):
        for value in [85,130,float('nan')]:
            self.schema['presets']['Small']['height']=value
            with self.assertRaisesRegex(ValueError,'Out-of-range'):self.inspect()
    def test_unknown_preset_cannot_override_fixed_interface(self):
        self.schema['presets']['Small']['thread_pitch']=2
        with self.assertRaisesRegex(ValueError,'exactly the public'):self.inspect()
    def test_unbounded_or_expression_control_rejected(self):
        for line in ['height=100;','height=50*2; // [80:10:120]']:
            self.write(self.text.replace('height=100; // [80:10:120]',line))
            with self.assertRaises(ValueError):self.inspect()
    def test_external_asset_rejected(self):
        self.write(self.text+'import("private-part.stl");\n')
        with self.assertRaisesRegex(ValueError,'self-contained'):self.inspect()
    def test_ranges_match_source_and_schema(self):
        self.schema['parameters'][0]['maximum']=130
        with self.assertRaisesRegex(ValueError,'annotations'):self.inspect()

if __name__=='__main__':unittest.main()
