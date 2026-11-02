// Browser QA host only. This is not the Codex/ChatGPT host implementation.
import {AppBridge,PostMessageTransport} from '@modelcontextprotocol/ext-apps/app-bridge';
const iframe=document.querySelector('iframe');
const rpc=async(name,args)=>{const r=await fetch('/call',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,arguments:args})});if(!r.ok)throw new Error(await r.text());return r.json();};
const bridge=new AppBridge(null,{name:'Local QA harness',version:'0.1.0'},{serverTools:{},message:{text:{}},updateModelContext:{text:{}},downloadFile:{}},{hostContext:{theme:'light',displayMode:'inline'}});
bridge.oncalltool=params=>rpc(params.name,params.arguments||{});
bridge.onmessage=async params=>{document.querySelector('#events').textContent='MESSAGE CAPTURED (no model call): '+JSON.stringify(params);return {};};
bridge.onupdatemodelcontext=async()=>({});
bridge.ondownloadfile=async params=>{document.querySelector('#events').textContent='DOWNLOAD REQUEST CAPTURED: '+params.contents[0].resource.uri;return {};};
bridge.onsizechange=({height})=>{iframe.style.height=Math.max(700,height)+'px';};
bridge.oninitialized=async()=>{await bridge.sendToolInput({arguments:{}});const params=new URLSearchParams(location.search);await bridge.sendToolResult(await rpc('open_capture_to_print',params.get('project')?{projectId:params.get('project')}:{}));};
await bridge.connect(new PostMessageTransport(iframe.contentWindow,iframe.contentWindow));
iframe.src='/workbench';
