const { chromium } = require('playwright');
const path = require('path');
const url = require('url');

(async () => {
  const htmlPath = path.resolve(__dirname, '..', 'index.html');
  const outPath = path.resolve(__dirname, '..', 'assets', 'preview.png');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1400 }, deviceScaleFactor: 2 });
  await page.goto(url.pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });
  // 让交互页面完成初始渲染/计算
  await page.waitForTimeout(1200);
  await page.screenshot({ path: outPath, fullPage: true });
  await browser.close();
  console.log('screenshot saved ->', outPath);
})().catch(e => { console.error(e); process.exit(1); });
