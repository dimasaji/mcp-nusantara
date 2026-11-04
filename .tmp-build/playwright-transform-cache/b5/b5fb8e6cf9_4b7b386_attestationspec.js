// 75d9207f8cd9ec96d7915d17d0f019eeff9d8ee5
import { test as base, expect } from '@playwright/test';
import { build } from 'esbuild';
import path from 'node:path';

// A virtual origin fulfilled entirely through Playwright; no test web server.
const origin = 'http://attestation-e2e.invalid';
if (process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || process.env.CPLANE_E2E_LIVE) throw new Error('MOCK_ONLY_MODE_REQUIRED');
const scope = 'R2-A8:ATTESTATION:ONE_GENERATION';
const snapshot = () => ({
  projection_contract: 'ATTESTATION_FOUNDATION_V1',
  evidence_id: 'r2-a9-auth-process',
  evidence_type: 'SCOPED_IN_PROCESS',
  source: 'SYNTHETIC BROWSER TEST — NOT LIVE EVIDENCE',
  scope,
  created_at: '2026-10-08T00:00:00Z',
  status: 'NOT_VERIFIED',
  evidence_version: 'a'.repeat(64),
  live_actions: 'LOCKED',
  operator_policy: 'NOT_PROVISIONED',
  binding: {
    scope,
    target: '127.0.0.1:8000',
    pid: 123,
    process_start: 134000000000000000,
    runtime_instance: 'synthetic-instance',
    source_snapshot: 'synthetic-source',
    scoped_loaded_code: 'synthetic-code',
    configuration_digest: 'b'.repeat(64),
    endpoint: {
      origin: 'http://127.0.0.1:11434',
      connection_origin: 'http://127.0.0.1:11434'
    },
    profile: 'ATTESTATION',
    active_process_build: 'NOT_DIRECTLY_VERIFIED',
    runtime_identity: 'NOT_VERIFIED'
  },
  reviews: [],
  provider_receipt: null
});
let assets;
const test = base.extend({
  mock: async ({
    context,
    page
  }, use, testInfo) => {
    var _launch$proxy, _launch$args;
    const launch = testInfo.project.use.launchOptions;
    if (process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || testInfo.config.webServer || testInfo.project.use.baseURL !== origin || testInfo.project.use.serviceWorkers !== 'block' || (launch === null || launch === void 0 || (_launch$proxy = launch.proxy) === null || _launch$proxy === void 0 ? void 0 : _launch$proxy.server) !== 'http://127.0.0.1:9' || launch.proxy.bypass !== '<-loopback>' || !((_launch$args = launch.args) !== null && _launch$args !== void 0 && _launch$args.includes('--host-resolver-rules=MAP * ~NOTFOUND'))) throw new Error('UNSAFE_TEST_CONFIGURATION');
    assets !== null && assets !== void 0 ? assets : assets = await build({
      absWorkingDir: path.resolve(testInfo.config.rootDir, '..'),
      entryPoints: ['src/main.tsx'],
      bundle: true,
      write: false,
      outdir: 'virtual',
      jsx: 'automatic',
      define: {
        'process.env.NODE_ENV': '"production"',
        '__CPLANE_BUILD__': JSON.stringify({
          version: 'SYNTHETIC',
          gitCommit: 'NOT_VERIFIED',
          timestamp: '2026-10-08T00:00:00Z',
          environment: 'MOCK_ONLY',
          sourceId: 'NOT_LIVE_EVIDENCE'
        })
      },
      logLevel: 'silent'
    });
    const s = snapshot();
    const mock = {
      snapshot: s,
      snapshotStatus: 200,
      intention: {
        review_id: 'synthetic-review',
        scope,
        evidence_version: s.evidence_version,
        state: 'PENDING',
        expires_at: '2026-10-08T00:02:00Z'
      },
      intentionStatus: 200,
      posts: [],
      blocked: [],
      expectedBlocked: [],
      requests: [],
      errors: [],
      console: [],
      expectedConsole: []
    };
    page.on('pageerror', e => mock.errors.push(e.message));
    page.on('console', message => {
      if (message.type() === 'error') mock.console.push(message.text());
    });
    await context.routeWebSocket(/.*/, socket => {
      mock.blocked.push('WEBSOCKET ' + socket.url());
      socket.close();
    });
    await context.route('**/*', async route => {
      const request = route.request(),
        url = new URL(request.url()),
        method = request.method();
      mock.requests.push(method + ' ' + request.url());
      if (url.origin === origin && !url.search) {
        if (url.pathname === '/v1/control-plane/snapshot' && method === 'GET') {
          await route.fulfill({
            status: mock.snapshotStatus,
            json: mock.snapshot
          });
          return;
        }
        if (url.pathname === '/v1/control-plane/intention' && method === 'POST') {
          const body = request.postDataJSON();
          const current = mock.snapshot;
          if (JSON.stringify(body) === JSON.stringify({
            scope: current.scope,
            evidence_version: current.evidence_version
          })) {
            mock.posts.push(body);
            await route.fulfill({
              status: mock.intentionStatus,
              json: mock.intention
            });
            return;
          }
        }
        if (method === 'GET' && ['/overview', '/evidence', '/test', '/review', '/decision'].includes(url.pathname) && request.isNavigationRequest()) {
          await route.fulfill({
            contentType: 'text/html',
            body: '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script src="/main.js"></script></body></html>'
          });
          return;
        }
        if (method === 'GET' && ['/main.js', '/main.css'].includes(url.pathname)) {
          var _assets$outputFiles;
          const file = (_assets$outputFiles = assets.outputFiles) === null || _assets$outputFiles === void 0 ? void 0 : _assets$outputFiles.find(f => path.basename(f.path) === url.pathname.slice(1));
          if (file) {
            await route.fulfill({
              contentType: url.pathname.endsWith('.js') ? 'text/javascript' : 'text/css',
              body: Buffer.from(file.contents)
            });
            return;
          }
        }
      }
      mock.blocked.push(method + ' ' + request.url());
      await route.abort('blockedbyclient');
    });
    await use(mock);
    await testInfo.attach('mock-network-evidence', {
      body: JSON.stringify({
        ...mock,
        live: false
      }),
      contentType: 'application/json'
    });
    expect(mock.blocked, 'unexpected network request').toEqual(mock.expectedBlocked);
    expect(mock.errors, 'browser runtime errors').toEqual([]);
    expect(mock.console, 'unexpected browser console error').toEqual(mock.expectedConsole);
  }
});
async function noAuthority(page) {
  for (const name of ['APPROVE', 'ARM', 'EXECUTE', 'CONFIRM APPROVAL']) await expect(page.getByRole('button', {
    name,
    exact: true
  })).toHaveCount(0);
}
async function review(page, mock) {
  await page.goto('/overview');
  await noAuthority(page);
  await expect(page.getByRole('button', {
    name: 'Continue to Evidence',
    exact: true
  })).toBeDisabled();
  await page.getByLabel('I have read the ATTESTATION scope and limitations.').check();
  await page.getByRole('button', {
    name: 'Continue to Evidence',
    exact: true
  }).click();
  await expect(page).toHaveURL(origin + '/evidence');
  await noAuthority(page);
  await page.getByLabel('I inspected the exact evidence version and identity scope.').check();
  await page.getByRole('button', {
    name: 'Continue to Human Test',
    exact: true
  }).click();
  await expect(page).toHaveURL(origin + '/test');
  await noAuthority(page);
  await expect(page.getByRole('button', {
    name: 'Continue to Review',
    exact: true
  })).toBeDisabled();
  for (const [id, result] of [['runtime', 'PASS'], ['separate', 'FAIL'], ['boundary', 'BLOCKED']]) await page.getByRole('group', {
    name: 'Observation ' + id
  }).getByRole('button', {
    name: result,
    exact: true
  }).click();
  await page.getByRole('button', {
    name: 'Continue to Review',
    exact: true
  }).click();
  await expect(page).toHaveURL(origin + '/review');
  await noAuthority(page);
  await expect(page.getByText('separate: FAIL', {
    exact: true
  })).toBeVisible();
  await expect(page.getByText('boundary: BLOCKED', {
    exact: true
  })).toBeVisible();
  await page.getByLabel('I reviewed these observations and the NOT_VERIFIED limitations.').check();
  await page.getByRole('button', {
    name: 'Continue to Decision',
    exact: true
  }).click();
  await expect(page).toHaveURL(origin + '/decision');
  await noAuthority(page);
  expect(mock.posts).toEqual([]);
}
test('five stages render, scroll and submit only explicit PENDING intention', async ({
  page,
  mock
}, info) => {
  await page.setViewportSize({
    width: 390,
    height: 640
  });
  await review(page, mock);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  await page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  }).click();
  await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention; no authorization granted.');
  await expect(page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  })).toBeDisabled();
  expect(mock.posts).toHaveLength(1);
  await noAuthority(page);
  await expect(page.getByText('NOT_VERIFIED', {
    exact: true
  }).first()).toBeVisible();
  await info.attach('rendering-metrics', {
    body: JSON.stringify(await page.evaluate(() => ({
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      scrollY,
      documentHeight: document.documentElement.scrollHeight
    }))),
    contentType: 'application/json'
  });
  await page.screenshot({
    path: info.outputPath('pending-mobile.png'),
    fullPage: true
  });
});
for (const path of ['/evidence', '/test', '/review', '/decision']) test('direct ' + path + ' cannot bypass review', async ({
  page,
  mock
}) => {
  await page.goto(path);
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toBeVisible();
  await noAuthority(page);
  expect(mock.posts).toEqual([]);
});
for (const kind of ['API failure', 'malformed snapshot']) test(kind + ' remains unavailable', async ({
  page,
  mock
}) => {
  mock.snapshotStatus = kind === 'API failure' ? 503 : 200;
  mock.snapshot = kind === 'API failure' ? {
    error: 'synthetic-unavailable'
  } : {
    status: 'PASS'
  };
  if (kind === 'API failure') mock.expectedConsole = ['Failed to load resource: the server responded with a status of 503 (Service Unavailable)'];
  await page.goto('/decision');
  await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  await expect(page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  })).toHaveCount(0);
  await noAuthority(page);
});
for (const kind of ['API rejection', 'invented authority', 'wrong evidence']) test(kind + ' intention fails closed without automatic retry', async ({
  page,
  mock
}) => {
  await review(page, mock);
  if (kind === 'API rejection') {
    mock.intentionStatus = 409;
    mock.expectedConsole = ['Failed to load resource: the server responded with a status of 409 (Conflict)'];
  } else mock.intention = {
    ...mock.intention,
    ...(kind === 'invented authority' ? {
      state: 'APPROVED'
    } : {
      evidence_version: 'c'.repeat(64)
    })
  };
  await page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);
  await expect(page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  })).toBeDisabled();
  expect(mock.posts).toHaveLength(1);
  await noAuthority(page);
});
test('material context change clears pending and relocks the session', async ({
  page,
  mock
}) => {
  await review(page, mock);
  await page.getByRole('button', {
    name: 'Create PENDING intention',
    exact: true
  }).click();
  await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention');
  const s = mock.snapshot;
  mock.snapshot = {
    ...s,
    evidence_version: 'c'.repeat(64),
    binding: {
      ...s.binding,
      runtime_instance: 'synthetic-new-instance'
    }
  };
  await page.getByRole('button', {
    name: 'Refresh evidence',
    exact: true
  }).click();
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);
  expect(mock.posts).toHaveLength(1);
  await page.getByRole('button', {
    name: 'Go to System',
    exact: true
  }).click();
  await expect(page.getByLabel('I have read the ATTESTATION scope and limitations.')).not.toBeChecked();
  await noAuthority(page);
});
test('network boundary aborts an unlisted virtual-origin request', async ({
  page,
  mock
}) => {
  await page.goto('/overview');
  mock.expectedBlocked = ['GET ' + origin + '/unlisted-boundary-test'];
  mock.expectedConsole = ['Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector'];
  const failed = await page.evaluate(async () => {
    try {
      await fetch('/unlisted-boundary-test');
      return false;
    } catch {
      return true;
    }
  });
  expect(failed).toBe(true);
  expect(mock.blocked).toEqual(mock.expectedBlocked);
  expect(mock.posts).toEqual([]);
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6WyJ0ZXN0IiwiYmFzZSIsImV4cGVjdCIsImJ1aWxkIiwicGF0aCIsIm9yaWdpbiIsInByb2Nlc3MiLCJlbnYiLCJDUExBTkVfQVRURVNUQVRJT05fRTJFIiwiQ1BMQU5FX0UyRV9MSVZFIiwiRXJyb3IiLCJzY29wZSIsInNuYXBzaG90IiwicHJvamVjdGlvbl9jb250cmFjdCIsImV2aWRlbmNlX2lkIiwiZXZpZGVuY2VfdHlwZSIsInNvdXJjZSIsImNyZWF0ZWRfYXQiLCJzdGF0dXMiLCJldmlkZW5jZV92ZXJzaW9uIiwicmVwZWF0IiwibGl2ZV9hY3Rpb25zIiwib3BlcmF0b3JfcG9saWN5IiwiYmluZGluZyIsInRhcmdldCIsInBpZCIsInByb2Nlc3Nfc3RhcnQiLCJydW50aW1lX2luc3RhbmNlIiwic291cmNlX3NuYXBzaG90Iiwic2NvcGVkX2xvYWRlZF9jb2RlIiwiY29uZmlndXJhdGlvbl9kaWdlc3QiLCJlbmRwb2ludCIsImNvbm5lY3Rpb25fb3JpZ2luIiwicHJvZmlsZSIsImFjdGl2ZV9wcm9jZXNzX2J1aWxkIiwicnVudGltZV9pZGVudGl0eSIsInJldmlld3MiLCJwcm92aWRlcl9yZWNlaXB0IiwiYXNzZXRzIiwiZXh0ZW5kIiwibW9jayIsImNvbnRleHQiLCJwYWdlIiwidXNlIiwidGVzdEluZm8iLCJfbGF1bmNoJHByb3h5IiwiX2xhdW5jaCRhcmdzIiwibGF1bmNoIiwicHJvamVjdCIsImxhdW5jaE9wdGlvbnMiLCJjb25maWciLCJ3ZWJTZXJ2ZXIiLCJiYXNlVVJMIiwic2VydmljZVdvcmtlcnMiLCJwcm94eSIsInNlcnZlciIsImJ5cGFzcyIsImFyZ3MiLCJpbmNsdWRlcyIsImFic1dvcmtpbmdEaXIiLCJyZXNvbHZlIiwicm9vdERpciIsImVudHJ5UG9pbnRzIiwiYnVuZGxlIiwid3JpdGUiLCJvdXRkaXIiLCJqc3giLCJkZWZpbmUiLCJKU09OIiwic3RyaW5naWZ5IiwidmVyc2lvbiIsImdpdENvbW1pdCIsInRpbWVzdGFtcCIsImVudmlyb25tZW50Iiwic291cmNlSWQiLCJsb2dMZXZlbCIsInMiLCJzbmFwc2hvdFN0YXR1cyIsImludGVudGlvbiIsInJldmlld19pZCIsInN0YXRlIiwiZXhwaXJlc19hdCIsImludGVudGlvblN0YXR1cyIsInBvc3RzIiwiYmxvY2tlZCIsImV4cGVjdGVkQmxvY2tlZCIsInJlcXVlc3RzIiwiZXJyb3JzIiwiY29uc29sZSIsImV4cGVjdGVkQ29uc29sZSIsIm9uIiwiZSIsInB1c2giLCJtZXNzYWdlIiwidHlwZSIsInRleHQiLCJyb3V0ZVdlYlNvY2tldCIsInNvY2tldCIsInVybCIsImNsb3NlIiwicm91dGUiLCJyZXF1ZXN0IiwiVVJMIiwibWV0aG9kIiwic2VhcmNoIiwicGF0aG5hbWUiLCJmdWxmaWxsIiwianNvbiIsImJvZHkiLCJwb3N0RGF0YUpTT04iLCJjdXJyZW50IiwiaXNOYXZpZ2F0aW9uUmVxdWVzdCIsImNvbnRlbnRUeXBlIiwiX2Fzc2V0cyRvdXRwdXRGaWxlcyIsImZpbGUiLCJvdXRwdXRGaWxlcyIsImZpbmQiLCJmIiwiYmFzZW5hbWUiLCJzbGljZSIsImVuZHNXaXRoIiwiQnVmZmVyIiwiZnJvbSIsImNvbnRlbnRzIiwiYWJvcnQiLCJhdHRhY2giLCJsaXZlIiwidG9FcXVhbCIsIm5vQXV0aG9yaXR5IiwibmFtZSIsImdldEJ5Um9sZSIsImV4YWN0IiwidG9IYXZlQ291bnQiLCJyZXZpZXciLCJnb3RvIiwidG9CZURpc2FibGVkIiwiZ2V0QnlMYWJlbCIsImNoZWNrIiwiY2xpY2siLCJ0b0hhdmVVUkwiLCJpZCIsInJlc3VsdCIsImdldEJ5VGV4dCIsInRvQmVWaXNpYmxlIiwiaW5mbyIsInNldFZpZXdwb3J0U2l6ZSIsIndpZHRoIiwiaGVpZ2h0IiwiZXZhbHVhdGUiLCJ3aW5kb3ciLCJzY3JvbGxUbyIsImRvY3VtZW50IiwiZG9jdW1lbnRFbGVtZW50Iiwic2Nyb2xsSGVpZ2h0IiwicG9sbCIsInNjcm9sbFkiLCJ0b0JlR3JlYXRlclRoYW4iLCJ0b0NvbnRhaW5UZXh0IiwidG9IYXZlTGVuZ3RoIiwiZmlyc3QiLCJ2aWV3cG9ydFdpZHRoIiwiaW5uZXJXaWR0aCIsImRvY3VtZW50V2lkdGgiLCJzY3JvbGxXaWR0aCIsImRvY3VtZW50SGVpZ2h0Iiwic2NyZWVuc2hvdCIsIm91dHB1dFBhdGgiLCJmdWxsUGFnZSIsImtpbmQiLCJlcnJvciIsIm5vdCIsInRvQmVDaGVja2VkIiwiZmFpbGVkIiwiZmV0Y2giLCJ0b0JlIl0sInNvdXJjZXMiOlsiYXR0ZXN0YXRpb24uc3BlYy50cyJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQge3Rlc3QgYXMgYmFzZSwgZXhwZWN0LCB0eXBlIFBhZ2V9IGZyb20gJ0BwbGF5d3JpZ2h0L3Rlc3QnO1xuaW1wb3J0IHtidWlsZH0gZnJvbSAnZXNidWlsZCc7XG5pbXBvcnQgcGF0aCBmcm9tICdub2RlOnBhdGgnO1xuXG4vLyBBIHZpcnR1YWwgb3JpZ2luIGZ1bGZpbGxlZCBlbnRpcmVseSB0aHJvdWdoIFBsYXl3cmlnaHQ7IG5vIHRlc3Qgd2ViIHNlcnZlci5cbmNvbnN0IG9yaWdpbiA9ICdodHRwOi8vYXR0ZXN0YXRpb24tZTJlLmludmFsaWQnO1xuaWYocHJvY2Vzcy5lbnYuQ1BMQU5FX0FUVEVTVEFUSU9OX0UyRSAhPT0gJ01PQ0tfT05MWScgfHwgcHJvY2Vzcy5lbnYuQ1BMQU5FX0UyRV9MSVZFKVxuICB0aHJvdyBuZXcgRXJyb3IoJ01PQ0tfT05MWV9NT0RFX1JFUVVJUkVEJyk7XG5jb25zdCBzY29wZSA9ICdSMi1BODpBVFRFU1RBVElPTjpPTkVfR0VORVJBVElPTic7XG5jb25zdCBzbmFwc2hvdCA9ICgpID0+ICh7cHJvamVjdGlvbl9jb250cmFjdDonQVRURVNUQVRJT05fRk9VTkRBVElPTl9WMScsIGV2aWRlbmNlX2lkOidyMi1hOS1hdXRoLXByb2Nlc3MnLFxuICBldmlkZW5jZV90eXBlOidTQ09QRURfSU5fUFJPQ0VTUycsIHNvdXJjZTonU1lOVEhFVElDIEJST1dTRVIgVEVTVCDigJQgTk9UIExJVkUgRVZJREVOQ0UnLCBzY29wZSxcbiAgY3JlYXRlZF9hdDonMjAyNi0xMC0wOFQwMDowMDowMFonLCBzdGF0dXM6J05PVF9WRVJJRklFRCcsIGV2aWRlbmNlX3ZlcnNpb246J2EnLnJlcGVhdCg2NCksXG4gIGxpdmVfYWN0aW9uczonTE9DS0VEJywgb3BlcmF0b3JfcG9saWN5OidOT1RfUFJPVklTSU9ORUQnLCBiaW5kaW5nOntzY29wZSx0YXJnZXQ6JzEyNy4wLjAuMTo4MDAwJyxcbiAgICBwaWQ6MTIzLHByb2Nlc3Nfc3RhcnQ6MTM0MDAwMDAwMDAwMDAwMDAwLHJ1bnRpbWVfaW5zdGFuY2U6J3N5bnRoZXRpYy1pbnN0YW5jZScsc291cmNlX3NuYXBzaG90OidzeW50aGV0aWMtc291cmNlJyxcbiAgICBzY29wZWRfbG9hZGVkX2NvZGU6J3N5bnRoZXRpYy1jb2RlJyxjb25maWd1cmF0aW9uX2RpZ2VzdDonYicucmVwZWF0KDY0KSxcbiAgICBlbmRwb2ludDp7b3JpZ2luOidodHRwOi8vMTI3LjAuMC4xOjExNDM0Jyxjb25uZWN0aW9uX29yaWdpbjonaHR0cDovLzEyNy4wLjAuMToxMTQzNCd9LHByb2ZpbGU6J0FUVEVTVEFUSU9OJyxcbiAgICBhY3RpdmVfcHJvY2Vzc19idWlsZDonTk9UX0RJUkVDVExZX1ZFUklGSUVEJyxydW50aW1lX2lkZW50aXR5OidOT1RfVkVSSUZJRUQnfSxyZXZpZXdzOltdLHByb3ZpZGVyX3JlY2VpcHQ6bnVsbH0pO1xudHlwZSBNb2NrID0ge3NuYXBzaG90OnVua25vd247IHNuYXBzaG90U3RhdHVzOm51bWJlcjsgaW50ZW50aW9uOnVua25vd247IGludGVudGlvblN0YXR1czpudW1iZXI7XG4gIHBvc3RzOnVua25vd25bXTsgYmxvY2tlZDpzdHJpbmdbXTsgZXhwZWN0ZWRCbG9ja2VkOnN0cmluZ1tdOyByZXF1ZXN0czpzdHJpbmdbXTsgZXJyb3JzOnN0cmluZ1tdOyBjb25zb2xlOnN0cmluZ1tdOyBleHBlY3RlZENvbnNvbGU6c3RyaW5nW119O1xubGV0IGFzc2V0czpBd2FpdGVkPFJldHVyblR5cGU8dHlwZW9mIGJ1aWxkPj47XG5jb25zdCB0ZXN0ID0gYmFzZS5leHRlbmQ8e21vY2s6TW9ja30+KHtcbiAgbW9jazphc3luYyAoe2NvbnRleHQscGFnZX0sdXNlLHRlc3RJbmZvKSA9PiB7XG4gICAgY29uc3QgbGF1bmNoID0gdGVzdEluZm8ucHJvamVjdC51c2UubGF1bmNoT3B0aW9ucztcbiAgICBpZihwcm9jZXNzLmVudi5DUExBTkVfQVRURVNUQVRJT05fRTJFICE9PSAnTU9DS19PTkxZJyB8fCB0ZXN0SW5mby5jb25maWcud2ViU2VydmVyIHx8XG4gICAgICB0ZXN0SW5mby5wcm9qZWN0LnVzZS5iYXNlVVJMICE9PSBvcmlnaW4gfHwgdGVzdEluZm8ucHJvamVjdC51c2Uuc2VydmljZVdvcmtlcnMgIT09ICdibG9jaycgfHxcbiAgICAgIGxhdW5jaD8ucHJveHk/LnNlcnZlciAhPT0gJ2h0dHA6Ly8xMjcuMC4wLjE6OScgfHwgbGF1bmNoLnByb3h5LmJ5cGFzcyAhPT0gJzwtbG9vcGJhY2s+JyB8fFxuICAgICAgIWxhdW5jaC5hcmdzPy5pbmNsdWRlcygnLS1ob3N0LXJlc29sdmVyLXJ1bGVzPU1BUCAqIH5OT1RGT1VORCcpKSB0aHJvdyBuZXcgRXJyb3IoJ1VOU0FGRV9URVNUX0NPTkZJR1VSQVRJT04nKTtcbiAgICBhc3NldHMgPz89IGF3YWl0IGJ1aWxkKHthYnNXb3JraW5nRGlyOnBhdGgucmVzb2x2ZSh0ZXN0SW5mby5jb25maWcucm9vdERpciwnLi4nKSxcbiAgICAgIGVudHJ5UG9pbnRzOlsnc3JjL21haW4udHN4J10sYnVuZGxlOnRydWUsd3JpdGU6ZmFsc2Usb3V0ZGlyOid2aXJ0dWFsJyxqc3g6J2F1dG9tYXRpYycsXG4gICAgICBkZWZpbmU6eydwcm9jZXNzLmVudi5OT0RFX0VOVic6J1wicHJvZHVjdGlvblwiJywnX19DUExBTkVfQlVJTERfXyc6SlNPTi5zdHJpbmdpZnkoe3ZlcnNpb246J1NZTlRIRVRJQycsXG4gICAgICAgIGdpdENvbW1pdDonTk9UX1ZFUklGSUVEJyx0aW1lc3RhbXA6JzIwMjYtMTAtMDhUMDA6MDA6MDBaJyxlbnZpcm9ubWVudDonTU9DS19PTkxZJyxzb3VyY2VJZDonTk9UX0xJVkVfRVZJREVOQ0UnfSl9LGxvZ0xldmVsOidzaWxlbnQnfSk7XG4gICAgY29uc3QgcyA9IHNuYXBzaG90KCk7XG4gICAgY29uc3QgbW9jazpNb2NrID0ge3NuYXBzaG90OnMsc25hcHNob3RTdGF0dXM6MjAwLGludGVudGlvbjp7cmV2aWV3X2lkOidzeW50aGV0aWMtcmV2aWV3JyxzY29wZSxcbiAgICAgIGV2aWRlbmNlX3ZlcnNpb246cy5ldmlkZW5jZV92ZXJzaW9uLHN0YXRlOidQRU5ESU5HJyxleHBpcmVzX2F0OicyMDI2LTEwLTA4VDAwOjAyOjAwWid9LFxuICAgICAgaW50ZW50aW9uU3RhdHVzOjIwMCxwb3N0czpbXSxibG9ja2VkOltdLGV4cGVjdGVkQmxvY2tlZDpbXSxyZXF1ZXN0czpbXSxlcnJvcnM6W10sY29uc29sZTpbXSxleHBlY3RlZENvbnNvbGU6W119O1xuICAgIHBhZ2Uub24oJ3BhZ2VlcnJvcicsZT0+bW9jay5lcnJvcnMucHVzaChlLm1lc3NhZ2UpKTtcbiAgICBwYWdlLm9uKCdjb25zb2xlJyxtZXNzYWdlPT57aWYobWVzc2FnZS50eXBlKCk9PT0nZXJyb3InKW1vY2suY29uc29sZS5wdXNoKG1lc3NhZ2UudGV4dCgpKTt9KTtcbiAgICBhd2FpdCBjb250ZXh0LnJvdXRlV2ViU29ja2V0KC8uKi8sc29ja2V0PT57bW9jay5ibG9ja2VkLnB1c2goJ1dFQlNPQ0tFVCAnK3NvY2tldC51cmwoKSk7c29ja2V0LmNsb3NlKCk7fSk7XG4gICAgYXdhaXQgY29udGV4dC5yb3V0ZSgnKiovKicsYXN5bmMgcm91dGU9PntcbiAgICAgIGNvbnN0IHJlcXVlc3Q9cm91dGUucmVxdWVzdCgpLHVybD1uZXcgVVJMKHJlcXVlc3QudXJsKCkpLG1ldGhvZD1yZXF1ZXN0Lm1ldGhvZCgpO1xuICAgICAgbW9jay5yZXF1ZXN0cy5wdXNoKG1ldGhvZCsnICcrcmVxdWVzdC51cmwoKSk7XG4gICAgICBpZih1cmwub3JpZ2luPT09b3JpZ2luICYmICF1cmwuc2VhcmNoKXtcbiAgICAgICAgaWYodXJsLnBhdGhuYW1lPT09Jy92MS9jb250cm9sLXBsYW5lL3NuYXBzaG90JyAmJiBtZXRob2Q9PT0nR0VUJyl7XG4gICAgICAgICAgYXdhaXQgcm91dGUuZnVsZmlsbCh7c3RhdHVzOm1vY2suc25hcHNob3RTdGF0dXMsanNvbjptb2NrLnNuYXBzaG90fSk7cmV0dXJuO1xuICAgICAgICB9XG4gICAgICAgIGlmKHVybC5wYXRobmFtZT09PScvdjEvY29udHJvbC1wbGFuZS9pbnRlbnRpb24nICYmIG1ldGhvZD09PSdQT1NUJyl7XG4gICAgICAgICAgY29uc3QgYm9keT1yZXF1ZXN0LnBvc3REYXRhSlNPTigpO1xuICAgICAgICAgIGNvbnN0IGN1cnJlbnQ9bW9jay5zbmFwc2hvdCBhcyBSZXR1cm5UeXBlPHR5cGVvZiBzbmFwc2hvdD47XG4gICAgICAgICAgaWYoSlNPTi5zdHJpbmdpZnkoYm9keSk9PT1KU09OLnN0cmluZ2lmeSh7c2NvcGU6Y3VycmVudC5zY29wZSxldmlkZW5jZV92ZXJzaW9uOmN1cnJlbnQuZXZpZGVuY2VfdmVyc2lvbn0pKXtcbiAgICAgICAgICAgIG1vY2sucG9zdHMucHVzaChib2R5KTthd2FpdCByb3V0ZS5mdWxmaWxsKHtzdGF0dXM6bW9jay5pbnRlbnRpb25TdGF0dXMsanNvbjptb2NrLmludGVudGlvbn0pO3JldHVybjtcbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgICAgaWYobWV0aG9kPT09J0dFVCcgJiYgWycvb3ZlcnZpZXcnLCcvZXZpZGVuY2UnLCcvdGVzdCcsJy9yZXZpZXcnLCcvZGVjaXNpb24nXS5pbmNsdWRlcyh1cmwucGF0aG5hbWUpICYmIHJlcXVlc3QuaXNOYXZpZ2F0aW9uUmVxdWVzdCgpKXtcbiAgICAgICAgICBhd2FpdCByb3V0ZS5mdWxmaWxsKHtjb250ZW50VHlwZTondGV4dC9odG1sJyxib2R5Oic8IWRvY3R5cGUgaHRtbD48aHRtbD48aGVhZD48bWV0YSBjaGFyc2V0PVwidXRmLThcIj48bWV0YSBuYW1lPVwidmlld3BvcnRcIiBjb250ZW50PVwid2lkdGg9ZGV2aWNlLXdpZHRoXCI+PGxpbmsgcmVsPVwiaWNvblwiIGhyZWY9XCJkYXRhOixcIj48bGluayByZWw9XCJzdHlsZXNoZWV0XCIgaHJlZj1cIi9tYWluLmNzc1wiPjwvaGVhZD48Ym9keT48ZGl2IGlkPVwicm9vdFwiPjwvZGl2PjxzY3JpcHQgc3JjPVwiL21haW4uanNcIj48L3NjcmlwdD48L2JvZHk+PC9odG1sPid9KTtyZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgaWYobWV0aG9kPT09J0dFVCcgJiYgWycvbWFpbi5qcycsJy9tYWluLmNzcyddLmluY2x1ZGVzKHVybC5wYXRobmFtZSkpe1xuICAgICAgICAgIGNvbnN0IGZpbGU9YXNzZXRzLm91dHB1dEZpbGVzPy5maW5kKGY9PnBhdGguYmFzZW5hbWUoZi5wYXRoKT09PXVybC5wYXRobmFtZS5zbGljZSgxKSk7XG4gICAgICAgICAgaWYoZmlsZSl7YXdhaXQgcm91dGUuZnVsZmlsbCh7Y29udGVudFR5cGU6dXJsLnBhdGhuYW1lLmVuZHNXaXRoKCcuanMnKT8ndGV4dC9qYXZhc2NyaXB0JzondGV4dC9jc3MnLGJvZHk6QnVmZmVyLmZyb20oZmlsZS5jb250ZW50cyl9KTtyZXR1cm47fVxuICAgICAgICB9XG4gICAgICB9XG4gICAgICBtb2NrLmJsb2NrZWQucHVzaChtZXRob2QrJyAnK3JlcXVlc3QudXJsKCkpO2F3YWl0IHJvdXRlLmFib3J0KCdibG9ja2VkYnljbGllbnQnKTtcbiAgICB9KTtcbiAgICBhd2FpdCB1c2UobW9jayk7XG4gICAgYXdhaXQgdGVzdEluZm8uYXR0YWNoKCdtb2NrLW5ldHdvcmstZXZpZGVuY2UnLHtib2R5OkpTT04uc3RyaW5naWZ5KHsuLi5tb2NrLGxpdmU6ZmFsc2V9KSxjb250ZW50VHlwZTonYXBwbGljYXRpb24vanNvbid9KTtcbiAgICBleHBlY3QobW9jay5ibG9ja2VkLCd1bmV4cGVjdGVkIG5ldHdvcmsgcmVxdWVzdCcpLnRvRXF1YWwobW9jay5leHBlY3RlZEJsb2NrZWQpO1xuICAgIGV4cGVjdChtb2NrLmVycm9ycywnYnJvd3NlciBydW50aW1lIGVycm9ycycpLnRvRXF1YWwoW10pO1xuICAgIGV4cGVjdChtb2NrLmNvbnNvbGUsJ3VuZXhwZWN0ZWQgYnJvd3NlciBjb25zb2xlIGVycm9yJykudG9FcXVhbChtb2NrLmV4cGVjdGVkQ29uc29sZSk7XG4gIH0sXG59KTtcbmFzeW5jIGZ1bmN0aW9uIG5vQXV0aG9yaXR5KHBhZ2U6UGFnZSl7XG4gIGZvcihjb25zdCBuYW1lIG9mIFsnQVBQUk9WRScsJ0FSTScsJ0VYRUNVVEUnLCdDT05GSVJNIEFQUFJPVkFMJ10pXG4gICAgYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lLGV4YWN0OnRydWV9KSkudG9IYXZlQ291bnQoMCk7XG59XG5hc3luYyBmdW5jdGlvbiByZXZpZXcocGFnZTpQYWdlLG1vY2s6TW9jayl7XG4gIGF3YWl0IHBhZ2UuZ290bygnL292ZXJ2aWV3Jyk7YXdhaXQgbm9BdXRob3JpdHkocGFnZSk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ29udGludWUgdG8gRXZpZGVuY2UnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlMYWJlbCgnSSBoYXZlIHJlYWQgdGhlIEFUVEVTVEFUSU9OIHNjb3BlIGFuZCBsaW1pdGF0aW9ucy4nKS5jaGVjaygpO1xuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ29udGludWUgdG8gRXZpZGVuY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZSkudG9IYXZlVVJMKG9yaWdpbisnL2V2aWRlbmNlJyk7YXdhaXQgbm9BdXRob3JpdHkocGFnZSk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlMYWJlbCgnSSBpbnNwZWN0ZWQgdGhlIGV4YWN0IGV2aWRlbmNlIHZlcnNpb24gYW5kIGlkZW50aXR5IHNjb3BlLicpLmNoZWNrKCk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidDb250aW51ZSB0byBIdW1hbiBUZXN0JyxleGFjdDp0cnVlfSkuY2xpY2soKTtcbiAgYXdhaXQgZXhwZWN0KHBhZ2UpLnRvSGF2ZVVSTChvcmlnaW4rJy90ZXN0Jyk7YXdhaXQgbm9BdXRob3JpdHkocGFnZSk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ29udGludWUgdG8gUmV2aWV3JyxleGFjdDp0cnVlfSkpLnRvQmVEaXNhYmxlZCgpO1xuICBmb3IoY29uc3QgW2lkLHJlc3VsdF0gb2YgW1sncnVudGltZScsJ1BBU1MnXSxbJ3NlcGFyYXRlJywnRkFJTCddLFsnYm91bmRhcnknLCdCTE9DS0VEJ11dKVxuICAgIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdncm91cCcse25hbWU6J09ic2VydmF0aW9uICcraWR9KS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6cmVzdWx0LGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ29udGludWUgdG8gUmV2aWV3JyxleGFjdDp0cnVlfSkuY2xpY2soKTtcbiAgYXdhaXQgZXhwZWN0KHBhZ2UpLnRvSGF2ZVVSTChvcmlnaW4rJy9yZXZpZXcnKTthd2FpdCBub0F1dGhvcml0eShwYWdlKTtcbiAgYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlUZXh0KCdzZXBhcmF0ZTogRkFJTCcse2V4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTtcbiAgYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlUZXh0KCdib3VuZGFyeTogQkxPQ0tFRCcse2V4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTtcbiAgYXdhaXQgcGFnZS5nZXRCeUxhYmVsKCdJIHJldmlld2VkIHRoZXNlIG9ic2VydmF0aW9ucyBhbmQgdGhlIE5PVF9WRVJJRklFRCBsaW1pdGF0aW9ucy4nKS5jaGVjaygpO1xuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ29udGludWUgdG8gRGVjaXNpb24nLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZSkudG9IYXZlVVJMKG9yaWdpbisnL2RlY2lzaW9uJyk7YXdhaXQgbm9BdXRob3JpdHkocGFnZSk7ZXhwZWN0KG1vY2sucG9zdHMpLnRvRXF1YWwoW10pO1xufVxudGVzdCgnZml2ZSBzdGFnZXMgcmVuZGVyLCBzY3JvbGwgYW5kIHN1Ym1pdCBvbmx5IGV4cGxpY2l0IFBFTkRJTkcgaW50ZW50aW9uJyxhc3luYyh7cGFnZSxtb2NrfSxpbmZvKT0+e1xuICBhd2FpdCBwYWdlLnNldFZpZXdwb3J0U2l6ZSh7d2lkdGg6MzkwLGhlaWdodDo2NDB9KTthd2FpdCByZXZpZXcocGFnZSxtb2NrKTtcbiAgYXdhaXQgcGFnZS5ldmFsdWF0ZSgoKT0+d2luZG93LnNjcm9sbFRvKDAsZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50LnNjcm9sbEhlaWdodCkpO1xuICBhd2FpdCBleHBlY3QucG9sbCgoKT0+cGFnZS5ldmFsdWF0ZSgoKT0+d2luZG93LnNjcm9sbFkpKS50b0JlR3JlYXRlclRoYW4oMCk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidDcmVhdGUgUEVORElORyBpbnRlbnRpb24nLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ3N0YXR1cycpKS50b0NvbnRhaW5UZXh0KCdQRU5ESU5HIOKAlCB1bnRydXN0ZWQgaW50ZW50aW9uOyBubyBhdXRob3JpemF0aW9uIGdyYW50ZWQuJyk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ3JlYXRlIFBFTkRJTkcgaW50ZW50aW9uJyxleGFjdDp0cnVlfSkpLnRvQmVEaXNhYmxlZCgpO1xuICBleHBlY3QobW9jay5wb3N0cykudG9IYXZlTGVuZ3RoKDEpO2F3YWl0IG5vQXV0aG9yaXR5KHBhZ2UpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQoJ05PVF9WRVJJRklFRCcse2V4YWN0OnRydWV9KS5maXJzdCgpKS50b0JlVmlzaWJsZSgpO1xuICBhd2FpdCBpbmZvLmF0dGFjaCgncmVuZGVyaW5nLW1ldHJpY3MnLHtib2R5OkpTT04uc3RyaW5naWZ5KGF3YWl0IHBhZ2UuZXZhbHVhdGUoKCk9Pih7dmlld3BvcnRXaWR0aDppbm5lcldpZHRoLFxuICAgIGRvY3VtZW50V2lkdGg6ZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50LnNjcm9sbFdpZHRoLHNjcm9sbFksZG9jdW1lbnRIZWlnaHQ6ZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50LnNjcm9sbEhlaWdodH0pKSksY29udGVudFR5cGU6J2FwcGxpY2F0aW9uL2pzb24nfSk7XG4gIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDppbmZvLm91dHB1dFBhdGgoJ3BlbmRpbmctbW9iaWxlLnBuZycpLGZ1bGxQYWdlOnRydWV9KTtcbn0pO1xuZm9yKGNvbnN0IHBhdGggb2YgWycvZXZpZGVuY2UnLCcvdGVzdCcsJy9yZXZpZXcnLCcvZGVjaXNpb24nXSl0ZXN0KCdkaXJlY3QgJytwYXRoKycgY2Fubm90IGJ5cGFzcyByZXZpZXcnLGFzeW5jKHtwYWdlLG1vY2t9KT0+e1xuICBhd2FpdCBwYWdlLmdvdG8ocGF0aCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdyZWdpb24nLHtuYW1lOidMb2NrZWQgc3RhZ2UnfSkpLnRvQmVWaXNpYmxlKCk7XG4gIGF3YWl0IG5vQXV0aG9yaXR5KHBhZ2UpO2V4cGVjdChtb2NrLnBvc3RzKS50b0VxdWFsKFtdKTtcbn0pO1xuZm9yKGNvbnN0IGtpbmQgb2YgWydBUEkgZmFpbHVyZScsJ21hbGZvcm1lZCBzbmFwc2hvdCddKXRlc3Qoa2luZCsnIHJlbWFpbnMgdW5hdmFpbGFibGUnLGFzeW5jKHtwYWdlLG1vY2t9KT0+e1xuICBtb2NrLnNuYXBzaG90U3RhdHVzPWtpbmQ9PT0nQVBJIGZhaWx1cmUnPzUwMzoyMDA7bW9jay5zbmFwc2hvdD1raW5kPT09J0FQSSBmYWlsdXJlJz97ZXJyb3I6J3N5bnRoZXRpYy11bmF2YWlsYWJsZSd9OntzdGF0dXM6J1BBU1MnfTtcbiAgaWYoa2luZD09PSdBUEkgZmFpbHVyZScpbW9jay5leHBlY3RlZENvbnNvbGU9WydGYWlsZWQgdG8gbG9hZCByZXNvdXJjZTogdGhlIHNlcnZlciByZXNwb25kZWQgd2l0aCBhIHN0YXR1cyBvZiA1MDMgKFNlcnZpY2UgVW5hdmFpbGFibGUpJ107XG4gIGF3YWl0IHBhZ2UuZ290bygnL2RlY2lzaW9uJyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdhbGVydCcpKS50b0NvbnRhaW5UZXh0KCdVTktOT1dOJyk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYWxlcnQnKSkudG9Db250YWluVGV4dCgnTm8gaGVhbHRoeSBzdGF0ZSBoYXMgYmVlbiBpbmZlcnJlZCcpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0NyZWF0ZSBQRU5ESU5HIGludGVudGlvbicsZXhhY3Q6dHJ1ZX0pKS50b0hhdmVDb3VudCgwKTthd2FpdCBub0F1dGhvcml0eShwYWdlKTtcbn0pO1xuZm9yKGNvbnN0IGtpbmQgb2YgWydBUEkgcmVqZWN0aW9uJywnaW52ZW50ZWQgYXV0aG9yaXR5Jywnd3JvbmcgZXZpZGVuY2UnXSl0ZXN0KGtpbmQrJyBpbnRlbnRpb24gZmFpbHMgY2xvc2VkIHdpdGhvdXQgYXV0b21hdGljIHJldHJ5Jyxhc3luYyh7cGFnZSxtb2NrfSk9PntcbiAgYXdhaXQgcmV2aWV3KHBhZ2UsbW9jayk7XG4gIGlmKGtpbmQ9PT0nQVBJIHJlamVjdGlvbicpe1xuICAgIG1vY2suaW50ZW50aW9uU3RhdHVzPTQwOTtcbiAgICBtb2NrLmV4cGVjdGVkQ29uc29sZT1bJ0ZhaWxlZCB0byBsb2FkIHJlc291cmNlOiB0aGUgc2VydmVyIHJlc3BvbmRlZCB3aXRoIGEgc3RhdHVzIG9mIDQwOSAoQ29uZmxpY3QpJ107XG4gIH1cbiAgZWxzZSBtb2NrLmludGVudGlvbj17Li4uKG1vY2suaW50ZW50aW9uIGFzIG9iamVjdCksLi4uKGtpbmQ9PT0naW52ZW50ZWQgYXV0aG9yaXR5Jz97c3RhdGU6J0FQUFJPVkVEJ306e2V2aWRlbmNlX3ZlcnNpb246J2MnLnJlcGVhdCg2NCl9KX07XG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidDcmVhdGUgUEVORElORyBpbnRlbnRpb24nLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2FsZXJ0JykpLnRvQmVWaXNpYmxlKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdzdGF0dXMnKSkudG9IYXZlQ291bnQoMCk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ3JlYXRlIFBFTkRJTkcgaW50ZW50aW9uJyxleGFjdDp0cnVlfSkpLnRvQmVEaXNhYmxlZCgpO1xuICBleHBlY3QobW9jay5wb3N0cykudG9IYXZlTGVuZ3RoKDEpO2F3YWl0IG5vQXV0aG9yaXR5KHBhZ2UpO1xufSk7XG50ZXN0KCdtYXRlcmlhbCBjb250ZXh0IGNoYW5nZSBjbGVhcnMgcGVuZGluZyBhbmQgcmVsb2NrcyB0aGUgc2Vzc2lvbicsYXN5bmMoe3BhZ2UsbW9ja30pPT57XG4gIGF3YWl0IHJldmlldyhwYWdlLG1vY2spO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidDcmVhdGUgUEVORElORyBpbnRlbnRpb24nLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ3N0YXR1cycpKS50b0NvbnRhaW5UZXh0KCdQRU5ESU5HIOKAlCB1bnRydXN0ZWQgaW50ZW50aW9uJyk7XG4gIGNvbnN0IHM9bW9jay5zbmFwc2hvdCBhcyBSZXR1cm5UeXBlPHR5cGVvZiBzbmFwc2hvdD47XG4gIG1vY2suc25hcHNob3Q9ey4uLnMsZXZpZGVuY2VfdmVyc2lvbjonYycucmVwZWF0KDY0KSxiaW5kaW5nOnsuLi5zLmJpbmRpbmcscnVudGltZV9pbnN0YW5jZTonc3ludGhldGljLW5ldy1pbnN0YW5jZSd9fTtcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1JlZnJlc2ggZXZpZGVuY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ3JlZ2lvbicse25hbWU6J0xvY2tlZCBzdGFnZSd9KSkudG9CZVZpc2libGUoKTtcbiAgYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdzdGF0dXMnKSkudG9IYXZlQ291bnQoMCk7ZXhwZWN0KG1vY2sucG9zdHMpLnRvSGF2ZUxlbmd0aCgxKTtcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0dvIHRvIFN5c3RlbScsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5TGFiZWwoJ0kgaGF2ZSByZWFkIHRoZSBBVFRFU1RBVElPTiBzY29wZSBhbmQgbGltaXRhdGlvbnMuJykpLm5vdC50b0JlQ2hlY2tlZCgpO2F3YWl0IG5vQXV0aG9yaXR5KHBhZ2UpO1xufSk7XG50ZXN0KCduZXR3b3JrIGJvdW5kYXJ5IGFib3J0cyBhbiB1bmxpc3RlZCB2aXJ0dWFsLW9yaWdpbiByZXF1ZXN0Jyxhc3luYyh7cGFnZSxtb2NrfSk9PntcbiAgYXdhaXQgcGFnZS5nb3RvKCcvb3ZlcnZpZXcnKTtcbiAgbW9jay5leHBlY3RlZEJsb2NrZWQ9WydHRVQgJytvcmlnaW4rJy91bmxpc3RlZC1ib3VuZGFyeS10ZXN0J107XG4gIG1vY2suZXhwZWN0ZWRDb25zb2xlPVsnRmFpbGVkIHRvIGxvYWQgcmVzb3VyY2U6IG5ldDo6RVJSX0JMT0NLRURfQllfQ0xJRU5ULkluc3BlY3RvciddO1xuICBjb25zdCBmYWlsZWQ9YXdhaXQgcGFnZS5ldmFsdWF0ZShhc3luYygpPT57dHJ5e2F3YWl0IGZldGNoKCcvdW5saXN0ZWQtYm91bmRhcnktdGVzdCcpO3JldHVybiBmYWxzZTt9Y2F0Y2h7cmV0dXJuIHRydWU7fX0pO1xuICBleHBlY3QoZmFpbGVkKS50b0JlKHRydWUpO2V4cGVjdChtb2NrLmJsb2NrZWQpLnRvRXF1YWwobW9jay5leHBlY3RlZEJsb2NrZWQpO2V4cGVjdChtb2NrLnBvc3RzKS50b0VxdWFsKFtdKTtcbn0pO1xuIl0sIm1hcHBpbmdzIjoiQUFBQSxTQUFRQSxJQUFJLElBQUlDLElBQUksRUFBRUMsTUFBTSxRQUFrQixrQkFBa0I7QUFDaEUsU0FBUUMsS0FBSyxRQUFPLFNBQVM7QUFDN0IsT0FBT0MsSUFBSSxNQUFNLFdBQVc7O0FBRTVCO0FBQ0EsTUFBTUMsTUFBTSxHQUFHLGdDQUFnQztBQUMvQyxJQUFHQyxPQUFPLENBQUNDLEdBQUcsQ0FBQ0Msc0JBQXNCLEtBQUssV0FBVyxJQUFJRixPQUFPLENBQUNDLEdBQUcsQ0FBQ0UsZUFBZSxFQUNsRixNQUFNLElBQUlDLEtBQUssQ0FBQyx5QkFBeUIsQ0FBQztBQUM1QyxNQUFNQyxLQUFLLEdBQUcsa0NBQWtDO0FBQ2hELE1BQU1DLFFBQVEsR0FBR0EsQ0FBQSxNQUFPO0VBQUNDLG1CQUFtQixFQUFDLDJCQUEyQjtFQUFFQyxXQUFXLEVBQUMsb0JBQW9CO0VBQ3hHQyxhQUFhLEVBQUMsbUJBQW1CO0VBQUVDLE1BQU0sRUFBQyw0Q0FBNEM7RUFBRUwsS0FBSztFQUM3Rk0sVUFBVSxFQUFDLHNCQUFzQjtFQUFFQyxNQUFNLEVBQUMsY0FBYztFQUFFQyxnQkFBZ0IsRUFBQyxHQUFHLENBQUNDLE1BQU0sQ0FBQyxFQUFFLENBQUM7RUFDekZDLFlBQVksRUFBQyxRQUFRO0VBQUVDLGVBQWUsRUFBQyxpQkFBaUI7RUFBRUMsT0FBTyxFQUFDO0lBQUNaLEtBQUs7SUFBQ2EsTUFBTSxFQUFDLGdCQUFnQjtJQUM5RkMsR0FBRyxFQUFD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