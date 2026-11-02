import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
import {ProjectStore,hash} from '../mcp/store.mjs';
const ROOT=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const base={title:'Test spacer',description:'A measured spacer for a workflow test.',measurements:[{name:'Width',value:15,unit:'mm',source:'measured'}],printer:{model:'unspecified',nozzle:'',material:'',plate:''},confirmed:false};
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jBv0AAAAASUVORK5CYII=','base64');
async function setup(t){await fs.mkdir(path.join(ROOT,'output/test-ui'),{recursive:true});const dir=await fs.mkdtemp(path.join(ROOT,'output/test-ui/case-'));t.after(()=>fs.rm(dir,{recursive:true,force:true}));return new ProjectStore(dir,ROOT);}
test('unit and measurement provenance survive save and reload',async t=>{const s=await setup(t);const brief={...base,measurements:[{name:'Door',value:1.5,unit:'cm',source:'estimated'}]};const p=await s.save({brief});assert.deepEqual((await s.read(p.id)).brief,brief);});
test('unknown units and nonpositive measurements fail',async t=>{const s=await setup(t);await assert.rejects(s.save({brief:{...base,measurements:[{name:'Width',value:-2,unit:'mm',source:'measured'}]}}));await assert.rejects(s.save({brief:{...base,measurements:[{name:'Width',value:2,unit:'feet',source:'measured'}]}}));});
test('stale edits cannot overwrite newer brief',async t=>{const s=await setup(t);const p=await s.save({brief:base});await s.save({projectId:p.id,expectedVersion:1,brief:{...base,title:'New title'}});await assert.rejects(s.save({projectId:p.id,expectedVersion:1,brief:base}),/changed elsewhere/);assert.equal((await s.read(p.id)).brief.title,'New title');});
test('concurrent writes do not silently lose changes',async t=>{const s=await setup(t);const p=await s.save({brief:base});const results=await Promise.allSettled([s.save({projectId:p.id,expectedVersion:1,brief:{...base,title:'A'}}),s.save({projectId:p.id,expectedVersion:1,brief:{...base,title:'B'}})]);assert.equal(results.filter(x=>x.status==='fulfilled').length,1);assert.equal((await s.read(p.id)).version,2);});
test('path-shaped project IDs are rejected',async t=>{const s=await setup(t);await assert.rejects(s.read('../other'));});
test('linked project metadata is rejected',async t=>{const s=await setup(t);const p=await s.save({brief:base});const metadata=path.join(s.directory(p.id),'project.json');await fs.rename(metadata,metadata+'.saved');await fs.symlink(metadata+'.saved',metadata);await assert.rejects(s.read(p.id),/Linked/);});
test('bundled inline UI script remains valid JavaScript',async t=>{const s=await setup(t);const html=await fs.readFile(path.join(ROOT,'dist/workbench.html'),'utf8');assert.ok(!html.includes('/*__APP_SCRIPT__*/'));const script=html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];assert.ok(script);const file=path.join(s.root,'inline.mjs');await fs.writeFile(file,script);const result=spawnSync(process.execPath,['--check',file],{encoding:'utf8'});assert.equal(result.status,0,result.stderr);});
test('photo attaches to one project, invalidates confirmation and retains hash',async t=>{const s=await setup(t);const p=await s.save({brief:{...base,confirmed:true}});const updated=await s.addPhoto({projectId:p.id,expectedVersion:1,name:'../../photo.png',mimeType:'image/png',base64:png.toString('base64')});assert.equal(updated.brief.confirmed,false);assert.equal(updated.photos[0].name,'photo.png');assert.equal(updated.photos[0].sha256,hash(png));assert.deepEqual((await s.photo(p.id,updated.photos[0].id)).bytes,png);const other=await s.save({brief:base});await assert.rejects(s.photo(other.id,updated.photos[0].id),/does not belong/);});
test('wrong image type and malformed base64 are rejected',async t=>{const s=await setup(t);const p=await s.save({brief:base});for(const [mimeType,base64]of [['image/jpeg',png.toString('base64')],['image/png','!!!!'],['image/svg+xml',Buffer.from('<svg/>').toString('base64')]])await assert.rejects(s.addPhoto({projectId:p.id,expectedVersion:1,name:'test',mimeType,base64}));});
test('modified photo bytes are detected',async t=>{const s=await setup(t);const p=await s.save({brief:base});const updated=await s.addPhoto({projectId:p.id,expectedVersion:1,name:'p.png',mimeType:'image/png',base64:png.toString('base64')});await fs.writeFile(path.join(s.directory(p.id),'photos',updated.photos[0].id),'changed');await assert.rejects(s.photo(p.id,updated.photos[0].id),/checksum/);});
test('unconfirmed and estimated briefs cannot start CAD',async t=>{const s=await setup(t);const p=await s.save({brief:base});await assert.rejects(s.build({projectId:p.id,expectedVersion:1,scad:'cube(1);',contract:{}}),/Confirm/);const next=await s.save({projectId:p.id,expectedVersion:1,brief:{...base,confirmed:true,measurements:[{...base.measurements[0],source:'estimated'}]}});await assert.rejects(s.build({projectId:p.id,expectedVersion:next.version,scad:'cube(1);',contract:{}}),/Estimated/);});
test('failed CAD keeps a failed project and original candidate',async t=>{const s=await setup(t);s.runPython=async()=>{throw new Error('simulated exporter failure');};const p=await s.save({brief:{...base,confirmed:true}});await assert.rejects(s.build({projectId:p.id,expectedVersion:1,scad:'cube(1);',contract:{}}),/simulated/);assert.equal((await s.read(p.id)).status,'build_failed');assert.equal((await fs.readdir(path.join(s.directory(p.id),'candidates'))).length,1);});
test('artifact reads bind revision, hash and allowlisted kind',async t=>{const s=await setup(t);const p=await s.save({brief:base});const dir=path.join(s.directory(p.id),'example');await fs.mkdir(dir);const bytes=Buffer.from('cube(1);');await fs.writeFile(path.join(dir,'design.scad'),bytes);p.latestRun={revision:'r1',relativeDirectory:'example',part:'parts/x.stl',artifacts:[{path:'design.scad',bytes:bytes.length,sha256:hash(bytes)}]};await fs.writeFile(path.join(s.directory(p.id),'project.json'),JSON.stringify(p));assert.equal((await s.artifact(p.id,'r1','scad')).base64,bytes.toString('base64'));await assert.rejects(s.artifact(p.id,'old','scad'),/revision/);await assert.rejects(s.artifact(p.id,'r1','../secret'),/Unknown/);await fs.writeFile(path.join(dir,'design.scad'),'changed');await assert.rejects(s.artifact(p.id,'r1','scad'),/checksum/);});
test('compiled MCP server advertises UI resource and handles real stdio calls',async t=>{
 const s=await setup(t);const client=new Client({name:'integration-test',version:'1.0.0'});
 await client.connect(new StdioClientTransport({command:process.execPath,args:[path.join(ROOT,'dist/server.mjs')],env:{...process.env,CAPTURE_TO_PRINT_DATA_DIR:s.root}}));t.after(()=>client.close());
 const tools=await client.listTools();const open=tools.tools.find(x=>x.name==='open_capture_to_print');assert.equal(open._meta.ui.resourceUri,'ui://capture-to-print/workbench-v0.2.html');
 const resource=await client.readResource({uri:open._meta.ui.resourceUri});assert.equal(resource.contents[0].mimeType,'text/html;profile=mcp-app');assert.match(resource.contents[0].text,/Add reference photos/);
 const saved=await client.callTool({name:'save_design_brief',arguments:{brief:base}});assert.ok(saved.structuredContent.project.id);
 const listed=await client.callTool({name:'list_design_projects',arguments:{}});assert.equal(listed.structuredContent.projects.length,1);
 const invalid=await client.callTool({name:'get_design_project',arguments:{projectId:'../outside'}});assert.equal(invalid.isError,true);
});

