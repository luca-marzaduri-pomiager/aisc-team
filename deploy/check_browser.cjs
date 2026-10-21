// Run after `npm ci --prefix e2e` and installing Playwright Chromium.
const { chromium } = require('../e2e/node_modules/playwright');

(async () => {
  const base = `http://localhost:${process.env.AISC_PORT || '8092'}`;
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  const productBrand = /\bAISC\b|AI Assessment Sandbox|Luxembourg AI Factory|\blaif\b/i;
  const checkBranding = async (target) => {
    if (productBrand.test(await target.title()) || productBrand.test(await target.locator('body').innerText())) {
      throw new Error('Product branding remains visible');
    }
    if (await target.locator('img[src*="laif"], img[alt*="Luxembourg"]').count()) {
      throw new Error('Product logo remains visible');
    }
  };
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    await page.getByTestId('login-button').waitFor({ timeout: 60000 });
    await checkBranding(page);
    const catalogue = page.getByRole('button', { name: 'Public Catalogue', exact: true });
    await catalogue.waitFor();
    if (!(await catalogue.isDisabled())) {
      throw new Error('Unconfigured catalogue must be visible but disabled');
    }
    if (await page.evaluate(() => typeof navigator.registerProtocolHandler === 'function')) {
      await page.getByRole('button', { name: 'Register plugin links', exact: true }).waitFor();
    }
    await page.getByTestId('login-button').click();
    await page.locator('#username').waitFor();
    await checkBranding(page);
    await page.locator('#username').fill('user');
    await page.locator('#password').fill(process.env.AISC_TEST_PASSWORD || 'user');
    await page.locator('button[type="submit"], input[type="submit"]').click();
    await page.waitForURL(url => url.origin === base && !url.pathname.startsWith('/auth/'), { timeout: 60000 });
    await page.locator('.auth-user-btn').waitFor({ timeout: 60000 });
    await checkBranding(page);
    if (!(await catalogue.isVisible()) || !(await catalogue.isDisabled())) {
      throw new Error('Catalogue button must remain visible and disabled after login');
    }
    if (errors.length) throw new Error(errors.join('\n'));
    for (const path of ['/controls', '/qualification']) {
      const companion = await browser.newPage();
      await companion.goto(base + path, { waitUntil: 'domcontentloaded' });
      const header = await companion.locator('.site-header').innerText();
      if (productBrand.test(header) || productBrand.test(await companion.title())) {
        throw new Error('Product branding remains in ' + path);
      }
      if (await companion.locator('.site-header img').count()) {
        throw new Error('Product logo remains in ' + path);
      }
      await companion.close();
    }
    console.log('PASS browser login, neutral interface, restored toolbar buttons, unconfigured catalogue disabled');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
