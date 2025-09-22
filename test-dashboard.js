const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Capture console logs
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('Browser Error:', msg.text());
    } else {
      console.log('Browser Log:', msg.text());
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    console.error('Page Error:', error.message);
  });

  try {
    console.log('Navigating to dashboard...');
    await page.goto('http://localhost:5179', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Check if _interopRequireDefault is available
    const interopCheck = await page.evaluate(() => {
      return {
        windowInterop: typeof window._interopRequireDefault === 'function',
        globalInterop: typeof globalThis._interopRequireDefault === 'function',
        functionTest: window._interopRequireDefault({ default: 'test', __esModule: false })
      };
    });

    console.log('Interop function check:', interopCheck);

    // Check for MUI elements
    const hasContent = await page.evaluate(() => {
      return {
        rootElement: document.getElementById('root') !== null,
        rootChildren: document.getElementById('root')?.children.length > 0,
        bodyText: document.body.innerText.length > 0
      };
    });

    console.log('Content check:', hasContent);

    // Check for specific error text
    const errorText = await page.evaluate(() => {
      const errors = Array.from(document.querySelectorAll('*'))
        .map(el => el.textContent)
        .filter(text => text && text.includes('_interopRequireDefault'));
      return errors;
    });

    if (errorText.length > 0) {
      console.error('Found interop errors in page:', errorText);
    } else {
      console.log('✅ No interop errors found!');
    }

    // Take screenshot for verification
    await page.screenshot({ path: 'dashboard-test.png' });
    console.log('Screenshot saved as dashboard-test.png');

  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();