test('compact build retains five artifacts and clears only its transient inputs',async t=>{
 const s=await setup(t),p=await s.save({brief:{...base,confirmed:true}});let built;
 s.runPython=async(args,cwd,log)=>{
  if(args[0]==='verify')return '{}';
  const root=args[args.indexOf('--output-root')+1];built=path.join(root,'test-r1');await fs.mkdir(built,{recursive:true});
  const files=[];for(const [name,data]of Object.entries({'design.scad':'cube(1);','design-contract.json':'{}','part.stl':'mesh','preview.png':'image'})){
   await fs.writeFile(path.join(built,name),data);files.push({path:name,bytes:Buffer.byteLength(data),sha256:hash(Buffer.from(data))});
  }
  await fs.writeFile(path.join(built,'revision.json'),JSON.stringify({revision:'r1',checks:{required_checks_passed:true,checks:[]},files}));
  await fs.writeFile(log,JSON.stringify({run:built}));
 };
 const result=await s.build({projectId:p.id,expectedVersion:1,scad:'cube(1);',contract:{}});
 assert.equal(result.latestRun.format,2);assert.equal(result.latestRun.artifacts.length,5);
 assert.equal((await fs.readdir(built)).length,5);
 assert.deepEqual(await fs.readdir(path.join(s.directory(p.id),'candidates')),[]);
 assert.equal(result.latestRun.fullBundle,undefined);
 await assert.rejects(s.artifact(p.id,'r1','bundle'),/Create full ZIP/);
 assert.equal((await s.artifact(p.id,'r1','checks')).name,'revision.json');
 assert.equal((await s.artifact(p.id,'r1','preview')).name,'preview.png');
});

