import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup...');
  
  // Start browser for setup
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the dashboard to be ready
    console.log('⏳ Waiting for dashboard to be ready...');
    await page.goto(config.projects[0].use.baseURL || 'http://localhost:5179');
    
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
    
    // Check if the dashboard is accessible
    const title = await page.title();
    console.log(`✅ Dashboard loaded with title: ${title}`);
    
    // You can add additional setup here, such as:
    // - Creating test users
    // - Setting up test data
    // - Authenticating test accounts
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
    console.log('✅ Global setup completed');
  }
}

export default globalSetup;
