import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {mkdir} from "node:fs/promises";
import {dirname,resolve} from "node:path";
import {fileURLToPath} from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"../..");
const shots=resolve(root,"docs/screenshots/sprint06");
async function open(page,id="INC-001",port=8765){
  await page.goto(`http://127.0.0.1:${port}/?incident=${id}`);
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  await expect(page.locator(".react-flow__edge").first()).toBeAttached();
}
async function rehearse(page,intent="TRACE_DEPENDENCY_PATH"){
  await page.getByRole("button",{name:"Explore investigation steps"}).click();
  await page.getByLabel("Investigation intent").selectOption(intent);
  const response=page.waitForResponse(r=>r.url().endsWith("/console/agent/rehearse"));
  await page.getByRole("button",{name:"Rehearse graph investigation",exact:true}).click();
  const native=await response;expect(native.status()).toBe(200);
  await expect(page.getByTestId("agent-report")).toBeVisible();
  return native.json();
}
async function shot(page,name){await mkdir(shots,{recursive:true});await page.screenshot({path:resolve(shots,name+".png"),fullPage:false});}

test("sprint06 first viewport shows actual proof summary without local POST",async({page})=>{
  const posts=[],foreign=[],errors=[];
  page.on("request",r=>{if(r.method()==="POST")posts.push(r.url());if(!r.url().startsWith("http://127.0.0.1:8765"))foreign.push(r.url());});
  page.on("pageerror",e=>errors.push(e.message));await open(page);
  await expect(page.getByRole("heading",{name:"Why this graph matters"})).toBeInViewport();
  await expect(page.getByRole("button",{name:/Focus proof DEP-001/})).toBeInViewport();
  await shot(page,"01-first-viewport");expect(posts).toEqual([]);expect(foreign).toEqual([]);expect(errors).toEqual([]);
});
test("sprint06 genuine offline tools expose reverse TARGETS and exact proof focus",async({page})=>{
  await open(page);const r=await rehearse(page);
  expect(r.ai_directed_tools).toBe(false);expect(r.model_interactions).toBe(0);
  expect(r.tool_trace[1].tool_name).toBe("trace_deployment");
  expect(r.tool_trace[1].result.graph_paths.some(p=>p.edges.some(e=>e.type==="TARGETS"&&e.traversal_direction==="REVERSE"))).toBe(true);
  await page.getByRole("button",{name:/Inspect tool step 2 trace_deployment/}).click();
  await expect(page.getByRole("region",{name:"Selected native tool step"})).toContainText("DEP-001");
  await expect(page.getByRole("region",{name:"Selected native tool step"})).toContainText("Reverse traversal");
  await page.getByRole("button",{name:"Focus selected paths"}).click();
  await page.evaluate(()=>window.scrollTo(0,300));await shot(page,"02-native-tool-proof");
});
test("sprint06 native competing deployment rehearsal keeps both candidates",async({page})=>{
  await open(page);const r=await rehearse(page,"CHECK_COMPETING_DEPLOYMENTS");
  expect(r.tool_trace.filter(s=>s.tool_name==="trace_deployment").flatMap(s=>s.subject_ids)).toContain("DEP-002");
  expect(r.tool_trace).toHaveLength(4);expect(r.validated_claims.at(-1).claim_type).toBe("NO_CAUSAL_VERDICT");
  await page.getByTestId("agent-report").scrollIntoViewIfNeeded();await shot(page,"03-offline-tool-trace");
});
test("sprint06 reconciliation retains conflict and undetermined native results",async({page})=>{
  await open(page,"CASE-INC");const r=await rehearse(page,"RECONCILE_OBSERVATIONS");
  expect(r.tool_trace.flatMap(s=>s.result.comparisons).map(c=>c.classification)).toEqual(["CONFLICTING_OBSERVATIONS","UNDETERMINED"]);
  await page.getByRole("button",{name:/Inspect tool step 2 compare_observations/}).click();
  await page.getByRole("tab",{name:/Observations/}).click();
  await page.getByRole("button",{name:/Inspect CONFLICTING_OBSERVATIONS/}).click();
  await page.evaluate(()=>window.scrollTo(0,650));await shot(page,"04-structured-conflict");
});
test("sprint06 native gap rehearsal preserves unknown time and source bounds",async({page})=>{
  await open(page,"CASE-INC");const r=await rehearse(page,"FIND_EVIDENCE_GAPS");
  expect(r.gap_codes).toContain("UNKNOWN_EVENT_TIMES");
  expect(r.external_verification_status).toBe("NOT_PERFORMED");
  expect(r.tool_trace.some(s=>s.tool_name==="inspect_gaps")).toBe(true);
});
test("sprint06 capped native source stays visibly partial",async({page})=>{
  await open(page,"EV-CAPS",8769);const r=await rehearse(page);
  expect(r.source_truncated).toBe(true);
  await expect(page.getByText(/Bounded source\/subject context/)).toBeVisible();
});
test("sprint06 actual installed capabilities require explicit opt-in and no automatic inference",async({page})=>{
  const posts=[];page.on("request",r=>{if(r.method()==="POST")posts.push(new URL(r.url()).pathname);});
  await open(page);await page.getByText("Explore investigation steps").click();expect(posts).toEqual([]);
  await page.getByText("Agent investigation (local)",{exact:true}).click();
  await expect(page.getByLabel("Agent installed model")).toBeVisible();
  await expect(page.getByText("Run confirmed local agent")).toBeDisabled();
  expect(posts).toEqual(["/console/models/capabilities"]);
});
test("sprint06 admitted rehearsal claim drills into existing typed citation inspector",async({page})=>{
  await open(page);await rehearse(page);
  await page.getByText(/Admitted claim citations/).click();
  await page.locator(".agent-claim").filter({hasText:"DEPLOYMENT_CONNECTED"}).first().click();
  await expect(page.getByRole("region",{name:"Selected claim"})).toContainText("GRAPH_PATH");
  await expect(page.locator(".react-flow__node.selected").first()).toBeAttached();
});
test("sprint06 URL navigation never restores a fictional executed run",async({page})=>{
  await open(page);await rehearse(page);await page.getByRole("button",{name:/Inspect tool step 2 trace_deployment/}).click();
  await page.reload();await expect(page.getByTestId("causal-status")).toBeVisible();
  await expect(page.getByTestId("agent-report")).toHaveCount(0);
  await expect(page.getByRole("region",{name:"Selected native tool step"})).toHaveCount(0);
  expect(new URL(page.url()).searchParams.get("selection")).toBe("node:DEP-001");
});
test("sprint06 keyboard, expanded-panel axe and reduced motion remain usable",async({page})=>{
  await page.emulateMedia({reducedMotion:"reduce"});await open(page);await rehearse(page);
  const step=page.getByRole("button",{name:/Inspect tool step 2 trace_deployment/});await step.focus();await page.keyboard.press("Enter");
  await expect(page.getByRole("region",{name:"Selected native tool step"})).toBeVisible();
  const scan=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze();expect(scan.violations).toEqual([]);
});
for(const [width,height,name] of [[1024,768,"tablet"],[720,900,"reflow"],[390,844,"phone"]]){
  test(`sprint06 ${name} actual tool panel reflows without document overflow`,async({page})=>{
    await page.setViewportSize({width,height});await open(page);
    if(width<900)await page.getByRole("button",{name:"Details",exact:true}).click();
    await rehearse(page);await page.getByTestId("agent-report").scrollIntoViewIfNeeded();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
    if(name==="phone")await shot(page,"05-phone-rehearsal");
  });
}
