import {App} from '@modelcontextprotocol/ext-apps';
const app=new App({name:'capture-to-print',version:'0.4.0'},{},{strict:true});
const $=id=>document.getElementById(id);
let project=null,ready=false,busy=false,dirty=false,currentView='face';
const imageCache=new Map();
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error);}
function setBusy(value){busy=value;document.querySelectorAll('button,input,textarea,select').forEach(b=>b.disabled=value||!ready);}
async function action(fn){if(busy)return;setBusy(true);try{await fn();}catch(error){notice(error.message||String(error),true);}finally{setBusy(false);}}
async function call(name,args){const result=await app.callServerTool({name,arguments:args});if(result.isError)throw new Error(result.content?.find(x=>x.type==='text')?.text||'The operation failed.');return result;}
function measurementRow(value={name:'',value:'',unit:'mm',source:'measured'}){
  const row=document.createElement('div');row.className='measure-row';
  row.innerHTML='<input data-field="name" aria-label="Measurement name" placeholder="Door thickness"><input data-field="value" type="number" min="0.001" step="any" aria-label="Measurement value"><select data-field="unit" aria-label="Measurement unit"><option>mm</option><option>cm</option><option>in</option></select><select data-field="source" aria-label="Measurement confidence"><option value="measured">Measured</option><option value="estimated">Estimate</option></select><button class="remove" aria-label="Remove measurement">×</button>';
  for(const [key,val]of Object.entries(value))row.querySelector(`[data-field=${key}]`).value=val;
  row.querySelector('button').onclick=()=>{row.remove();markDirty();};$('measurements').append(row);
}
function brief(){
  const measurements=[...$('measurements').children].map(row=>Object.fromEntries([...row.querySelectorAll('[data-field]')].map(x=>[x.dataset.field,x.dataset.field==='value'?Number(x.value):x.value])));
  if(!$('title').value.trim()||!$('description').value.trim())throw new Error('Add a project name and description first.');
  for(const m of measurements)if(!m.name.trim()||!Number.isFinite(m.value)||m.value<=0)throw new Error('Each measurement needs a name and a positive value. Remove unused rows.');
  return {title:$('title').value,description:$('description').value,measurements,printer:{model:$('printer').value,nozzle:$('nozzle').value,material:$('material').value,plate:$('plate').value},confirmed:$('confirmed').checked};
}
function markDirty(){dirty=true;$('saved-state').textContent='Unsaved changes';$('generate').textContent=$('confirmed').checked?'Generate with Codex':'Discuss with Codex';}
async function setProject(value){
  project=value;dirty=false;imageCache.clear();
  $('projects').value=value?.id||'';
  const b=value?.brief||{title:'',description:'',measurements:[],printer:{model:'unspecified',nozzle:'',material:'',plate:''},confirmed:false};
  for(const key of ['title','description'])$(key).value=b[key];
  for(const key of ['nozzle','material','plate'])$(key).value=b.printer[key];
  $('printer').value=b.printer.model;$('confirmed').checked=b.confirmed;
  $('measurements').replaceChildren();b.measurements.forEach(measurementRow);
  $('generate').textContent=b.confirmed?'Generate with Codex':'Discuss with Codex';
  $('saved-state').textContent=value?`Saved · brief version ${value.version}`:'No project saved yet.';
  $('photos').value='';$('photo-list').replaceChildren();
  for(const photo of value?.photos||[]){
    const figure=document.createElement('figure'),img=document.createElement('img'),caption=document.createElement('figcaption');
    img.alt=photo.name;caption.textContent=photo.name;figure.append(img,caption);$('photo-list').append(figure);
    try{const r=await call('view_reference_photo',{projectId:value.id,photoId:photo.id});const c=r.content.find(x=>x.type==='image');if(c)img.src=`data:${c.mimeType};base64,${c.data}`;}catch{caption.textContent+=' (preview unavailable)';}
  }
  await renderReview();
}
async function save(){
  const data=brief();const r=await call('save_design_brief',{...(project?{projectId:project.id,expectedVersion:project.version}:{}),brief:data});
  await setProject(r.structuredContent.project);await listProjects();notice('Brief saved.');return project;
}
async function listProjects(items){
  if(!items){const r=await call('list_design_projects',{});items=r.structuredContent.projects;}
  $('projects').replaceChildren(new Option('New project',''));
  for(const p of items)$('projects').add(new Option(p.title,p.id));
  $('projects').value=project?.id||'';
}
async function artifact(kind){
  if(!project?.latestRun)throw new Error('No build is available.');
  const r=await call('get_design_artifact',{projectId:project.id,revision:project.latestRun.revision,kind});return r.structuredContent.artifact;
}
async function showView(view){
  const compact=project.latestRun.format===2;
  const cacheKey=project.latestRun.revision+':'+(compact?'preview':view);
  if(!imageCache.has(cacheKey))imageCache.set(cacheKey,await artifact(compact?'preview':view));
  const a=imageCache.get(cacheKey);let src=`data:${a.mimeType};base64,${a.base64}`;
  if(compact){
    const img=new Image();img.src=src;await img.decode();
    const canvas=document.createElement('canvas');canvas.width=img.naturalWidth/2;canvas.height=img.naturalHeight/2;
    const i=['face','back','edge','oblique'].indexOf(view);
    canvas.getContext('2d').drawImage(img,(i%2)*canvas.width,Math.floor(i/2)*canvas.height,canvas.width,canvas.height,0,0,canvas.width,canvas.height);
    src=canvas.toDataURL('image/png');
  }
  $('preview').src=src;$('preview').alt=`${view} view of revision ${a.revision}`;currentView=view;
  $('views').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
}
async function renderReview(){
  const run=project?.latestRun;$('review-empty').classList.toggle('hidden',!!run);$('review-content').classList.toggle('hidden',!run);
  $('review-status').textContent=project?.status==='needs_rebuild'?'Previous build':run?'Awaiting review':'No build yet';
  if(project?.status==='build_failed')notice(project.lastError||'Build failed. Ask Codex to inspect the retained logs.',true);
  if(!run)return;
  $('revision').textContent=`Revision ${run.revision}${run.briefVersion!==project.version?' · brief has changed; rebuild before accepting':''}`;
  const required=run.checks.checks.filter(c=>c.required);$('check-summary').textContent=`${required.filter(c=>c.status==='pass').length} of ${required.length} required checks passed. Dimensions below are millimeters.`;
  $('check-rows').replaceChildren();
  for(const c of required.filter(x=>'expected_mm'in x)){
    const tr=document.createElement('tr');for(const text of [c.id.replaceAll('_',' '),c.measured_mm==null?'—':Number(c.measured_mm).toFixed(2),`${c.expected_mm} ± ${c.tolerance_mm}`,c.status]){const td=document.createElement('td');td.textContent=text;tr.append(td);}tr.lastChild.className=c.status==='pass'?'pass':'fail';$('check-rows').append(tr);
  }
  $('unassessed').textContent=run.checks.checks.filter(c=>c.status==='unassessed').map(c=>c.id.replaceAll('_',' ')).join(', ')+'.';
  $('export-bundle').textContent=run.format===2&&!run.fullBundle?'Create full ZIP':'Download full ZIP';
  document.querySelector('[data-download=preview]').classList.toggle('hidden',run.format!==2);
  await showView(currentView);
}
async function message(text){const result=await app.sendMessage({role:'user',content:[{type:'text',text}]});if(result?.isError)throw new Error('The host did not send the message. Copy your brief into the conversation instead.');}
$('save').onclick=()=>action(save);
$('generate').onclick=()=>action(async()=>{
  if(dirty||!project)await save();
  const context={projectId:project.id,briefVersion:project.version,brief:project.brief,referencePhotos:project.photos.map(p=>({id:p.id,name:p.name}))};
  try{await app.updateModelContext({content:[{type:'text',text:JSON.stringify(context)}]});}catch{/* message below contains the ID and version for fetching the exact saved brief */}
  await message(`Use capture-to-print for project ${project.id}, brief version ${project.version}. Read get_design_project and inspect its reference photos. ${project.brief.confirmed?'Develop the editable OpenSCAD and build it only when all fit-critical measurements and checks are supported.':'Discuss the design and ask for missing measurements before generating CAD.'} Follow the packaged CAD rules, preserve revisions, use my existing host allowance only, and show the result with open_capture_to_print. No automatic printing.`);
  notice('Sent to the conversation. Continue there; reload this panel when the build is ready.');
});
$('add-measurement').onclick=()=>{measurementRow();markDirty();};
document.querySelector('section[aria-label="Design brief"]').addEventListener('input',markDirty);
$('projects').onchange=()=>action(async()=>{if(dirty){$('projects').value=project?.id||'';throw new Error('Save this brief before changing projects.');}const id=$('projects').value;await setProject(id?(await call('get_design_project',{projectId:id})).structuredContent.project:null);notice('');});
$('new-project').onclick=()=>action(async()=>{if(dirty)throw new Error('Save this brief before starting another project.');await setProject(null);$('projects').value='';notice('');});
$('refresh').onclick=()=>action(async()=>{if(dirty)throw new Error('Save unsaved changes before reloading.');if(project)await setProject((await call('get_design_project',{projectId:project.id})).structuredContent.project);await listProjects();notice('Loaded the latest saved state.');});
$('photos').onchange=()=>action(async()=>{
  const files=[...$('photos').files];if(!files.length)return;
  if((project?.photos.length||0)+files.length>4)throw new Error('Choose at most four reference photos per project.');
  for(const file of files)if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>8*1024*1024)throw new Error('Use JPG, PNG or WebP files up to 8 MB. Convert HEIC first.');
  if(dirty||!project)await save();
  for(const file of files){
    const base64=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read this photo.'));reader.readAsDataURL(file);});
    const r=await call('attach_reference_photo',{projectId:project.id,expectedVersion:project.version,name:file.name,mimeType:file.type,base64});project=r.structuredContent.project;
  }
  await setProject(project);notice('Photos attached. Recheck the brief after adding new reference information.');
});
$('views').onclick=e=>{const button=e.target.closest('[data-view]');if(button)action(()=>showView(button.dataset.view));};
document.querySelectorAll('[data-download]').forEach(button=>button.onclick=()=>action(async()=>{
  const a=await artifact(button.dataset.download);const result=await app.downloadFile({contents:[{type:'resource',resource:{uri:`file:///${encodeURIComponent(a.name)}`,mimeType:a.mimeType,blob:a.base64}}]});
  if(result?.isError)throw new Error('Download was cancelled or not supported. Ask Codex for this artifact in the conversation.');
  notice('Download requested. Check the saved file before deleting any project data.');
}));
$('export-bundle').onclick=()=>action(async()=>{
  const r=await call('export_design_bundle',{projectId:project.id,revision:project.latestRun.revision});
  project=r.structuredContent.project;
  const a=await artifact('bundle');const result=await app.downloadFile({contents:[{type:'resource',resource:{uri:`file:///${encodeURIComponent(a.name)}`,mimeType:a.mimeType,blob:a.base64}}]});
  if(result?.isError)throw new Error('Download was cancelled or unsupported. The requested bundle is saved; ask Codex for its path.');
  $('export-bundle').textContent='Download full ZIP';notice('Full ZIP created on request. Check the downloaded file.');
});
$('send-feedback').onclick=()=>action(async()=>{const feedback=$('feedback').value.trim();if(!feedback)throw new Error('Enter your review notes first.');if(project.latestRun.briefVersion!==project.version||dirty)throw new Error('The brief changed. Rebuild before accepting this revision.');await message(`My review of capture-to-print project ${project.id}, revision ${project.latestRun.revision}: ${feedback}\nRecord this feedback against that exact revision. This is not authorization to print.`);notice('Review sent to the conversation.');});
app.ontoolresult=async result=>{if(busy||dirty)return;const data=result.structuredContent;setBusy(true);try{if(data?.projects)await listProjects(data.projects);if(data&&'project'in data)await setProject(data.project);}catch(error){notice(error.message,true);}finally{setBusy(false);}};
setBusy(false);
try{await app.connect();ready=true;$('connection').textContent='Private · connected';setBusy(false);}
catch(error){$('connection').textContent='Not connected';notice('Open this panel through the capture-to-print plugin. The host connection is unavailable.',true);}
