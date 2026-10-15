import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
const root = resolve('dist') + sep;
const port = Number(process.env.PORT || 4173);
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8'};
createServer(async(req,res)=>{
  try{
    const name = decodeURIComponent((req.url || '/').split('?')[0]);
    const requested = resolve('dist',name.replace(/^\/+/, '') || 'index.html');
    if(!requested.startsWith(root)){res.writeHead(403);res.end();return;}
    const file = await stat(requested);
    if(!file.isFile()){res.writeHead(404);res.end();return;}
    const ext = requested.slice(requested.lastIndexOf('.'));
    res.writeHead(200,{'Content-Type':types[ext]||'application/octet-stream','Cache-Control':'no-cache'});
    res.end(await readFile(requested));
  }catch{res.writeHead(404);res.end('Not Found');}
}).listen(port,()=>console.log(`本地工程验证：http://localhost:${port}/`));
