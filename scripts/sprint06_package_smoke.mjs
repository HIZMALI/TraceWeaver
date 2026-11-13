// External installed-wheel browser proof. Node drives Chromium, not the Python server.
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,".verification/overnight/browsers");
const {chromium,expect}=await import("../web/node_modules/@playwright/test/index.mjs");
const base=process.argv[2];
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))throw new Error("Numeric loopback required");
const browser=await chromium.launch();
try{
 const page=await browser.newPage(), errors=[], posts=[];
 page.on("pageerror",e=>errors.push(e.message));
 page.on("request",r=>{if(r.method()==="POST")posts.push(new URL(r.url()).pathname);});
 await page.goto(base+"/?incident=INC-001");await expect(page.locator(".react-flow__edge")).toHaveCount(14);
 await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
 expect(posts).toEqual([]);
 await page.getByRole("button",{name:"Explore investigation steps"}).click();
 const response=page.waitForResponse(r=>r.url().endsWith("/console/agent/rehearse"));
 await page.getByRole("button",{name:"Rehearse graph investigation",exact:true}).click();
 const actual=await response;expect(actual.status()).toBe(200);const report=await actual.json();
 await expect(page.getByTestId("agent-report")).toBeVisible();
 expect(report.tool_trace).toHaveLength(4);expect(report.ai_directed_tools).toBe(false);
 await page.getByRole("button",{name:/Inspect tool step 2 trace_deployment/}).click();
 await expect(page.getByRole("region",{name:"Selected native tool step"})).toContainText("Reverse traversal");
 expect(errors).toEqual([]);
 console.log(JSON.stringify({browser:browser.version(),native_edges:14,real_packaged_ui:true,
  page_errors:errors.length,initial_ai_calls:0,agent_tools:report.tool_trace.map(s=>s.tool_name),
  agent_native_queries:report.native_query_count,claims:report.validated_claims.length,
  citations:report.validated_citation_count,mode:report.mode_executed}));
}finally{await browser.close();}
