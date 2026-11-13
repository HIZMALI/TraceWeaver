import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { mkdir, writeFile } from 'node:fs/promises';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,'.verification/overnight/browsers');
const { chromium } = await import('@playwright/test');
const server=spawn(resolve(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),
  [resolve(root,'web/e2e/backend.py'),'--port','8765'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
const base='http://127.0.0.1:8765';
let browser;
try{
  let ready=false;
  for(let n=0;n<100;n++){try{if((await fetch(base+'/health')).ok){ready=true;break;}}catch{/* Await owned server readiness, never application retries. */}await new Promise(r=>setTimeout(r,50));}
  if(!ready)throw new Error('Owned native server unavailable');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/?incident=INC-001');
  await page.getByTestId('causal-status').waitFor({state:'visible',timeout:15000});
  if(await page.getByTestId('causal-status').innerText()!=='NOT_ESTABLISHED')throw new Error('Causal contract failed');
  await page.locator('.react-flow__edge').first().waitFor({timeout:15000});
  const edgeCount=await page.locator('.react-flow__edge').count();
  if(edgeCount<1)throw new Error('No real graph edges rendered');
  await mkdir(resolve(root,'.verification/overnight'),{recursive:true});
  await page.screenshot({path:resolve(root,'.verification/overnight/G1-desktop.png'),fullPage:true});
  await page.getByRole('navigation',{name:'Returned incidents'}).getByRole('button').filter({hasText:'CASE-INC'}).click();
  await page.getByRole('button',{name:/Inspect candidate CASE-DEP-BEFORE/}).waitFor();
  await page.getByRole('tab',{name:/Observations/}).click();
  await page.getByRole('button',{name:/Inspect CONFLICTING_OBSERVATIONS/}).waitFor();
  await page.screenshot({path:resolve(root,'.verification/overnight/G1-case.png'),fullPage:true});
  if(errors.length)throw new Error('Browser page errors: '+errors.join(';'));
  const result={browser:browser.version(),inc001_edges:edgeCount,case_inc_visible:true,page_errors:errors.length,real_backend:true};
  await writeFile(resolve(root,'.verification/overnight/G1-browser.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
}finally{
  if(browser)await browser.close();
  if(server.exitCode===null&&server.pid){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM');}
}
