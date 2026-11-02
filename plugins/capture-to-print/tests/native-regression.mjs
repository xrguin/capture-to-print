// Explicit native integration test. Uses the unchanged plant-label fixture, no model/API calls.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
const root=process.cwd();
await fs.mkdir(path.join(root,'output'),{recursive:true});
const evidence=await fs.mkdtemp(path.join(root,'output/five-file-native-'));
const dataRoot=path.join(evidence,'projects');
const sha=b=>createHash('sha256').update(b).digest('hex');
const client=new Client({name:'capture-to-print-native-regression',version:'0.2.0'});
await client.connect(new StdioClientTransport({command:'/bin/sh',args:[path.join(root,'scripts/launch-mcp.sh')],env:{...process.env,CAPTURE_TO_PRINT_NODE:process.execPath,CAPTURE_TO_PRINT_DATA_DIR:dataRoot}}));
try{
 const contract=JSON.parse(await fs.readFile('fixtures/plant-label/contract.json','utf8'));
 const brief={title:'Plant label — regression',description:'Unchanged Basil label. Native UI-to-CAD integration test; not a new design or user approval.',measurements:contract.dimensions.map(x=>({name:x.id,value:x.expected_mm,unit:'mm',source:'measured'})),printer:{model:'unspecified',nozzle:'',material:'',plate:''},confirmed:true};
 const saved=await client.callTool({name:'save_design_brief',arguments:{brief}});
 if(saved.isError)throw new Error(JSON.stringify(saved));
 const p=saved.structuredContent.project;
 const result=await client.callTool({name:'build_cad_candidate',arguments:{projectId:p.id,expectedVersion:p.version,scad:await fs.readFile('fixtures/plant-label/design.scad','utf8'),contract}},undefined,{timeout:660000});
 if(result.isError)throw new Error(JSON.stringify(result));
 const project=result.structuredContent.project;
 const run=path.join(dataRoot,project.id,project.latestRun.relativeDirectory);
 const names=(await fs.readdir(run)).sort();assert.deepEqual(names,['design-contract.json','design.scad','part.stl','preview.png','revision.json']);
 assert.equal(project.latestRun.fullBundle,undefined);
 const before=Object.fromEntries(await Promise.all(names.map(async name=>[name,sha(await fs.readFile(path.join(run,name)))])));
 for(const kind of ['scad','stl','checks','contract','preview']){
  const r=await client.callTool({name:'get_design_artifact',arguments:{projectId:project.id,revision:project.latestRun.revision,kind}});
  assert.equal(r.isError,undefined,JSON.stringify(r));assert.ok(r.structuredContent.artifact.base64);
 }
 const refused=await client.callTool({name:'get_design_artifact',arguments:{projectId:project.id,revision:project.latestRun.revision,kind:'bundle'}});
 assert.equal(refused.isError,true);
 const exported=await client.callTool({name:'export_design_bundle',arguments:{projectId:project.id,revision:project.latestRun.revision}});
 assert.equal(exported.isError,undefined,JSON.stringify(exported));
 const a=await client.callTool({name:'get_design_artifact',arguments:{projectId:project.id,revision:project.latestRun.revision,kind:'bundle'}});
 assert.equal(a.isError,undefined,JSON.stringify(a));
 const after=Object.fromEntries(await Promise.all(names.map(async name=>[name,sha(await fs.readFile(path.join(run,name)))])));
 assert.deepEqual(before,after);
 const report={projectId:project.id,revision:project.latestRun.revision,status:project.status,checks:project.latestRun.checks,runDirectory:run,dataRoot,
  files:before,bundle:path.join(dataRoot,project.id,exported.structuredContent.bundle.path),bundle_sha256:a.structuredContent.artifact.sha256};
 await fs.writeFile(path.join(evidence,'result.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({evidence,projectId:project.id,revision:project.latestRun.revision,status:project.status,extents_mm:project.latestRun.checks.extents_mm,file_count:names.length},null,2));

}finally{await client.close();}
