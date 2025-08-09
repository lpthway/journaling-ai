// E2E Test Helpers for Journaling AI Application

const { expect } = require('@playwright/test');

/**
 * Common test utilities and helpers
 */
class TestHelpers {
  
  /**
   * Wait for application to be ready
   * @param {Page} page - Playwright page object
   */
  static async waitForAppReady(page) {
    try {
      // Wait for React app to load (with fallback)
      await page.waitForSelector('[data-testid="app-ready"]', { 
        timeout: 10000,
        state: 'attached'
      });
    } catch {
      // Fallback: wait for basic page elements
      await page.waitForSelector('body', { timeout: 10000 });
    }
    
    // Wait for any loading spinners to disappear
    await page.waitForSelector('.loading, .spinner, [data-testid="loading"]', { 
      state: 'hidden',
      timeout: 5000
    }).catch(() => {
      // Ignore if no loading spinner exists
    });
    
    // Ensure page is fully loaded
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  }

  /**
   * Navigate to a specific page and wait for it to load
   * @param {Page} page - Playwright page object
   * @param {string} path - Path to navigate to
   */
  static async navigateToPage(page, path) {
    await page.goto(path);
    await this.waitForAppReady(page);
    
    // Wait for navigation to complete
    await page.waitForLoadState('networkidle', { timeout: 10000 });
  }

  /**
   * Fill form field with error handling
   * @param {Page} page - Playwright page object
   * @param {string} selector - Field selector
   * @param {string} value - Value to fill
   */
  static async fillField(page, selector, value) {
    const field = page.locator(selector);
    await field.waitFor({ state: 'visible', timeout: 5000 });
    await field.clear();
    await field.fill(value);
    
    // Verify field was filled
    await expect(field).toHaveValue(value);
  }

  /**
   * Click button with retry logic
   * @param {Page} page - Playwright page object
   * @param {string} selector - Button selector
   */
  static async clickButton(page, selector) {
    const button = page.locator(selector);
    await button.waitFor({ state: 'visible', timeout: 5000 });
    await button.click();
  }

  /**
   * Wait for toast notification
   * @param {Page} page - Playwright page object
   * @param {string} expectedMessage - Expected toast message (optional)
   */
  static async waitForToast(page, expectedMessage = null) {
    const toast = page.locator('[data-testid="toast"], .Toastify__toast, .toast');
    await toast.first().waitFor({ state: 'visible', timeout: 5000 });
    
    if (expectedMessage) {
      await expect(toast.first()).toContainText(expectedMessage);
    }
    
    return toast.first();
  }

  /**
   * Wait for API request to complete
   * @param {Page} page - Playwright page object  
   * @param {string} endpoint - API endpoint to wait for
   */
  static async waitForApiRequest(page, endpoint) {
    return page.waitForResponse(response => 
      response.url().includes(endpoint) && response.status() === 200,
      { timeout: 10000 }
    );
  }

  /**
   * Create a test journal entry
   * @param {Page} page - Playwright page object
   * @param {Object} entryData - Entry data
   */
  static async createJournalEntry(page, entryData = {}) {
    const defaultEntry = {
      title: 'Test Entry ' + Date.now(),
      content: 'This is a test journal entry created by E2E tests.',
      mood: 'happy',
      tags: ['test', 'e2e'],
      ...entryData
    };

    // Navigate to journal page
    await this.navigateToPage(page, '/');
    
    // Click new entry button
    await this.clickButton(page, '[data-testid="new-entry-btn"], .new-entry, button:has-text("New Entry")');
    
    // Fill entry form
    if (defaultEntry.title) {
      await this.fillField(page, '[data-testid="entry-title"], input[placeholder*="title"]', defaultEntry.title);
    }
    
    await this.fillField(page, '[data-testid="entry-content"], textarea[placeholder*="content"]', defaultEntry.content);
    
    // Set mood if specified
    if (defaultEntry.mood) {
      await page.selectOption('[data-testid="mood-select"], select', defaultEntry.mood);
    }
    
    // Add tags if specified
    if (defaultEntry.tags && defaultEntry.tags.length > 0) {
      for (const tag of defaultEntry.tags) {
        await this.fillField(page, '[data-testid="tag-input"], input[placeholder*="tag"]', tag);
        await page.keyboard.press('Enter');
      }
    }
    
    // Save entry
    await this.clickButton(page, '[data-testid="save-entry-btn"], button:has-text("Save")');
    
    // Wait for save to complete
    await this.waitForToast(page, 'saved');
    
    return defaultEntry;
  }

