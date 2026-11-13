// Explicit finite live verification. Never part of default tests; never pulls a model.
import {spawn,spawnSync} from 'node:child_process';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFile} from 'node:fs/promises';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,'.verification/overnight/browsers');
const {chromium}=await import('@playwright/test');
const server=spawn(resolve(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),['web/e2e/backend.py','--port','8771'],{cwd:root,windowsHide:true,stdio:'ignore'});
let browser;const result={actual_ui:true,provider:'127.0.0.1:11434',model:'qwen3:8b',status:'NOT_RUN'};
try{
  let ready=false;for(let n=0;n<100;n++){try{if((await fetch('http://127.0.0.1:8771/health')).ok){ready=true;break;}}catch{/* Owned server readiness. */}await new Promise(r=>setTimeout(r,50));}if(!ready)throw new Error('Native server unavailable');
  browser=await chromium.launch();const page=await browser.newPage({viewport:{width:1440,height:900}});
  await page.goto('http://127.0.0.1:8771/?incident=INC-001');await page.getByTestId('causal-status').waitFor();
  await page.getByRole('button',{name:'Compare with local AI selection',exact:true}).click();
  await page.getByRole('combobox',{name:'Installed local model'}).waitFor();
  if(await page.getByRole('combobox',{name:'Installed local model'}).locator('option').filter({hasText:/^qwen3:8b$/}).count()!==1){result.status='BLOCKED_NOT_INSTALLED';}
  else{
    await page.getByRole('combobox',{name:'Installed local model'}).selectOption('qwen3:8b');await page.getByRole('checkbox').check();
    const response=page.waitForResponse(r=>r.url().endsWith('/console/selection')&&r.request().method()==='POST',{timeout:60000});
    const start=performance.now();await page.getByRole('button',{name:'Run confirmed local selection',exact:true}).click();
    const http=await response;if(!http.ok())throw new Error('Selection HTTP '+http.status());const body=await http.json(),e=body.explanation;
    Object.assign(result,{elapsed_ms:Math.round(performance.now()-start),status:e.mode_executed==='OLLAMA'?'PASS':'REJECTED',mode_executed:e.mode_executed,ai_generated_selection:e.ai_generated_selection,explanation_status:e.explanation_status,validated_claim_count:e.validated_claim_count,validated_citation_count:e.validated_citation_count,accepted_claim_ids:e.claims.map(c=>c.claim_id),rejection_codes:e.rejection_codes,source_fingerprint:body.source_fingerprint});
    if(e.mode_executed==='OLLAMA'){
      await page.getByRole('button',{name:/Inspect local claim/}).first().waitFor();await page.getByRole('button',{name:/Inspect local claim/}).first().click();
      await page.getByRole('region',{name:'Selected claim'}).waitFor();await page.evaluate(()=>{document.activeElement?.blur();scrollTo(0,0);});
      await page.screenshot({path:resolve(root,'docs/screenshots/07-live-local-selection.png'),fullPage:true});
    }
  }
}finally{
  if(browser)await browser.close();if(server.exitCode===null&&server.pid){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM');}
  await writeFile(resolve(root,'.verification/overnight/live-local.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}
