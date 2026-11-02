import {build} from 'esbuild';
import fs from 'node:fs/promises';
import path from 'node:path';
await fs.mkdir('dist',{recursive:true});
const ui=await build({entryPoints:['ui/app.mjs'],bundle:true,format:'esm',platform:'browser',target:'es2022',write:false,minify:true,legalComments:'inline',metafile:true});
const template=await fs.readFile('ui/workbench.html','utf8');
await fs.writeFile('dist/workbench.html',template.replace('/*__APP_SCRIPT__*/',()=>ui.outputFiles[0].text.replaceAll('</script','<\\/script')));
const server=await build({entryPoints:['mcp/server.mjs'],outfile:'dist/server.mjs',bundle:true,platform:'node',format:'esm',target:'node22',legalComments:'inline',metafile:true,banner:{js:"import { createRequire as __createRequire } from 'node:module'; const require = __createRequire(import.meta.url);"}});
// Include the actual license files of every dependency contributing to a bundle.
const packages=new Set();
for(const input of [...Object.keys(ui.metafile.inputs),...Object.keys(server.metafile.inputs)]) {
  if(!input.includes('node_modules/'))continue;
  let dir=path.dirname(path.resolve(input));
  while(dir!==path.dirname(dir)) {
    try {await fs.access(path.join(dir,'package.json'));const pkg=JSON.parse(await fs.readFile(path.join(dir,'package.json'),'utf8'));if(pkg.name){packages.add(dir);break;}} catch {}
    dir=path.dirname(dir);
  }
}
const notices=[];
for(const dir of [...packages].sort()) {
  const pkg=JSON.parse(await fs.readFile(path.join(dir,'package.json'),'utf8'));
  const licenses=(await fs.readdir(dir,{withFileTypes:true})).filter(e=>e.isFile()&&/^(licen[sc]e|notice|copying)([.-]|$)/i.test(e.name));
  if(!licenses.length)throw new Error(`No license found for bundled ${pkg.name}`);
  notices.push(`${pkg.name} ${pkg.version} (${pkg.license})\n${'='.repeat(72)}`);
  for(const file of licenses)notices.push(`${file.name}\n${await fs.readFile(path.join(dir,file.name),'utf8')}`);
}
await fs.writeFile('dist/THIRD_PARTY_LICENSES.txt',notices.join('\n\n'));
console.log('Built embedded workbench and stdio MCP server.');
