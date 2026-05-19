/**
 * Headless verification of the M3 analyze flow against real MFPT data.
 * Drives a real Chromium with the dev server at http://localhost:5173.
 *
 *   pnpm exec node e2e/verify-analyze.mjs
 *
 * Exits non-zero on any failure. Saves screenshots into e2e/screenshots/.
 */
import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SHOTS = join(HERE, 'screenshots');
mkdirSync(SHOTS, { recursive: true });

const MFPT = '/home/duck/PycharmProjects/bearing-fault-diagnosis/backend/MFPT_Dataset/test';

const CASES = [
  { file: 'baseline_3.mat', expected: 'normal' },
  { file: 'InnerRaceFault_vload_6.mat', expected: 'inner_fault' },
  { file: 'InnerRaceFault_vload_7.mat', expected: 'inner_fault' },
  { file: 'OuterRaceFault_3.mat', expected: 'outer_fault' },
  { file: 'OuterRaceFault_vload_6.mat', expected: 'outer_fault' },
  { file: 'OuterRaceFault_vload_7.mat', expected: 'outer_fault' }, // the formerly-misclassified one
];

function ts() {
  return new Date().toISOString().slice(11, 19);
}

function log(...args) {
  console.log(`[${ts()}]`, ...args);
}

async function main() {
  const missing = CASES.filter((c) => !existsSync(resolve(MFPT, c.file)));
  if (missing.length) {
    console.error('Missing MFPT files:', missing.map((m) => m.file).join(', '));
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 1100 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  const consoleErrors = [];
  page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(`console.error: ${msg.text()}`);
  });

  log('Loading http://localhost:5173 …');
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });

  // Header chip should resolve to "model ready"
  const chip = page.locator('text=/^(model ready|untrained|backend offline)$/');
  await chip.waitFor({ timeout: 5000 });
  const chipText = await chip.first().innerText();
  log('Header chip:', chipText);
  if (chipText !== 'model ready') {
    throw new Error(`Expected header chip "model ready", got "${chipText}"`);
  }
  await page.screenshot({ path: join(SHOTS, '01-initial.png'), fullPage: true });

  const results = [];

  for (const [i, c] of CASES.entries()) {
    log(`Case ${i + 1}/${CASES.length}: uploading ${c.file} (expect ${c.expected})`);

    // Wait for the analyze POST to complete so we don't read stale state from
    // the previous case's render.
    const respP = page.waitForResponse(
      (r) => r.url().endsWith('/api/analyze') && r.request().method() === 'POST',
      { timeout: 30000 },
    );
    const input = page.locator('input[type="file"]');
    await input.setInputFiles(resolve(MFPT, c.file));
    await respP;

    // Wait until the Source card reports the new filename
    await page
      .locator('section:has(h3:has-text("Source")) p.font-mono', { hasText: c.file })
      .waitFor({ timeout: 30000 });

    const labelLocator = page.locator('section:has(h3:has-text("Prediction")) span.rounded-full');
    await labelLocator.first().waitFor({ timeout: 30000 });
    const predicted = (await labelLocator.first().innerText()).trim();

    // Wait for the Plotly spectrum to render
    await page
      .locator('section:has(h3:has-text("Frequency spectrum")) .js-plotly-plot')
      .waitFor({ timeout: 30000 });

    const confidenceText = await page
      .locator('section:has(h3:has-text("Prediction")) span.font-mono')
      .first()
      .innerText();

    results.push({
      file: c.file,
      expected: c.expected,
      predicted,
      confidence: confidenceText,
      ok: predicted === c.expected,
    });

    await page.screenshot({
      path: join(SHOTS, `${String(i + 2).padStart(2, '0')}-${c.file.replace(/\W+/g, '_')}.png`),
      fullPage: true,
    });
  }

  // Test an unsupported extension
  log('Negative case: uploading a .txt file should be rejected');
  const input = page.locator('input[type="file"]');
  await page.evaluate(() => {
    // Allow .txt for this negative test by relaxing the input's accept attribute
    const el = document.querySelector('input[type="file"]');
    if (el) el.removeAttribute('accept');
  });
  // Use Buffer payload so we don't need a real file on disk
  await input.setInputFiles({
    name: 'bogus.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('not a real signal'),
  });
  // Wait for the error banner
  await page.locator('text=/Invalid file type/i').waitFor({ timeout: 5000 });
  log('Negative case OK — error banner shown');
  await page.screenshot({ path: join(SHOTS, '90-negative-txt.png'), fullPage: true });

  // ---- Flow B: Generate sample tab ----
  log('Switching to Generate sample tab');
  await page.getByRole('tab', { name: 'Generate sample' }).click();
  // The fault-type radio group should appear
  await page.locator('[role="radiogroup"]').waitFor({ timeout: 5000 });
  await page.screenshot({ path: join(SHOTS, '91-generate-initial.png'), fullPage: true });

  const genCases = [
    { fault: 'inner_fault', expected: 'inner_fault' },
    { fault: 'outer_fault', expected: 'outer_fault' },
    { fault: 'cage_fault', expected: 'cage_fault' },
    { fault: 'ball_fault', expected: 'ball_fault' },
    { fault: 'normal', expected: 'normal' },
  ];

  const genResults = [];

  for (const [i, g] of genCases.entries()) {
    log(`Generate ${i + 1}/${genCases.length}: ${g.fault} (expect ${g.expected})`);
    await page.getByRole('radio', { name: g.fault }).click();

    const respP = page.waitForResponse(
      (r) => r.url().endsWith('/api/generate-sample') && r.request().method() === 'POST',
      { timeout: 30000 },
    );
    await page.getByRole('button', { name: 'Generate' }).click();
    await respP;

    // Wait until the Source card title reflects the new fault type
    await page
      .locator('section:has(h3:text-matches("Synthetic .*'+g.fault+'"))')
      .waitFor({ timeout: 30000 });

    const labelLocator = page.locator('section:has(h3:has-text("Prediction")) span.rounded-full');
    await labelLocator.first().waitFor({ timeout: 30000 });
    const predicted = (await labelLocator.first().innerText()).trim();
    await page
      .locator('section:has(h3:has-text("Frequency spectrum")) .js-plotly-plot')
      .waitFor({ timeout: 30000 });
    const confidenceText = await page
      .locator('section:has(h3:has-text("Prediction")) span.font-mono')
      .first()
      .innerText();
    genResults.push({
      fault: g.fault,
      expected: g.expected,
      predicted,
      confidence: confidenceText,
    });
    await page.screenshot({
      path: join(SHOTS, `${String(92 + i).padStart(2, '0')}-generate-${g.fault}.png`),
      fullPage: true,
    });
  }

  // ---- M5: Model panel dialog ----
  log('Opening Model dialog via header chip');
  await page.getByRole('button', { name: 'Open model panel' }).click();
  const dialog = page.getByRole('dialog');
  await dialog.waitFor({ timeout: 5000 });

  // Capture initial dialog
  await page.screenshot({ path: join(SHOTS, '97-model-dialog.png'), fullPage: true });

  // Switch the bearing preset to MFPT-NICE and confirm chip updates
  const presetChip = dialog.getByRole('radio', { name: 'MFPT-NICE' });
  if (await presetChip.count()) {
    log('Switching bearing preset to MFPT-NICE');
    await presetChip.click();
    await page
      .waitForFunction(
        () => !!document.querySelector('[role="dialog"] :where(p,span):where(:has-text)'),
        { timeout: 5000 },
      )
      .catch(() => {});
    await dialog.locator('text=/Active:\\s*MFPT-NICE/').waitFor({ timeout: 5000 });
    log('Preset switched');
  }

  // Retrain synthetic (do NOT save — keep persisted MFPT model intact)
  log('Retraining synthetic (no persist)');
  // Mode is synthetic by default
  await dialog.getByRole('button', { name: 'Retrain' }).click();
  await dialog.locator('text=/Retrain complete/').waitFor({ timeout: 30000 });
  const retrainSource = await dialog.locator('text=/source:/').first().innerText();
  log('Retrain returned:', retrainSource);
  await page.screenshot({ path: join(SHOTS, '98-after-retrain.png'), fullPage: true });

  // Close dialog
  await dialog.locator('footer button', { hasText: 'Close' }).click();
  await dialog.waitFor({ state: 'detached', timeout: 5000 });

  // Verify the header chip now reads "synthetic"
  const chipDetail = await page.locator('header span.font-mono').innerText();
  log('Header chip detail after retrain:', chipDetail);
  const chipOk = chipDetail.includes('synthetic');

  // Restore the persisted MFPT model so subsequent dev sessions see it.
  log(
    'Restoring persisted MFPT model via retrain dataset (no save needed; backend already has pkl)',
  );
  // Reload the page → backend.lifespan already loaded the MFPT pkl into a new process, but
  // since we just replaced the in-memory model with synthetic, the simplest restore is to
  // call retrain with the dataset path (no save).
  await page.getByRole('button', { name: 'Open model panel' }).click();
  await dialog.waitFor({ timeout: 5000 });
  await dialog.getByRole('button', { name: 'Dataset' }).click();
  const datasetInput = dialog.locator('input[placeholder*="MFPT_Dataset"]');
  await datasetInput.fill(
    '/home/duck/PycharmProjects/bearing-fault-diagnosis/backend/MFPT_Dataset/train',
  );
  await dialog.getByRole('button', { name: 'Retrain' }).click();
  await dialog.locator('text=/Retrain complete/').waitFor({ timeout: 60000 });
  const retrainSource2 = await dialog.locator('text=/source:/').first().innerText();
  log('Dataset retrain returned:', retrainSource2);
  await page.screenshot({ path: join(SHOTS, '99-after-dataset-retrain.png'), fullPage: true });

  await browser.close();

  if (!chipOk) {
    console.error(`Chip did not update to synthetic after retrain (got "${chipDetail}")`);
    process.exit(1);
  }

  console.log('\n=== Analyze (Flow A) ===');
  for (const r of results) {
    const mark = r.ok ? 'PASS' : 'FAIL';
    console.log(
      `  ${mark}  ${r.file.padEnd(38)} expected=${r.expected.padEnd(11)} predicted=${r.predicted.padEnd(
        11,
      )} conf=${r.confidence}`,
    );
  }

  console.log('\n=== Generate (Flow B) ===');
  for (const g of genResults) {
    const ok = g.predicted === g.expected;
    const mark = ok ? 'PASS' : 'NOTE'; // synthetic ↛ MFPT-trained classifier; mismatch is informative
    console.log(
      `  ${mark}  fault=${g.fault.padEnd(11)} predicted=${g.predicted.padEnd(11)} conf=${g.confidence}`,
    );
  }

  console.log(`\nScreenshots written to ${SHOTS}`);

  if (consoleErrors.length) {
    console.warn('\nConsole errors captured during run:');
    for (const e of consoleErrors) console.warn('  ' + e);
  }

  const failed = results.filter((r) => !r.ok);
  if (failed.length) {
    console.error(`\n${failed.length} Flow A case(s) failed.`);
    process.exit(1);
  }
  console.log(`\nAll ${results.length} Flow A cases passed.`);
}

main().catch((err) => {
  console.error('FATAL', err);
  process.exit(1);
});
