// aede5f3d54cc636753aa2e6f2cc9ce2335510fda
import { test, expect } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const output = resolve('../artifacts/ncp-v1-ui-followup-20261019');
const reference = resolve('../artifacts/ncp-v1-ui-local-20261019/reference/dist');
async function serveReference(page) {
  await page.route('**/__reference__/**', async route => {
    const name = new URL(route.request().url()).pathname.split('/').at(-1) || 'index.html';
    if (!['index.html', 'app.js', 'core.js', 'styles.css'].includes(name)) return route.abort();
    await route.fulfill({
      body: readFileSync(resolve(reference, name)),
      contentType: name.endsWith('.js') ? 'text/javascript' : name.endsWith('.css') ? 'text/css' : 'text/html'
    });
  });
}
test('same viewport reference and local comparison', async ({
  page
}) => {
  await serveReference(page);
  const report = [];
  for (const width of [1440, 390]) {
    await page.setViewportSize({
      width,
      height: width === 1440 ? 1000 : 844
    });
    for (const [ref, local] of [['workspace', 'workspace'], ['human', 'approvals']]) {
      var _process$env$NCP_CAPT;
      await page.goto(`/__reference__/index.html#${ref}`);
      await expect(page.getByRole('heading', {
        name: ref === 'workspace' ? 'AI Workspace' : 'Human Control',
        exact: true
      })).toBeVisible();
      const tabs = ref === 'workspace' ? ['Aktivitas tugas', 'Blocker', 'Evidence'] : [];
      await page.screenshot({
        path: resolve(output, `reference-${ref}-${width}.png`),
        fullPage: true
      });
      for (const tab of tabs) {
        await page.locator('[data-action="workspace-tab"]').filter({
          hasText: tab
        }).first().click();
        await page.screenshot({
          path: resolve(output, `reference-${ref}-${tab.split(' ')[0]}-${width}.png`),
          fullPage: true
        });
      }
      report.push({
        surface: 'reference',
        page: ref,
        width,
        tabs
      });
      await page.goto(`/${local}`);
      await expect(page.getByRole('heading', {
        name: ref === 'workspace' ? 'AI Workspace' : 'Human Control',
        exact: true
      })).toBeVisible();
      await expect(page.locator(ref === 'workspace' ? '.op-task-meta' : '.op-human .op-specs').first()).toContainText(/ollama|openrouter/i);
      await page.screenshot({
        path: resolve(output, `${(_process$env$NCP_CAPT = process.env.NCP_CAPTURE_STAGE) !== null && _process$env$NCP_CAPT !== void 0 ? _process$env$NCP_CAPT : 'after'}-${local}-${width}.png`),
        fullPage: true
      });
    }
  }
  writeFileSync(resolve(output, 'comparison-viewports.json'), JSON.stringify(report, null, 2));
});
test('reference tabs, filters, task/blocker/evidence/gate and decision drawers', async ({
  page
}) => {
  test.setTimeout(90000);
  await page.emulateMedia({
    reducedMotion: 'reduce'
  });
  await serveReference(page);
  const inspected = [];
  for (const width of [1440, 390]) {
    await page.setViewportSize({
      width,
      height: width === 1440 ? 1000 : 844
    });
    await page.goto('/__reference__/index.html#workspace');
    await page.locator('[data-action="workspace-tab"][data-id="tasks"]').click();
    await page.getByRole('button', {
      name: 'Buka detail tugas',
      exact: true
    }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    inspected.push(`task drawer ${width}`);
    await page.screenshot({
      path: resolve(output, `reference-task-drawer-${width}.png`)
    });
    await page.keyboard.press('Escape');
    await page.locator('[data-action="workspace-tab"][data-id="blockers"]').click();
    for (const id of ['open', 'resolved', 'all']) {
      await page.locator(`[data-action="blocker-filter"][data-id="${id}"]`).click();
      inspected.push(`blocker filter ${id} ${width}`);
    }
    const blockers = await page.locator('main .blocker-list [data-action="blocker"]').count();
    for (let i = 0; i < blockers; i++) {
      await page.locator('main .blocker-list [data-action="blocker"]').nth(i).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.screenshot({
        path: resolve(output, `reference-blocker-${i}-${width}.png`)
      });
      await page.keyboard.press('Escape');
    }
    await page.locator('[data-action="workspace-tab"][data-id="evidence"]').click();
    for (const filter of ['PASS', 'FAIL', 'HOLD', 'ALL']) {
      await page.locator(`[data-action="evidence-filter"][data-id="${filter}"]`).click();
      inspected.push(`evidence filter ${filter} ${width}`);
    }
    await page.locator('tbody [data-action="evidence"]').first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.screenshot({
      path: resolve(output, `reference-evidence-drawer-${width}.png`)
    });
    await page.keyboard.press('Escape');
    await page.goto('/__reference__/index.html#human');
    const gates = page.locator('.gate-item');
    for (let i = 0; i < (await gates.count()); i++) {
      await gates.nth(i).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      inspected.push(`gate ${i + 1} ${width}`);
      await page.screenshot({
        path: resolve(output, `reference-gate-${i + 1}-${width}.png`)
      });
      await page.keyboard.press('Escape');
    }
    await page.getByRole('button', {
      name: 'Tinjau & beri keputusan',
      exact: true
    }).click();
    await expect(page.locator('[data-action="select-decision"][data-id="PASS"]')).toBeDisabled();
    for (const choice of ['FAIL', 'HOLD']) {
      const button = page.locator(`[data-action="select-decision"][data-id="${choice}"]`);
      await button.click();
      await expect(button).toHaveAttribute('aria-pressed', 'true');
    }
    await page.screenshot({
      path: resolve(output, `reference-decision-drawer-${width}.png`)
    });
    await page.keyboard.press('Escape');
    await page.getByRole('button', {
      name: 'Lihat kebijakan',
      exact: true
    }).click();
    await expect(page.getByRole('heading', {
      name: 'Pengaturan & Teknis',
      exact: true
    })).toBeVisible();
    inspected.push(`policy link ${width}`);
  }
  writeFileSync(resolve(output, 'reference-interaction-checklist.json'), JSON.stringify(inspected, null, 2));
});
test('live workspace and human controls remain read only while browsing', async ({
  page
}) => {
  const mutations = [],
    errors = [];
  page.on('request', r => {
    if (new URL(r.url()).pathname.startsWith('/v1/') && r.method() !== 'GET') mutations.push(`${r.method()} ${new URL(r.url()).pathname}`);
  });
  page.on('pageerror', e => errors.push(e.message));
  for (const width of [1440, 390]) {
    await page.setViewportSize({
      width,
      height: width === 1440 ? 1000 : 844
    });
    await page.goto('/workspace');
    await page.getByRole('button', {
      name: 'Fokus PIAK-03 ↗'
    }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await page.getByRole('tab', {
      name: 'Aktivitas tugas'
    }).focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByRole('tab', {
      name: /Blocker/
    })).toHaveAttribute('aria-selected', 'true');
    for (const tab of ['Aktivitas tugas', 'Blocker', 'Evidence', 'Chat V1']) {
      await page.getByRole('tab', {
        name: new RegExp(`^${tab}`)
      }).click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      if (tab === 'Blocker') {
        await page.getByRole('button', {
          name: 'Selesai',
          exact: true
        }).click();
        await expect(page.getByText(/Riwayat penyelesaian blocker/)).toBeVisible();
        await page.getByRole('button', {
          name: 'Terbuka',
          exact: true
        }).click();
        await page.getByRole('button', {
          name: /^Detail blocker/
        }).first().click();
        await expect(page.getByRole('dialog')).toBeVisible();
        await page.screenshot({
          path: resolve(output, `live-blocker-drawer-${width}.png`)
        });
        await page.keyboard.press('Escape');
      }
      if (tab === 'Evidence') {
        await expect(page.locator('.op-evidence tbody tr').first()).toBeVisible();
        await page.locator('.op-evidence tbody .detail-trigger').first().click();
        await expect(page.getByRole('dialog')).toBeVisible();
        await page.screenshot({
          path: resolve(output, `live-evidence-drawer-${width}.png`)
        });
        await page.keyboard.press('Escape');
      }
      if (tab === 'Chat V1') await expect(page.getByLabel('Pertanyaan Anda')).toBeVisible();
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: resolve(output, `live-workspace-${tab.split(' ')[0]}-${width}.png`),
        fullPage: true
      });
    }
    await page.goto('/approvals');
    for (const name of ['Evidence valid', 'Plan siap', 'Operator terautentikasi', 'Keputusan tersedia', 'Izin eksekusi']) {
      await page.getByRole('button', {
        name: `${name} ↗`,
        exact: true
      }).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.keyboard.press('Escape');
    }
    await page.getByRole('button', {
      name: 'Tinjau & beri keputusan',
      exact: true
    }).click();
    const drawer = page.getByRole('dialog', {
      name: 'Tinjau keputusan Anda'
    });
    for (const name of ['PASS', 'FAIL', 'HOLD']) await expect(drawer.getByRole('button', {
      name: new RegExp(name)
    })).toBeDisabled();
    await expect(drawer.getByRole('button', {
      name: 'Simpan keputusan'
    })).toBeDisabled();
    await page.screenshot({
      path: resolve(output, `live-decision-locked-${width}.png`)
    });
    await page.keyboard.press('Escape');
    await expect(page.getByRole('button', {
      name: 'Tinjau & beri keputusan',
      exact: true
    })).toBeFocused();
    await page.getByRole('button', {
      name: 'Lihat kebijakan ↗'
    }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await page.getByRole('button', {
      name: 'Periksa evidence',
      exact: true
    }).click();
    await expect(page.getByRole('dialog', {
      name: 'Paket evidence'
    })).toBeVisible();
    await page.keyboard.press('Escape');
    for (const name of ['Keputusan', 'Eksekusi', 'Semua']) await page.getByRole('group', {
      name: 'Filter riwayat'
    }).getByRole('button', {
      name,
      exact: true
    }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
  writeFileSync(resolve(output, 'live-readonly-checks.json'), JSON.stringify({
    mutations,
    errors,
    viewport: [1440, 390]
  }, null, 2));
});
for (const width of [1440, 390]) test(`isolated browser contract at ${width}: tasks, filters, decisions, history, rejection and lost authorization`, async ({
  page
}) => {
  await page.setViewportSize({
    width,
    height: width === 1440 ? 1000 : 844
  });
  const packageId = 'evp_sha256_' + 'b'.repeat(64),
    binding = {
      plan_id: 'isolated-plan',
      version: 'isolated-v1',
      action: 'CONTROLLED_FILE_WRITE'
    };
  const plan = {
    change_id: 'isolated-plan',
    objective: 'Tugas PIAK-03 — fixture terisolasi',
    expected_change: 'Contoh pengujian UI, bukan tugas produksi',
    target_files: ['fixture.txt'],
    operation: 'write',
    plan_binding: binding,
    risk: 'LOW',
    tests_required: ['test_fixture'],
    rollback: 'restore fixture',
    checked_at: '2026-10-19T10:00:00Z',
    source: 'BROWSER_TEST_ONLY'
  };
  let allowed = true,
    authorized = true,
    reject = false;
  const decisions = [],
    posts = [];
  await page.route('**/v1/control-plane/**', async route => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    let body;
    if (path.endsWith('/model-status')) body = {
      model: 'fixture-local',
      provider: 'ollama',
      revision: 2,
      process_id: 1,
      consistency_scope: 'CURRENT_PROCESS_ONLY',
      availability: 'NOT_VERIFIED',
      status: 'NOT_VERIFIED',
      selection_enabled: false,
      selection_source: 'TEST_ONLY',
      last_request: null
    };else if (path.endsWith('/evidence-package')) body = {
      package_id: packageId,
      generated_at: '2026-10-19T10:00:00Z',
      read_scope: 'BROWSER_TEST_ONLY',
      runtime_status: 'NOT_VERIFIED',
      pass_allowed: allowed,
      blockers: allowed ? [] : [{
        id: 'AC1',
        reason: 'ARTIFACT_INVALID'
      }],
      criteria: Array.from({
        length: 15
      }, (_, i) => ({
        id: `AC${i + 1}`,
        summary: `Prasyarat uji ${i + 1}`,
        status: allowed ? 'VALID' : 'INVALID',
        evidence: ['proof'],
        tests: ['test_fixture'],
        reason: null
      })),
      evidence: [{
        id: 'proof',
        path: 'test-only/proof.json',
        classification: 'CURRENT_OFFLINE',
        validation_status: 'VALID',
        sha256: null,
        bytes: 4,
        reason: null
      }, {
        id: 'missing',
        path: 'test-only/missing.json',
        classification: 'CURRENT_OFFLINE',
        validation_status: 'MISSING',
        sha256: null,
        bytes: null,
        reason: 'ARTIFACT_INVALID'
      }]
    };else if (!authorized) return route.fulfill({
      status: 403,
      json: {
        detail: 'FORBIDDEN'
      }
    });else if (path.endsWith('/history')) body = {
      decisions,
      executions: [{
        timestamp: plan.checked_at,
        change_id: 'previous-fixture',
        package_id: packageId,
        decision_id: null,
        result: 'BLOCKED',
        files_changed: [],
        reason: 'TEST_ONLY_BLOCKED'
      }],
      decision_audit: 'VALIDATED_HASH_CHAIN',
      execution_audit: 'BROWSER_TEST_ONLY'
    };else if (path.endsWith('/execution-context')) body = plan;else if (path.endsWith('/operations-summary')) body = {
      scope: 'BROWSER_TEST_ONLY',
      source: 'fixture',
      pending_work: 1,
      pending_review: 1,
      reason: null,
      checked_at: plan.checked_at,
      tasks: [{
        id: plan.change_id,
        objective: plan.objective,
        status: 'HOLD',
        updated_at: plan.checked_at,
        source: 'BROWSER_TEST_ONLY'
      }]
    };else if (path.endsWith('/decisions') && request.method() === 'POST') {
      const submitted = request.postDataJSON();
      posts.push(submitted);
      if (reject) return route.fulfill({
        status: 409,
        json: {
          detail: 'EVIDENCE_PACKAGE_CHANGED'
        }
      });
      const record = {
        package_id: packageId,
        decision: submitted.decision,
        decision_id: 'dec_' + String(posts.length).padStart(32, '0'),
        notes: submitted.notes,
        plan_binding: binding,
        reviewer_principal: 'ISOLATED_BROWSER_TEST',
        authentication: 'TEST_ONLY',
        timestamp: new Date().toISOString(),
        test_evidence: ['proof'],
        blockers: [],
        record_hash: 'c'.repeat(64)
      };
      decisions.push(record);
      body = record;
    } else return route.abort();
    await route.fulfill({
      json: body
    });
  });
  await page.goto('/approvals');
  await page.getByRole('button', {
    name: 'Akses operator ↗'
  }).click();
  await page.getByLabel('Token operator', {
    exact: true
  }).fill('isolated-browser-test');
  await expect(page.getByRole('dialog', {
    name: 'Akses operator'
  }).getByText('Operator terautentikasi sebagai pemegang token admin bersama.')).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('navigation', {
    name: 'Navigasi operator'
  }).getByRole('link', {
    name: /AI Workspace/
  }).click();
  await expect(page.getByText(plan.objective).first()).toBeVisible();
  await page.getByRole('button', {
    name: 'Buka detail tugas ↗'
  }).click();
  await expect(page.getByRole('dialog')).toContainText('fixture.txt');
  await page.keyboard.press('Escape');
  await page.getByRole('searchbox', {
    name: 'Cari tugas yang dimuat'
  }).fill('tidak-cocok');
  await expect(page.getByText('Tidak ada tugas yang cocok dalam cakupan yang dibaca.')).toBeVisible();
  await page.getByRole('searchbox').fill('');
  await page.getByRole('button', {
    name: 'Tugas isolated-plan ↗'
  }).click();
  await expect(page.getByRole('dialog')).toContainText('BROWSER_TEST_ONLY');
  await page.keyboard.press('Escape');
  await page.getByRole('tab', {
    name: /Evidence/
  }).click();
  await page.getByRole('group', {
    name: 'Filter evidence'
  }).getByRole('button', {
    name: 'MISSING',
    exact: true
  }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await page.screenshot({
    path: resolve(output, `fixture-evidence-filter-${width}.png`),
    fullPage: true
  });
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', {
    name: 'Ekspor JSON'
  }).click();
  const download = await downloading;
  const downloaded = JSON.parse(readFileSync(await download.path(), 'utf8'));
  expect(downloaded.package.package_id).toBe(packageId);
  expect(downloaded.package.evidence).toHaveLength(2);
  await page.getByRole('navigation', {
    name: 'Navigasi operator'
  }).getByRole('link', {
    name: /Human Control/
  }).click();
  for (const choice of ['PASS', 'FAIL', 'HOLD']) {
    const prior = posts.length;
    await page.getByRole('button', {
      name: 'Tinjau & beri keputusan',
      exact: true
    }).click();
    const dialog = page.getByRole('dialog', {
      name: 'Tinjau keputusan Anda'
    });
    await dialog.getByRole('button', {
      name: new RegExp(choice)
    }).click();
    if (choice === 'PASS') {
      await dialog.getByRole('button', {
        name: 'Periksa evidence sebelum memutuskan'
      }).click();
      await expect(page.getByRole('dialog', {
        name: 'Paket evidence'
      })).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(dialog).toBeVisible();
    }
    expect(posts.length).toBe(prior);
    await dialog.getByLabel('Alasan keputusan (opsional)').fill(`Keputusan ${choice} dalam fixture`);
    await page.screenshot({
      path: resolve(output, `fixture-decision-${choice}-${width}.png`)
    });
    await dialog.getByRole('button', {
      name: 'Simpan keputusan'
    }).click();
    await expect(dialog).not.toBeVisible();
    await expect(page.getByRole('region', {
      name: 'History'
    }).getByRole('cell', {
      name: new RegExp(`Keputusan ${choice} dalam fixture`)
    })).toBeVisible();
  }
  for (const filter of ['Keputusan', 'Eksekusi', 'Semua']) await page.getByRole('group', {
    name: 'Filter riwayat'
  }).getByRole('button', {
    name: filter,
    exact: true
  }).click();
  await page.getByRole('button', {
    name: /^Keputusan dec_/
  }).first().click();
  await expect(page.getByRole('dialog')).toContainText('ISOLATED_BROWSER_TEST');
  await page.keyboard.press('Escape');
  await page.getByRole('button', {
    name: 'Eksekusi previous-fixture 1 ↗'
  }).click();
  await expect(page.getByRole('dialog')).toContainText('TEST_ONLY_BLOCKED');
  await page.keyboard.press('Escape');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: resolve(output, `fixture-human-history-${width}.png`),
    fullPage: true
  });
  allowed = false;
  reject = true;
  await page.getByRole('button', {
    name: 'Muat ulang review',
    exact: true
  }).click();
  await page.getByRole('button', {
    name: 'Tinjau & beri keputusan',
    exact: true
  }).click();
  let dialog = page.getByRole('dialog', {
    name: 'Tinjau keputusan Anda'
  });
  await expect(dialog.getByRole('button', {
    name: /PASS/
  })).toBeDisabled();
  await dialog.getByRole('button', {
    name: /HOLD/
  }).click();
  await dialog.getByRole('button', {
    name: 'Simpan keputusan'
  }).click();
  await expect(dialog.getByRole('status')).toContainText('evidence package changed');
  await expect(dialog).toBeVisible();
  await page.keyboard.press('Escape');
  authorized = false;
  await page.getByRole('button', {
    name: 'Akses operator ↗'
  }).click();
  await page.getByLabel('Token operator', {
    exact: true
  }).fill('invalid-browser-test');
  await page.keyboard.press('Escape');
  await page.getByRole('button', {
    name: 'Tinjau & beri keputusan',
    exact: true
  }).click();
  dialog = page.getByRole('dialog', {
    name: 'Tinjau keputusan Anda'
  });
  await expect(dialog.getByRole('button', {
    name: /HOLD/
  })).toBeDisabled();
  await expect(dialog.getByRole('button', {
    name: 'Simpan keputusan'
  })).toBeDisabled();
  expect(posts).toHaveLength(4);
  expect(posts.every(p => p.plan_binding.version === binding.version)).toBe(true);
  writeFileSync(resolve(output, `isolated-browser-contract-${width}.json`), JSON.stringify({
    scope: 'MOCK_API_ONLY; production mutations intercepted',
    decisions: posts.map(p => p.decision),
    binding,
    unauthorizedBlocked: true,
    exportPackageVerified: true
  }, null, 2));
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6WyJ0ZXN0IiwiZXhwZWN0IiwicmVhZEZpbGVTeW5jIiwid3JpdGVGaWxlU3luYyIsInJlc29sdmUiLCJvdXRwdXQiLCJyZWZlcmVuY2UiLCJzZXJ2ZVJlZmVyZW5jZSIsInBhZ2UiLCJyb3V0ZSIsIm5hbWUiLCJVUkwiLCJyZXF1ZXN0IiwidXJsIiwicGF0aG5hbWUiLCJzcGxpdCIsImF0IiwiaW5jbHVkZXMiLCJhYm9ydCIsImZ1bGZpbGwiLCJib2R5IiwiY29udGVudFR5cGUiLCJlbmRzV2l0aCIsInJlcG9ydCIsIndpZHRoIiwic2V0Vmlld3BvcnRTaXplIiwiaGVpZ2h0IiwicmVmIiwibG9jYWwiLCJfcHJvY2VzcyRlbnYkTkNQX0NBUFQiLCJnb3RvIiwiZ2V0QnlSb2xlIiwiZXhhY3QiLCJ0b0JlVmlzaWJsZSIsInRhYnMiLCJzY3JlZW5zaG90IiwicGF0aCIsImZ1bGxQYWdlIiwidGFiIiwibG9jYXRvciIsImZpbHRlciIsImhhc1RleHQiLCJmaXJzdCIsImNsaWNrIiwicHVzaCIsInN1cmZhY2UiLCJ0b0NvbnRhaW5UZXh0IiwicHJvY2VzcyIsImVudiIsIk5DUF9DQVBUVVJFX1NUQUdFIiwiSlNPTiIsInN0cmluZ2lmeSIsInNldFRpbWVvdXQiLCJlbXVsYXRlTWVkaWEiLCJyZWR1Y2VkTW90aW9uIiwiaW5zcGVjdGVkIiwia2V5Ym9hcmQiLCJwcmVzcyIsImlkIiwiYmxvY2tlcnMiLCJjb3VudCIsImkiLCJudGgiLCJnYXRlcyIsInRvQmVEaXNhYmxlZCIsImNob2ljZSIsImJ1dHRvbiIsInRvSGF2ZUF0dHJpYnV0ZSIsIm11dGF0aW9ucyIsImVycm9ycyIsIm9uIiwiciIsInN0YXJ0c1dpdGgiLCJtZXRob2QiLCJlIiwibWVzc2FnZSIsImZvY3VzIiwiUmVnRXhwIiwiZXZhbHVhdGUiLCJkb2N1bWVudCIsImRvY3VtZW50RWxlbWVudCIsInNjcm9sbFdpZHRoIiwiaW5uZXJXaWR0aCIsInRvQmUiLCJnZXRCeVRleHQiLCJnZXRCeUxhYmVsIiwid2luZG93Iiwic2Nyb2xsVG8iLCJkcmF3ZXIiLCJ0b0JlRm9jdXNlZCIsInRvRXF1YWwiLCJ2aWV3cG9ydCIsInBhY2thZ2VJZCIsInJlcGVhdCIsImJpbmRpbmciLCJwbGFuX2lkIiwidmVyc2lvbiIsImFjdGlvbiIsInBsYW4iLCJjaGFuZ2VfaWQiLCJvYmplY3RpdmUiLCJleHBlY3RlZF9jaGFuZ2UiLCJ0YXJnZXRfZmlsZXMiLCJvcGVyYXRpb24iLCJwbGFuX2JpbmRpbmciLCJyaXNrIiwidGVzdHNfcmVxdWlyZWQiLCJyb2xsYmFjayIsImNoZWNrZWRfYXQiLCJzb3VyY2UiLCJhbGxvd2VkIiwiYXV0aG9yaXplZCIsInJlamVjdCIsImRlY2lzaW9ucyIsInBvc3RzIiwibW9kZWwiLCJwcm92aWRlciIsInJldmlzaW9uIiwicHJvY2Vzc19pZCIsImNvbnNpc3RlbmN5X3Njb3BlIiwiYXZhaWxhYmlsaXR5Iiwic3RhdHVzIiwic2VsZWN0aW9uX2VuYWJsZWQiLCJzZWxlY3Rpb25fc291cmNlIiwibGFzdF9yZXF1ZXN0IiwicGFja2FnZV9pZCIsImdlbmVyYXRlZF9hdCIsInJlYWRfc2NvcGUiLCJydW50aW1lX3N0YXR1cyIsInBhc3NfYWxsb3dlZCIsInJlYXNvbiIsImNyaXRlcmlhIiwiQXJyYXkiLCJmcm9tIiwibGVuZ3RoIiwiXyIsInN1bW1hcnkiLCJldmlkZW5jZSIsInRlc3RzIiwiY2xhc3NpZmljYXRpb24iLCJ2YWxpZGF0aW9uX3N0YXR1cyIsInNoYTI1NiIsImJ5dGVzIiwianNvbiIsImRldGFpbCIsImV4ZWN1dGlvbnMiLCJ0aW1lc3RhbXAiLCJkZWNpc2lvbl9pZCIsInJlc3VsdCIsImZpbGVzX2NoYW5nZWQiLCJkZWNpc2lvbl9hdWRpdCIsImV4ZWN1dGlvbl9hdWRpdCIsInNjb3BlIiwicGVuZGluZ193b3JrIiwicGVuZGluZ19yZXZpZXciLCJ0YXNrcyIsInVwZGF0ZWRfYXQiLCJzdWJtaXR0ZWQiLCJwb3N0RGF0YUpTT04iLCJyZWNvcmQiLCJkZWNpc2lvbiIsIlN0cmluZyIsInBhZFN0YXJ0Iiwibm90ZXMiLCJyZXZpZXdlcl9wcmluY2lwYWwiLCJhdXRoZW50aWNhdGlvbiIsIkRhdGUiLCJ0b0lTT1N0cmluZyIsInRlc3RfZXZpZGVuY2UiLCJyZWNvcmRfaGFzaCIsImZpbGwiLCJ0b0hhdmVDb3VudCIsImRvd25sb2FkaW5nIiwid2FpdEZvckV2ZW50IiwiZG93bmxvYWQiLCJkb3dubG9hZGVkIiwicGFyc2UiLCJwYWNrYWdlIiwidG9IYXZlTGVuZ3RoIiwicHJpb3IiLCJkaWFsb2ciLCJub3QiLCJldmVyeSIsInAiLCJtYXAiLCJ1bmF1dGhvcml6ZWRCbG9ja2VkIiwiZXhwb3J0UGFja2FnZVZlcmlmaWVkIl0sInNvdXJjZXMiOlsib3BlcmF0b3ItZm9sbG93dXAuc3BlYy50cyJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQge3Rlc3QsZXhwZWN0LHR5cGUgUGFnZX0gZnJvbSAnQHBsYXl3cmlnaHQvdGVzdCc7XHJcbmltcG9ydCB7cmVhZEZpbGVTeW5jLHdyaXRlRmlsZVN5bmN9IGZyb20gJ25vZGU6ZnMnO1xyXG5pbXBvcnQge3Jlc29sdmV9IGZyb20gJ25vZGU6cGF0aCc7XHJcbmNvbnN0IG91dHB1dD1yZXNvbHZlKCcuLi9hcnRpZmFjdHMvbmNwLXYxLXVpLWZvbGxvd3VwLTIwMjYxMDE5Jyk7XHJcbmNvbnN0IHJlZmVyZW5jZT1yZXNvbHZlKCcuLi9hcnRpZmFjdHMvbmNwLXYxLXVpLWxvY2FsLTIwMjYxMDE5L3JlZmVyZW5jZS9kaXN0Jyk7XHJcbmFzeW5jIGZ1bmN0aW9uIHNlcnZlUmVmZXJlbmNlKHBhZ2U6UGFnZSl7XHJcbiBhd2FpdCBwYWdlLnJvdXRlKCcqKi9fX3JlZmVyZW5jZV9fLyoqJyxhc3luYyByb3V0ZT0+e1xyXG4gIGNvbnN0IG5hbWU9bmV3IFVSTChyb3V0ZS5yZXF1ZXN0KCkudXJsKCkpLnBhdGhuYW1lLnNwbGl0KCcvJykuYXQoLTEpfHwnaW5kZXguaHRtbCc7XHJcbiAgaWYoIVsnaW5kZXguaHRtbCcsJ2FwcC5qcycsJ2NvcmUuanMnLCdzdHlsZXMuY3NzJ10uaW5jbHVkZXMobmFtZSkpcmV0dXJuIHJvdXRlLmFib3J0KCk7XHJcbiAgYXdhaXQgcm91dGUuZnVsZmlsbCh7Ym9keTpyZWFkRmlsZVN5bmMocmVzb2x2ZShyZWZlcmVuY2UsbmFtZSkpLGNvbnRlbnRUeXBlOm5hbWUuZW5kc1dpdGgoJy5qcycpPyd0ZXh0L2phdmFzY3JpcHQnOm5hbWUuZW5kc1dpdGgoJy5jc3MnKT8ndGV4dC9jc3MnOid0ZXh0L2h0bWwnfSk7XHJcbiB9KTtcclxufVxyXG50ZXN0KCdzYW1lIHZpZXdwb3J0IHJlZmVyZW5jZSBhbmQgbG9jYWwgY29tcGFyaXNvbicsYXN5bmMoe3BhZ2V9KT0+e1xyXG4gYXdhaXQgc2VydmVSZWZlcmVuY2UocGFnZSk7XHJcbiBjb25zdCByZXBvcnQ6dW5rbm93bltdPVtdO1xyXG4gZm9yKGNvbnN0IHdpZHRoIG9mIFsxNDQwLDM5MF0pe1xyXG4gIGF3YWl0IHBhZ2Uuc2V0Vmlld3BvcnRTaXplKHt3aWR0aCxoZWlnaHQ6d2lkdGg9PT0xNDQwPzEwMDA6ODQ0fSk7XHJcbiAgZm9yKGNvbnN0IFtyZWYsbG9jYWxdIG9mIFtbJ3dvcmtzcGFjZScsJ3dvcmtzcGFjZSddLFsnaHVtYW4nLCdhcHByb3ZhbHMnXV0pe1xyXG4gICBhd2FpdCBwYWdlLmdvdG8oYC9fX3JlZmVyZW5jZV9fL2luZGV4Lmh0bWwjJHtyZWZ9YCk7XHJcbiAgIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnaGVhZGluZycse25hbWU6cmVmPT09J3dvcmtzcGFjZSc/J0FJIFdvcmtzcGFjZSc6J0h1bWFuIENvbnRyb2wnLGV4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTtcclxuICAgY29uc3QgdGFicz1yZWY9PT0nd29ya3NwYWNlJz9bJ0FrdGl2aXRhcyB0dWdhcycsJ0Jsb2NrZXInLCdFdmlkZW5jZSddOltdO1xyXG4gICBhd2FpdCBwYWdlLnNjcmVlbnNob3Qoe3BhdGg6cmVzb2x2ZShvdXRwdXQsYHJlZmVyZW5jZS0ke3JlZn0tJHt3aWR0aH0ucG5nYCksZnVsbFBhZ2U6dHJ1ZX0pO1xyXG4gICBmb3IoY29uc3QgdGFiIG9mIHRhYnMpe1xyXG4gICAgYXdhaXQgcGFnZS5sb2NhdG9yKCdbZGF0YS1hY3Rpb249XCJ3b3Jrc3BhY2UtdGFiXCJdJykuZmlsdGVyKHtoYXNUZXh0OnRhYn0pLmZpcnN0KCkuY2xpY2soKTtcclxuICAgIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgcmVmZXJlbmNlLSR7cmVmfS0ke3RhYi5zcGxpdCgnICcpWzBdfS0ke3dpZHRofS5wbmdgKSxmdWxsUGFnZTp0cnVlfSk7XHJcbiAgIH1cclxuICAgcmVwb3J0LnB1c2goe3N1cmZhY2U6J3JlZmVyZW5jZScscGFnZTpyZWYsd2lkdGgsdGFic30pO1xyXG4gICBhd2FpdCBwYWdlLmdvdG8oYC8ke2xvY2FsfWApO1xyXG4gICBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2hlYWRpbmcnLHtuYW1lOnJlZj09PSd3b3Jrc3BhY2UnPydBSSBXb3Jrc3BhY2UnOidIdW1hbiBDb250cm9sJyxleGFjdDp0cnVlfSkpLnRvQmVWaXNpYmxlKCk7XHJcbiAgIGF3YWl0IGV4cGVjdChwYWdlLmxvY2F0b3IocmVmPT09J3dvcmtzcGFjZSc/Jy5vcC10YXNrLW1ldGEnOicub3AtaHVtYW4gLm9wLXNwZWNzJykuZmlyc3QoKSkudG9Db250YWluVGV4dCgvb2xsYW1hfG9wZW5yb3V0ZXIvaSk7XHJcbiAgIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgJHtwcm9jZXNzLmVudi5OQ1BfQ0FQVFVSRV9TVEFHRT8/J2FmdGVyJ30tJHtsb2NhbH0tJHt3aWR0aH0ucG5nYCksZnVsbFBhZ2U6dHJ1ZX0pO1xyXG4gIH1cclxuIH1cclxuIHdyaXRlRmlsZVN5bmMocmVzb2x2ZShvdXRwdXQsJ2NvbXBhcmlzb24tdmlld3BvcnRzLmpzb24nKSxKU09OLnN0cmluZ2lmeShyZXBvcnQsbnVsbCwyKSk7XHJcbn0pO1xyXG5cclxudGVzdCgncmVmZXJlbmNlIHRhYnMsIGZpbHRlcnMsIHRhc2svYmxvY2tlci9ldmlkZW5jZS9nYXRlIGFuZCBkZWNpc2lvbiBkcmF3ZXJzJyxhc3luYyh7cGFnZX0pPT57XHJcbiB0ZXN0LnNldFRpbWVvdXQoOTAwMDApO1xyXG4gYXdhaXQgcGFnZS5lbXVsYXRlTWVkaWEoe3JlZHVjZWRNb3Rpb246J3JlZHVjZSd9KTtcclxuIGF3YWl0IHNlcnZlUmVmZXJlbmNlKHBhZ2UpO1xyXG4gY29uc3QgaW5zcGVjdGVkOnN0cmluZ1tdPVtdO1xyXG4gZm9yKGNvbnN0IHdpZHRoIG9mIFsxNDQwLDM5MF0pe1xyXG4gIGF3YWl0IHBhZ2Uuc2V0Vmlld3BvcnRTaXplKHt3aWR0aCxoZWlnaHQ6d2lkdGg9PT0xNDQwPzEwMDA6ODQ0fSk7XHJcbiAgYXdhaXQgcGFnZS5nb3RvKCcvX19yZWZlcmVuY2VfXy9pbmRleC5odG1sI3dvcmtzcGFjZScpO1xyXG4gIGF3YWl0IHBhZ2UubG9jYXRvcignW2RhdGEtYWN0aW9uPVwid29ya3NwYWNlLXRhYlwiXVtkYXRhLWlkPVwidGFza3NcIl0nKS5jbGljaygpO1xyXG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidCdWthIGRldGFpbCB0dWdhcycsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XHJcbiAgYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9CZVZpc2libGUoKTtpbnNwZWN0ZWQucHVzaChgdGFzayBkcmF3ZXIgJHt3aWR0aH1gKTtcclxuICBhd2FpdCBwYWdlLnNjcmVlbnNob3Qoe3BhdGg6cmVzb2x2ZShvdXRwdXQsYHJlZmVyZW5jZS10YXNrLWRyYXdlci0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIGF3YWl0IHBhZ2UubG9jYXRvcignW2RhdGEtYWN0aW9uPVwid29ya3NwYWNlLXRhYlwiXVtkYXRhLWlkPVwiYmxvY2tlcnNcIl0nKS5jbGljaygpO1xyXG4gIGZvcihjb25zdCBpZCBvZiBbJ29wZW4nLCdyZXNvbHZlZCcsJ2FsbCddKXthd2FpdCBwYWdlLmxvY2F0b3IoYFtkYXRhLWFjdGlvbj1cImJsb2NrZXItZmlsdGVyXCJdW2RhdGEtaWQ9XCIke2lkfVwiXWApLmNsaWNrKCk7aW5zcGVjdGVkLnB1c2goYGJsb2NrZXIgZmlsdGVyICR7aWR9ICR7d2lkdGh9YCk7fVxyXG4gIGNvbnN0IGJsb2NrZXJzPWF3YWl0IHBhZ2UubG9jYXRvcignbWFpbiAuYmxvY2tlci1saXN0IFtkYXRhLWFjdGlvbj1cImJsb2NrZXJcIl0nKS5jb3VudCgpO1xyXG4gIGZvcihsZXQgaT0wO2k8YmxvY2tlcnM7aSsrKXtcclxuICAgYXdhaXQgcGFnZS5sb2NhdG9yKCdtYWluIC5ibG9ja2VyLWxpc3QgW2RhdGEtYWN0aW9uPVwiYmxvY2tlclwiXScpLm50aChpKS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnZGlhbG9nJykpLnRvQmVWaXNpYmxlKCk7XHJcbiAgIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgcmVmZXJlbmNlLWJsb2NrZXItJHtpfS0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIH1cclxuICBhd2FpdCBwYWdlLmxvY2F0b3IoJ1tkYXRhLWFjdGlvbj1cIndvcmtzcGFjZS10YWJcIl1bZGF0YS1pZD1cImV2aWRlbmNlXCJdJykuY2xpY2soKTtcclxuICBmb3IoY29uc3QgZmlsdGVyIG9mIFsnUEFTUycsJ0ZBSUwnLCdIT0xEJywnQUxMJ10pe2F3YWl0IHBhZ2UubG9jYXRvcihgW2RhdGEtYWN0aW9uPVwiZXZpZGVuY2UtZmlsdGVyXCJdW2RhdGEtaWQ9XCIke2ZpbHRlcn1cIl1gKS5jbGljaygpO2luc3BlY3RlZC5wdXNoKGBldmlkZW5jZSBmaWx0ZXIgJHtmaWx0ZXJ9ICR7d2lkdGh9YCk7fVxyXG4gIGF3YWl0IHBhZ2UubG9jYXRvcigndGJvZHkgW2RhdGEtYWN0aW9uPVwiZXZpZGVuY2VcIl0nKS5maXJzdCgpLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9CZVZpc2libGUoKTtcclxuICBhd2FpdCBwYWdlLnNjcmVlbnNob3Qoe3BhdGg6cmVzb2x2ZShvdXRwdXQsYHJlZmVyZW5jZS1ldmlkZW5jZS1kcmF3ZXItJHt3aWR0aH0ucG5nYCl9KTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuICBhd2FpdCBwYWdlLmdvdG8oJy9fX3JlZmVyZW5jZV9fL2luZGV4Lmh0bWwjaHVtYW4nKTtcclxuICBjb25zdCBnYXRlcz1wYWdlLmxvY2F0b3IoJy5nYXRlLWl0ZW0nKTtcclxuICBmb3IobGV0IGk9MDtpPGF3YWl0IGdhdGVzLmNvdW50KCk7aSsrKXtcclxuICAgYXdhaXQgZ2F0ZXMubnRoKGkpLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9CZVZpc2libGUoKTtpbnNwZWN0ZWQucHVzaChgZ2F0ZSAke2krMX0gJHt3aWR0aH1gKTtcclxuICAgYXdhaXQgcGFnZS5zY3JlZW5zaG90KHtwYXRoOnJlc29sdmUob3V0cHV0LGByZWZlcmVuY2UtZ2F0ZS0ke2krMX0tJHt3aWR0aH0ucG5nYCl9KTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuICB9XHJcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1RpbmphdSAmIGJlcmkga2VwdXR1c2FuJyxleGFjdDp0cnVlfSkuY2xpY2soKTtcclxuICBhd2FpdCBleHBlY3QocGFnZS5sb2NhdG9yKCdbZGF0YS1hY3Rpb249XCJzZWxlY3QtZGVjaXNpb25cIl1bZGF0YS1pZD1cIlBBU1NcIl0nKSkudG9CZURpc2FibGVkKCk7XHJcbiAgZm9yKGNvbnN0IGNob2ljZSBvZiBbJ0ZBSUwnLCdIT0xEJ10pe2NvbnN0IGJ1dHRvbj1wYWdlLmxvY2F0b3IoYFtkYXRhLWFjdGlvbj1cInNlbGVjdC1kZWNpc2lvblwiXVtkYXRhLWlkPVwiJHtjaG9pY2V9XCJdYCk7YXdhaXQgYnV0dG9uLmNsaWNrKCk7YXdhaXQgZXhwZWN0KGJ1dHRvbikudG9IYXZlQXR0cmlidXRlKCdhcmlhLXByZXNzZWQnLCd0cnVlJyk7fVxyXG4gIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgcmVmZXJlbmNlLWRlY2lzaW9uLWRyYXdlci0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidMaWhhdCBrZWJpamFrYW4nLGV4YWN0OnRydWV9KS5jbGljaygpO1xyXG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnaGVhZGluZycse25hbWU6J1BlbmdhdHVyYW4gJiBUZWtuaXMnLGV4YWN0OnRydWV9KSkudG9CZVZpc2libGUoKTtpbnNwZWN0ZWQucHVzaChgcG9saWN5IGxpbmsgJHt3aWR0aH1gKTtcclxuIH1cclxuIHdyaXRlRmlsZVN5bmMocmVzb2x2ZShvdXRwdXQsJ3JlZmVyZW5jZS1pbnRlcmFjdGlvbi1jaGVja2xpc3QuanNvbicpLEpTT04uc3RyaW5naWZ5KGluc3BlY3RlZCxudWxsLDIpKTtcclxufSk7XHJcblxyXG50ZXN0KCdsaXZlIHdvcmtzcGFjZSBhbmQgaHVtYW4gY29udHJvbHMgcmVtYWluIHJlYWQgb25seSB3aGlsZSBicm93c2luZycsYXN5bmMoe3BhZ2V9KT0+e1xyXG4gY29uc3QgbXV0YXRpb25zOnN0cmluZ1tdPVtdLGVycm9yczpzdHJpbmdbXT1bXTtcclxuIHBhZ2Uub24oJ3JlcXVlc3QnLHI9PntpZihuZXcgVVJMKHIudXJsKCkpLnBhdGhuYW1lLnN0YXJ0c1dpdGgoJy92MS8nKSYmci5tZXRob2QoKSE9PSdHRVQnKW11dGF0aW9ucy5wdXNoKGAke3IubWV0aG9kKCl9ICR7bmV3IFVSTChyLnVybCgpKS5wYXRobmFtZX1gKTt9KTtcclxuIHBhZ2Uub24oJ3BhZ2VlcnJvcicsZT0+ZXJyb3JzLnB1c2goZS5tZXNzYWdlKSk7XHJcbiBmb3IoY29uc3Qgd2lkdGggb2YgWzE0NDAsMzkwXSl7XHJcbiAgYXdhaXQgcGFnZS5zZXRWaWV3cG9ydFNpemUoe3dpZHRoLGhlaWdodDp3aWR0aD09PTE0NDA/MTAwMDo4NDR9KTthd2FpdCBwYWdlLmdvdG8oJy93b3Jrc3BhY2UnKTtcclxuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonRm9rdXMgUElBSy0wMyDihpcnfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycpKS50b0JlVmlzaWJsZSgpO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCd0YWInLHtuYW1lOidBa3Rpdml0YXMgdHVnYXMnfSkuZm9jdXMoKTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdBcnJvd1JpZ2h0Jyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCd0YWInLHtuYW1lOi9CbG9ja2VyL30pKS50b0hhdmVBdHRyaWJ1dGUoJ2FyaWEtc2VsZWN0ZWQnLCd0cnVlJyk7XHJcbiAgZm9yKGNvbnN0IHRhYiBvZiBbJ0FrdGl2aXRhcyB0dWdhcycsJ0Jsb2NrZXInLCdFdmlkZW5jZScsJ0NoYXQgVjEnXSl7XHJcbiAgIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCd0YWInLHtuYW1lOm5ldyBSZWdFeHAoYF4ke3RhYn1gKX0pLmNsaWNrKCk7XHJcbiAgIGV4cGVjdChhd2FpdCBwYWdlLmV2YWx1YXRlKCgpPT5kb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuc2Nyb2xsV2lkdGg8PWlubmVyV2lkdGgpKS50b0JlKHRydWUpO1xyXG4gICBpZih0YWI9PT0nQmxvY2tlcicpe1xyXG4gICAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1NlbGVzYWknLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5VGV4dCgvUml3YXlhdCBwZW55ZWxlc2FpYW4gYmxvY2tlci8pKS50b0JlVmlzaWJsZSgpO1xyXG4gICAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1RlcmJ1a2EnLGV4YWN0OnRydWV9KS5jbGljaygpO1xyXG4gICAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6L15EZXRhaWwgYmxvY2tlci99KS5maXJzdCgpLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9CZVZpc2libGUoKTtcclxuICAgIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgbGl2ZS1ibG9ja2VyLWRyYXdlci0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gICB9XHJcbiAgIGlmKHRhYj09PSdFdmlkZW5jZScpe1xyXG4gICAgYXdhaXQgZXhwZWN0KHBhZ2UubG9jYXRvcignLm9wLWV2aWRlbmNlIHRib2R5IHRyJykuZmlyc3QoKSkudG9CZVZpc2libGUoKTtcclxuICAgIGF3YWl0IHBhZ2UubG9jYXRvcignLm9wLWV2aWRlbmNlIHRib2R5IC5kZXRhaWwtdHJpZ2dlcicpLmZpcnN0KCkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycpKS50b0JlVmlzaWJsZSgpO1xyXG4gICAgYXdhaXQgcGFnZS5zY3JlZW5zaG90KHtwYXRoOnJlc29sdmUob3V0cHV0LGBsaXZlLWV2aWRlbmNlLWRyYXdlci0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gICB9XHJcbiAgIGlmKHRhYj09PSdDaGF0IFYxJylhd2FpdCBleHBlY3QocGFnZS5nZXRCeUxhYmVsKCdQZXJ0YW55YWFuIEFuZGEnKSkudG9CZVZpc2libGUoKTtcclxuICAgYXdhaXQgcGFnZS5ldmFsdWF0ZSgoKT0+d2luZG93LnNjcm9sbFRvKDAsMCkpO2F3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgbGl2ZS13b3Jrc3BhY2UtJHt0YWIuc3BsaXQoJyAnKVswXX0tJHt3aWR0aH0ucG5nYCksZnVsbFBhZ2U6dHJ1ZX0pO1xyXG4gIH1cclxuICBhd2FpdCBwYWdlLmdvdG8oJy9hcHByb3ZhbHMnKTtcclxuICBmb3IoY29uc3QgbmFtZSBvZiBbJ0V2aWRlbmNlIHZhbGlkJywnUGxhbiBzaWFwJywnT3BlcmF0b3IgdGVyYXV0ZW50aWthc2knLCdLZXB1dHVzYW4gdGVyc2VkaWEnLCdJemluIGVrc2VrdXNpJ10pe1xyXG4gICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpgJHtuYW1lfSDihpdgLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnZGlhbG9nJykpLnRvQmVWaXNpYmxlKCk7XHJcbiAgIGF3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIH1cclxuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonVGluamF1ICYgYmVyaSBrZXB1dHVzYW4nLGV4YWN0OnRydWV9KS5jbGljaygpO2NvbnN0IGRyYXdlcj1wYWdlLmdldEJ5Um9sZSgnZGlhbG9nJyx7bmFtZTonVGluamF1IGtlcHV0dXNhbiBBbmRhJ30pO1xyXG4gIGZvcihjb25zdCBuYW1lIG9mIFsnUEFTUycsJ0ZBSUwnLCdIT0xEJ10pYXdhaXQgZXhwZWN0KGRyYXdlci5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6bmV3IFJlZ0V4cChuYW1lKX0pKS50b0JlRGlzYWJsZWQoKTtcclxuICBhd2FpdCBleHBlY3QoZHJhd2VyLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonU2ltcGFuIGtlcHV0dXNhbid9KSkudG9CZURpc2FibGVkKCk7XHJcbiAgYXdhaXQgcGFnZS5zY3JlZW5zaG90KHtwYXRoOnJlc29sdmUob3V0cHV0LGBsaXZlLWRlY2lzaW9uLWxvY2tlZC0ke3dpZHRofS5wbmdgKX0pO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonVGluamF1ICYgYmVyaSBrZXB1dHVzYW4nLGV4YWN0OnRydWV9KSkudG9CZUZvY3VzZWQoKTtcclxuICBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonTGloYXQga2ViaWpha2FuIOKGlyd9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnZGlhbG9nJykpLnRvQmVWaXNpYmxlKCk7YXdhaXQgcGFnZS5rZXlib2FyZC5wcmVzcygnRXNjYXBlJyk7XHJcbiAgYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1Blcmlrc2EgZXZpZGVuY2UnLGV4YWN0OnRydWV9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnZGlhbG9nJyx7bmFtZTonUGFrZXQgZXZpZGVuY2UnfSkpLnRvQmVWaXNpYmxlKCk7YXdhaXQgcGFnZS5rZXlib2FyZC5wcmVzcygnRXNjYXBlJyk7XHJcbiAgZm9yKGNvbnN0IG5hbWUgb2YgWydLZXB1dHVzYW4nLCdFa3Nla3VzaScsJ1NlbXVhJ10pYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2dyb3VwJyx7bmFtZTonRmlsdGVyIHJpd2F5YXQnfSkuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lLGV4YWN0OnRydWV9KS5jbGljaygpO1xyXG4gIGV4cGVjdChhd2FpdCBwYWdlLmV2YWx1YXRlKCgpPT5kb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuc2Nyb2xsV2lkdGg8PWlubmVyV2lkdGgpKS50b0JlKHRydWUpO1xyXG4gfVxyXG4gZXhwZWN0KG11dGF0aW9ucykudG9FcXVhbChbXSk7ZXhwZWN0KGVycm9ycykudG9FcXVhbChbXSk7XHJcbiB3cml0ZUZpbGVTeW5jKHJlc29sdmUob3V0cHV0LCdsaXZlLXJlYWRvbmx5LWNoZWNrcy5qc29uJyksSlNPTi5zdHJpbmdpZnkoe211dGF0aW9ucyxlcnJvcnMsdmlld3BvcnQ6WzE0NDAsMzkwXX0sbnVsbCwyKSk7XHJcbn0pO1xyXG5cclxuZm9yKGNvbnN0IHdpZHRoIG9mIFsxNDQwLDM5MF0pdGVzdChgaXNvbGF0ZWQgYnJvd3NlciBjb250cmFjdCBhdCAke3dpZHRofTogdGFza3MsIGZpbHRlcnMsIGRlY2lzaW9ucywgaGlzdG9yeSwgcmVqZWN0aW9uIGFuZCBsb3N0IGF1dGhvcml6YXRpb25gLGFzeW5jKHtwYWdlfSk9PntcclxuIGF3YWl0IHBhZ2Uuc2V0Vmlld3BvcnRTaXplKHt3aWR0aCxoZWlnaHQ6d2lkdGg9PT0xNDQwPzEwMDA6ODQ0fSk7XHJcbiBjb25zdCBwYWNrYWdlSWQ9J2V2cF9zaGEyNTZfJysnYicucmVwZWF0KDY0KSxiaW5kaW5nPXtwbGFuX2lkOidpc29sYXRlZC1wbGFuJyx2ZXJzaW9uOidpc29sYXRlZC12MScsYWN0aW9uOidDT05UUk9MTEVEX0ZJTEVfV1JJVEUnfTtcclxuIGNvbnN0IHBsYW49e2NoYW5nZV9pZDonaXNvbGF0ZWQtcGxhbicsb2JqZWN0aXZlOidUdWdhcyBQSUFLLTAzIOKAlCBmaXh0dXJlIHRlcmlzb2xhc2knLGV4cGVjdGVkX2NoYW5nZTonQ29udG9oIHBlbmd1amlhbiBVSSwgYnVrYW4gdHVnYXMgcHJvZHVrc2knLHRhcmdldF9maWxlczpbJ2ZpeHR1cmUudHh0J10sb3BlcmF0aW9uOid3cml0ZScscGxhbl9iaW5kaW5nOmJpbmRpbmcscmlzazonTE9XJyx0ZXN0c19yZXF1aXJlZDpbJ3Rlc3RfZml4dHVyZSddLHJvbGxiYWNrOidyZXN0b3JlIGZpeHR1cmUnLGNoZWNrZWRfYXQ6JzIwMjYtMTAtMTlUMTA6MDA6MDBaJyxzb3VyY2U6J0JST1dTRVJfVEVTVF9PTkxZJ307XHJcbiBsZXQgYWxsb3dlZD10cnVlLGF1dGhvcml6ZWQ9dHJ1ZSxyZWplY3Q9ZmFsc2U7XHJcbiBjb25zdCBkZWNpc2lvbnM6UmVjb3JkPHN0cmluZyx1bmtub3duPltdPVtdLHBvc3RzOlJlY29yZDxzdHJpbmcsdW5rbm93bj5bXT1bXTtcclxuIGF3YWl0IHBhZ2Uucm91dGUoJyoqL3YxL2NvbnRyb2wtcGxhbmUvKionLGFzeW5jIHJvdXRlPT57XHJcbiAgY29uc3QgcmVxdWVzdD1yb3V0ZS5yZXF1ZXN0KCkscGF0aD1uZXcgVVJMKHJlcXVlc3QudXJsKCkpLnBhdGhuYW1lO1xyXG4gIGxldCBib2R5OnVua25vd247XHJcbiAgaWYocGF0aC5lbmRzV2l0aCgnL21vZGVsLXN0YXR1cycpKWJvZHk9e21vZGVsOidmaXh0dXJlLWxvY2FsJyxwcm92aWRlcjonb2xsYW1hJyxyZXZpc2lvbjoyLHByb2Nlc3NfaWQ6MSxjb25zaXN0ZW5jeV9zY29wZTonQ1VSUkVOVF9QUk9DRVNTX09OTFknLGF2YWlsYWJpbGl0eTonTk9UX1ZFUklGSUVEJyxzdGF0dXM6J05PVF9WRVJJRklFRCcsc2VsZWN0aW9uX2VuYWJsZWQ6ZmFsc2Usc2VsZWN0aW9uX3NvdXJjZTonVEVTVF9PTkxZJyxsYXN0X3JlcXVlc3Q6bnVsbH07XHJcbiAgZWxzZSBpZihwYXRoLmVuZHNXaXRoKCcvZXZpZGVuY2UtcGFja2FnZScpKWJvZHk9e3BhY2thZ2VfaWQ6cGFja2FnZUlkLGdlbmVyYXRlZF9hdDonMjAyNi0xMC0xOVQxMDowMDowMFonLHJlYWRfc2NvcGU6J0JST1dTRVJfVEVTVF9PTkxZJyxydW50aW1lX3N0YXR1czonTk9UX1ZFUklGSUVEJyxwYXNzX2FsbG93ZWQ6YWxsb3dlZCxibG9ja2VyczphbGxvd2VkP1tdOlt7aWQ6J0FDMScscmVhc29uOidBUlRJRkFDVF9JTlZBTElEJ31dLGNyaXRlcmlhOkFycmF5LmZyb20oe2xlbmd0aDoxNX0sKF8saSk9Pih7aWQ6YEFDJHtpKzF9YCxzdW1tYXJ5OmBQcmFzeWFyYXQgdWppICR7aSsxfWAsc3RhdHVzOmFsbG93ZWQ/J1ZBTElEJzonSU5WQUxJRCcsZXZpZGVuY2U6Wydwcm9vZiddLHRlc3RzOlsndGVzdF9maXh0dXJlJ10scmVhc29uOm51bGx9KSksZXZpZGVuY2U6W3tpZDoncHJvb2YnLHBhdGg6J3Rlc3Qtb25seS9wcm9vZi5qc29uJyxjbGFzc2lmaWNhdGlvbjonQ1VSUkVOVF9PRkZMSU5FJyx2YWxpZGF0aW9uX3N0YXR1czonVkFMSUQnLHNoYTI1NjpudWxsLGJ5dGVzOjQscmVhc29uOm51bGx9LHtpZDonbWlzc2luZycscGF0aDondGVzdC1vbmx5L21pc3NpbmcuanNvbicsY2xhc3NpZmljYXRpb246J0NVUlJFTlRfT0ZGTElORScsdmFsaWRhdGlvbl9zdGF0dXM6J01JU1NJTkcnLHNoYTI1NjpudWxsLGJ5dGVzOm51bGwscmVhc29uOidBUlRJRkFDVF9JTlZBTElEJ31dfTtcclxuICBlbHNlIGlmKCFhdXRob3JpemVkKXJldHVybiByb3V0ZS5mdWxmaWxsKHtzdGF0dXM6NDAzLGpzb246e2RldGFpbDonRk9SQklEREVOJ319KTtcclxuICBlbHNlIGlmKHBhdGguZW5kc1dpdGgoJy9oaXN0b3J5JykpYm9keT17ZGVjaXNpb25zLGV4ZWN1dGlvbnM6W3t0aW1lc3RhbXA6cGxhbi5jaGVja2VkX2F0LGNoYW5nZV9pZDoncHJldmlvdXMtZml4dHVyZScscGFja2FnZV9pZDpwYWNrYWdlSWQsZGVjaXNpb25faWQ6bnVsbCxyZXN1bHQ6J0JMT0NLRUQnLGZpbGVzX2NoYW5nZWQ6W10scmVhc29uOidURVNUX09OTFlfQkxPQ0tFRCd9XSxkZWNpc2lvbl9hdWRpdDonVkFMSURBVEVEX0hBU0hfQ0hBSU4nLGV4ZWN1dGlvbl9hdWRpdDonQlJPV1NFUl9URVNUX09OTFknfTtcclxuICBlbHNlIGlmKHBhdGguZW5kc1dpdGgoJy9leGVjdXRpb24tY29udGV4dCcpKWJvZHk9cGxhbjtcclxuICBlbHNlIGlmKHBhdGguZW5kc1dpdGgoJy9vcGVyYXRpb25zLXN1bW1hcnknKSlib2R5PXtzY29wZTonQlJPV1NFUl9URVNUX09OTFknLHNvdXJjZTonZml4dHVyZScscGVuZGluZ193b3JrOjEscGVuZGluZ19yZXZpZXc6MSxyZWFzb246bnVsbCxjaGVja2VkX2F0OnBsYW4uY2hlY2tlZF9hdCx0YXNrczpbe2lkOnBsYW4uY2hhbmdlX2lkLG9iamVjdGl2ZTpwbGFuLm9iamVjdGl2ZSxzdGF0dXM6J0hPTEQnLHVwZGF0ZWRfYXQ6cGxhbi5jaGVja2VkX2F0LHNvdXJjZTonQlJPV1NFUl9URVNUX09OTFknfV19O1xyXG4gIGVsc2UgaWYocGF0aC5lbmRzV2l0aCgnL2RlY2lzaW9ucycpJiZyZXF1ZXN0Lm1ldGhvZCgpPT09J1BPU1QnKXtcclxuICAgY29uc3Qgc3VibWl0dGVkPXJlcXVlc3QucG9zdERhdGFKU09OKCk7cG9zdHMucHVzaChzdWJtaXR0ZWQpO1xyXG4gICBpZihyZWplY3QpcmV0dXJuIHJvdXRlLmZ1bGZpbGwoe3N0YXR1czo0MDksanNvbjp7ZGV0YWlsOidFVklERU5DRV9QQUNLQUdFX0NIQU5HRUQnfX0pO1xyXG4gICBjb25zdCByZWNvcmQ9e3BhY2thZ2VfaWQ6cGFja2FnZUlkLGRlY2lzaW9uOnN1Ym1pdHRlZC5kZWNpc2lvbixkZWNpc2lvbl9pZDonZGVjXycrU3RyaW5nKHBvc3RzLmxlbmd0aCkucGFkU3RhcnQoMzIsJzAnKSxub3RlczpzdWJtaXR0ZWQubm90ZXMscGxhbl9iaW5kaW5nOmJpbmRpbmcscmV2aWV3ZXJfcHJpbmNpcGFsOidJU09MQVRFRF9CUk9XU0VSX1RFU1QnLGF1dGhlbnRpY2F0aW9uOidURVNUX09OTFknLHRpbWVzdGFtcDpuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCksdGVzdF9ldmlkZW5jZTpbJ3Byb29mJ10sYmxvY2tlcnM6W10scmVjb3JkX2hhc2g6J2MnLnJlcGVhdCg2NCl9O1xyXG4gICBkZWNpc2lvbnMucHVzaChyZWNvcmQpO2JvZHk9cmVjb3JkO1xyXG4gIH1lbHNlIHJldHVybiByb3V0ZS5hYm9ydCgpO1xyXG4gIGF3YWl0IHJvdXRlLmZ1bGZpbGwoe2pzb246Ym9keX0pO1xyXG4gfSk7XHJcbiBhd2FpdCBwYWdlLmdvdG8oJy9hcHByb3ZhbHMnKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQWtzZXMgb3BlcmF0b3Ig4oaXJ30pLmNsaWNrKCk7XHJcbiBhd2FpdCBwYWdlLmdldEJ5TGFiZWwoJ1Rva2VuIG9wZXJhdG9yJyx7ZXhhY3Q6dHJ1ZX0pLmZpbGwoJ2lzb2xhdGVkLWJyb3dzZXItdGVzdCcpO1xyXG4gYXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnLHtuYW1lOidBa3NlcyBvcGVyYXRvcid9KS5nZXRCeVRleHQoJ09wZXJhdG9yIHRlcmF1dGVudGlrYXNpIHNlYmFnYWkgcGVtZWdhbmcgdG9rZW4gYWRtaW4gYmVyc2FtYS4nKSkudG9CZVZpc2libGUoKTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCduYXZpZ2F0aW9uJyx7bmFtZTonTmF2aWdhc2kgb3BlcmF0b3InfSkuZ2V0QnlSb2xlKCdsaW5rJyx7bmFtZTovQUkgV29ya3NwYWNlL30pLmNsaWNrKCk7XHJcbiBhd2FpdCBleHBlY3QocGFnZS5nZXRCeVRleHQocGxhbi5vYmplY3RpdmUpLmZpcnN0KCkpLnRvQmVWaXNpYmxlKCk7XHJcbiBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQnVrYSBkZXRhaWwgdHVnYXMg4oaXJ30pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9Db250YWluVGV4dCgnZml4dHVyZS50eHQnKTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdzZWFyY2hib3gnLHtuYW1lOidDYXJpIHR1Z2FzIHlhbmcgZGltdWF0J30pLmZpbGwoJ3RpZGFrLWNvY29rJyk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlUZXh0KCdUaWRhayBhZGEgdHVnYXMgeWFuZyBjb2NvayBkYWxhbSBjYWt1cGFuIHlhbmcgZGliYWNhLicpKS50b0JlVmlzaWJsZSgpO1xyXG4gYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ3NlYXJjaGJveCcpLmZpbGwoJycpO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidUdWdhcyBpc29sYXRlZC1wbGFuIOKGlyd9KS5jbGljaygpO2F3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgnZGlhbG9nJykpLnRvQ29udGFpblRleHQoJ0JST1dTRVJfVEVTVF9PTkxZJyk7YXdhaXQgcGFnZS5rZXlib2FyZC5wcmVzcygnRXNjYXBlJyk7XHJcbiBhd2FpdCBwYWdlLmdldEJ5Um9sZSgndGFiJyx7bmFtZTovRXZpZGVuY2UvfSkuY2xpY2soKTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnZ3JvdXAnLHtuYW1lOidGaWx0ZXIgZXZpZGVuY2UnfSkuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidNSVNTSU5HJyxleGFjdDp0cnVlfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5sb2NhdG9yKCd0Ym9keSB0cicpKS50b0hhdmVDb3VudCgxKTtcclxuIGF3YWl0IHBhZ2Uuc2NyZWVuc2hvdCh7cGF0aDpyZXNvbHZlKG91dHB1dCxgZml4dHVyZS1ldmlkZW5jZS1maWx0ZXItJHt3aWR0aH0ucG5nYCksZnVsbFBhZ2U6dHJ1ZX0pO1xyXG4gY29uc3QgZG93bmxvYWRpbmc9cGFnZS53YWl0Rm9yRXZlbnQoJ2Rvd25sb2FkJyk7YXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J0Vrc3BvciBKU09OJ30pLmNsaWNrKCk7Y29uc3QgZG93bmxvYWQ9YXdhaXQgZG93bmxvYWRpbmc7XHJcbiBjb25zdCBkb3dubG9hZGVkPUpTT04ucGFyc2UocmVhZEZpbGVTeW5jKChhd2FpdCBkb3dubG9hZC5wYXRoKCkpISwndXRmOCcpKTtleHBlY3QoZG93bmxvYWRlZC5wYWNrYWdlLnBhY2thZ2VfaWQpLnRvQmUocGFja2FnZUlkKTtleHBlY3QoZG93bmxvYWRlZC5wYWNrYWdlLmV2aWRlbmNlKS50b0hhdmVMZW5ndGgoMik7XHJcbiBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnbmF2aWdhdGlvbicse25hbWU6J05hdmlnYXNpIG9wZXJhdG9yJ30pLmdldEJ5Um9sZSgnbGluaycse25hbWU6L0h1bWFuIENvbnRyb2wvfSkuY2xpY2soKTtcclxuIGZvcihjb25zdCBjaG9pY2Ugb2YgWydQQVNTJywnRkFJTCcsJ0hPTEQnXSl7XHJcbiAgY29uc3QgcHJpb3I9cG9zdHMubGVuZ3RoO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidUaW5qYXUgJiBiZXJpIGtlcHV0dXNhbicsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XHJcbiAgY29uc3QgZGlhbG9nPXBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnLHtuYW1lOidUaW5qYXUga2VwdXR1c2FuIEFuZGEnfSk7YXdhaXQgZGlhbG9nLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpuZXcgUmVnRXhwKGNob2ljZSl9KS5jbGljaygpO1xyXG4gIGlmKGNob2ljZT09PSdQQVNTJyl7YXdhaXQgZGlhbG9nLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonUGVyaWtzYSBldmlkZW5jZSBzZWJlbHVtIG1lbXV0dXNrYW4nfSkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycse25hbWU6J1Bha2V0IGV2aWRlbmNlJ30pKS50b0JlVmlzaWJsZSgpO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO2F3YWl0IGV4cGVjdChkaWFsb2cpLnRvQmVWaXNpYmxlKCk7fVxyXG4gIGV4cGVjdChwb3N0cy5sZW5ndGgpLnRvQmUocHJpb3IpO2F3YWl0IGRpYWxvZy5nZXRCeUxhYmVsKCdBbGFzYW4ga2VwdXR1c2FuIChvcHNpb25hbCknKS5maWxsKGBLZXB1dHVzYW4gJHtjaG9pY2V9IGRhbGFtIGZpeHR1cmVgKTtcclxuICBhd2FpdCBwYWdlLnNjcmVlbnNob3Qoe3BhdGg6cmVzb2x2ZShvdXRwdXQsYGZpeHR1cmUtZGVjaXNpb24tJHtjaG9pY2V9LSR7d2lkdGh9LnBuZ2ApfSk7XHJcbiAgYXdhaXQgZGlhbG9nLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonU2ltcGFuIGtlcHV0dXNhbid9KS5jbGljaygpO2F3YWl0IGV4cGVjdChkaWFsb2cpLm5vdC50b0JlVmlzaWJsZSgpO1xyXG4gIGF3YWl0IGV4cGVjdChwYWdlLmdldEJ5Um9sZSgncmVnaW9uJyx7bmFtZTonSGlzdG9yeSd9KS5nZXRCeVJvbGUoJ2NlbGwnLHtuYW1lOm5ldyBSZWdFeHAoYEtlcHV0dXNhbiAke2Nob2ljZX0gZGFsYW0gZml4dHVyZWApfSkpLnRvQmVWaXNpYmxlKCk7XHJcbiB9XHJcbiBmb3IoY29uc3QgZmlsdGVyIG9mIFsnS2VwdXR1c2FuJywnRWtzZWt1c2knLCdTZW11YSddKWF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdncm91cCcse25hbWU6J0ZpbHRlciByaXdheWF0J30pLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTpmaWx0ZXIsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XHJcbiBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTovXktlcHV0dXNhbiBkZWNfL30pLmZpcnN0KCkuY2xpY2soKTthd2FpdCBleHBlY3QocGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycpKS50b0NvbnRhaW5UZXh0KCdJU09MQVRFRF9CUk9XU0VSX1RFU1QnKTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuIGF3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidFa3Nla3VzaSBwcmV2aW91cy1maXh0dXJlIDEg4oaXJ30pLmNsaWNrKCk7YXdhaXQgZXhwZWN0KHBhZ2UuZ2V0QnlSb2xlKCdkaWFsb2cnKSkudG9Db250YWluVGV4dCgnVEVTVF9PTkxZX0JMT0NLRUQnKTthd2FpdCBwYWdlLmtleWJvYXJkLnByZXNzKCdFc2NhcGUnKTtcclxuIGF3YWl0IHBhZ2UuZXZhbHVhdGUoKCk9PndpbmRvdy5zY3JvbGxUbygwLDApKTthd2FpdCBwYWdlLnNjcmVlbnNob3Qoe3BhdGg6cmVzb2x2ZShvdXRwdXQsYGZpeHR1cmUtaHVtYW4taGlzdG9yeS0ke3dpZHRofS5wbmdgKSxmdWxsUGFnZTp0cnVlfSk7XHJcbiBhbGxvd2VkPWZhbHNlO3JlamVjdD10cnVlO2F3YWl0IHBhZ2UuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOidNdWF0IHVsYW5nIHJldmlldycsZXhhY3Q6dHJ1ZX0pLmNsaWNrKCk7XHJcbiBhd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonVGluamF1ICYgYmVyaSBrZXB1dHVzYW4nLGV4YWN0OnRydWV9KS5jbGljaygpO2xldCBkaWFsb2c9cGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycse25hbWU6J1RpbmphdSBrZXB1dHVzYW4gQW5kYSd9KTtcclxuIGF3YWl0IGV4cGVjdChkaWFsb2cuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9QQVNTL30pKS50b0JlRGlzYWJsZWQoKTthd2FpdCBkaWFsb2cuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9IT0xEL30pLmNsaWNrKCk7YXdhaXQgZGlhbG9nLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonU2ltcGFuIGtlcHV0dXNhbid9KS5jbGljaygpO1xyXG4gYXdhaXQgZXhwZWN0KGRpYWxvZy5nZXRCeVJvbGUoJ3N0YXR1cycpKS50b0NvbnRhaW5UZXh0KCdldmlkZW5jZSBwYWNrYWdlIGNoYW5nZWQnKTthd2FpdCBleHBlY3QoZGlhbG9nKS50b0JlVmlzaWJsZSgpO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gYXV0aG9yaXplZD1mYWxzZTthd2FpdCBwYWdlLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonQWtzZXMgb3BlcmF0b3Ig4oaXJ30pLmNsaWNrKCk7YXdhaXQgcGFnZS5nZXRCeUxhYmVsKCdUb2tlbiBvcGVyYXRvcicse2V4YWN0OnRydWV9KS5maWxsKCdpbnZhbGlkLWJyb3dzZXItdGVzdCcpO2F3YWl0IHBhZ2Uua2V5Ym9hcmQucHJlc3MoJ0VzY2FwZScpO1xyXG4gYXdhaXQgcGFnZS5nZXRCeVJvbGUoJ2J1dHRvbicse25hbWU6J1RpbmphdSAmIGJlcmkga2VwdXR1c2FuJyxleGFjdDp0cnVlfSkuY2xpY2soKTtkaWFsb2c9cGFnZS5nZXRCeVJvbGUoJ2RpYWxvZycse25hbWU6J1RpbmphdSBrZXB1dHVzYW4gQW5kYSd9KTtcclxuIGF3YWl0IGV4cGVjdChkaWFsb2cuZ2V0QnlSb2xlKCdidXR0b24nLHtuYW1lOi9IT0xEL30pKS50b0JlRGlzYWJsZWQoKTthd2FpdCBleHBlY3QoZGlhbG9nLmdldEJ5Um9sZSgnYnV0dG9uJyx7bmFtZTonU2ltcGFuIGtlcHV0dXNhbid9KSkudG9CZURpc2FibGVkKCk7XHJcbiBleHBlY3QocG9zdHMpLnRvSGF2ZUxlbmd0aCg0KTtleHBlY3QocG9zdHMuZXZlcnkocD0+KHAucGxhbl9iaW5kaW5nIGFzIHR5cGVvZiBiaW5kaW5nKS52ZXJzaW9uPT09YmluZGluZy52ZXJzaW9uKSkudG9CZSh0cnVlKTtcclxuIHdyaXRlRmlsZVN5bmMocmVzb2x2ZShvdXRwdXQsYGlzb2xhdGVkLWJyb3dzZXItY29udHJhY3QtJHt3aWR0aH0uanNvbmApLEpTT04uc3RyaW5naWZ5KHtzY29wZTonTU9DS19BUElfT05MWTsgcHJvZHVjdGlvbiBtdXRhdGlvbnMgaW50ZXJjZXB0ZWQnLGRlY2lzaW9uczpwb3N0cy5tYXAocD0+cC5kZWNpc2lvbiksYmluZGluZyx1bmF1dGhvcml6ZWRCbG9ja2VkOnRydWUsZXhwb3J0UGFja2FnZVZlcmlmaWVkOnRydWV9LG51bGwsMikpO1xyXG59KTtcclxuIl0sIm1hcHBpbmdzIjoiQUFBQSxTQUFRQSxJQUFJLEVBQUNDLE1BQU0sUUFBaUIsa0JBQWtCO0FBQ3RELFNBQVFDLFlBQVksRUFBQ0MsYUFBYSxRQUFPLFNBQVM7QUFDbEQsU0FBUUMsT0FBTyxRQUFPLFdBQVc7QUFDakMsTUFBTUMsTUFBTSxHQUFDRCxPQUFPLENBQUMsMENBQTBDLENBQUM7QUFDaEUsTUFBTUUsU0FBUyxHQUFDRixPQUFPLENBQUMsc0RB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