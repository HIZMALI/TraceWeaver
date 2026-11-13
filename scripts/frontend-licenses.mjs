// Reproducible notices for the actual installed production dependency tree.
import {readFile,readdir,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),web=resolve(root,'web');
const manifest=JSON.parse(await readFile(resolve(web,'package.json'),'utf8'));
const seen=new Map();
async function visit(name){
  if(seen.has(name))return;
  const directory=resolve(web,'node_modules',name),meta=JSON.parse(await readFile(resolve(directory,'package.json'),'utf8'));
  const names=(await readdir(directory)).filter(n=>/^(license|copying|notice)(\.|$)/i.test(n));
  if(!names.length)throw new Error('Review missing license: '+name);
  const notices=await Promise.all(names.map(n=>readFile(resolve(directory,n),'utf8')));
  seen.set(name,{name:meta.name,version:meta.version,license:meta.license,notices});
  for(const dependency of Object.keys(meta.dependencies??{}))await visit(dependency);
}
for(const name of Object.keys(manifest.dependencies))await visit(name);
const entries=[...seen.values()].sort((a,b)=>a.name.localeCompare(b.name,'en'));
await mkdir(resolve(web,'public/assets'),{recursive:true});
await writeFile(resolve(web,'public/assets/third-party-licenses.txt'),entries.map(e=>`${e.name} ${e.version} (${e.license})\n${'='.repeat(72)}\n${e.notices.join('\n')}\n`).join('\n'),'utf8');
console.log(JSON.stringify(entries.map(({name,version,license})=>({name,version,license})),null,2));