  /**
   * Start a new AI chat session
   * @param {Page} page - Playwright page object
   * @param {string} message - Initial message
   * @param {string} sessionType - Type of session (optional)
   */
  static async startChatSession(page, message = 'Hello, this is a test message', sessionType = null) {
    // Navigate to chat page
    await this.navigateToPage(page, '/chat');
    
    // Select session type if specified
    if (sessionType) {
      await page.selectOption('[data-testid="session-type"], select', sessionType);
    }
    
    // Send initial message
    await this.fillField(page, '[data-testid="chat-input"], textarea[placeholder*="message"]', message);
    await this.clickButton(page, '[data-testid="send-message-btn"], button[type="submit"]');
    
    // Wait for AI response
    await page.waitForSelector('[data-testid="ai-message"], .ai-message', { timeout: 30000 });
    
    return { message, sessionType };
  }

  /**
   * Perform search with specified query
   * @param {Page} page - Playwright page object
   * @param {string} query - Search query
   */
  static async performSearch(page, query) {
    // Use header search if available
    const headerSearch = page.locator('[data-testid="header-search"], .header-search input');
    const searchVisible = await headerSearch.isVisible().catch(() => false);
    
    if (searchVisible) {
      await this.fillField(page, '[data-testid="header-search"], .header-search input', query);
      await page.keyboard.press('Enter');
    } else {
      // Use page-specific search
      await this.fillField(page, '[data-testid="search-input"], input[type="search"]', query);
      await this.clickButton(page, '[data-testid="search-btn"], button:has-text("Search")');
    }
    
    // Wait for search results
    await page.waitForSelector('[data-testid="search-results"], .search-results', { timeout: 10000 });
    
    return query;
  }

