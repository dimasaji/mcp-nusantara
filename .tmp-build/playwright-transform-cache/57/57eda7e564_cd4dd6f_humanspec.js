// 59962d454254349342d110fd1426a2151fffa675
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
const fixture = () => JSON.parse(fs.readFileSync(process.env.CPLANE_SNAPSHOT_FILE, 'utf8'));
const reviewAck = 'I have reviewed the evidence, all human test results and unresolved limitations.';
async function start(page) {
  await page.goto('/overview');
  await page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  }).check();
  await page.getByRole('button', {
    name: /Continue to Evidence/
  }).click();
}
async function inspect(page, count = 14) {
  for (let i = 1; i <= count; i++) {
    await page.locator('details.gate-card').filter({
      has: page.locator('summary strong', {
        hasText: new RegExp('^R3\\.' + i + '$')
      })
    }).locator('summary').click();
    const button = page.getByRole('button', {
      name: 'I have inspected R3.' + i + ' source',
      exact: true
    });
    if (await button.isEnabled()) await button.click();
  }
}
async function evidence(page) {
  await start(page);
  await inspect(page);
  await page.getByRole('checkbox', {
    name: 'I have inspected all gate sources and read their limitations.'
  }).check();
  await page.getByRole('button', {
    name: /Continue to Human Test/
  }).click();
}
async function tests(page, result = '✓ PASS') {
  for (const group of await page.getByRole('group', {
    name: /^Result for /
  }).all()) await group.getByRole('button', {
    name: result,
    exact: true
  }).click();
  await page.getByRole('button', {
    name: /Review human results/
  }).click();
}
async function review(page) {
  await page.getByRole('checkbox', {
    name: reviewAck
  }).check();
  await page.getByRole('button', {
    name: /Continue to Decision/
  }).click();
}
for (const path of ['/evidence', '/test', '/review', '/decision']) test('direct ' + path + ' is locked without upstream completion', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await page.goto(path);
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toContainText('Acknowledge the System');
  await expect(page.getByRole('button', {
    name: 'APPROVE',
    exact: true
  })).toHaveCount(0);
  await expect(page.getByRole('list', {
    name: 'Human acceptance progress'
  })).toContainText('Locked');
  await page.getByRole('button', {
    name: 'Go to System →'
  }).click();
  await expect(page.getByRole('heading', {
    name: 'System',
    exact: true
  })).toBeVisible();
});
test('all five transitions require explicit completion and confirmation; no backend mutation', async ({
  page
}) => {
  if (process.env.CPLANE_E2E_LIVE !== '1') await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  const mutations = [];
  const errors = [];
  page.on('request', r => {
    if (r.url().includes('/v1/') && r.method() !== 'GET') mutations.push(r.method());
  });
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/overview');
  if (process.env.CPLANE_HUMAN_SCREENSHOT) await page.screenshot({
    path: process.env.CPLANE_HUMAN_SCREENSHOT.replace('mobile', 'desktop'),
    fullPage: true
  });
  await expect(page.getByRole('button', {
    name: 'Evidence Locked',
    exact: true
  })).toBeDisabled();
  await expect(page.getByRole('button', {
    name: /Continue to Evidence/
  })).toBeDisabled();
  await expect(page.getByRole('button', {
    name: /Open Human Decision/
  })).toBeDisabled();
  await page.getByRole('button', {
    name: /Inspect runtime evidence/
  }).click();
  await expect(page.getByRole('heading', {
    name: 'Runtime',
    exact: true
  })).toBeVisible();
  await page.getByRole('link', {
    name: 'System',
    exact: true
  }).click();
  await page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  }).check();
  await expect(page.getByRole('list', {
    name: 'Human acceptance progress'
  })).toContainText('Available');
  await page.getByRole('button', {
    name: /Continue to Evidence/
  }).click();
  await expect(page.getByRole('list', {
    name: 'Human acceptance progress'
  })).toContainText('Completed');
  await inspect(page, 13);
  const evidenceAck = page.getByRole('checkbox', {
    name: 'I have inspected all gate sources and read their limitations.'
  });
  await expect(evidenceAck).toBeDisabled();
  await expect(page.getByRole('button', {
    name: 'Human Test Locked',
    exact: true
  })).toBeDisabled();
  await page.locator('details.gate-card').filter({
    has: page.locator('summary strong', {
      hasText: 'R3.14'
    })
  }).locator('summary').click();
  await page.getByRole('button', {
    name: 'I have inspected R3.14 source',
    exact: true
  }).click();
  await expect(evidenceAck).toBeEnabled();
  await expect(evidenceAck).not.toBeChecked();
  await expect(page.getByRole('button', {
    name: /Continue to Human Test/
  })).toBeDisabled();
  await evidenceAck.check();
  await page.getByRole('button', {
    name: /Continue to Human Test/
  }).click();
  await expect(page.getByText('○ NOT TESTED', {
    exact: true
  })).toHaveCount(8);
  const groups = await page.getByRole('group', {
    name: /^Result for /
  }).all();
  for (const group of groups.slice(0, 7)) await group.getByRole('button', {
    name: '✓ PASS',
    exact: true
  }).click();
  await expect(page.getByRole('button', {
    name: /Review human results/
  })).toBeDisabled();
  await expect(page.getByRole('button', {
    name: 'Review Locked',
    exact: true
  })).toBeDisabled();
  await groups[7].getByRole('button', {
    name: '✓ PASS',
    exact: true
  }).click();
  await page.getByRole('link', {
    name: /N NUSANTARA HUMAN ACCEPTANCE CONSOLE/
  }).click();
  await page.getByRole('link', {
    name: 'Human Test',
    exact: true
  }).click();
  await expect(page.getByRole('group', {
    name: 'Result for open'
  }).getByRole('button', {
    name: '✓ PASS',
    exact: true
  })).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', {
    name: /Review human results/
  }).click();
  await expect(page.getByRole('heading', {
    name: 'Known limitations',
    exact: true
  })).toBeVisible();
  await expect(page.getByText('○ NOT VERIFIED', {
    exact: true
  })).toBeVisible();
  await expect(page.getByRole('button', {
    name: 'Decision Locked',
    exact: true
  })).toBeDisabled();
  await expect(page.getByRole('checkbox', {
    name: reviewAck
  })).not.toBeChecked();
  await expect(page.getByRole('button', {
    name: /Continue to Decision/
  })).toBeDisabled();
  await review(page);
  await expect(page.getByRole('button', {
    name: 'PASS',
    exact: true
  })).toBeDisabled();
  await expect(page.getByRole('button', {
    name: 'FAIL',
    exact: true
  })).toBeDisabled();
  await expect(page.getByRole('button', {
    name: 'HOLD',
    exact: true
  })).toBeDisabled();
  await page.getByRole('button', {
    name: 'Refresh evidence',
    exact: true
  }).click();
  await expect(page.getByRole('button', {
    name: 'PASS',
    exact: true
  })).toBeDisabled();
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
  await page.reload();
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toContainText('Acknowledge the System');
});
// Obsolete: this case exercised the retired session-only decision UI (APPROVE/REJECT with a
// mandatory reason). The current decision step is server-bound and operator-token gated; its
// coverage lives in control-plane/tests/human.test.tsx and the /review-execute page tests.
for (const decision of ['REJECT', 'HOLD']) test.fixme(decision + ' follows review of explicit FAIL/BLOCKED and requires a reason', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await evidence(page);
  await tests(page, decision === 'REJECT' ? '✕ FAIL' : '! BLOCKED');
  await review(page);
  await expect(page.getByRole('button', {
    name: 'APPROVE',
    exact: true
  })).toBeDisabled();
  await page.getByRole('button', {
    name: decision,
    exact: true
  }).click();
  const save = page.getByRole('button', {
    name: decision === 'REJECT' ? 'Confirm Rejection' : 'Save HOLD',
    exact: true
  });
  await expect(save).toBeDisabled();
  await page.getByRole('radio', {
    name: 'Other',
    exact: true
  }).check();
  await expect(save).toBeDisabled();
  await page.getByRole('textbox', {
    name: 'Notes (required)'
  }).fill('Need human review');
  await save.click();
  await expect(page.getByText('Human decision recorded in this session', {
    exact: true
  })).toBeVisible();
  await expect(page.getByText('○ NOT VERIFIED', {
    exact: true
  })).toBeVisible();
});
test('withdrawing Evidence acknowledgement relocks Test Review Decision', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await evidence(page);
  await tests(page);
  await review(page);
  await page.getByRole('link', {
    name: 'Evidence',
    exact: true
  }).click();
  await page.getByRole('checkbox', {
    name: 'I have inspected all gate sources and read their limitations.'
  }).uncheck();
  for (const name of ['Human Test', 'Review', 'Decision']) await expect(page.getByRole('button', {
    name: name + ' Locked',
    exact: true
  })).toBeDisabled();
});
test('changing and clearing results invalidates Review acknowledgement and locks downstream', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await evidence(page);
  await tests(page);
  await review(page);
  await page.getByRole('link', {
    name: 'Human Test',
    exact: true
  }).click();
  const group = page.getByRole('group', {
    name: 'Result for open'
  });
  await group.getByRole('button', {
    name: '✕ FAIL',
    exact: true
  }).click();
  await expect(page.getByRole('button', {
    name: 'Decision Locked',
    exact: true
  })).toBeDisabled();
  await page.getByRole('link', {
    name: 'Review',
    exact: true
  }).click();
  await expect(page.getByRole('checkbox', {
    name: reviewAck
  })).not.toBeChecked();
  await page.getByRole('link', {
    name: 'Human Test',
    exact: true
  }).click();
  await group.getByRole('button', {
    name: 'Clear result',
    exact: true
  }).click();
  await expect(page.getByRole('button', {
    name: 'Review Locked',
    exact: true
  })).toBeDisabled();
});
test('withdrawing System acknowledgement relocks every downstream stage', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await evidence(page);
  await tests(page);
  await review(page);
  await page.getByRole('link', {
    name: 'System',
    exact: true
  }).click();
  await page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  }).uncheck();
  for (const name of ['Evidence', 'Human Test', 'Review', 'Decision']) await expect(page.getByRole('button', {
    name: name + ' Locked',
    exact: true
  })).toBeDisabled();
});
test('missing evidence source cannot unlock Test', async ({
  page
}) => {
  const s = fixture();
  s.gates.find(g => g.id === 'R3.1').evidence = ['missing'];
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: s
  }));
  await start(page);
  await inspect(page);
  await expect(page.getByText(/13 of 14 gates inspected/)).toBeVisible();
  await expect(page.getByRole('checkbox', {
    name: 'I have inspected all gate sources and read their limitations.'
  })).toBeDisabled();
});
test('material evidence changes invalidate the entire session but timestamp-only refresh preserves it', async ({
  page
}) => {
  let snapshot = fixture();
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: snapshot
  }));
  await evidence(page);
  await tests(page);
  await review(page);
  snapshot = {
    ...snapshot,
    timestamp: new Date().toISOString()
  };
  await page.getByRole('button', {
    name: 'Refresh evidence',
    exact: true
  }).click();
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toHaveCount(0);
  snapshot = {
    ...snapshot,
    gates: snapshot.gates.map(g => g.id === 'R3.1' ? {
      ...g,
      status: 'UNKNOWN'
    } : g)
  };
  await page.getByRole('button', {
    name: 'Refresh evidence',
    exact: true
  }).click();
  await expect(page.getByRole('region', {
    name: 'Locked stage'
  })).toContainText('Acknowledge the System');
  await page.getByRole('button', {
    name: 'Go to System →'
  }).click();
  await expect(page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  })).not.toBeChecked();
});
test('unavailable evidence never exposes decision controls', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    status: 503,
    json: {
      error: 'unavailable'
    }
  }));
  await page.goto('/decision');
  await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  await expect(page.getByRole('button', {
    name: 'APPROVE',
    exact: true
  })).toHaveCount(0);
  await expect(page.getByRole('list', {
    name: 'Human acceptance progress'
  })).toContainText('Locked');
});
test('mobile persistent progress shows states without overflow', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await page.setViewportSize({
    width: 390,
    height: 844
  });
  await page.goto('/overview');
  await expect(page.getByRole('list', {
    name: 'Human acceptance progress'
  })).toContainText('Current');
  await expect(page.getByRole('button', {
    name: 'Human Test Locked',
    exact: true
  })).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  if (process.env.CPLANE_HUMAN_SCREENSHOT) await page.screenshot({
    path: process.env.CPLANE_HUMAN_SCREENSHOT,
    fullPage: true
  });
});
test('checklist text and alternate System button unlock Evidence only through explicit human action', async ({
  page
}) => {
  await page.route('**/v1/control-plane/snapshot', r => r.fulfill({
    json: fixture()
  }));
  await page.goto('/overview');
  const checkbox = page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  });
  await expect(checkbox).not.toBeChecked();
  const label = page.locator('label').filter({
    has: checkbox
  });
  await label.click();
  await expect(checkbox).toBeChecked();
  await expect(page.getByRole('link', {
    name: 'Evidence',
    exact: true
  })).toBeVisible();
  await label.click();
  await expect(checkbox).not.toBeChecked();
  await expect(page.getByRole('button', {
    name: 'Evidence Locked',
    exact: true
  })).toBeDisabled();
  await page.getByRole('button', {
    name: 'Acknowledge System',
    exact: true
  }).click();
  await expect(checkbox).toBeChecked();
  await page.getByRole('button', {
    name: /Continue to Evidence/
  }).click();
  await expect(page.getByRole('heading', {
    name: 'Evidence',
    exact: true
  })).toBeVisible();
  await expect(page.getByRole('button', {
    name: 'Human Test Locked',
    exact: true
  })).toBeDisabled();
});
test('slow background refresh does not disable System checklist or infer acknowledgement', async ({
  page
}) => {
  let hold = false;
  let release;
  const pending = new Promise(resolve => {
    release = resolve;
  });
  await page.route('**/v1/control-plane/snapshot', async r => {
    if (hold) await pending;
    await r.fulfill({
      json: fixture()
    });
  });
  await page.goto('/overview');
  const checkbox = page.getByRole('checkbox', {
    name: 'I have read the system summary and limitations.'
  });
  await expect(checkbox).toBeEnabled();
  hold = true;
  await page.getByRole('button', {
    name: 'Refresh evidence',
    exact: true
  }).click();
  await expect(page.getByRole('button', {
    name: 'Reading evidence…',
    exact: true
  })).toBeVisible();
  await expect(checkbox).not.toBeChecked();
  await checkbox.click();
  await expect(checkbox).toBeChecked();
  await expect(page.getByRole('button', {
    name: /Continue to Evidence/
  })).toBeDisabled();
  release();
  await expect(page.getByRole('button', {
    name: /Continue to Evidence/
  })).toBeEnabled();
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6WyJ0ZXN0IiwiZXhwZWN0IiwiZnMiLCJmaXh0dXJlIiwiSlNPTiIsInBhcnNlIiwicmVhZEZpbGVTeW5jIiwicHJvY2VzcyIsImVudiIsIkNQTEFORV9TTkFQU0hPVF9GSUxFIiwicmV2aWV3QWNrIiwic3RhcnQiLCJwYWdlIiwiZ290byIsImdldEJ5Um9sZSIsIm5hbWUiLCJjaGVjayIsImNsaWNrIiwiaW5zcGVjdCIsImNvdW50IiwiaSIsImxvY2F0b3IiLCJmaWx0ZXIiLCJoYXMiLCJoYXNUZXh0IiwiUmVnRXhwIiwiYnV0dG9uIiwiZXhhY3QiLCJpc0VuYWJsZWQiLCJldmlkZW5jZSIsInRlc3RzIiwicmVzdWx0IiwiZ3JvdXAiLCJhbGwiLCJyZXZpZXciLCJwYXRoIiwicm91dGUiLCJyIiwiZnVsZmlsbCIsImpzb24iLCJ0b0NvbnRhaW5UZXh0IiwidG9IYXZlQ291bnQiLCJ0b0JlVmlzaWJsZSIsIkNQTEFORV9FMkVfTElWRSIsIm11dGF0aW9ucyIsImVycm9ycyIsIm9uIiwidXJsIiwiaW5jbHVkZXMiLCJtZXRob2QiLCJwdXNoIiwiZSIsIm1lc3NhZ2UiLCJDUExBTkVfSFVNQU5fU0NSRUVOU0hPVCIsInNjcmVlbnNob3QiLCJyZXBsYWNlIiwiZnVsbFBhZ2UiLCJ0b0JlRGlzYWJsZWQiLCJldmlkZW5jZUFjayIsInRvQmVFbmFibGVkIiwibm90IiwidG9CZUNoZWNrZWQiLCJnZXRCeVRleHQiLCJncm91cHMiLCJzbGljZSIsInRvSGF2ZUF0dHJpYnV0ZSIsInRvRXF1YWwiLCJyZWxvYWQiLCJkZWNpc2lvbiIsImZpeG1lIiwic2F2ZSIsImZpbGwiLCJ1bmNoZWNrIiwicyIsImdhdGVzIiwiZmluZCIsImciLCJpZCIsInNuYXBzaG90IiwidGltZXN0YW1wIiwiRGF0ZSIsInRvSVNPU3RyaW5nIiwibWFwIiwic3RhdHVzIiwiZXJyb3IiLCJzZXRWaWV3cG9ydFNpemUiLCJ3aWR0aCIsImhlaWdodCIsImV2YWx1YXRlIiwiZG9jdW1lbnQiLCJkb2N1bWVudEVsZW1lbnQiLCJzY3JvbGxXaWR0aCIsIndpbmRvdyIsImlubmVyV2lkdGgiLCJ0b0JlIiwiY2hlY2tib3giLCJsYWJlbCIsImhvbGQiLCJyZWxlYXNlIiwicGVuZGluZyIsIlByb21pc2UiLCJyZXNvbHZlIl0sInNvdXJjZXMiOlsiaHVtYW4uc3BlYy50cyJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQge3Rlc3QsZXhwZWN0LHR5cGUgUGFnZX0gZnJvbSAnQHBsYXl3cmlnaHQvdGVzdCc7XG5pbXBvcnQgZnMgZnJvbSAnbm9kZTpmcyc7XG5jb25zdCBmaXh0dXJlPSgpPT5KU09OLnBhcnNlKGZzLnJlYWRGaWxlU3luYyhwcm9jZXNzLmVudi5DUExBTkVfU05BUFNIT1RfRklMRSEsJ3V0ZjgnKSk7XG5jb25zdCByZXZpZXdBY2s9J0kgaGF2ZSByZXZpZXdlZCB0aGUgZXZpZGVuY2UsIGFsbCBodW1hbiB0ZXN0IHJlc3VsdHMgYW5kIHVucmVzb2x2ZWQgbGltaXRhdGlvbnMuJztcbmFzeW5jIGZ1bmN0aW9uIHN0YXJ0KHBhZ2U6UGFnZSl7YXdhaXQgcGFnZS5nb3RvKCcvb3ZlcnZpZXcnKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgcmVhZCB0aGUgc3lzdGVtIHN1bW1hcnkgYW5kIGxpbWl0YXRpb25zLid9KS5jaGVjaygpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBFdmlkZW5jZS99KS5jbGljaygpO31cbmFzeW5jIGZ1bmN0aW9uIGluc3BlY3QocGFnZTpQYWdlLGNvdW50PTE0KXtmb3IobGV0IGk9MTtpPD1jb3VudDtpKyspe2F3YWl0IHBhZ2UubG9jYXRvcignZGV0YWlscy5nYXRlLWNhcmQnKS5maWx0ZXIoe2hhczpwYWdlLmxvY2F0b3IoJ3N1bW1hcnkgc3Ryb25nJyx7aGFzVGV4dDpuZXcgUmVnRXhwKCdeUjNcXFxcLicraSsnJCcpfSl9KS5sb2NhdG9yKCdzdW1tYXJ5JykuY2xpY2soKTtjb25zdCBidXR0b249cGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0kgaGF2ZSBpbnNwZWN0ZWQgUjMuJytpKycgc291cmNlJyxleGFjdDp0cnVlfSk7aWYoYXdhaXQgYnV0dG9uLmlzRW5hYmxlZCgpKWF3YWl0IGJ1dHRvbi5jbGljaygpO319XG5hc3luYyBmdW5jdGlvbiBldmlkZW5jZShwYWdlOlBhZ2Upe2F3YWl0IHN0YXJ0KHBhZ2UpO2F3YWl0IGluc3BlY3QocGFnZSk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2NoZWNrYm94Jyx7bmFtZTonSSBoYXZlIGluc3BlY3RlZCBhbGwgZ2F0ZSBzb3VyY2VzIGFuZCByZWFkIHRoZWlyIGxpbWl0YXRpb25zLid9KS5jaGVjaygpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBIdW1hbiBUZXN0L30pLmNsaWNrKCk7fVxuYXN5bmMgZnVuY3Rpb24gdGVzdHMocGFnZTpQYWdlLHJlc3VsdD0n4pyTIFBBU1MnKXtmb3IoY29uc3QgZ3JvdXAgb2YgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2dyb3VwJyx7bmFtZTovXlJlc3VsdCBmb3IgL30pLmFsbCgpKWF3YWl0IGdyb3VwLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpyZXN1bHQsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L1JldmlldyBodW1hbiByZXN1bHRzL30pLmNsaWNrKCk7fVxuYXN5bmMgZnVuY3Rpb24gcmV2aWV3KHBhZ2U6UGFnZSl7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2NoZWNrYm94Jyx7bmFtZTpyZXZpZXdBY2t9KS5jaGVjaygpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBEZWNpc2lvbi99KS5jbGljaygpO31cbmZvcihjb25zdCBwYXRoIG9mIFsnL2V2aWRlbmNlJywnL3Rlc3QnLCcvcmV2aWV3JywnL2RlY2lzaW9uJ10pdGVzdCgnZGlyZWN0ICcrcGF0aCsnIGlzIGxvY2tlZCB3aXRob3V0IHVwc3RyZWFtIGNvbXBsZXRpb24nLGFzeW5jKHtwYWdlfSk9Pnthd2FpdCBwYWdlLnJvdXRlKCcqKi92MS9jb250cm9sLXBsYW5lL3NuYXBzaG90JyxyPT5yLmZ1bGZpbGwoe2pzb246Zml4dHVyZSgpfSkpO2F3YWl0IHBhZ2UuZ290byhwYXRoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ3JlZ2lvbicse25hbWU6J0xvY2tlZCBzdGFnZSd9KSkudG9Db250YWluVGV4dCgnQWNrbm93bGVkZ2UgdGhlIFN5c3RlbScpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQVBQUk9WRScsZXhhY3Q6dHJ1ZX0pKS50b0hhdmVDb3VudCgwKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2xpc3QnLHtuYW1lOidIdW1hbiBhY2NlcHRhbmNlIHByb2dyZXNzJ30pKS50b0NvbnRhaW5UZXh0KCdMb2NrZWQnKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonR28gdG8gU3lzdGVtIOKGkid9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnaGVhZGluZycse25hbWU6J1N5c3RlbScsZXhhY3Q6dHJ1ZX0pKS50b0JlVmlzaWJsZSgpO30pO1xudGVzdCgnYWxsIGZpdmUgdHJhbnNpdGlvbnMgcmVxdWlyZSBleHBsaWNpdCBjb21wbGV0aW9uIGFuZCBjb25maXJtYXRpb247IG5vIGJhY2tlbmQgbXV0YXRpb24nLGFzeW5jKHtwYWdlfSk9PntcbiAgaWYocHJvY2Vzcy5lbnYuQ1BMQU5FX0UyRV9MSVZFIT09JzEnKWF3YWl0IHBhZ2Uucm91dGUoJyoqL3YxL2NvbnRyb2wtcGxhbmUvc25hcHNob3QnLHI9PnIuZnVsZmlsbCh7anNvbjpmaXh0dXJlKCl9KSk7XG4gIGNvbnN0IG11dGF0aW9uczpzdHJpbmdbXT1bXTtjb25zdCBlcnJvcnM6c3RyaW5nW109W107cGFnZS5vbigncmVxdWVzdCcscj0+e2lmKHIudXJsKCkuaW5jbHVkZXMoJy92MS8nKSYmci5tZXRob2QoKSE9PSdHRVQnKW11dGF0aW9ucy5wdXNoKHIubWV0aG9kKCkpO30pO3BhZ2Uub24oJ3BhZ2VlcnJvcicsZT0+ZXJyb3JzLnB1c2goZS5tZXNzYWdlKSk7XG4gIGF3YWl0IHBhZ2UuZ290bygnL292ZXJ2aWV3Jyk7aWYocHJvY2Vzcy5lbnYuQ1BMQU5FX0hVTUFOX1NDUkVFTlNIT1QpYXdhaXQgcGFnZS5zY3JlZW5zaG90KHtwYXRoOnByb2Nlc3MuZW52LkNQTEFORV9IVU1BTl9TQ1JFRU5TSE9ULnJlcGxhY2UoJ21vYmlsZScsJ2Rlc2t0b3AnKSxmdWxsUGFnZTp0cnVlfSk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidFdmlkZW5jZSBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBFdmlkZW5jZS99KSkudG9CZURpc2FibGVkKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9PcGVuIEh1bWFuIERlY2lzaW9uL30pKS50b0JlRGlzYWJsZWQoKTtcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L0luc3BlY3QgcnVudGltZSBldmlkZW5jZS99KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnaGVhZGluZycse25hbWU6J1J1bnRpbWUnLGV4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnbGluaycse25hbWU6J1N5c3RlbScsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdjaGVja2JveCcse25hbWU6J0kgaGF2ZSByZWFkIHRoZSBzeXN0ZW0gc3VtbWFyeSBhbmQgbGltaXRhdGlvbnMuJ30pLmNoZWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdsaXN0Jyx7bmFtZTonSHVtYW4gYWNjZXB0YW5jZSBwcm9ncmVzcyd9KSkudG9Db250YWluVGV4dCgnQXZhaWxhYmxlJyk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L0NvbnRpbnVlIHRvIEV2aWRlbmNlL30pLmNsaWNrKCk7XG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnbGlzdCcse25hbWU6J0h1bWFuIGFjY2VwdGFuY2UgcHJvZ3Jlc3MnfSkpLnRvQ29udGFpblRleHQoJ0NvbXBsZXRlZCcpO2F3YWl0IGluc3BlY3QocGFnZSwxMyk7Y29uc3QgZXZpZGVuY2VBY2s9cGFnZS5nZXRCeVJvbGUoJ2NoZWNrYm94Jyx7bmFtZTonSSBoYXZlIGluc3BlY3RlZCBhbGwgZ2F0ZSBzb3VyY2VzIGFuZCByZWFkIHRoZWlyIGxpbWl0YXRpb25zLid9KTthd2FpdCBleHBlY3QoZXZpZGVuY2VBY2spLnRvQmVEaXNhYmxlZCgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonSHVtYW4gVGVzdCBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7XG4gIGF3YWl0IHBhZ2UubG9jYXRvcignZGV0YWlscy5nYXRlLWNhcmQnKS5maWx0ZXIoe2hhczpwYWdlLmxvY2F0b3IoJ3N1bW1hcnkgc3Ryb25nJyx7aGFzVGV4dDonUjMuMTQnfSl9KS5sb2NhdG9yKCdzdW1tYXJ5JykuY2xpY2soKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonSSBoYXZlIGluc3BlY3RlZCBSMy4xNCBzb3VyY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChldmlkZW5jZUFjaykudG9CZUVuYWJsZWQoKTthd2FpdCBleHBlY3QoZXZpZGVuY2VBY2spLm5vdC50b0JlQ2hlY2tlZCgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTovQ29udGludWUgdG8gSHVtYW4gVGVzdC99KSkudG9CZURpc2FibGVkKCk7YXdhaXQgZXZpZGVuY2VBY2suY2hlY2soKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTovQ29udGludWUgdG8gSHVtYW4gVGVzdC99KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQoJ+KXiyBOT1QgVEVTVEVEJyx7ZXhhY3Q6dHJ1ZX0pKS50b0hhdmVDb3VudCg4KTtjb25zdCBncm91cHM9YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2dyb3VwJyx7bmFtZTovXlJlc3VsdCBmb3IgL30pLmFsbCgpO2Zvcihjb25zdCBncm91cCBvZiBncm91cHMuc2xpY2UoMCw3KSlhd2FpdCBncm91cC5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J+KckyBQQVNTJyxleGFjdDp0cnVlfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L1JldmlldyBodW1hbiByZXN1bHRzL30pKS50b0JlRGlzYWJsZWQoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1JldmlldyBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7YXdhaXQgZ3JvdXBzWzddLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTon4pyTIFBBU1MnLGV4YWN0OnRydWV9KS5jbGljaygpO1xuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnbGluaycse25hbWU6L04gTlVTQU5UQVJBIEhVTUFOIEFDQ0VQVEFOQ0UgQ09OU09MRS99KS5jbGljaygpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdsaW5rJyx7bmFtZTonSHVtYW4gVGVzdCcsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdncm91cCcse25hbWU6J1Jlc3VsdCBmb3Igb3Blbid9KS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J+KckyBQQVNTJyxleGFjdDp0cnVlfSkpLnRvSGF2ZUF0dHJpYnV0ZSgnYXJpYS1wcmVzc2VkJywndHJ1ZScpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9SZXZpZXcgaHVtYW4gcmVzdWx0cy99KS5jbGljaygpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2hlYWRpbmcnLHtuYW1lOidLbm93biBsaW1pdGF0aW9ucycsZXhhY3Q6dHJ1ZX0pKS50b0JlVmlzaWJsZSgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5VGV4dCgn4peLIE5PVCBWRVJJRklFRCcse2V4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0RlY2lzaW9uIExvY2tlZCcsZXhhY3Q6dHJ1ZX0pKS50b0JlRGlzYWJsZWQoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2NoZWNrYm94Jyx7bmFtZTpyZXZpZXdBY2t9KSkubm90LnRvQmVDaGVja2VkKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBEZWNpc2lvbi99KSkudG9CZURpc2FibGVkKCk7YXdhaXQgcmV2aWV3KHBhZ2UpO1xuICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1BBU1MnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidGQUlMJyxleGFjdDp0cnVlfSkpLnRvQmVEaXNhYmxlZCgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonSE9MRCcsZXhhY3Q6dHJ1ZX0pKS50b0JlRGlzYWJsZWQoKTtcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1JlZnJlc2ggZXZpZGVuY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonUEFTUycsZXhhY3Q6dHJ1ZX0pKS50b0JlRGlzYWJsZWQoKTtleHBlY3QobXV0YXRpb25zKS50b0VxdWFsKFtdKTtleHBlY3QoZXJyb3JzKS50b0VxdWFsKFtdKTthd2FpdCBwYWdlLnJlbG9hZCgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgncmVnaW9uJyx7bmFtZTonTG9ja2VkIHN0YWdlJ30pKS50b0NvbnRhaW5UZXh0KCdBY2tub3dsZWRnZSB0aGUgU3lzdGVtJyk7XG59KTtcbi8vIE9ic29sZXRlOiB0aGlzIGNhc2UgZXhlcmNpc2VkIHRoZSByZXRpcmVkIHNlc3Npb24tb25seSBkZWNpc2lvbiBVSSAoQVBQUk9WRS9SRUpFQ1Qgd2l0aCBhXG4vLyBtYW5kYXRvcnkgcmVhc29uKS4gVGhlIGN1cnJlbnQgZGVjaXNpb24gc3RlcCBpcyBzZXJ2ZXItYm91bmQgYW5kIG9wZXJhdG9yLXRva2VuIGdhdGVkOyBpdHNcbi8vIGNvdmVyYWdlIGxpdmVzIGluIGNvbnRyb2wtcGxhbmUvdGVzdHMvaHVtYW4udGVzdC50c3ggYW5kIHRoZSAvcmV2aWV3LWV4ZWN1dGUgcGFnZSB0ZXN0cy5cbmZvcihjb25zdCBkZWNpc2lvbiBvZiBbJ1JFSkVDVCcsJ0hPTEQnXSl0ZXN0LmZpeG1lKGRlY2lzaW9uKycgZm9sbG93cyByZXZpZXcgb2YgZXhwbGljaXQgRkFJTC9CTE9DS0VEIGFuZCByZXF1aXJlcyBhIHJlYXNvbicsYXN5bmMoe3BhZ2V9KT0+e2F3YWl0IHBhZ2Uucm91dGUoJyoqL3YxL2NvbnRyb2wtcGxhbmUvc25hcHNob3QnLHI9PnIuZnVsZmlsbCh7anNvbjpmaXh0dXJlKCl9KSk7YXdhaXQgZXZpZGVuY2UocGFnZSk7YXdhaXQgdGVzdHMocGFnZSxkZWNpc2lvbj09PSdSRUpFQ1QnPyfinJUgRkFJTCc6JyEgQkxPQ0tFRCcpO2F3YWl0IHJldmlldyhwYWdlKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0FQUFJPVkUnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6ZGVjaXNpb24sZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7Y29uc3Qgc2F2ZT1wYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpkZWNpc2lvbj09PSdSRUpFQ1QnPydDb25maXJtIFJlamVjdGlvbic6J1NhdmUgSE9MRCcsZXhhY3Q6dHJ1ZX0pO2F3YWl0IGV4cGVjdChzYXZlKS50b0JlRGlzYWJsZWQoKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgncmFkaW8nLHtuYW1lOidPdGhlcicsZXhhY3Q6dHJ1ZX0pLmNoZWNrKCk7YXdhaXQgZXhwZWN0KHNhdmUpLnRvQmVEaXNhYmxlZCgpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCd0ZXh0Ym94Jyx7bmFtZTonTm90ZXMgKHJlcXVpcmVkKSd9KS5maWxsKCdOZWVkIGh1bWFuIHJldmlldycpO2F3YWl0IHNhdmUuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQoJ0h1bWFuIGRlY2lzaW9uIHJlY29yZGVkIGluIHRoaXMgc2Vzc2lvbicse2V4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQoJ+KXiyBOT1QgVkVSSUZJRUQnLHtleGFjdDp0cnVlfSkpLnRvQmVWaXNpYmxlKCk7fSk7XG50ZXN0KCd3aXRoZHJhd2luZyBFdmlkZW5jZSBhY2tub3dsZWRnZW1lbnQgcmVsb2NrcyBUZXN0IFJldmlldyBEZWNpc2lvbicsYXN5bmMoe3BhZ2V9KT0+e2F3YWl0IHBhZ2Uucm91dGUoJyoqL3YxL2NvbnRyb2wtcGxhbmUvc25hcHNob3QnLHI9PnIuZnVsZmlsbCh7anNvbjpmaXh0dXJlKCl9KSk7YXdhaXQgZXZpZGVuY2UocGFnZSk7YXdhaXQgdGVzdHMocGFnZSk7YXdhaXQgcmV2aWV3KHBhZ2UpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdsaW5rJyx7bmFtZTonRXZpZGVuY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdjaGVja2JveCcse25hbWU6J0kgaGF2ZSBpbnNwZWN0ZWQgYWxsIGdhdGUgc291cmNlcyBhbmQgcmVhZCB0aGVpciBsaW1pdGF0aW9ucy4nfSkudW5jaGVjaygpO2Zvcihjb25zdCBuYW1lIG9mIFsnSHVtYW4gVGVzdCcsJ1JldmlldycsJ0RlY2lzaW9uJ10pYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOm5hbWUrJyBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7fSk7XG50ZXN0KCdjaGFuZ2luZyBhbmQgY2xlYXJpbmcgcmVzdWx0cyBpbnZhbGlkYXRlcyBSZXZpZXcgYWNrbm93bGVkZ2VtZW50IGFuZCBsb2NrcyBkb3duc3RyZWFtJyxhc3luYyh7cGFnZX0pPT57YXdhaXQgcGFnZS5yb3V0ZSgnKiovdjEvY29udHJvbC1wbGFuZS9zbmFwc2hvdCcscj0+ci5mdWxmaWxsKHtqc29uOmZpeHR1cmUoKX0pKTthd2FpdCBldmlkZW5jZShwYWdlKTthd2FpdCB0ZXN0cyhwYWdlKTthd2FpdCByZXZpZXcocGFnZSk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2xpbmsnLHtuYW1lOidIdW1hbiBUZXN0JyxleGFjdDp0cnVlfSkuY2xpY2soKTtjb25zdCBncm91cD1wYWdlLmdldEJ5Um9sZSgnZ3JvdXAnLHtuYW1lOidSZXN1bHQgZm9yIG9wZW4nfSk7YXdhaXQgZ3JvdXAuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOifinJUgRkFJTCcsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidEZWNpc2lvbiBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2xpbmsnLHtuYW1lOidSZXZpZXcnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOnJldmlld0Fja30pKS5ub3QudG9CZUNoZWNrZWQoKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnbGluaycse25hbWU6J0h1bWFuIFRlc3QnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGdyb3VwLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQ2xlYXIgcmVzdWx0JyxleGFjdDp0cnVlfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1JldmlldyBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7fSk7XG50ZXN0KCd3aXRoZHJhd2luZyBTeXN0ZW0gYWNrbm93bGVkZ2VtZW50IHJlbG9ja3MgZXZlcnkgZG93bnN0cmVhbSBzdGFnZScsYXN5bmMoe3BhZ2V9KT0+e2F3YWl0IHBhZ2Uucm91dGUoJyoqL3YxL2NvbnRyb2wtcGxhbmUvc25hcHNob3QnLHI9PnIuZnVsZmlsbCh7anNvbjpmaXh0dXJlKCl9KSk7YXdhaXQgZXZpZGVuY2UocGFnZSk7YXdhaXQgdGVzdHMocGFnZSk7YXdhaXQgcmV2aWV3KHBhZ2UpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdsaW5rJyx7bmFtZTonU3lzdGVtJyxleGFjdDp0cnVlfSkuY2xpY2soKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgcmVhZCB0aGUgc3lzdGVtIHN1bW1hcnkgYW5kIGxpbWl0YXRpb25zLid9KS51bmNoZWNrKCk7Zm9yKGNvbnN0IG5hbWUgb2YgWydFdmlkZW5jZScsJ0h1bWFuIFRlc3QnLCdSZXZpZXcnLCdEZWNpc2lvbiddKWF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpuYW1lKycgTG9ja2VkJyxleGFjdDp0cnVlfSkpLnRvQmVEaXNhYmxlZCgpO30pO1xudGVzdCgnbWlzc2luZyBldmlkZW5jZSBzb3VyY2UgY2Fubm90IHVubG9jayBUZXN0Jyxhc3luYyh7cGFnZX0pPT57Y29uc3Qgcz1maXh0dXJlKCk7cy5nYXRlcy5maW5kKChnOntpZDpzdHJpbmd9KT0+Zy5pZD09PSdSMy4xJykuZXZpZGVuY2U9WydtaXNzaW5nJ107YXdhaXQgcGFnZS5yb3V0ZSgnKiovdjEvY29udHJvbC1wbGFuZS9zbmFwc2hvdCcscj0+ci5mdWxmaWxsKHtqc29uOnN9KSk7YXdhaXQgc3RhcnQocGFnZSk7YXdhaXQgaW5zcGVjdChwYWdlKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQoLzEzIG9mIDE0IGdhdGVzIGluc3BlY3RlZC8pKS50b0JlVmlzaWJsZSgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgaW5zcGVjdGVkIGFsbCBnYXRlIHNvdXJjZXMgYW5kIHJlYWQgdGhlaXIgbGltaXRhdGlvbnMuJ30pKS50b0JlRGlzYWJsZWQoKTt9KTtcbnRlc3QoJ21hdGVyaWFsIGV2aWRlbmNlIGNoYW5nZXMgaW52YWxpZGF0ZSB0aGUgZW50aXJlIHNlc3Npb24gYnV0IHRpbWVzdGFtcC1vbmx5IHJlZnJlc2ggcHJlc2VydmVzIGl0Jyxhc3luYyh7cGFnZX0pPT57bGV0IHNuYXBzaG90PWZpeHR1cmUoKTthd2FpdCBwYWdlLnJvdXRlKCcqKi92MS9jb250cm9sLXBsYW5lL3NuYXBzaG90JyxyPT5yLmZ1bGZpbGwoe2pzb246c25hcHNob3R9KSk7YXdhaXQgZXZpZGVuY2UocGFnZSk7YXdhaXQgdGVzdHMocGFnZSk7YXdhaXQgcmV2aWV3KHBhZ2UpO3NuYXBzaG90PXsuLi5zbmFwc2hvdCx0aW1lc3RhbXA6bmV3IERhdGUoKS50b0lTT1N0cmluZygpfTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonUmVmcmVzaCBldmlkZW5jZScsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdyZWdpb24nLHtuYW1lOidMb2NrZWQgc3RhZ2UnfSkpLnRvSGF2ZUNvdW50KDApO3NuYXBzaG90PXsuLi5zbmFwc2hvdCxnYXRlczpzbmFwc2hvdC5nYXRlcy5tYXAoKGc6e2lkOnN0cmluZ30pPT5nLmlkPT09J1IzLjEnP3suLi5nLHN0YXR1czonVU5LTk9XTid9OmcpfTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonUmVmcmVzaCBldmlkZW5jZScsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdyZWdpb24nLHtuYW1lOidMb2NrZWQgc3RhZ2UnfSkpLnRvQ29udGFpblRleHQoJ0Fja25vd2xlZGdlIHRoZSBTeXN0ZW0nKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonR28gdG8gU3lzdGVtIOKGkid9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgcmVhZCB0aGUgc3lzdGVtIHN1bW1hcnkgYW5kIGxpbWl0YXRpb25zLid9KSkubm90LnRvQmVDaGVja2VkKCk7fSk7XG50ZXN0KCd1bmF2YWlsYWJsZSBldmlkZW5jZSBuZXZlciBleHBvc2VzIGRlY2lzaW9uIGNvbnRyb2xzJyxhc3luYyh7cGFnZX0pPT57YXdhaXQgcGFnZS5yb3V0ZSgnKiovdjEvY29udHJvbC1wbGFuZS9zbmFwc2hvdCcscj0+ci5mdWxmaWxsKHtzdGF0dXM6NTAzLGpzb246e2Vycm9yOid1bmF2YWlsYWJsZSd9fSkpO2F3YWl0IHBhZ2UuZ290bygnL2RlY2lzaW9uJyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdhbGVydCcpKS50b0NvbnRhaW5UZXh0KCdObyBoZWFsdGh5IHN0YXRlIGhhcyBiZWVuIGluZmVycmVkJyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidBUFBST1ZFJyxleGFjdDp0cnVlfSkpLnRvSGF2ZUNvdW50KDApO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnbGlzdCcse25hbWU6J0h1bWFuIGFjY2VwdGFuY2UgcHJvZ3Jlc3MnfSkpLnRvQ29udGFpblRleHQoJ0xvY2tlZCcpO30pO1xudGVzdCgnbW9iaWxlIHBlcnNpc3RlbnQgcHJvZ3Jlc3Mgc2hvd3Mgc3RhdGVzIHdpdGhvdXQgb3ZlcmZsb3cnLGFzeW5jKHtwYWdlfSk9Pnthd2FpdCBwYWdlLnJvdXRlKCcqKi92MS9jb250cm9sLXBsYW5lL3NuYXBzaG90JyxyPT5yLmZ1bGZpbGwoe2pzb246Zml4dHVyZSgpfSkpO2F3YWl0IHBhZ2Uuc2V0Vmlld3BvcnRTaXplKHt3aWR0aDozOTAsaGVpZ2h0Ojg0NH0pO2F3YWl0IHBhZ2UuZ290bygnL292ZXJ2aWV3Jyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdsaXN0Jyx7bmFtZTonSHVtYW4gYWNjZXB0YW5jZSBwcm9ncmVzcyd9KSkudG9Db250YWluVGV4dCgnQ3VycmVudCcpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonSHVtYW4gVGVzdCBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7ZXhwZWN0KGF3YWl0IHBhZ2UuZXZhbHVhdGUoKCk9PmRvY3VtZW50LmRvY3VtZW50RWxlbWVudC5zY3JvbGxXaWR0aDw9d2luZG93LmlubmVyV2lkdGgpKS50b0JlKHRydWUpO2lmKHByb2Nlc3MuZW52LkNQTEFORV9IVU1BTl9TQ1JFRU5TSE9UKWF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpwcm9jZXNzLmVudi5DUExBTkVfSFVNQU5fU0NSRUVOU0hPVCxmdWxsUGFnZTp0cnVlfSk7fSk7XG50ZXN0KCdjaGVja2xpc3QgdGV4dCBhbmQgYWx0ZXJuYXRlIFN5c3RlbSBidXR0b24gdW5sb2NrIEV2aWRlbmNlIG9ubHkgdGhyb3VnaCBleHBsaWNpdCBodW1hbiBhY3Rpb24nLGFzeW5jKHtwYWdlfSk9PntcbiAgYXdhaXQgcGFnZS5yb3V0ZSgnKiovdjEvY29udHJvbC1wbGFuZS9zbmFwc2hvdCcscj0+ci5mdWxmaWxsKHtqc29uOmZpeHR1cmUoKX0pKTthd2FpdCBwYWdlLmdvdG8oJy9vdmVydmlldycpO1xuICBjb25zdCBjaGVja2JveD1wYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgcmVhZCB0aGUgc3lzdGVtIHN1bW1hcnkgYW5kIGxpbWl0YXRpb25zLid9KTthd2FpdCBleHBlY3QoY2hlY2tib3gpLm5vdC50b0JlQ2hlY2tlZCgpO1xuICBjb25zdCBsYWJlbD1wYWdlLmxvY2F0b3IoJ2xhYmVsJykuZmlsdGVyKHtoYXM6Y2hlY2tib3h9KTthd2FpdCBsYWJlbC5jbGljaygpO2F3YWl0IGV4cGVjdChjaGVja2JveCkudG9CZUNoZWNrZWQoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2xpbmsnLHtuYW1lOidFdmlkZW5jZScsZXhhY3Q6dHJ1ZX0pKS50b0JlVmlzaWJsZSgpO1xuICBhd2FpdCBsYWJlbC5jbGljaygpO2F3YWl0IGV4cGVjdChjaGVja2JveCkubm90LnRvQmVDaGVja2VkKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidFdmlkZW5jZSBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7XG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidBY2tub3dsZWRnZSBTeXN0ZW0nLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChjaGVja2JveCkudG9CZUNoZWNrZWQoKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTovQ29udGludWUgdG8gRXZpZGVuY2UvfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2hlYWRpbmcnLHtuYW1lOidFdmlkZW5jZScsZXhhY3Q6dHJ1ZX0pKS50b0JlVmlzaWJsZSgpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonSHVtYW4gVGVzdCBMb2NrZWQnLGV4YWN0OnRydWV9KSkudG9CZURpc2FibGVkKCk7XG59KTtcbnRlc3QoJ3Nsb3cgYmFja2dyb3VuZCByZWZyZXNoIGRvZXMgbm90IGRpc2FibGUgU3lzdGVtIGNoZWNrbGlzdCBvciBpbmZlciBhY2tub3dsZWRnZW1lbnQnLGFzeW5jKHtwYWdlfSk9PntcbiAgbGV0IGhvbGQ9ZmFsc2U7bGV0IHJlbGVhc2UhOigpPT52b2lkO2NvbnN0IHBlbmRpbmc9bmV3IFByb21pc2U8dm9pZD4ocmVzb2x2ZT0+e3JlbGVhc2U9cmVzb2x2ZTt9KTthd2FpdCBwYWdlLnJvdXRlKCcqKi92MS9jb250cm9sLXBsYW5lL3NuYXBzaG90Jyxhc3luYyByPT57aWYoaG9sZClhd2FpdCBwZW5kaW5nO2F3YWl0IHIuZnVsZmlsbCh7anNvbjpmaXh0dXJlKCl9KTt9KTtcbiAgYXdhaXQgcGFnZS5nb3RvKCcvb3ZlcnZpZXcnKTtjb25zdCBjaGVja2JveD1wYWdlLmdldEJ5Um9sZSgnY2hlY2tib3gnLHtuYW1lOidJIGhhdmUgcmVhZCB0aGUgc3lzdGVtIHN1bW1hcnkgYW5kIGxpbWl0YXRpb25zLid9KTthd2FpdCBleHBlY3QoY2hlY2tib3gpLnRvQmVFbmFibGVkKCk7aG9sZD10cnVlO1xuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonUmVmcmVzaCBldmlkZW5jZScsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidSZWFkaW5nIGV2aWRlbmNl4oCmJyxleGFjdDp0cnVlfSkpLnRvQmVWaXNpYmxlKCk7YXdhaXQgZXhwZWN0KGNoZWNrYm94KS5ub3QudG9CZUNoZWNrZWQoKTthd2FpdCBjaGVja2JveC5jbGljaygpO2F3YWl0IGV4cGVjdChjaGVja2JveCkudG9CZUNoZWNrZWQoKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L0NvbnRpbnVlIHRvIEV2aWRlbmNlL30pKS50b0JlRGlzYWJsZWQoKTtyZWxlYXNlKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9Db250aW51ZSB0byBFdmlkZW5jZS99KSku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RUFBQztJQUFDQyxJQUFJLEVBQUMsUUFBUTtJQUFDWSxLQUFLLEVBQUM7RUFBSSxDQUFDLENBQUMsQ0FBQ1YsS0FBSyxDQUFDLENBQUM7RUFBQyxNQUFNaEIsTUFBTSxDQUFDVyxJQUFJLENBQUNFLFNBQVMsQ0FBQyxRQUFRLEVBQUM7SUFBQ0MsSUFBSSxFQUFDO0VBQXNCLENBQUMsQ0FBQyxDQUFDLENBQUMwQyxZQUFZLENBQUMsQ0FBQztFQUFDLE1BQU14RCxNQUFNLENBQUNXLElBQUksQ0FBQ0UsU0FBUyxDQUFDLFFBQVEsRUFBQztJQUFDQyxJQUFJLEVBQUMsZUFBZTtJQUFDWSxLQUFLLEVBQUM7RUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDOEIsWUFBWSxDQUFDLENBQUM7RUFBQyxNQUFNTSxNQUFNLENBQUMsQ0FBQyxDQUFDLENBQUNqRCxTQUFTLENBQUMsUUFBUSxFQUFDO0lBQUNDLElBQUksRUFBQyxRQUFRO0lBQUNZLEtBQUssRUFBQztFQUFJLENBQUMsQ0FBQyxDQUFDVixLQUFLLENBQUMsQ0FBQztFQUMxZSxNQUFNTCxJQUFJLENBQUNFLFNBQVMsQ0FBQyxNQUFNLEVBQUM7SUFBQ0MsSUFBSSxFQUFDO0VBQXNDLENBQUMsQ0FBQyxDQUFDRSxLQUFLLENBQUMsQ0FBQztFQUFDLE1BQU1MLElBQUksQ0FBQ0UsU0FBUyxDQUFDLE1BQU0sRUFBQztJQUFDQyxJQUFJLEVBQUMsWUFBWTtJQUFDWSxLQUFLLEVBQUM7RUFBSSxDQUFDLENBQUMsQ0FBQ1YsS0FBSyxDQUFDLENBQUM7RUFBQyxNQUFNaEIsTUFBTSxDQUFDVyxJQUFJLENBQUNFLFNBQVMsQ0FBQyxPQUFPLEVBQUM7SUFBQ0MsSUFBSSxFQUFDO0VBQWlCLENBQUMsQ0FBQyxDQUFDRCxTQUFTLENBQUMsUUFBUSxFQUFDO0lBQUNDLElBQUksRUFBQyxRQUFRO0lBQUNZLEtBQUssRUFBQztFQUFJLENBQUMsQ0FBQyxDQUFDLENBQUNzQyxlQUFlLENBQUMsY0FBYyxFQUFDLE1BQU0sQ0FBQztFQUFDLE1BQU1yRCxJQUFJLENBQUNFLFNBQVMs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