// Finite local descriptive measurements. Three newly allocated native synthetic stores.
import {spawn,spawnSync} from 'node:child_process';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFile} from 'node:fs/promises';
import os from 'node:os';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,'.verification/overnight/browsers');
const {chromium,expect}=await import('@playwright/test');
const browser=await chromium.launch(),results=[];
function summarize(values){const v=[...values].sort((a,b)=>a-b);return {n:v.length,median_ms:+((v[Math.floor((v.length-1)/2)]+v[Math.ceil((v.length-1)/2)])/2).toFixed(2),p95_nearest_rank_ms:+v[Math.ceil(v.length*.95)-1].toFixed(2)};}
try{
 for(const [profile,n] of [['perf-small',4],['perf-medium',30],['perf-capped',110]]){
  const server=spawn(resolve(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),['web/e2e/backend.py','--port','8774','--profile',profile],{cwd:root,windowsHide:true,stdio:'ignore'});
  const base='http://127.0.0.1:8774';let context;
  try{
   let health;for(let k=0;k<100;k++){try{const r=await fetch(base+'/health');if(r.ok){health=await r.json();break;}}catch{/* Owned native server readiness. */}await new Promise(r=>setTimeout(r,50));}if(!health)throw new Error('Scale server unavailable');
   context=await browser.newContext({viewport:{width:1440,height:900}});const page=await context.newPage(),samples=[];
   const errors=[];page.on('pageerror',e=>errors.push(e.message));const rows=Math.min(n,100),nodes=Math.min(2+3*rows,300),edges=1+4*rows-Math.max(2+3*rows-300,0);
   for(let repeat=0;repeat<7;repeat++){
    const responsePromise=page.waitForResponse(r=>r.url().includes('/dashboard?'));
    const start=performance.now();await page.goto(base+'/?incident=PERF-INC');const response=await responsePromise;await response.finished();
    await expect(page.locator('.react-flow__node')).toHaveCount(nodes);await expect(page.locator('.react-flow__edge')).toHaveCount(edges);
    await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const loaded=performance.now()-start;
    const selection=performance.now();await page.getByRole('button',{name:'Inspect candidate PERF-D000 on PERF-SVC',exact:true}).click();await expect(page.getByRole('region',{name:'Selected candidate'})).toBeVisible();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
    const timing=response.request().timing();samples.push({load_ms:+loaded.toFixed(2),selection_ms:+(performance.now()-selection).toFixed(2),api_request_ms:+(timing.responseEnd-timing.requestStart).toFixed(2)});
   }
   if(errors.length)throw new Error('Scale page errors');
   let workingSet=null;if(process.platform==='win32'){const r=spawnSync('powershell',['-NoProfile','-Command',`$ownedIds=@([int]${server.pid}); for($depth=0;$depth -lt 3;$depth++){ $children=@(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -in $ownedIds } | Select-Object -ExpandProperty ProcessId); $ownedIds=@($ownedIds+$children | Sort-Object -Unique) }; ($ownedIds | ForEach-Object { (Get-Process -Id $_ -ErrorAction SilentlyContinue).WorkingSet64 } | Measure-Object -Sum).Sum`],{windowsHide:true,encoding:'utf8',timeout:20000});workingSet=Number(r.stdout.trim())||null;}
   results.push({profile,stored_nodes:health.node_count,stored_edges:health.relationship_count,returned_candidates:rows,returned_evidence:rows,rendered_nodes:nodes,rendered_edges:edges,first_context_load_ms:samples[0].load_ms,warm_load:summarize(samples.slice(1).map(s=>s.load_ms)),selection:summarize(samples.map(s=>s.selection_ms)),api_request:summarize(samples.map(s=>s.api_request_ms)),owned_process_tree_working_set_bytes:workingSet,samples});
  }finally{if(context)await context.close();if(server.exitCode===null&&server.pid){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM');}}
 }
 const report={browser:browser.version(),node:process.version,os:os.platform()+' '+os.release(),cpu:os.cpus()[0].model,total_memory_bytes:os.totalmem(),method:'One cold browser context + six same-context navigations per scale; no OS cache flush. Seven proof-selection samples. Node wall time includes Playwright polling/scrolling and two animation frames. API request time is browser network timing, not pure Cypher cost. Nearest-rank p95 is descriptive at small n.',results};
 await writeFile(resolve(root,'.verification/overnight/performance.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
