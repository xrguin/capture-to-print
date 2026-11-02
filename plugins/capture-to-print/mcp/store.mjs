import fs from 'node:fs/promises';
import path from 'node:path';
import {randomUUID, createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {z} from 'zod';

export const hash = bytes => createHash('sha256').update(bytes).digest('hex');
export const idSchema = z.string().uuid();
export const briefSchema = z.object({
  title: z.string().trim().min(1).max(120),
  description: z.string().trim().min(1).max(6000),
  measurements: z.array(z.object({name:z.string().trim().min(1).max(80),value:z.number().finite().positive().max(100000),unit:z.enum(['mm','cm','in']),source:z.enum(['measured','estimated'])}).strict()).max(30),
  printer: z.object({model:z.enum(['unspecified','A1 mini','P1P','other']),nozzle:z.string().max(30),material:z.string().max(80),plate:z.string().max(80)}).strict(),
  confirmed: z.boolean()
}).strict();
const clone = value => structuredClone(value);
export async function saveJson(file, value) {
  const temp = file+'.'+randomUUID()+'.tmp';
  await fs.writeFile(temp,JSON.stringify(value,null,2)+'\n',{mode:0o600});
  await fs.rename(temp,file);
}
export class ProjectStore {
  constructor(root, pluginRoot, runtime={}) { this.root=path.resolve(root);this.pluginRoot=pluginRoot;this.runtime=runtime;this.active=new Set();this.mutating=new Set(); }
  async exclusive(id,fn) {if(this.mutating.has(id))throw new Error('This project is being updated. Reload and try again.');this.mutating.add(id);try{return await fn();}finally{this.mutating.delete(id);}}
  directory(id) { idSchema.parse(id);return path.join(this.root,id); }
  async read(id) {
    const dir=this.directory(id);
    if ((await fs.lstat(dir)).isSymbolicLink()) throw new Error('Linked project directories are not supported.');
    await this.contained(path.join(dir,'project.json'),dir);
    const project=JSON.parse(await fs.readFile(path.join(dir,'project.json'),'utf8'));
    if(project.id!==id) throw new Error('Project identity mismatch.');
    return project;
  }
  async list() {
    await fs.mkdir(this.root,{recursive:true,mode:0o700});
    const entries=await fs.readdir(this.root,{withFileTypes:true});
    const projects=[];
    for(const entry of entries) if(entry.isDirectory()&&idSchema.safeParse(entry.name).success) {
      try { const p=await this.read(entry.name);projects.push({id:p.id,title:p.brief.title,version:p.version,updatedAt:p.updatedAt}); } catch { /* corrupt projects remain on disk */ }
    }
    return projects.sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt)).slice(0,40);
  }
  async save(args) {return this.exclusive(args.projectId||randomUUID(),()=>this.saveInternal(args));}
  async saveInternal({projectId,expectedVersion,brief}) {
    brief=briefSchema.parse(brief);
    let p;
    if(projectId) {
      p=await this.read(projectId);
      if(this.active.has(projectId)) throw new Error('Build in progress. Wait before editing the brief.');
      if(expectedVersion!==p.version) throw new Error('This brief changed elsewhere. Reload it before saving.');
      await saveJson(path.join(this.directory(projectId),`brief-v${p.version}.json`),p.brief);
      p.version++;p.brief=brief;p.status=p.latestRun?'needs_rebuild':'draft';
    } else {
      if(expectedVersion!==undefined&&expectedVersion!==0) throw new Error('A new project starts at version zero.');
      p={id:randomUUID(),version:1,brief,photos:[],status:'draft',latestRun:null,createdAt:new Date().toISOString()};
      await fs.mkdir(this.directory(p.id),{recursive:true,mode:0o700});
    }
    p.updatedAt=new Date().toISOString();await saveJson(path.join(this.directory(p.id),'project.json'),p);
    return clone(p);
  }
  async addPhoto(args) {return this.exclusive(args.projectId,()=>this.addPhotoInternal(args));}
  async addPhotoInternal({projectId,expectedVersion,name,mimeType,base64}) {
    const p=await this.read(projectId);
    if(p.version!==expectedVersion||this.active.has(projectId)) throw new Error('Project changed or is building. Reload before adding a photo.');
    if(p.photos.length>=4) throw new Error('This pilot accepts up to four reference photos per project.');
    if(typeof base64!=='string'||base64.length>11200000) throw new Error('Invalid or oversized photo encoding.');
    const bytes=Buffer.from(base64,'base64');
    if(bytes.toString('base64')!==base64) throw new Error('Invalid photo encoding.');
    if(bytes.length===0||bytes.length>8*1024*1024) throw new Error('Choose an image up to 8 MiB.');
    const valid = mimeType==='image/png'&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])) ||
      mimeType==='image/jpeg'&&bytes[0]===255&&bytes[1]===216&&bytes[2]===255 ||
      mimeType==='image/webp'&&bytes.toString('ascii',0,4)==='RIFF'&&bytes.toString('ascii',8,12)==='WEBP';
    if(!valid) throw new Error('Use an actual JPEG, PNG or WebP image. HEIC must be converted first.');
    const photo={id:randomUUID(),name:path.basename(name).slice(0,120),mimeType,bytes:bytes.length,sha256:hash(bytes)};
    const dir=path.join(this.directory(projectId),'photos');await fs.mkdir(dir,{recursive:true,mode:0o700});
    await fs.writeFile(path.join(dir,photo.id),bytes,{flag:'wx',mode:0o600});
    p.photos.push(photo);p.version++;p.brief.confirmed=false;p.status=p.latestRun?'needs_rebuild':'draft';p.updatedAt=new Date().toISOString();
    await saveJson(path.join(this.directory(projectId),'project.json'),p);return clone(p);
  }
  async photo(projectId,photoId) {
    idSchema.parse(photoId);const p=await this.read(projectId);const meta=p.photos.find(x=>x.id===photoId);
    if(!meta) throw new Error('Photo does not belong to this project.');
    const file=path.join(this.directory(projectId),'photos',photoId);
    await this.contained(file,this.directory(projectId));const bytes=await fs.readFile(file);
    if(hash(bytes)!==meta.sha256) throw new Error('Photo checksum mismatch.');
    return {meta,bytes};
  }
  async contained(file,root) {
    const resolved=await fs.realpath(file);const base=await fs.realpath(root);
    if(!resolved.startsWith(base+path.sep)) throw new Error('Artifact escaped its project.');
    if((await fs.lstat(file)).isSymbolicLink()) throw new Error('Linked artifacts are not supported.');
  }
  async runPython(args,cwd,log,timeout=660000) {
    const fd=log?await fs.open(log,'w',0o600):null;
    try {
      return await new Promise((resolve,reject)=>{
        const child=spawn(this.runtime.python||'python3',[path.join(this.pluginRoot,'scripts/capture_to_print.py'),...args],{cwd,env:process.env,stdio:['ignore',fd?fd.fd:'pipe',fd?fd.fd:'pipe'],detached:true});
        let expired=false,text='';
        const stop=()=>{try{process.kill(-child.pid,'SIGKILL');}catch{}};
        const collect=chunk=>{text+=chunk.toString();if(Buffer.byteLength(text)>1024*1024){expired=true;stop();}};
        if(!fd){child.stdout.on('data',collect);child.stderr.on('data',collect);}
        const timer=setTimeout(()=>{expired=true;stop();},timeout);
        child.once('error',err=>{clearTimeout(timer);reject(err);});
        child.once('close',(code,signal)=>{clearTimeout(timer);code===0&&!expired?resolve(text):reject(new Error(expired?'CAD stage exceeded its time/output limit.':`CAD process failed (${code??signal}); ${fd?'inspect its retained log.':text.slice(-3000)}`));});
      });
    } finally {if(fd)await fd.close();}
  }
  async build(args) {return this.exclusive(args.projectId,()=>this.buildInternal(args));}
  async buildInternal({projectId,expectedVersion,scad,contract}) {
    const p=await this.read(projectId);
    if(p.version!==expectedVersion) throw new Error('Brief version changed. Reconfirm before building.');
    if(!p.brief.confirmed||!p.brief.measurements.length) throw new Error('Confirm a brief with measured dimensions before building.');
    if(p.brief.measurements.some(m=>m.source!=='measured')) throw new Error('Estimated dimensions need confirmation as measurements before this pilot can build.');
    if(this.active.has(projectId)) throw new Error('A build is already running.');
    if(typeof scad!=='string'||Buffer.byteLength(scad)>1024*1024) throw new Error('SCAD must fit the 1 MiB source limit.');
    if(!contract||typeof contract!=='object'||Array.isArray(contract)) throw new Error('Provide the supported measurement contract.');
    this.active.add(projectId);
    const candidate=path.join(this.directory(projectId),'candidates',randomUUID());
    try {
      await fs.mkdir(candidate,{recursive:true});
      await fs.writeFile(path.join(candidate,'design.scad'),scad);
      await saveJson(path.join(candidate,'contract.json'),{...contract,source_sha256:hash(Buffer.from(scad))});
      p.status='building';p.lastError=null;await saveJson(path.join(this.directory(projectId),'project.json'),p);
      const args=['build','--source',path.join(candidate,'design.scad'),'--contract',path.join(candidate,'contract.json'),'--output-root',path.join(this.directory(projectId),'runs')];
      if(this.runtime.openscad) args.push('--openscad',this.runtime.openscad);
      if(this.runtime.fcMatch) args.push('--fc-match',this.runtime.fcMatch);
      const log=path.join(candidate,'runner.log');await this.runPython(args,candidate,log);
      const result=JSON.parse(await fs.readFile(log,'utf8'));
      await this.attachRun(p,result.run);
      await fs.rm(candidate,{recursive:true});
      return this.read(projectId);
    } catch(error) {
      p.status='build_failed';p.lastError=error.message;p.updatedAt=new Date().toISOString();
      await saveJson(path.join(this.directory(projectId),'project.json'),p);throw error;
    } finally {this.active.delete(projectId);}
  }
  async attachRun(p,run) {
    const compact=await fs.access(path.join(run,'revision.json')).then(()=>true,()=>false);
    await this.contained(path.join(run,compact?'revision.json':'manifest.json'),this.directory(p.id));
    await this.runPython(['verify',run],this.directory(p.id),null,30000);
    if(compact){
      const record=JSON.parse(await fs.readFile(path.join(run,'revision.json'),'utf8'));
      const bytes=await fs.readFile(path.join(run,'revision.json'));
      p.latestRun={format:2,revision:record.revision,briefVersion:p.version,relativeDirectory:path.relative(this.directory(p.id),run),
        checks:record.checks,artifacts:[...record.files,{path:'revision.json',bytes:bytes.length,sha256:hash(bytes)}],part:'part.stl'};
    }else{
      const manifest=JSON.parse(await fs.readFile(path.join(run,'manifest.json'),'utf8'));
      const checks=JSON.parse(await fs.readFile(path.join(run,'checks.json'),'utf8'));
      const bundle=await fs.readFile(path.join(run,'draft-bundle.zip'));
      p.latestRun={revision:manifest.revision,briefVersion:p.version,relativeDirectory:path.relative(this.directory(p.id),run),
        checks,artifacts:[...manifest.files,{path:'draft-bundle.zip',bytes:bundle.length,sha256:hash(bundle)}],part:manifest.parts[0].path};
    }
    p.status='awaiting_user_review';p.updatedAt=new Date().toISOString();
    await saveJson(path.join(this.directory(p.id),'project.json'),p);
  }
  async exportBundle({projectId,revision}) {
    return this.exclusive(projectId,async()=>{
      const p=await this.read(projectId),run=p.latestRun;
      if(!run||run.revision!==revision)throw new Error('That build revision is no longer the selected result.');
      if(this.active.has(projectId))throw new Error('Wait for the current build before exporting.');
      if(run.format!==2)return {project:p,artifact:await this.artifact(projectId,revision,'bundle')};
      if(!run.fullBundle){
        const directory=path.join(this.directory(projectId),run.relativeDirectory);
        await this.contained(path.join(directory,'revision.json'),this.directory(projectId));
        const destination=path.join(this.directory(projectId),'exports',revision+'-'+randomUUID()+'.zip');
        const result=JSON.parse(await this.runPython(['export',directory,'--output',destination],this.directory(projectId)));
        if(result.revision!==revision||path.resolve(result.bundle)!==destination)throw new Error('Export identity mismatch.');
        run.fullBundle={path:path.relative(this.directory(projectId),destination),bytes:result.bytes,sha256:result.sha256};
        await saveJson(path.join(this.directory(projectId),'project.json'),p);
      }
      return {project:p,bundle:{...run.fullBundle,revision}};
    });
  }
  async artifact(projectId,revision,kind) {
    const p=await this.read(projectId);const run=p.latestRun;
    if(!run||run.revision!==revision) throw new Error('That build revision is no longer the selected result.');
    const allowed=run.format===2
      ?{scad:'design.scad',stl:'part.stl',contract:'design-contract.json',preview:'preview.png',checks:'revision.json',revision:'revision.json',bundle:run.fullBundle?.path}
      :{scad:'design.scad',stl:run.part,contract:'design-contract.json',bundle:'draft-bundle.zip',checks:'checks.json',face:'previews/face.png',back:'previews/back.png',edge:'previews/edge.png',oblique:'previews/oblique.png'};
    if(!Object.hasOwn(allowed,kind)) throw new Error('Unknown artifact.');
    const external=run.format===2&&kind==='bundle';
    if(external&&!run.fullBundle)throw new Error('No full bundle yet. Request Create full ZIP first.');
    const name=allowed[kind];const item=external?run.fullBundle:run.artifacts.find(x=>x.path===name);
    if(!item) throw new Error('Artifact is not in the selected manifest.');
    if(item.bytes>16*1024*1024) throw new Error('This file exceeds the panel download limit. Ask Codex for the bundle path.');
    const file=path.join(this.directory(projectId),external?'':run.relativeDirectory,name);await this.contained(file,this.directory(projectId));
    const bytes=await fs.readFile(file);if(bytes.length!==item.bytes||hash(bytes)!==item.sha256) throw new Error('Artifact checksum mismatch.');
    const mimeType=name.endsWith('.png')?'image/png':name.endsWith('.zip')?'application/zip':name.endsWith('.json')?'application/json':name.endsWith('.stl')?'model/stl':'text/plain';
    return {name:path.basename(name),mimeType,base64:bytes.toString('base64'),sha256:item.sha256,revision};
  }
}
