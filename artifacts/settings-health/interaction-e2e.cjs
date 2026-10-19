const { chromium } = require('../../control-plane/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');

const baseUrl = 'http://127.0.0.1:5180';
const delayMs = 900;

async function main() {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const page = await browser.newPage();
  const requests = [];
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.name));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.origin !== baseUrl || url.pathname !== '/health' || request.method() !== 'GET') return;
    const headers = request.headers();
    requests.push({
      method: request.method(),
      path: url.pathname,
      hasAuthorization: Boolean(headers.authorization),
      hasOperatorToken: Object.keys(headers).some(name => /operator.*token|x-admin-token/i.test(name)),
    });
  });

  await page.route(`${baseUrl}/health`, async route => {
    await new Promise(resolve => setTimeout(resolve, delayMs));
    await route.continue();
  });

  try {
    const ui = await page.goto(`${baseUrl}/settings`, { waitUntil: 'domcontentloaded' });
    if (ui?.status() !== 200) throw new Error(`Settings HTTP ${ui?.status() ?? 'none'}`);
    await page.getByRole('heading', { name: 'Health Backend aktual' }).waitFor();
    await page.getByText('GET /health - HTTP 200', { exact: true }).waitFor({ timeout: 15000 });

    const checkOnce = async index => {
      const button = page.getByRole('button', { name: 'Periksa health' });
      await button.waitFor({ state: 'visible' });
      const previousTime = (await page.getByText(/Pemeriksaan terakhir:/).textContent()).trim();
      const requestCount = requests.length;
      const responsePromise = page.waitForResponse(response => {
        const url = new URL(response.url());
        return url.origin === baseUrl && url.pathname === '/health' && response.request().method() === 'GET';
      }, { timeout: 10000 }).then(response => ({ response }), error => ({ error: error.message }));
      await button.click();
      const busyButton = page.locator('button').filter({ hasText: 'Memeriksa' });
      try { await busyButton.waitFor({ state: 'visible', timeout: 5000 }); }
      catch {
        const panel = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Health Backend aktual' }) });
        throw new Error(`Click ${index} showed no busy button. Health panel: ${(await panel.innerText()).replace(/\s+/g, ' ')}`);
      }
      const loadingButtonText = (await busyButton.textContent()).trim();
      if (loadingButtonText !== 'Memeriksa…') throw new Error(`Click ${index} showed unexpected button text: ${loadingButtonText}`);
      const liveStatus = page.locator('[role="status"]').filter({ hasText: 'Memeriksa GET /health pada Backend' });
      await liveStatus.waitFor({ state: 'visible', timeout: 5000 });
      const liveStatusText = await liveStatus.textContent();
      if (!liveStatusText?.includes('Memeriksa GET /health pada Backend…')) throw new Error(`Click ${index} showed an unexpected loading message`);
      const responseResult = await responsePromise;
      if (responseResult.error) throw new Error(`Click ${index} health request failed: ${responseResult.error}`);
      const response = responseResult.response;
      const body = await response.json();
      await page.getByRole('button', { name: 'Periksa health' }).waitFor({ state: 'visible' });
      await page.waitForFunction(previous => {
        const node = [...document.querySelectorAll('p')].find(item => item.textContent?.startsWith('Pemeriksaan terakhir:'));
        return node && node.textContent.trim() !== previous;
      }, previousTime, { timeout: 10000 });
      const currentTime = (await page.getByText(/Pemeriksaan terakhir:/).textContent()).trim();
      const request = requests.at(-1);
      if (requests.length !== requestCount + 1) throw new Error(`Click ${index} did not issue exactly one GET /health`);
      if (response.status() !== 200 || body.status !== 'ok') throw new Error(`Click ${index} returned unexpected health result`);
      if (currentTime === previousTime) throw new Error(`Click ${index} did not update the last-check time`);
      return {
        click: index,
        loadingButtonText,
        loadingStatusText: liveStatusText.trim(),
        request,
        httpStatus: response.status(),
        backendStatus: body.status,
        resultVisible: await page.getByText('GET /health - HTTP 200', { exact: true }).isVisible(),
        lastCheckChanged: currentTime !== previousTime,
        lastCheckLabel: currentTime,
      };
    };

    const results = [await checkOnce(1), await checkOnce(2)];
    const caveatVisible = await page.getByText(/GET \/health hanya memeriksa kesehatan Backend; hasilnya tidak membuktikan inferensi model berhasil\./).isVisible();
    const evidence = {
      settingsUrl: page.url(),
      settingsHttp: ui.status(),
      controlledNetworkDelayMs: delayMs,
      clicks: results,
      noOperatorCredentialSent: requests.every(request => !request.hasAuthorization && !request.hasOperatorToken),
      modelInferenceCaveatVisible: caveatVisible,
      pageErrors,
    };
    if (!caveatVisible || pageErrors.length || !evidence.noOperatorCredentialSent) throw new Error(`Browser verification failed: ${JSON.stringify(evidence)}`);
    fs.writeFileSync(path.join(__dirname, 'interaction-e2e.json'), `${JSON.stringify(evidence, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify(evidence, null, 2)}\n`);
  } finally {
    await page.close({ runBeforeUnload: false }).catch(() => {});
    await browser.close();
  }
}

main().catch(error => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
