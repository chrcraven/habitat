#!/usr/bin/env node
/**
 * Regenerates the screenshots embedded in docs/manual/*.md.
 *
 * Drives a *live* local Habitat instance (real backend + real frontend
 * dev server, real Postgres/PostGIS) through Playwright, walking the same
 * signup -> property -> activity/sighting -> link -> species/tasks/admin/
 * public-site flow a new user would, and saves a PNG at each meaningful
 * step into docs/manual/images/.
 *
 * See README.md in this directory for prerequisites (DB setup, running
 * servers, installing this script's own dependencies) before running this.
 *
 * Usage:
 *   node capture.js                # full run, defaults below
 *   BASE_URL=http://localhost:5173 OUT_DIR=../images node capture.js
 *
 * Env vars (all optional):
 *   BASE_URL              Frontend dev server origin. Default http://localhost:5173
 *   OUT_DIR                Where to write PNGs. Default ../images (i.e. docs/manual/images)
 *   PLAYWRIGHT_BROWSERS_PATH  Where prebuilt Chromium lives, if you have one
 *                          outside Playwright's normal cache (this repo's
 *                          sandbox environment sets this to /opt/pw-browsers
 *                          and skips `playwright install`). If unset and no
 *                          prebuilt browser is found, falls back to
 *                          Playwright's own bundled Chromium — run
 *                          `npx playwright install chromium` first in that
 *                          case.
 *   SKIP_TILE_ABORT=1      Don't abort OpenStreetMap tile requests (see
 *                          "Basemap tiles" in README.md) — set this if
 *                          you're running somewhere with real internet
 *                          access and want actual map imagery in the
 *                          screenshots instead of a blank background.
 *
 * MAINTENANCE: this file is a checked-in project asset, not a scratch
 * script — per CLAUDE.md's "Keep the user manual current" convention,
 * update it (don't recreate it from scratch in a new session) whenever a
 * UI change means a screenshot needs to look different, and re-run it to
 * refresh docs/manual/images/. If a new manual chapter needs a new
 * screenshot, add a new captureX() step below and a shot() call — the
 * MANIFEST comment block under each step's shot() call documents which
 * chapter file(s) embed the resulting image.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE_URL || 'http://localhost:5173';
const OUT = path.resolve(__dirname, process.env.OUT_DIR || '../images');
const SKIP_TILE_ABORT = process.env.SKIP_TILE_ABORT === '1';

const rand = Math.floor(Math.random() * 100000);
const email = `manual-demo-${rand}@example.com`;
const password = 'ManualDemo123!';
const orgName = 'Willow Creek Preserve';

/** Finds a Chromium binary Playwright can launch, without requiring
 * `playwright install` to have downloaded one into the default cache —
 * this repo's sandbox environment pre-installs Chromium under
 * PLAYWRIGHT_BROWSERS_PATH instead (see /root/.ccr/README.md-equivalent
 * environment notes). Falls back to Playwright's own resolution (its
 * bundled/downloaded browser) if nothing is found there. */
function findChromiumExecutable() {
  const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (!browsersPath || !fs.existsSync(browsersPath)) return undefined;
  const candidates = fs
    .readdirSync(browsersPath)
    .filter((name) => name.startsWith('chromium-'))
    .sort()
    .reverse(); // prefer the highest-numbered build if more than one
  for (const dir of candidates) {
    const exe = path.join(browsersPath, dir, 'chrome-linux', 'chrome');
    if (fs.existsSync(exe)) return exe;
  }
  return undefined;
}

async function shot(page, name) {
  fs.mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: path.join(OUT, name) });
  console.log('captured', name);
}

/** Places vertices by clicking into the MapCanvas at fractional
 * (x, y) positions within its bounding box — [0,0] top-left, [1,1]
 * bottom-right — rather than real map coordinates, since the demo
 * account's map view/zoom varies run to run. */
async function clickCanvasPoints(page, points) {
  const canvas = page.locator('.map-canvas');
  const box = await canvas.boundingBox();
  for (const [xr, yr] of points) {
    await page.mouse.click(box.x + box.width * xr, box.y + box.height * yr);
    await page.waitForTimeout(150);
  }
}

/** Clicks a control that POSTs a new record, and returns the created
 * record's id from the response body — more reliable than waiting on a
 * URL/DOM change, since it doesn't depend on guessing the exact
 * post-navigation selector. */
async function postAndGetId(page, urlSubstr, triggerFn) {
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes(urlSubstr) && r.request().method() === 'POST'),
    triggerFn(),
  ]);
  return (await resp.json()).id;
}

