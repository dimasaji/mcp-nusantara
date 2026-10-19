// @vitest-environment node
import {afterEach, expect, it} from 'vitest';
import {createServer as createHttpServer} from 'node:http';
import {once} from 'node:events';
import {createServer, type ViteDevServer} from 'vite';

let vite: ViteDevServer | undefined;
let backend: ReturnType<typeof createHttpServer> | undefined;
const previousTarget = process.env.NUSANTARA_BACKEND_URL;
afterEach(async () => {
  await vite?.close();
  if (backend) await new Promise<void>(resolve => backend!.close(() => resolve()));
  if (previousTarget === undefined) delete process.env.NUSANTARA_BACKEND_URL;
  else process.env.NUSANTARA_BACKEND_URL = previousTarget;
});

it('forwards document bytes, operator auth and pipeline History through the Control Panel origin', async () => {
  const received: Array<{method: string; url: string; token: string | undefined; name: string | undefined; body: Buffer}> = [];
  backend = createHttpServer(async (request, response) => {
    const chunks: Buffer[] = [];
    for await (const chunk of request) chunks.push(Buffer.from(chunk));
    received.push({method: request.method!, url: request.url!, token: request.headers['x-admin-token'] as string,
      name: request.headers['x-document-name'] as string, body: Buffer.concat(chunks)});
    response.writeHead(200, {'Content-Type': 'application/json'});
    response.end(JSON.stringify(request.method === 'POST' ? {status: 'READY'} : {runs: [{status: 'READY'}]}));
  });
  backend.listen(0, '127.0.0.1');
  await once(backend, 'listening');
  const address = backend.address() as {port: number};
  process.env.NUSANTARA_BACKEND_URL = `http://127.0.0.1:${address.port}`;
  vite = await createServer({configFile: 'vite.config.ts', server: {port: 0, strictPort: false, open: false}, logLevel: 'silent'});
  await vite.listen();
  const origin = `http://127.0.0.1:${(vite.httpServer!.address() as {port: number}).port}`;
  const bytes = Buffer.from('%PDF-1.4\nrequest-body-preserved\n');
  const uploaded = await fetch(`${origin}/v1/knowledge/pipeline/documents`, {method: 'POST',
    headers: {'Content-Type': 'application/octet-stream', 'X-Admin-Token': 'isolated-fixture',
      'X-Document-Name': 'petunjuk.pdf'}, body: bytes});
  expect(uploaded.status).toBe(200);
  expect(await uploaded.json()).toEqual({status: 'READY'});
  const history = await fetch(`${origin}/v1/knowledge/pipeline/status`, {headers: {'X-Admin-Token': 'isolated-fixture'}});
  expect(history.status).toBe(200);
  expect(await history.json()).toEqual({runs: [{status: 'READY'}]});
  const watch = await fetch(`${origin}/v1/knowledge/pipeline/watch?enabled=true`, {method: 'POST',
    headers: {'X-Admin-Token': 'isolated-fixture'}});
  expect(watch.status).toBe(200);
  expect(received).toEqual([
    {method: 'POST', url: '/v1/knowledge/pipeline/documents', token: 'isolated-fixture', name: 'petunjuk.pdf', body: bytes},
    {method: 'GET', url: '/v1/knowledge/pipeline/status', token: 'isolated-fixture', name: undefined, body: Buffer.alloc(0)},
    {method: 'POST', url: '/v1/knowledge/pipeline/watch?enabled=true', token: 'isolated-fixture', name: undefined, body: Buffer.alloc(0)},
  ]);
}, 20000);
