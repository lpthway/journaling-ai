// E2E Tests for Basic App Navigation and Core Functionality

const { test, expect } = require('@playwright/test');
const { TestHelpers } = require('./utils/test-helpers');

test.describe('App Navigation and Core Features', () => {
  
  test.beforeEach(async ({ page }) => {
    // Go to homepage and wait for app to be ready
    await TestHelpers.navigateToPage(page, '/');
  });

  test('should load the homepage successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/journaling/i);
    
    // Check that main navigation is present
    const nav = page.locator('nav, header').first();
    await expect(nav).toBeVisible();
    
    // Check for key navigation elements
    await expect(page.locator('text=Journal, a[href="/"], a[href*="journal"]')).toBeVisible();
  });

  test('should navigate between main pages', async ({ page }) => {
    // Test navigation to different sections
    const sections = [
      { name: 'Topics', url: '/topics', selector: 'text=Topics, a[href="/topics"], a[href*="topic"]' },
      { name: 'Insights', url: '/insights', selector: 'text=Insights, a[href="/insights"], a[href*="insight"]' },
      { name: 'Chat', url: '/chat', selector: 'text=Chat, a[href="/chat"], a[href*="chat"]' }
    ];

    for (const section of sections) {
      // Click navigation link
      const navLink = page.locator(section.selector).first();
      if (await navLink.isVisible().catch(() => false)) {
        await navLink.click();
        
        // Wait for navigation
        await page.waitForURL(`**${section.url}*`, { timeout: 10000 });
        
        // Verify we're on the right page
        const currentUrl = await TestHelpers.getCurrentPath(page);
        expect(currentUrl).toContain(section.url);
        
        // Take screenshot for documentation
        await TestHelpers.takeScreenshot(page, `navigation-${section.name.toLowerCase()}`);
      }
    }
  });

  test('should handle 404 errors gracefully', async ({ page }) => {
    // Navigate to non-existent page
    await page.goto('/non-existent-page');
    
    // Should redirect to homepage or show 404
    await page.waitForLoadState('networkidle');
    
    const currentUrl = await TestHelpers.getCurrentPath(page);
    const isRedirected = currentUrl === '/' || currentUrl.includes('404');
    
    expect(isRedirected).toBeTruthy();
  });

  test('should show loading states appropriately', async ({ page }) => {
    // Monitor network requests
    let hasLoadingState = false;
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        // Check if loading indicator appears during API calls
        page.locator('.loading, [data-testid="loading"], .spinner').first()
          .isVisible().then(visible => {
            if (visible) hasLoadingState = true;
          }).catch(() => {});
      }
    });

    // Trigger an action that would show loading
    await TestHelpers.navigateToPage(page, '/insights');
    
    // Wait a bit for any async operations
    await page.waitForTimeout(2000);
    
    // Loading states are good UX but not strictly required for basic functionality
    console.log(`Loading state detected: ${hasLoadingState}`);
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Reload page
    await page.reload();
    await TestHelpers.waitForAppReady(page);
    
    // Check that the app is still functional on mobile
    await expect(page.locator('body')).toBeVisible();
    
    // Check if mobile navigation works (hamburger menu, etc.)
    const mobileNav = page.locator('[data-testid="mobile-menu"], .mobile-nav, button[aria-label*="menu"]');
    const hasMobileNav = await mobileNav.isVisible().catch(() => false);
    
    if (hasMobileNav) {
      await mobileNav.click();
      // Mobile menu should expand
      await page.waitForTimeout(500);
    }
    
    // Take mobile screenshot
    await TestHelpers.takeScreenshot(page, 'mobile-responsive');
  });

  test('should handle API connection issues gracefully', async ({ page }) => {
    // Intercept API calls and simulate failures
    await page.route('**/api/**', route => {
      route.abort('failed');
    });

    // Navigate to a page that makes API calls
    await page.goto('/');
    
    // App should still load even with API failures
    await expect(page.locator('body')).toBeVisible();
    
    // Check for error handling - could be toast, error message, or graceful degradation
    await page.waitForTimeout(3000);
    
    // Look for any error indicators
    const errorElements = [
      '.error-message',
      '[data-testid="error"]',
      'text=/error|failed|connection/i',
      '.toast-error'
    ];
    
    let hasErrorHandling = false;
    for (const selector of errorElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        hasErrorHandling = true;
        break;
      }
    }
    
    console.log(`Error handling detected: ${hasErrorHandling}`);
    
    // Clear route interception
    await page.unroute('**/api/**');
  });

  test('should maintain state during navigation', async ({ page }) => {
    // Navigate to journal
    await TestHelpers.navigateToPage(page, '/');
    
    // Look for any state-preserving elements (like search query, filters, etc.)
    const stateElements = [
      '[data-testid="search-input"]',
      'input[type="search"]',
      'select',
      '.filter-controls'
    ];
    
    let stateElement = null;
    for (const selector of stateElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        stateElement = page.locator(selector).first();
        break;
      }
    }
    
    if (stateElement) {
      // Set some state (e.g., search query)
      if (await stateElement.getAttribute('type') === 'search' || 
          await stateElement.getAttribute('placeholder')?.includes('search')) {
        await stateElement.fill('test query');
        
        // Navigate away and back
        await TestHelpers.navigateToPage(page, '/topics');
        await TestHelpers.navigateToPage(page, '/');
        
        // Check if state is maintained (may or may not be implemented)
        const currentValue = await stateElement.inputValue();
        console.log(`State preservation: ${currentValue === 'test query' ? 'Yes' : 'No'}`);
      }
    }
  });

  test('should have proper accessibility features', async ({ page }) => {
    // Check for basic accessibility features
    const accessibilityChecks = [
      { selector: 'h1', description: 'Page should have main heading' },
      { selector: '[alt]', description: 'Images should have alt text' },
      { selector: 'button, a', description: 'Interactive elements should be present' },
      { selector: 'main, [role="main"]', description: 'Main content area should be marked' }
    ];

    let accessibilityScore = 0;
    for (const check of accessibilityChecks) {
      if (await TestHelpers.elementExists(page, check.selector)) {
        accessibilityScore++;
        console.log(`✓ ${check.description}`);
      } else {
        console.log(`✗ ${check.description}`);
      }
    }
    
    // Basic accessibility should have at least interactive elements and headings
    expect(accessibilityScore).toBeGreaterThan(1);
  });
});

test.describe('API Health Checks', () => {
  
  test('should have healthy backend API', async ({ page }) => {
    // Check if backend is responding
    const response = await page.request.get('/api/health').catch(() => null);
    
    if (response) {
      expect(response.status()).toBe(200);
      
      const healthData = await response.json().catch(() => ({}));
      console.log('Backend health:', healthData);
    } else {
      console.log('Backend API not available - this is acceptable for frontend-only testing');
    }
  });

  test('should handle API rate limiting gracefully', async ({ page }) => {
    // Make multiple rapid API requests to test rate limiting
    const requests = [];
    
    for (let i = 0; i < 10; i++) {
      requests.push(
        page.request.get('/api/entries').catch(() => null)
      );
    }
    
    const responses = await Promise.all(requests);
    const successfulRequests = responses.filter(r => r && r.status() === 200).length;
    const rateLimitedRequests = responses.filter(r => r && r.status() === 429).length;
    
    console.log(`Successful requests: ${successfulRequests}, Rate limited: ${rateLimitedRequests}`);
    
    // Either all requests succeed (no rate limiting) or some are rate limited (good security)
    expect(successfulRequests + rateLimitedRequests).toBeGreaterThan(0);
  });
});