test('explicit bundle export binds revision, reuses export and leaves run unchanged',async t=>{
 const s=await setup(t),p=await s.save({brief:base});const dir=path.join(s.directory(p.id),'runs','r1');await fs.mkdir(dir,{recursive:true});
 await fs.writeFile(path.join(dir,'revision.json'),'original');
 p.latestRun={format:2,revision:'r1',relativeDirectory:'runs/r1',artifacts:[],part:'part.stl'};
 await fs.writeFile(path.join(s.directory(p.id),'project.json'),JSON.stringify(p));let exports=0;
 s.runPython=async(args)=>{assert.equal(args[0],'export');exports++;const dest=args[args.indexOf('--output')+1];await fs.mkdir(path.dirname(dest),{recursive:true});const data=Buffer.from('test zip');await fs.writeFile(dest,data);return JSON.stringify({bundle:dest,revision:'r1',sha256:hash(data),bytes:data.length});};
 await assert.rejects(s.exportBundle({projectId:p.id,revision:'old'}),/revision/);
 await s.exportBundle({projectId:p.id,revision:'r1'});await s.exportBundle({projectId:p.id,revision:'r1'});
 assert.equal(exports,1);assert.equal(await fs.readFile(path.join(dir,'revision.json'),'utf8'),'original');
 const a=await s.artifact(p.id,'r1','bundle');assert.equal(Buffer.from(a.base64,'base64').toString(),'test zip');
 const saved=await s.read(p.id);await fs.writeFile(path.join(s.directory(p.id),saved.latestRun.fullBundle.path),'tampered');
 await assert.rejects(s.artifact(p.id,'r1','bundle'),/checksum/);
});

test('failed on-demand export never records a downloadable bundle',async t=>{
 const s=await setup(t),p=await s.save({brief:base});const dir=path.join(s.directory(p.id),'runs/r1');await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'revision.json'),'original');
 p.latestRun={format:2,revision:'r1',relativeDirectory:'runs/r1',artifacts:[]};await fs.writeFile(path.join(s.directory(p.id),'project.json'),JSON.stringify(p));
 s.runPython=async()=>{throw new Error('missing pinned resource');};
 await assert.rejects(s.exportBundle({projectId:p.id,revision:'r1'}),/missing pinned/);
 assert.equal((await s.read(p.id)).latestRun.fullBundle,undefined);
 assert.equal(await fs.readFile(path.join(dir,'revision.json'),'utf8'),'original');
});
