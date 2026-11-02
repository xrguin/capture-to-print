"""Package bounded numeric OpenSCAD Customizer controls from a verified run.

This checks the declared parameter surface, not every possible model variant or
MakerWorld's hosted engine. Keep geometry checks and platform trials separate.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import zipfile

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n')
def number(value):
    return type(value) in (int,float) and math.isfinite(value)
def on_grid(value,p):
    return (number(value) and p['minimum']-1e-8<=value<=p['maximum']+1e-8
            and abs((value-p['minimum'])/p['step']-round((value-p['minimum'])/p['step']))<1e-7)

def inspect_source(source,schema):
    source=Path(source);text=source.read_text()
    if schema.get('schema_version')!=1 or sha(source)!=schema.get('source_sha256'):
        raise ValueError('Parameter schema must pin these exact source bytes')
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    if re.search(r'\b(?:include|use)\s*<|\b(?:import|surface)\s*\(',code):
        raise ValueError('Customizer package must be self-contained; external assets are unsupported')
    declared=schema.get('parameters',[])
    if not declared or len({p.get('name') for p in declared})!=len(declared):
        raise ValueError('Declare unique, nonempty parameters')
    for p in declared:
        if not re.fullmatch(r'[A-Za-z_]\w*',p.get('name','')) or not p.get('label'):
            raise ValueError('Each parameter needs a name and readable label')
        if not all(number(p.get(k)) for k in ['default','minimum','maximum','step']):
            raise ValueError('This inspector supports finite numeric controls only')
        if p['step']<=0 or p['minimum']>=p['maximum'] or not on_grid(p['default'],p) or not on_grid(p['maximum'],p):
            raise ValueError('Invalid bounds, step or default for '+p['name'])
    exposed={};hidden=False;group=None
    for line in text.splitlines():
        tab=re.fullmatch(r'\s*/\*\s*\[([^\]]+)\]\s*\*/\s*',line)
        if tab:group=tab[1];hidden=group=='Hidden';continue
        stripped=line.strip()
        if not stripped or stripped.startswith('//'):continue
        if '{' in line:break
        if hidden:continue
        assignment=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*=\s*([^;]+);\s*//\s*\[([^\]]+)\]\s*',line)
        if not assignment:
            raise ValueError('Use one bounded numeric literal per visible line, followed by [Hidden]')
        name,literal,annotation=assignment.groups()
        try:value=float(literal);bounds=[float(x) for x in annotation.split(':')]
        except ValueError:raise ValueError('Visible controls require numeric literals and explicit bounds')
        if name in exposed or len(bounds)!=3 or not group:
            raise ValueError('Duplicate control or missing group/min:step:max annotation')
        exposed[name]=dict(default=value,minimum=bounds[0],step=bounds[1],maximum=bounds[2],group=group)
    if not hidden:raise ValueError('Add [Hidden] after the public controls to protect internal dimensions')
    if set(exposed)!={p['name'] for p in declared}:
        raise ValueError('Exposed controls differ from the declared surface; check hidden fit dimensions')
    for p in declared:
        if any(abs(exposed[p['name']][k]-p[k])>1e-8 for k in ['default','minimum','maximum','step']):
            raise ValueError('Source annotations/default differ from schema for '+p['name'])
    presets=schema.get('presets',{})
    if not presets:raise ValueError('Provide at least one complete preset')
    for name,values in presets.items():
        if not isinstance(name,str) or not name or set(values)!=set(exposed):
            raise ValueError('Every named preset must specify exactly the public controls')
        if not all(on_grid(values[p['name']],p) for p in declared):
            raise ValueError('Out-of-range or off-step preset: '+name)
    return dict(passed=True,source_sha256=sha(source),exposed_parameters=exposed,presets=list(presets),
        scope='Source metadata and preset values only; this is not a full OpenSCAD parser or geometric range proof.',
        makerworld_hosted_execution='not tested by this command',user_acceptance='pending')

def package(run,schema_path,output):
    run,output=Path(run).resolve(),Path(output).resolve()
    spec=importlib.util.spec_from_file_location('ctp_parametric_core',Path(__file__).with_name('capture_to_print.py'))
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    core.verify_run(run)
    schema=json.loads(Path(schema_path).read_text())
    report=inspect_source(run/'design.scad',schema)
    contract=json.loads((run/'design-contract.json').read_text())
    compact=(run/'revision.json').exists()
    state=json.loads((run/('revision.json' if compact else 'state.json')).read_text())
    mesh=run/'part.stl' if compact else run/'parts'/(contract['name']+'.stl')
    report.update(revision=state['revision'],
        default_mesh_sha256=sha(mesh),
        schema_sha256=sha(schema_path),packager_sha256=sha(Path(__file__)))
    output.mkdir(parents=True,exist_ok=False)
    shutil.copy2(run/'design.scad',output/'model.scad')
    shutil.copy2(schema_path,output/'parameter-schema.json')
    shutil.copy2(mesh,output/'default-model.stl')
    save(output/'model.json',dict(fileFormatVersion='1',parameterSets={name:{k:str(v) for k,v in values.items()}
        for name,values in schema['presets'].items()}))
    save(output/'parameter-checks.json',report)
    rows=['| Control | Default | Minimum | Maximum | Step |','| --- | ---: | ---: | ---: | ---: |']
    rows += [f"| {p['label']} (`{p['name']}`) | {p['default']} | {p['minimum']} | {p['maximum']} | {p['step']} |" for p in schema['parameters']]
    (output/'PARAMETERS.md').write_text('# Customizer controls\n\n'+'\n'.join(rows)+'\n\nFixed interfaces:\n\n'+'\n'.join('- '+x for x in schema.get('fixed_dimensions',[]))+'\n')
    (output/'README.md').write_text('# Editable parametric model\n\n'
        'Open model.scad in OpenSCAD with Customizer enabled, or trial it in MakerWorld Parametric Model Maker. '
        'The .scad contains the controls; model.json contains optional local OpenSCAD presets. '
        'Do not upload the STL expecting editable controls.\n\n'
        'Example: openscad --backend CGAL -p model.json -P Compact -o compact.stl model.scad\n\n'
        'Only the default has the validation state of the linked run. Every changed preset needs its own geometry checks, '
        'previews, slicer profile and user review. Declared bounds are design limits, not proof of all combinations. '
        'Preserve fit interfaces unless a separately checked mating set is generated. A printer-ready 3MF applies to '
        'its exact mesh/settings, not all parameter values. MakerWorld execution and publication are separate steps; '
        'this command performs neither. Approval, physical fit and print performance are not inferred.\n')
    files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(output.rglob('*')) if p.is_file()]
    save(output/'manifest.json',dict(schema_version=1,status='awaiting_user_review',revision=report['revision'],files=files))
    archive=output.with_name(output.name+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(archive) as z:
        for item in files:
            if hashlib.sha256(z.read(item['path'])).hexdigest()!=item['sha256']:raise ValueError('ZIP mismatch')
    return dict(output=str(output),archive=str(archive),verified_files=len(files),**report)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('inspect');p.add_argument('--source',type=Path,required=True);p.add_argument('--parameters',type=Path,required=True)
    p=sub.add_parser('package');p.add_argument('--run',type=Path,required=True);p.add_argument('--parameters',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=inspect_source(args.source,json.loads(args.parameters.read_text())) if args.command=='inspect' else package(args.run,args.parameters,args.output)
        print(json.dumps(result,indent=2))
    except (ValueError,KeyError,OSError) as e:
        parser.exit(1,json.dumps(dict(status='failed',error=str(e)))+'\n')

if __name__=='__main__':main()
