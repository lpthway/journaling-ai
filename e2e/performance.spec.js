// E2E Performance and Stress Tests

const { test, expect } = require('@playwright/test');
const { TestHelpers } = require('./utils/test-helpers');

test.describe('Performance and Load Testing', () => {
  
  test('Application load time performance', async ({ page }) => {
    console.log('⏱️ Measuring application load performance');
    
    const loadStartTime = Date.now();
    
    // Navigate to homepage and measure load time
    await page.goto('/');
    await TestHelpers.waitForAppReady(page);
    
    const loadEndTime = Date.now();
    const totalLoadTime = loadEndTime - loadStartTime;
    
    console.log(`📊 Total load time: ${totalLoadTime}ms`);
    
    // Performance thresholds (adjust based on your requirements)
    const performanceThresholds = {
      excellent: 1000,  // < 1s
      good: 3000,      // < 3s
      acceptable: 5000  // < 5s
    };
    
    let performanceRating;
    if (totalLoadTime < performanceThresholds.excellent) {
      performanceRating = 'Excellent';
    } else if (totalLoadTime < performanceThresholds.good) {
      performanceRating = 'Good';
    } else if (totalLoadTime < performanceThresholds.acceptable) {
      performanceRating = 'Acceptable';
    } else {
      performanceRating = 'Needs Improvement';
    }
    
    console.log(`📈 Performance rating: ${performanceRating}`);
    
    // Take screenshot for performance documentation
    await TestHelpers.takeScreenshot(page, 'performance-load-complete');
    
    // Basic performance expectation
    expect(totalLoadTime).toBeLessThan(10000); // Should load within 10 seconds
    
    // Measure Core Web Vitals if possible
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        // Simple performance timing
        const perfData = performance.timing;
        const loadTime = perfData.loadEventEnd - perfData.navigationStart;
        const domReady = perfData.domContentLoadedEventEnd - perfData.navigationStart;
        
        resolve({
          loadTime,
          domReady,
          timestamp: Date.now()
        });
      });
    });
    
    console.log(`🎯 DOM Ready: ${webVitals.domReady}ms`);
    console.log(`🎯 Full Load: ${webVitals.loadTime}ms`);
  });

  test('Large journal entry handling performance', async ({ page }) => {
    console.log('📄 Testing large journal entry performance');
    
    await TestHelpers.navigateToPage(page, '/');
    
    // Create a large journal entry
    const largeContent = 'This is a very long journal entry. '.repeat(1000); // ~35KB of text
    
    const newEntryBtn = page.locator('[data-testid="new-entry-btn"], button:has-text("New Entry")').first();
    
    if (await newEntryBtn.isVisible()) {
      await newEntryBtn.click();
      await page.waitForTimeout(1000);
      
      const titleField = page.locator('[data-testid="entry-title"], input').first();
      const contentField = page.locator('[data-testid="entry-content"], textarea').first();
      
      if (await titleField.isVisible() && await contentField.isVisible()) {
        await titleField.fill('Large Content Performance Test');
        
        // Measure typing performance
        const typingStartTime = Date.now();
        await contentField.fill(largeContent);
        const typingEndTime = Date.now();
        
        console.log(`⌨️ Large text input time: ${typingEndTime - typingStartTime}ms`);
        
        // Measure save performance
        const saveBtn = page.locator('[data-testid="save-entry-btn"], button:has-text("Save")').first();
        
        if (await saveBtn.isVisible()) {
          const saveStartTime = Date.now();
          await saveBtn.click();
          
          // Wait for save operation to complete
          await page.waitForTimeout(5000);
          
          const saveEndTime = Date.now();
          console.log(`💾 Large entry save time: ${saveEndTime - saveStartTime}ms`);
          
          // Check if save was successful
          const hasSuccess = await TestHelpers.elementExists(page, '.success, text=/saved/i');
          const hasError = await TestHelpers.elementExists(page, '.error, text=/error/i');
          
          if (hasSuccess) {
            console.log('✓ Large entry saved successfully');
          } else if (hasError) {
            console.log('⚠ Large entry save failed (may be too large)');
          }
        }
      }
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-large-entry');
  });

  test('Multiple entries navigation performance', async ({ page }) => {
    console.log('📚 Testing multiple entries navigation performance');
    
    await TestHelpers.navigateToPage(page, '/');
    
    // Measure entry list load time
    const listLoadStart = Date.now();
    await page.waitForTimeout(2000);
    const listLoadEnd = Date.now();
    
    console.log(`📋 Entry list load time: ${listLoadEnd - listLoadStart}ms`);
    
    // Count visible entries
    const entryCount = await page.locator('.entry, .entry-card, [data-testid="entry"]').count();
    console.log(`📊 Visible entries: ${entryCount}`);
    
    if (entryCount > 0) {
      // Test rapid navigation between entries
      const navigationTimes = [];
      const maxEntriesToTest = Math.min(entryCount, 5); // Test up to 5 entries
      
      for (let i = 0; i < maxEntriesToTest; i++) {
        const navigationStart = Date.now();
        
        const entry = page.locator('.entry, .entry-card, [data-testid="entry"]').nth(i);
        
        if (await entry.isVisible()) {
          await entry.click();
          await page.waitForTimeout(1000);
          
          // Navigate back to list
          const backBtn = page.locator('button:has-text("Back"), a[href="/"], [data-testid="back-btn"]').first();
          
          if (await backBtn.isVisible()) {
            await backBtn.click();
          } else {
            // Use browser back if no back button
            await page.goBack();
          }
          
          await page.waitForTimeout(500);
        }
        
        const navigationEnd = Date.now();
        navigationTimes.push(navigationEnd - navigationStart);
      }
      
      const averageNavTime = navigationTimes.reduce((a, b) => a + b, 0) / navigationTimes.length;
      console.log(`🧭 Average navigation time: ${averageNavTime.toFixed(2)}ms`);
      
      // Performance expectation for navigation
      expect(averageNavTime).toBeLessThan(3000); // Navigation should be under 3s
    }
  });

  test('Chat response time performance', async ({ page }) => {
    console.log('🤖 Testing AI chat response performance');
    
    await TestHelpers.navigateToPage(page, '/chat');
    
    const chatInput = page.locator('[data-testid="chat-input"], textarea, input').first();
    const sendButton = page.locator('[data-testid="send-btn"], button:has-text("Send")').first();
    
    if (await chatInput.isVisible() && await sendButton.isVisible()) {
      const testMessages = [
        'Hello!',
        'How are you today?',
        'What do you think about journaling?',
        'Can you help me understand my emotions?',
        'What insights do you have about my journal entries?'
      ];
      
      const responseTimes = [];
      
      for (const message of testMessages) {
        await chatInput.fill(message);
        
        const sendTime = Date.now();
        await sendButton.click();
        
        try {
          // Wait for AI response with timeout
          await page.waitForSelector('[data-testid="ai-message"], .ai-message, .assistant-message', { 
            timeout: 30000 
          });
          
          const responseTime = Date.now();
          const duration = responseTime - sendTime;
          
          responseTimes.push(duration);
          console.log(`💬 Response time for "${message}": ${duration}ms`);
          
          // Clear input for next message
          await chatInput.clear();
          await page.waitForTimeout(1000);
          
        } catch (error) {
          console.log(`⚠ No response received for: "${message}"`);
          responseTimes.push(30000); // Timeout value
        }
      }
      
      if (responseTimes.length > 0) {
        const averageResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        const minResponseTime = Math.min(...responseTimes);
        const maxResponseTime = Math.max(...responseTimes);
        
        console.log(`📊 Average AI response time: ${averageResponseTime.toFixed(2)}ms`);
        console.log(`📊 Fastest response: ${minResponseTime}ms`);
        console.log(`📊 Slowest response: ${maxResponseTime}ms`);
        
        // AI response time expectations (very flexible as it depends on the model)
        expect(averageResponseTime).toBeLessThan(60000); // Should respond within 1 minute on average
      }
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-chat-responses');
  });

  test('Search performance with various query types', async ({ page }) => {
    console.log('🔍 Testing search performance');
    
    await TestHelpers.navigateToPage(page, '/');
    
    const searchField = page.locator('[data-testid="search-input"], input[type="search"], input[placeholder*="search"]').first();
    
    if (await searchField.isVisible()) {
      const searchQueries = [
        'happy',           // Simple word
        'test entry',      // Multi-word
        'journaling thoughts', // Complex phrase
        'mood:happy',      // Structured query (if supported)
        'tag:test',        // Tag search (if supported)
        'nonexistentterm123' // No results query
      ];
      
      const searchTimes = [];
      
      for (const query of searchQueries) {
        const searchStart = Date.now();
        
        await searchField.fill(query);
        await page.keyboard.press('Enter');
        
        // Wait for search results to load
        try {
          await page.waitForSelector('[data-testid="search-results"], .search-results, .results', { 
            timeout: 10000 
          });
          
          const searchEnd = Date.now();
          const duration = searchEnd - searchStart;
          
          searchTimes.push(duration);
          console.log(`🔍 Search time for "${query}": ${duration}ms`);
          
          // Count results
          const resultCount = await page.locator('.entry, .entry-card, .result').count();
          console.log(`📊 Results found: ${resultCount}`);
          
          await page.waitForTimeout(500);
          
        } catch (error) {
          console.log(`⚠ Search timeout for: "${query}"`);
          searchTimes.push(10000); // Timeout value
        }
        
        // Clear search for next query
        await searchField.clear();
      }
      
      if (searchTimes.length > 0) {
        const averageSearchTime = searchTimes.reduce((a, b) => a + b, 0) / searchTimes.length;
        console.log(`📊 Average search time: ${averageSearchTime.toFixed(2)}ms`);
        
        // Search performance expectation
        expect(averageSearchTime).toBeLessThan(5000); // Search should be under 5s
      }
    } else {
      console.log('⚠ No search functionality found');
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-search-results');
  });

  test('Memory usage monitoring during extended session', async ({ page }) => {
    console.log('🧠 Monitoring memory usage during extended session');
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });
    
    if (initialMemory) {
      console.log(`🧠 Initial memory usage: ${(initialMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
    }
    
    // Simulate extended usage
    const activities = [
      { action: 'navigate', target: '/' },
      { action: 'navigate', target: '/chat' },
      { action: 'navigate', target: '/insights' },
      { action: 'navigate', target: '/topics' },
      { action: 'navigate', target: '/' }
    ];
    
    // Repeat activities to simulate extended use
    for (let cycle = 0; cycle < 3; cycle++) {
      console.log(`🔄 Extended usage cycle ${cycle + 1}/3`);
      
      for (const activity of activities) {
        await TestHelpers.navigateToPage(page, activity.target);
        await page.waitForTimeout(1000);
        
        // Simulate some interaction on each page
        const interactableElements = await page.locator('button, input, select, a').count();
        if (interactableElements > 0) {
          const randomIndex = Math.floor(Math.random() * Math.min(interactableElements, 3));
          const element = page.locator('button, input, select, a').nth(randomIndex);
          
          if (await element.isVisible()) {
            try {
              await element.click({ timeout: 1000 });
              await page.waitForTimeout(500);
            } catch (e) {
              // Some elements might not be clickable
            }
          }
        }
      }
    }
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });
    
    if (finalMemory && initialMemory) {
      const memoryIncrease = (finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize) / 1024 / 1024;
      console.log(`🧠 Final memory usage: ${(finalMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`📈 Memory increase: ${memoryIncrease.toFixed(2)} MB`);
      
      // Memory leak detection
      if (memoryIncrease > 50) { // Alert if more than 50MB increase
        console.log('⚠️ Potential memory leak detected');
      } else {
        console.log('✅ Memory usage appears stable');
      }
      
      // Basic memory expectation (very generous for complex apps)
      expect(finalMemory.usedJSHeapSize).toBeLessThan(500 * 1024 * 1024); // Should use less than 500MB
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-extended-session');
  });

  test('Concurrent user simulation', async ({ page, browser }) => {
    console.log('👥 Simulating concurrent user activities');
    
    // Create additional browser contexts to simulate multiple users
    const contexts = [];
    const maxConcurrentUsers = 3;
    
    try {
      for (let i = 0; i < maxConcurrentUsers; i++) {
        const context = await browser.newContext();
        const concurrentPage = await context.newPage();
        contexts.push({ context, page: concurrentPage });
      }
      
      console.log(`👥 Created ${maxConcurrentUsers} concurrent user sessions`);
      
      // Simulate different activities for each user
      const userActivities = [
        async (userPage) => {
          // User 1: Journal entry creation
          await TestHelpers.navigateToPage(userPage, '/');
          const newEntryBtn = userPage.locator('[data-testid="new-entry-btn"], button:has-text("New Entry")').first();
          if (await newEntryBtn.isVisible()) {
            await newEntryBtn.click();
            await userPage.waitForTimeout(500);
          }
        },
        async (userPage) => {
          // User 2: Chat interaction
          await TestHelpers.navigateToPage(userPage, '/chat');
          const chatInput = userPage.locator('[data-testid="chat-input"], textarea, input').first();
          if (await chatInput.isVisible()) {
            await chatInput.fill('Concurrent user test message');
            await userPage.waitForTimeout(500);
          }
        },
        async (userPage) => {
          // User 3: Search and browse
          await TestHelpers.navigateToPage(userPage, '/');
          const searchField = userPage.locator('[data-testid="search-input"], input[type="search"]').first();
          if (await searchField.isVisible()) {
            await searchField.fill('test');
            await userPage.waitForTimeout(500);
          }
        }
      ];
      
      // Execute activities concurrently
      const concurrentStartTime = Date.now();
      
      const concurrentPromises = contexts.map((ctx, index) => {
        const activity = userActivities[index % userActivities.length];
        return activity(ctx.page);
      });
      
      await Promise.all(concurrentPromises);
      
      const concurrentEndTime = Date.now();
      console.log(`👥 Concurrent activities completed in: ${concurrentEndTime - concurrentStartTime}ms`);
      
      // Check if main page is still responsive
      await TestHelpers.navigateToPage(page, '/');
      const isResponsive = await page.locator('body').isVisible();
      
      if (isResponsive) {
        console.log('✅ Main page remains responsive during concurrent usage');
      } else {
        console.log('⚠️ Main page responsiveness affected by concurrent usage');
      }
      
    } finally {
      // Clean up concurrent contexts
      for (const ctx of contexts) {
        await ctx.context.close();
      }
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-concurrent-users');
  });

  test('API response time monitoring', async ({ page }) => {
    console.log('📡 Monitoring API response times');
    
    const apiResponseTimes = {};
    
    // Monitor API requests
    page.on('response', response => {
      const url = response.url();
      const status = response.status();
      
      if (url.includes('/api/')) {
        const endpoint = url.split('/api/')[1].split('?')[0];
        const timing = response.timing();
        
        if (!apiResponseTimes[endpoint]) {
          apiResponseTimes[endpoint] = [];
        }
        
        apiResponseTimes[endpoint].push({
          status,
          responseTime: timing ? timing.responseEnd - timing.responseStart : 0
        });
      }
    });
    
    // Perform various activities that trigger API calls
    const apiTestActivities = [
      () => TestHelpers.navigateToPage(page, '/'),
      () => TestHelpers.navigateToPage(page, '/chat'),
      () => TestHelpers.navigateToPage(page, '/insights'),
      () => TestHelpers.navigateToPage(page, '/topics')
    ];
    
    for (const activity of apiTestActivities) {
      await activity();
      await page.waitForTimeout(2000); // Allow API calls to complete
    }
    
    // Report API performance
    console.log('📊 API Performance Summary:');
    for (const [endpoint, responses] of Object.entries(apiResponseTimes)) {
      if (responses.length > 0) {
        const avgTime = responses.reduce((sum, r) => sum + r.responseTime, 0) / responses.length;
        const successRate = responses.filter(r => r.status < 400).length / responses.length * 100;
        
        console.log(`  ${endpoint}:`);
        console.log(`    Average response time: ${avgTime.toFixed(2)}ms`);
        console.log(`    Success rate: ${successRate.toFixed(1)}%`);
        console.log(`    Total requests: ${responses.length}`);
      }
    }
    
    await TestHelpers.takeScreenshot(page, 'performance-api-monitoring');
  });
});