  /**
   * Check if element exists without throwing
   * @param {Page} page - Playwright page object
   * @param {string} selector - Element selector
   */
  static async elementExists(page, selector) {
    try {
      await page.waitForSelector(selector, { timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Take screenshot with timestamp
   * @param {Page} page - Playwright page object
   * @param {string} name - Screenshot name
   */
  static async takeScreenshot(page, name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    
    await page.screenshot({ 
      path: `e2e/results/screenshots/${filename}`,
      fullPage: true 
    });
    
    return filename;
  }

  /**
   * Get current URL pathname
   * @param {Page} page - Playwright page object
   */
  static async getCurrentPath(page) {
    return page.evaluate(() => window.location.pathname);
  }

  /**
   * Wait for element to be stable (not moving/changing)
   * @param {Page} page - Playwright page object
   * @param {string} selector - Element selector
   */
  static async waitForStableElement(page, selector) {
    const element = page.locator(selector);
    await element.waitFor({ state: 'visible' });
    
    // Wait for element to stop moving/changing
    let previousBoundingBox = null;
    for (let i = 0; i < 5; i++) {
      const currentBoundingBox = await element.boundingBox();
      if (previousBoundingBox && 
          Math.abs(currentBoundingBox.x - previousBoundingBox.x) < 1 &&
          Math.abs(currentBoundingBox.y - previousBoundingBox.y) < 1) {
        break;
      }
      previousBoundingBox = currentBoundingBox;
      await page.waitForTimeout(200);
    }
  }

  /**
   * Authenticate user if needed
   * @param {Page} page - Playwright page object
   * @param {Object} credentials - Login credentials
   */
  static async authenticateIfNeeded(page, credentials = { email: 'test@example.com', password: 'testpassword123' }) {
    // Check if authentication is required
    const needsAuth = await this.elementExists(page, 'input[type="email"], .login-form, text=/login/i');
    
    if (needsAuth) {
      console.log('🔐 Authentication required - attempting login');
      
      const loginForm = page.locator('form, .login-form').first();
      const emailField = loginForm.locator('input[type="email"], input[name="email"]').first();
      const passwordField = loginForm.locator('input[type="password"], input[name="password"]').first();
      const loginButton = loginForm.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
      
      if (await emailField.isVisible() && await passwordField.isVisible()) {
        await emailField.fill(credentials.email);
        await passwordField.fill(credentials.password);
        await loginButton.click();
        
        // Wait for authentication to complete
        await page.waitForTimeout(3000);
        
        // Check if authentication was successful
        const isAuthenticated = await this.elementExists(page, '[data-testid="user-menu"], .user-profile, text=/logout/i');
        
        if (isAuthenticated) {
          console.log('✅ Authentication successful');
          return true;
        } else {
          console.log('⚠ Authentication failed or credentials invalid');
          return false;
        }
      }
    }
    
    return true; // Already authenticated or no auth required
  }

  /**
   * Check authentication status
   * @param {Page} page - Playwright page object
   */
  static async isAuthenticated(page) {
    const authenticatedElements = [
      '[data-testid="user-menu"]',
      '.user-profile',
      'text=/logout|sign out/i',
      '.authenticated',
      '[data-testid="app-authenticated"]'
    ];
    
    for (const selector of authenticatedElements) {
      if (await this.elementExists(page, selector)) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * Logout user if authenticated
   * @param {Page} page - Playwright page object
   */
  static async logoutIfAuthenticated(page) {
    const isAuth = await this.isAuthenticated(page);
    
    if (isAuth) {
      const logoutTriggers = [
        'button:has-text("Logout")',
        'a:has-text("Sign Out")',
        '[data-testid="logout-btn"]',
        '.logout'
      ];
      
      let logoutButton = null;
      for (const selector of logoutTriggers) {
        if (await this.elementExists(page, selector)) {
          logoutButton = page.locator(selector).first();
          break;
        }
      }
      
      // Try clicking user menu first if logout not immediately visible
      if (!logoutButton) {
        const userMenu = page.locator('[data-testid="user-menu"], .user-profile').first();
        if (await userMenu.isVisible()) {
          await userMenu.click();
          await page.waitForTimeout(500);
          
          for (const selector of logoutTriggers) {
            if (await this.elementExists(page, selector)) {
              logoutButton = page.locator(selector).first();
              break;
            }
          }
        }
      }
      
      if (logoutButton && await logoutButton.isVisible()) {
        await logoutButton.click();
        await page.waitForTimeout(2000);
        console.log('🚪 User logged out');
        return true;
      }
    }
    
    return false;
  }

  /**
   * Wait for network requests to complete
   * @param {Page} page - Playwright page object
   * @param {number} timeout - Timeout in milliseconds
   */
  static async waitForNetworkIdle(page, timeout = 5000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Simulate typing with realistic delays
   * @param {Page} page - Playwright page object
   * @param {string} selector - Input selector
   * @param {string} text - Text to type
   */
  static async typeRealistic(page, selector, text) {
    const field = page.locator(selector);
    await field.click();
    
    for (const char of text) {
      await field.type(char);
      await page.waitForTimeout(Math.random() * 100 + 50); // Random delay between 50-150ms
    }
  }

  /**
   * Check if page has error states
   * @param {Page} page - Playwright page object
   */
  static async hasErrors(page) {
    const errorSelectors = [
      '.error',
      '[data-testid="error"]',
      '.error-message',
      'text=/error|failed|something went wrong/i',
      '[role="alert"]'
    ];
    
    for (const selector of errorSelectors) {
      if (await this.elementExists(page, selector)) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * Get performance metrics
   * @param {Page} page - Playwright page object
   */
  static async getPerformanceMetrics(page) {
    return await page.evaluate(() => {
      const perfData = performance.timing;
      const navigation = performance.getEntriesByType('navigation')[0];
      
      return {
        loadTime: perfData.loadEventEnd - perfData.navigationStart,
        domReady: perfData.domContentLoadedEventEnd - perfData.navigationStart,
        firstByte: perfData.responseStart - perfData.navigationStart,
        navigation: navigation ? {
          domContentLoaded: navigation.domContentLoadedEventEnd,
          loadComplete: navigation.loadEventEnd
        } : null,
        memory: performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit
        } : null
      };
    });
  }
}

module.exports = { TestHelpers };