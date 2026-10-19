const { chromium } = require('../../control-plane/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');

const baseUrl = 'http://127.0.0.1:5180';
const healthPath = '/health';

async function main() {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const page = await browser.newPage();
  const healthRequests = [];
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.name));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname !== healthPath || request.method() !== 'GET') return;
    const headers = request.headers();
    healthRequests.push({
      origin: url.origin,
      path: url.pathname,
      method: request.method(),
      hasAuthorization: Boolean(headers.authorization),
      hasOperatorToken: Object.keys(headers).some(name => /operator.*token|x-admin-token/i.test(name)),
    });
  });

  try {
    const pageResponse = await page.goto(`${baseUrl}/settings`, { waitUntil: 'domcontentloaded' });
    if (pageResponse?.status() !== 200) throw new Error(`Settings page HTTP ${pageResponse?.status() ?? 'none'}`);
    await page.getByRole('heading', { name: 'Health Backend aktual' }).waitFor();
    await page.getByText('GET /health - HTTP 200', { exact: true }).waitFor({ timeout: 15000 });
    const button = page.getByRole('button', { name: 'Periksa health' });
    await button.waitFor({ state: 'visible' });
    const beforeClick = healthRequests.length;
    const responsePromise = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.origin === baseUrl && url.pathname === healthPath && response.request().method() === 'GET';
    }, { timeout: 10000 });
    await button.click();
    const healthResponse = await responsePromise;
    await page.getByText('GET /health - HTTP 200', { exact: true }).waitFor({ timeout: 10000 });
    const visibleCaveat = await page.getByText(/GET \/health hanya memeriksa kesehatan Backend; hasilnya tidak membuktikan inferensi model berhasil\./).isVisible();
    const body = await healthResponse.json();
    const result = {
      settingsHttp: pageResponse.status(),
      settingsUrl: page.url(),
      initialHealthVisible: true,
      manualClickIssuedGetHealth: healthRequests.length > beforeClick,
      browserRequest: healthRequests.at(-1),
      healthHttp: healthResponse.status(),
      healthPayloadStatus: typeof body.status === 'string' ? body.status : 'invalid',
      healthResultVisible: await page.getByText('GET /health - HTTP 200', { exact: true }).isVisible(),
      modelInferenceCaveatVisible: visibleCaveat,
      pageErrors,
    };
    if (!result.manualClickIssuedGetHealth || result.healthHttp !== 200 || result.healthPayloadStatus !== 'ok' || !visibleCaveat || pageErrors.length) {
      throw new Error(`Health UI verification failed: ${JSON.stringify(result)}`);
    }
    fs.writeFileSync(path.join(__dirname, 'browser-e2e.json'), `${JSON.stringify(result, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
