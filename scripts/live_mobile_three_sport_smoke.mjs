import { chromium } from 'playwright';
import fs from 'node:fs/promises';
const base = 'https://donovan1019.github.io/kennys-sports-lab-mobile/';
const out = 'artifacts/mobile-smoke';
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const failures = [];
const results = [];
try {
  for (const sport of ['nba', 'nfl', 'nhl']) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const url = base + sport + '.html?v=mobile-smoke-20261107';
    try {
      const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      if (!response || response.status() >= 400) throw Error('HTTP ' + (response?.status() ?? 'no response'));
      await page.screenshot({ path: out + '/' + sport + '.png', fullPage: true, animations: 'disabled' });
      const tabs = page.locator('nav.ksl-unified-sections a');
      const count = await tabs.count();
      if (!count) failures.push(sport + ': missing unified section navigation');
      const tabResults = [];
      for (let i = 0; i < count; i++) {
        const tab = tabs.nth(i);
        const href = await tab.getAttribute('href');
        const label = (await tab.innerText()).trim();
        if (!href) { failures.push(sport + ': blank tab link ' + label); continue; }
        if (href.startsWith('#')) {
          await tab.click({ timeout: 10000 });
          await page.waitForTimeout(250);
          const current = new URL(page.url());
          const hash = decodeURIComponent(current.hash.slice(1));
          const anchorExists = await page.locator('[id="' + hash.replaceAll('"', '\\"') + '"]').count();
          const nbaTab = sport === 'nba' && ['projections','stats','research','ml','sgp'].includes(hash);
          if (!anchorExists && !nbaTab) failures.push(sport + ': dead tab ' + label + ' (' + href + ')');
          if (nbaTab && hash !== href.slice(1)) failures.push(sport + ': wrong NBA tab ' + label);
        } else {
          const destination = new URL(href, url);
          const linkResponse = await page.request.get(destination.href, { timeout: 20000 });
          if (linkResponse.status() >= 400) failures.push(sport + ': tab ' + label + ' returned HTTP ' + linkResponse.status());
        }
        tabResults.push({ label, href });
      }
      if (errors.length) failures.push(sport + ': browser errors: ' + errors.slice(0, 3).join(' | '));
      results.push({ sport, url, status: response.status(), tabs: tabResults, errors });
    } catch (e) {
      failures.push(sport + ': ' + e.message);
      results.push({ sport, url, error: e.message });
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
await fs.writeFile(out + '/results.json', JSON.stringify({ results, failures }, null, 2));
console.log(JSON.stringify({ results, failures }, null, 2));
if (failures.length) process.exitCode = 1;
