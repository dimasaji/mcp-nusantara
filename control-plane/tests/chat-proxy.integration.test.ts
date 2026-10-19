// @vitest-environment node
import {afterEach,expect,it} from 'vitest';
import {createServer as createHttpServer} from 'node:http';
import {once} from 'node:events';
import {createServer,type ViteDevServer} from 'vite';

let vite:ViteDevServer|undefined;
let backend:ReturnType<typeof createHttpServer>|undefined;
const previousTarget=process.env.NUSANTARA_BACKEND_URL;
afterEach(async()=>{
  await vite?.close();vite=undefined;
  if(backend)await new Promise<void>(resolve=>backend!.close(()=>resolve()));backend=undefined;
  if(previousTarget===undefined)delete process.env.NUSANTARA_BACKEND_URL;
  else process.env.NUSANTARA_BACKEND_URL=previousTarget;
});

it('forwards Chat UI POST /v1/chat through the Vite proxy to a Hermes HTTP mock',async()=>{
  const received:Array<{method:string;url:string;body:string}> = [];
  const answer={response:'Jawaban simulasi dari Hermes.',model:'hermes-test',provider_status:'mock'};
  backend=createHttpServer(async(req,res)=>{
    const chunks:Buffer[]=[];for await(const chunk of req)chunks.push(Buffer.from(chunk));
    const body=Buffer.concat(chunks).toString('utf8');received.push({method:req.method!,url:req.url!,body});
    res.writeHead(200,{'content-type':'application/json'});res.end(JSON.stringify(answer));
  });
  backend.listen(0,'127.0.0.1');await once(backend,'listening');
  const backendPort=(backend.address() as {port:number}).port;
  process.env.NUSANTARA_BACKEND_URL=`http://127.0.0.1:${backendPort}`;
  vite=await createServer({configFile:'vite.config.ts',server:{port:0,strictPort:false,open:false},logLevel:'silent'});
  await vite.listen();
  const origin=`http://127.0.0.1:${(vite.httpServer!.address() as {port:number}).port}`;
  const body={user_input:'Pertanyaan uji',session_id:'mock-session'};

  const response=await fetch(`${origin}/v1/chat`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual(answer);
  expect(received).toEqual([{method:'POST',url:'/v1/chat',body:JSON.stringify(body)}]);
},20000);
