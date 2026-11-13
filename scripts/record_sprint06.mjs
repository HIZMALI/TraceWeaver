// Genuine bounded browser recording; no mocked responses, synthetic narration or uploads.
import {spawn,spawnSync} from "node:child_process";
import {mkdir,mkdtemp,access,copyFile,writeFile} from "node:fs/promises";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const out=resolve(root,"docs/video/sprint06"), scratch=resolve(root,".verification/sprint06");
await mkdir(out,{recursive:true});await mkdir(scratch,{recursive:true});
const target=resolve(out,"native-walkthrough.webm");
let exists=false;try{await access(target);exists=true;}catch{}
if(exists)throw new Error("Recording exists; preserve it and select a new named recording manually.");
const videoDir=await mkdtemp(resolve(scratch,"recording-"));
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,".verification/overnight/browsers");
const {chromium,expect}=await import("../web/node_modules/@playwright/test/index.mjs");
const server=spawn(resolve(root,".venv/Scripts/python.exe"),["web/e2e/backend.py","--port","8776"],
 {cwd:root,env:{...process.env,PYTHONPATH:resolve(root,"src")},windowsHide:true,stdio:"ignore"});
let browser,context,video;const events=[],start=performance.now();
const mark=text=>events.push({seconds:Number(((performance.now()-start)/1000).toFixed(3)),caption:text});
try{
 let ready=false;for(let i=0;i<100;i++){try{if((await fetch("http://127.0.0.1:8776/health")).ok){ready=true;break;}}catch{}
  await new Promise(r=>setTimeout(r,50));}if(!ready)throw new Error("Owned server not ready");
 browser=await chromium.launch({slowMo:180});context=await browser.newContext({viewport:{width:1440,height:900},
   recordVideo:{dir:videoDir,size:{width:1440,height:900}}});
 const page=await context.newPage();video=page.video();
 await page.goto("http://127.0.0.1:8776/?incident=INC-001");await expect(page.locator(".react-flow__edge")).toHaveCount(14);
 mark("Actual native Relate judge store. Synthetic incident; causation NOT_ESTABLISHED.");
 await page.getByRole("button",{name:/Focus proof DEP-001/}).click();
 await page.getByRole("button",{name:"Focus selected paths"}).click();
 mark("DEP-001 candidate proof follows stored Payment to Auth and reverse TARGETS.");
 await page.getByRole("button",{name:"Explore investigation steps"}).click();
 await page.getByRole("button",{name:"Rehearse graph investigation",exact:true}).click();
 await expect(page.getByTestId("agent-report")).toBeVisible();
 mark("Real deterministic native tool rehearsal. Offline, not AI-generated.");
 await page.getByRole("button",{name:/Inspect tool step 2 trace_deployment/}).click();
 await page.getByRole("region",{name:"Selected native tool step"}).scrollIntoViewIfNeeded();
 mark("Actual tool step focuses directed edge proof in the inspector.");
 await page.getByText(/Admitted claim citations/).click();
 await page.locator(".agent-claim").filter({hasText:"DEPLOYMENT_CONNECTED"}).first().click();
 await page.getByRole("region",{name:"Selected claim"}).scrollIntoViewIfNeeded();
 mark("Admitted factual statements use existing typed citations and server templates.");
 await page.goto("http://127.0.0.1:8776/?incident=CASE-INC");
 await page.getByRole("tab",{name:/Observations/}).click();
 await page.getByRole("button",{name:/Inspect CONFLICTING_OBSERVATIONS/}).click();
 await page.getByRole("region",{name:"Selected comparison"}).scrollIntoViewIfNeeded();
 mark("Structured conflict is separate from DEGRADED/UNDETERMINED comparisons. Source truth unverified.");
 await page.getByRole("button",{name:"Explore investigation steps"}).click();
 await page.getByRole("button",{name:"Agent investigation (local)",exact:true}).click();
 const models=page.getByLabel("Agent installed model");await expect(models).toBeVisible();
 const available=await models.locator("option").allTextContents();
 if(available.includes("qwen3:8b")){
  await models.selectOption("qwen3:8b");
  await page.getByLabel("I confirm one local agent action for this snapshot. No download.").check();
  const response=page.waitForResponse(r=>r.url().endsWith("/console/agent/investigate"),{timeout:110000});
  await page.getByText("Run confirmed local agent",{exact:true}).click();
  const r=await response;const report=await r.json();
  await expect(page.getByTestId("agent-report")).toBeVisible();
  mark(`Actual local model action status ${report.agent_status}; tools ${report.tool_trace.length}; admitted claims ${report.validated_claims.length}.`);
 }else mark("No eligible qwen3:8b currently available through actual capabilities. No model invocation or download.");
 await page.getByRole("region",{name:"Investigation steps",exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:resolve(root,"docs/screenshots/sprint06/06-local-capability-state.png")});
 mark("Current local capability state. Offline rehearsal remains available; no cause established.");
 await context.close();context=null;
 await copyFile(await video.path(),target);
 await writeFile(resolve(out,"captions.json"),JSON.stringify({kind:"GENUINE_SILENT_BROWSER_RECORDING",
   timing:"Wall-clock offsets from runner start, include browser/server startup; approximate caption anchors, not edited subtitle timecodes.",events},null,2)+"\n");
 console.log(JSON.stringify({recording:"docs/video/sprint06/native-walkthrough.webm",events}));
}finally{
 if(context)await context.close();if(browser)await browser.close();
 if(server.exitCode===null)spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true});
}
