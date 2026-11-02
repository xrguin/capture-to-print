import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
import {build} from 'esbuild';
const root=process.cwd();
const client=new Client({name:'Local UI QA',version:'0.1.0'});
await client.connect(new StdioClientTransport({command:process.execPath,args:[path.join(root,'dist/server.mjs')],env:{...process.env,CAPTURE_TO_PRINT_DATA_DIR:process.env.CAPTURE_TO_PRINT_DATA_DIR||path.join(root,'output/ui-qa/projects')}}));
const host=(await build({entryPoints:['tests/harness-host.mjs'],bundle:true,platform:'browser',format:'esm',write:false})).outputFiles[0].text;
const server=http.createServer(async(req,res)=>{
 try{
  if(req.headers.host!==`127.0.0.1:${server.address().port}`)throw new Error('Invalid host');
  const url=new URL(req.url,`http://${req.headers.host}`);
  if(req.method==='GET'&&url.pathname==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><title>Capture to Print — local UI QA</title><style>body{margin:0;background:#edf1ec;font:13px system-ui}header{padding:10px;background:#203e33;color:white}iframe{display:block;border:0;background:white;width:100%;height:900px;max-width:1040px;margin:auto}#events{padding:10px;white-space:pre-wrap}</style><header>Local UI test host · real MCP server · messages/download requests captured, no model call</header><iframe title="Capture to Print panel"></iframe><div id="events"></div><script type="module" src="/host.js"></script>');}
  else if(req.method==='GET'&&url.pathname==='/host.js'){res.setHeader('Content-Type','text/javascript');res.end(host);}
  else if(req.method==='GET'&&url.pathname==='/workbench'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(await fs.readFile(path.join(root,'dist/workbench.html')));}
  else if(req.method==='POST'&&url.pathname==='/call'){
   if(req.headers.origin!==`http://${req.headers.host}`||!req.headers['content-type']?.startsWith('application/json'))throw new Error('Invalid request origin');
   let body='';for await(const chunk of req){body+=chunk;if(body.length>12000000)throw new Error('Request too large');}
   const params=JSON.parse(body);if(params.name==='build_cad_candidate')throw new Error('Native CAD is tested separately, not from the browser QA host.');
   const result=await client.callTool(params);res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result));
  }else{res.statusCode=404;res.end('Not found');}
 }catch(error){res.statusCode=400;res.end(error.message);}
});
server.listen(0,'127.0.0.1',()=>console.log(`QA_URL=http://127.0.0.1:${server.address().port}`));
process.on('SIGTERM',async()=>{server.close();await client.close();process.exit(0);});
