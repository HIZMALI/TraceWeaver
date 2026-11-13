import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(root,'.verification/overnight/browsers');
const {chromium,expect}=await import('@playwright/test');
const base=process.argv[2];if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))throw new Error('Numeric loopback origin required');
const browser=await chromium.launch();
try{
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/?incident=INC-001');await expect(page.locator('.react-flow__edge')).toHaveCount(14);
 await expect(page.getByTestId('causal-status')).toHaveText('NOT_ESTABLISHED');
 if(errors.length)throw new Error('Packaged page error');
 console.log(JSON.stringify({browser:browser.version(),native_edges:14,real_packaged_ui:true,page_errors:0}));
}finally{await browser.close();}