async function main() {
  const executablePath = findChromiumExecutable();
  const browser = await chromium.launch(executablePath ? { executablePath } : {});
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  if (!SKIP_TILE_ABORT) {
    // Basemap tiles (OpenStreetMap) usually aren't reachable from a
    // sandboxed dev environment. Abort immediately instead of letting
    // MapLibre retry forever — drawn shapes/markers still render fine on
    // the blank background, just without real map imagery underneath.
    await page.route('https://tile.openstreetmap.org/**', (route) => route.abort());
  }

  // --- 1. Auth pages -------------------------------------------------
  // MANIFEST: login.png -> getting-started.md
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('text=Log in');
  await shot(page, 'login.png');

  // MANIFEST: signup.png -> getting-started.md
  await page.goto(`${BASE}/signup`);
  await page.waitForSelector('text=Create account');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.fill('input[placeholder*="your land"]', orgName);
  await shot(page, 'signup.png');
  await page.getByRole('button', { name: 'Create account' }).click();
  await page.waitForURL('**/properties');
  await page.waitForTimeout(500);

  // MANIFEST: properties-empty.png -> getting-started.md
  await shot(page, 'properties-empty.png');

  // --- 2. Property: draw, save, view ----------------------------------
  // MANIFEST: property-new.png -> properties.md
  await page.goto(`${BASE}/properties/new`);
  await page.waitForSelector('.map-canvas');
  await page.waitForTimeout(500);
  await clickCanvasPoints(page, [
    [0.35, 0.3],
    [0.65, 0.3],
    [0.65, 0.6],
    [0.35, 0.6],
  ]);
  await page.fill('input[placeholder*="Back Yard"]', 'Back Meadow');
  await shot(page, 'property-new.png');
  const propertyId = await postAndGetId(page, '/api/properties/', () =>
    page.getByRole('button', { name: 'Save property' }).click(),
  );
  await page.waitForURL(`**/properties/${propertyId}`);
  await page.waitForTimeout(500);

  // --- 3. Activity: draw, save, edit ----------------------------------
  // MANIFEST: activity-new.png -> activities.md
  await page.goto(`${BASE}/properties/${propertyId}/activities/new`);
  await page.waitForSelector('.map-canvas');
  await page.waitForTimeout(500);
  await clickCanvasPoints(page, [
    [0.4, 0.35],
    [0.6, 0.35],
    [0.55, 0.55],
    [0.42, 0.5],
  ]);
  await page.selectOption('select >> nth=0', { label: 'Planting' });
  await page.fill('textarea', 'Planted a native seed mix along the meadow edge.');
  await shot(page, 'activity-new.png');
  const activityId = await postAndGetId(page, '/api/activities/', () =>
    page.getByRole('button', { name: 'Save activity' }).click(),
  );
  await page.waitForURL(`**/properties/${propertyId}`);
  await page.waitForTimeout(500);

  // MANIFEST: activity-edit.png -> activities.md
  await page.goto(`${BASE}/properties/${propertyId}/activities/${activityId}/edit`);
  await page.waitForTimeout(500);
  await shot(page, 'activity-edit.png');

  // --- 4. Sighting: draw, save, edit + link ---------------------------
  // MANIFEST: sighting-new.png -> sightings.md
  await page.goto(`${BASE}/properties/${propertyId}/sightings/new`);
  await page.waitForSelector('.map-canvas');
  await page.waitForTimeout(500);
  await clickCanvasPoints(page, [[0.5, 0.45]]);
  await page.fill('input[placeholder="Common name"]', 'Western Bluebird');
  await page.fill('textarea', 'Perched on the fence line near the new planting.');
  await shot(page, 'sighting-new.png');
  const sightingId = await postAndGetId(page, '/api/sightings/', () =>
    page.getByRole('button', { name: 'Save sighting' }).click(),
  );
  await page.waitForURL(`**/properties/${propertyId}`);
  await page.waitForTimeout(500);

  // MANIFEST: sighting-edit-linked.png -> sightings.md, activities.md
  //           (Photos/Linked-records section — identical UI on both
  //           record types, see those chapters), linking-sightings-
  //           activities.md
  await page.goto(`${BASE}/properties/${propertyId}/sightings/${sightingId}/edit`);
  await page.waitForTimeout(500);
  const linkSelect = page.locator('.field-row select').last();
  const linkOptionValue = await linkSelect
    .locator('option', { hasText: 'Planting' })
    .getAttribute('value');
  await linkSelect.selectOption(linkOptionValue);
  await page.getByRole('button', { name: '+ Link' }).click();
  await page.waitForTimeout(500);
  await shot(page, 'sighting-edit-linked.png');

  // --- 5. Property map, now populated ---------------------------------
  // MANIFEST: property-map-with-records.png -> properties.md
  await page.goto(`${BASE}/properties/${propertyId}`);
  await page.waitForTimeout(500);
  await shot(page, 'property-map-with-records.png');

  // --- 6. Org-wide pages ----------------------------------------------
  // MANIFEST: species.png -> species.md
  await page.goto(`${BASE}/species`);
  await page.waitForTimeout(400);
  await shot(page, 'species.png');

  // MANIFEST: tasks.png -> tasks.md
  await page.goto(`${BASE}/tasks`);
  await page.waitForTimeout(400);
  await page.fill('input[placeholder*="bindweed"]', 'Check on new plantings in two weeks');
  await shot(page, 'tasks.png');

  // MANIFEST: org-admin.png -> organization-admin.md
  await page.goto(`${BASE}/admin`);
  await page.waitForTimeout(400);
  await shot(page, 'org-admin.png');

  // MANIFEST: account.png -> account.md
  await page.goto(`${BASE}/account`);
  await page.waitForTimeout(400);
  await shot(page, 'account.png');

  // --- 7. Public site ---------------------------------------------------
  // MANIFEST: public-org.png -> public-site.md
  // Back on /admin — the "View public site" link only lives there, and the
  // account.png step above navigated away from it.
  await page.goto(`${BASE}/admin`);
  await page.waitForTimeout(400);
  const publicLink = await page.locator('a:has-text("View public site")').getAttribute('href');
  await page.goto(`${BASE}${publicLink}`);
  await page.waitForTimeout(500);
  await shot(page, 'public-org.png');

  // MANIFEST: public-property.png -> public-site.md
  await page.locator('.card__link').first().click();
  await page.waitForTimeout(500);
  await shot(page, 'public-property.png');

  await browser.close();
  console.log(`DONE — ${OUT}`);
}

main().catch((err) => {
  console.error('SCRIPT ERROR:', err);
  process.exit(1);
});
