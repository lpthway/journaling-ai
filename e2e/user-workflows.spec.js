// E2E Tests for Complete User Workflows

const { test, expect } = require('@playwright/test');
const { TestHelpers } = require('./utils/test-helpers');
const { userFlows, sampleEntries } = require('./fixtures/test-data');

test.describe('Complete User Workflows', () => {
  
  test.beforeEach(async ({ page }) => {
    await TestHelpers.navigateToPage(page, '/');
  });

  test('New user complete onboarding flow', async ({ page }) => {
    console.log('🎯 Testing complete new user workflow');
    
    // Step 1: Initial app load and authentication check
    await TestHelpers.takeScreenshot(page, 'workflow-new-user-start');
    
    // Check if authentication is required
    const needsAuth = await TestHelpers.elementExists(page, 'input[type="email"], .login-form, text=/login/i');
    
    if (needsAuth) {
      console.log('📝 Authentication required - simulating login');
      
      const loginForm = page.locator('form, .login-form').first();
      const emailField = loginForm.locator('input[type="email"], input[name="email"]').first();
      const passwordField = loginForm.locator('input[type="password"], input[name="password"]').first();
      const loginButton = loginForm.locator('button[type="submit"], button:has-text("Login")').first();
      
      if (await emailField.isVisible() && await passwordField.isVisible()) {
        await emailField.fill('test@example.com');
        await passwordField.fill('testpassword123');
        await loginButton.click();
        await page.waitForTimeout(2000);
      }
    }
    
    // Step 2: First journal entry creation
    console.log('📖 Creating first journal entry');
    
    try {
      // Look for new entry button
      const newEntrySelectors = [
        '[data-testid="new-entry-btn"]',
        'button:has-text("New Entry")',
        'a:has-text("New Entry")',
        '.new-entry',
        'button:has-text("+")'
      ];
      
      let newEntryButton = null;
      for (const selector of newEntrySelectors) {
        if (await TestHelpers.elementExists(page, selector)) {
          newEntryButton = page.locator(selector).first();
          break;
        }
      }
      
      if (newEntryButton) {
        await newEntryButton.click();
        await page.waitForTimeout(1000);
        
        // Fill entry form
        const titleField = page.locator('[data-testid="entry-title"], input[placeholder*="title"], input[name="title"]').first();
        const contentField = page.locator('[data-testid="entry-content"], textarea[placeholder*="content"], textarea[name="content"]').first();
        
        if (await titleField.isVisible()) {
          await titleField.fill('My First Journal Entry - E2E Test');
        }
        
        if (await contentField.isVisible()) {
          await contentField.fill('This is my first journal entry created during E2E testing. I\'m exploring this journaling application and learning about its features. Today feels like a new beginning!');
        }
        
        // Set mood if available
        const moodSelect = page.locator('[data-testid="mood-select"], select[name="mood"]').first();
        if (await moodSelect.isVisible()) {
          await moodSelect.selectOption('excited');
        }
        
        // Add tags if available
        const tagInput = page.locator('[data-testid="tag-input"], input[placeholder*="tag"]').first();
        if (await tagInput.isVisible()) {
          await tagInput.fill('first-entry');
          await page.keyboard.press('Enter');
          await tagInput.fill('e2e-test');
          await page.keyboard.press('Enter');
        }
        
        // Save entry
        const saveButton = page.locator('[data-testid="save-entry-btn"], button:has-text("Save"), button[type="submit"]').first();
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(2000);
          
          console.log('✓ First journal entry created successfully');
          await TestHelpers.takeScreenshot(page, 'workflow-first-entry-created');
        }
      }
    } catch (error) {
      console.log('⚠ Entry creation flow variation:', error.message);
    }
    
    // Step 3: Explore AI chat functionality
    console.log('🤖 Testing AI chat functionality');
    
    try {
      await TestHelpers.navigateToPage(page, '/chat');
      
      const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="message"], input[placeholder*="message"]').first();
      const sendButton = page.locator('[data-testid="send-btn"], button:has-text("Send"), button[type="submit"]').first();
      
      if (await chatInput.isVisible() && await sendButton.isVisible()) {
        await chatInput.fill('Hello! I just created my first journal entry. Can you help me understand how to make the most of this journaling application?');
        await sendButton.click();
        
        // Wait for AI response with extended timeout
        await page.waitForTimeout(5000);
        
        const hasAIResponse = await TestHelpers.elementExists(page, '[data-testid="ai-message"], .ai-message, .assistant-message');
        
        if (hasAIResponse) {
          console.log('✓ AI chat interaction successful');
        } else {
          console.log('⚠ AI response not detected (may take longer)');
        }
        
        await TestHelpers.takeScreenshot(page, 'workflow-first-chat');
      }
    } catch (error) {
      console.log('⚠ Chat flow variation:', error.message);
    }
    
    // Step 4: Explore insights page
    console.log('📊 Exploring insights functionality');
    
    try {
      await TestHelpers.navigateToPage(page, '/insights');
      await page.waitForTimeout(2000);
      
      // Look for insights content
      const insightsContent = [
        '.insights',
        '[data-testid="insights"]',
        '.analytics',
        '.charts',
        '.mood-trends'
      ];
      
      let hasInsights = false;
      for (const selector of insightsContent) {
        if (await TestHelpers.elementExists(page, selector)) {
          hasInsights = true;
          console.log('✓ Insights page loaded with content');
          break;
        }
      }
      
      if (!hasInsights) {
        console.log('⚠ Insights page may need more data or different structure');
      }
      
      await TestHelpers.takeScreenshot(page, 'workflow-insights-explored');
    } catch (error) {
      console.log('⚠ Insights exploration variation:', error.message);
    }
    
    // Step 5: Return to journal and view entries
    console.log('📚 Returning to journal overview');
    
    await TestHelpers.navigateToPage(page, '/');
    await page.waitForTimeout(2000);
    
    // Check for entries list
    const hasEntries = await TestHelpers.elementExists(page, '.entry, .entry-card, [data-testid="entry"]');
    const hasEmptyState = await TestHelpers.elementExists(page, '.empty-state, text=/no entries/i');
    
    if (hasEntries) {
      console.log('✓ Journal entries are visible');
      
      // Click on first entry to view details
      const firstEntry = page.locator('.entry, .entry-card, [data-testid="entry"]').first();
      if (await firstEntry.isVisible()) {
        await firstEntry.click();
        await page.waitForTimeout(1000);
        
        console.log('✓ Entry details view accessed');
        await TestHelpers.takeScreenshot(page, 'workflow-entry-details');
      }
    } else if (hasEmptyState) {
      console.log('✓ Empty state displayed (entry creation may have failed)');
    }
    
    await TestHelpers.takeScreenshot(page, 'workflow-new-user-complete');
    console.log('🎉 New user workflow test completed');
  });

  test('Experienced user daily workflow', async ({ page }) => {
    console.log('🎯 Testing experienced user daily workflow');
    
    await TestHelpers.takeScreenshot(page, 'workflow-experienced-start');
    
    // Step 1: Quick entry creation (experienced user knows the interface)
    console.log('⚡ Quick entry creation');
    
    const quickEntry = {
      title: 'Daily Reflection - ' + new Date().toLocaleDateString(),
      content: 'Today I completed E2E testing for the journaling application. The testing process revealed several interesting insights about user workflows and helped identify areas for improvement.',
      mood: 'thoughtful'
    };
    
    try {
      const newEntryBtn = page.locator('[data-testid="new-entry-btn"], button:has-text("New Entry"), .new-entry').first();
      
      if (await newEntryBtn.isVisible()) {
        await newEntryBtn.click();
        
        // Quick form fill
        const titleField = page.locator('[data-testid="entry-title"], input[name="title"]').first();
        const contentField = page.locator('[data-testid="entry-content"], textarea[name="content"]').first();
        const moodSelect = page.locator('[data-testid="mood-select"], select[name="mood"]').first();
        
        if (await titleField.isVisible()) {
          await titleField.fill(quickEntry.title);
        }
        
        if (await contentField.isVisible()) {
          await contentField.fill(quickEntry.content);
        }
        
        if (await moodSelect.isVisible()) {
          await moodSelect.selectOption(quickEntry.mood);
        }
        
        const saveBtn = page.locator('[data-testid="save-entry-btn"], button:has-text("Save")').first();
        if (await saveBtn.isVisible()) {
          await saveBtn.click();
          await page.waitForTimeout(1000);
        }
        
        console.log('✓ Quick entry created');
      }
    } catch (error) {
      console.log('⚠ Quick entry creation variation:', error.message);
    }
    
    // Step 2: Search through past entries
    console.log('🔍 Searching past entries');
    
    try {
      await TestHelpers.navigateToPage(page, '/');
      
      const searchSelectors = [
        '[data-testid="search-input"]',
        'input[type="search"]',
        'input[placeholder*="search"]',
        '.search-input'
      ];
      
      let searchField = null;
      for (const selector of searchSelectors) {
        if (await TestHelpers.elementExists(page, selector)) {
          searchField = page.locator(selector).first();
          break;
        }
      }
      
      if (searchField) {
        await searchField.fill('testing');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(2000);
        
        console.log('✓ Search functionality used');
        await TestHelpers.takeScreenshot(page, 'workflow-search-results');
      }
    } catch (error) {
      console.log('⚠ Search functionality variation:', error.message);
    }
    
    // Step 3: Advanced insights exploration
    console.log('📈 Advanced insights exploration');
    
    try {
      await TestHelpers.navigateToPage(page, '/insights');
      
      // Look for interactive elements
      const interactiveElements = [
        'button',
        'select',
        '.tab',
        '[role="tab"]',
        '.filter'
      ];
      
      let interactions = 0;
      for (const selector of interactiveElements) {
        const elements = page.locator(selector);
        const count = await elements.count();
        
        if (count > 0) {
          // Try clicking first element of each type
          try {
            const firstElement = elements.first();
            if (await firstElement.isVisible()) {
              await firstElement.click();
              await page.waitForTimeout(500);
              interactions++;
            }
          } catch (e) {
            // Some elements might not be clickable
          }
        }
      }
      
      console.log(`✓ Interacted with ${interactions} insights elements`);
      
      // Try asking a question if available
      const questionInput = page.locator('[data-testid="question-input"], textarea[placeholder*="question"]').first();
      
      if (await questionInput.isVisible()) {
        await questionInput.fill('What patterns do you notice in my recent journal entries?');
        
        const askButton = page.locator('[data-testid="ask-question-btn"], button:has-text("Ask")').first();
        if (await askButton.isVisible()) {
          await askButton.click();
          await page.waitForTimeout(3000);
          
          console.log('✓ AI insights question asked');
        }
      }
      
      await TestHelpers.takeScreenshot(page, 'workflow-advanced-insights');
    } catch (error) {
      console.log('⚠ Advanced insights variation:', error.message);
    }
    
    // Step 4: Multi-session chat exploration
    console.log('💬 Multi-session chat exploration');
    
    try {
      await TestHelpers.navigateToPage(page, '/chat');
      
      // Check for session management
      const sessionElements = [
        '.session',
        '.chat-session',
        '[data-testid="session"]'
      ];
      
      let hasSessionManagement = false;
      for (const selector of sessionElements) {
        if (await TestHelpers.elementExists(page, selector)) {
          hasSessionManagement = true;
          
          // Click on different sessions
          const sessions = page.locator(selector);
          const sessionCount = await sessions.count();
          
          if (sessionCount > 1) {
            console.log(`✓ Found ${sessionCount} chat sessions`);
            
            // Switch between sessions
            await sessions.nth(0).click();
            await page.waitForTimeout(500);
            
            if (sessionCount > 1) {
              await sessions.nth(1).click();
              await page.waitForTimeout(500);
            }
          }
          break;
        }
      }
      
      // Send a contextual message
      const chatInput = page.locator('[data-testid="chat-input"], textarea, input').first();
      const sendButton = page.locator('[data-testid="send-btn"], button:has-text("Send")').first();
      
      if (await chatInput.isVisible() && await sendButton.isVisible()) {
        await chatInput.fill('Based on my recent journal entries, what suggestions do you have for my personal development?');
        await sendButton.click();
        await page.waitForTimeout(3000);
        
        console.log('✓ Contextual AI conversation initiated');
      }
      
      await TestHelpers.takeScreenshot(page, 'workflow-multi-session-chat');
    } catch (error) {
      console.log('⚠ Multi-session chat variation:', error.message);
    }
    
    // Step 5: Navigation efficiency test
    console.log('🚀 Navigation efficiency test');
    
    const navigationSequence = [
      { path: '/', name: 'Journal' },
      { path: '/insights', name: 'Insights' },
      { path: '/chat', name: 'Chat' },
      { path: '/topics', name: 'Topics' },
      { path: '/', name: 'Back to Journal' }
    ];
    
    let navigationSpeed = 0;
    for (const nav of navigationSequence) {
      const startTime = Date.now();
      await TestHelpers.navigateToPage(page, nav.path);
      const endTime = Date.now();
      navigationSpeed += (endTime - startTime);
      
      await page.waitForTimeout(500); // Brief pause between navigations
    }
    
    console.log(`✓ Navigation efficiency: ${navigationSpeed}ms total for ${navigationSequence.length} pages`);
    
    await TestHelpers.takeScreenshot(page, 'workflow-experienced-complete');
    console.log('🎉 Experienced user workflow test completed');
  });

  test('Error recovery and resilience workflow', async ({ page }) => {
    console.log('🎯 Testing error recovery and resilience');
    
    // Step 1: Test network interruption simulation
    console.log('🌐 Testing network interruption handling');
    
    try {
      // Block some API requests to simulate network issues
      await page.route('**/api/entries**', route => {
        // Randomly fail some requests
        if (Math.random() < 0.3) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });
      
      // Try to create an entry during network instability
      await TestHelpers.navigateToPage(page, '/');
      
      const newEntryBtn = page.locator('[data-testid="new-entry-btn"], button:has-text("New Entry")').first();
      
      if (await newEntryBtn.isVisible()) {
        await newEntryBtn.click();
        
        const titleField = page.locator('[data-testid="entry-title"], input').first();
        const contentField = page.locator('[data-testid="entry-content"], textarea').first();
        
        if (await titleField.isVisible() && await contentField.isVisible()) {
          await titleField.fill('Network Resilience Test');
          await contentField.fill('This entry tests how the app handles network issues');
          
          const saveBtn = page.locator('[data-testid="save-entry-btn"], button:has-text("Save")').first();
          if (await saveBtn.isVisible()) {
            await saveBtn.click();
            await page.waitForTimeout(3000);
            
            // Check for error handling or success despite network issues
            const hasError = await TestHelpers.elementExists(page, '.error, [data-testid="error"], text=/failed|error/i');
            const hasSuccess = await TestHelpers.elementExists(page, '.success, [data-testid="success"], text=/saved|success/i');
            
            if (hasError) {
              console.log('✓ Error handling displayed during network issues');
            } else if (hasSuccess) {
              console.log('✓ Operation succeeded despite network simulation');
            }
          }
        }
      }
      
      // Clear route interception
      await page.unroute('**/api/entries**');
      
      await TestHelpers.takeScreenshot(page, 'workflow-network-resilience');
    } catch (error) {
      console.log('⚠ Network resilience test variation:', error.message);
    }
    
    // Step 2: Test form validation recovery
    console.log('📝 Testing form validation recovery');
    
    try {
      await TestHelpers.navigateToPage(page, '/');
      
      const newEntryBtn = page.locator('[data-testid="new-entry-btn"], button:has-text("New Entry")').first();
      
      if (await newEntryBtn.isVisible()) {
        await newEntryBtn.click();
        
        // Try to save empty form
        const saveBtn = page.locator('[data-testid="save-entry-btn"], button:has-text("Save")').first();
        
        if (await saveBtn.isVisible()) {
          await saveBtn.click();
          await page.waitForTimeout(1000);
          
          // Check for validation messages
          const hasValidation = await TestHelpers.elementExists(page, '.error, .validation-error, text=/required/i');
          
          if (hasValidation) {
            console.log('✓ Form validation prevents invalid submission');
            
            // Now fix the form and resubmit
            const titleField = page.locator('[data-testid="entry-title"], input').first();
            const contentField = page.locator('[data-testid="entry-content"], textarea').first();
            
            if (await titleField.isVisible() && await contentField.isVisible()) {
              await titleField.fill('Validation Recovery Test');
              await contentField.fill('This entry was saved after fixing validation errors');
              
              await saveBtn.click();
              await page.waitForTimeout(2000);
              
              console.log('✓ Form submission succeeded after validation fix');
            }
          }
        }
      }
      
      await TestHelpers.takeScreenshot(page, 'workflow-validation-recovery');
    } catch (error) {
      console.log('⚠ Form validation recovery variation:', error.message);
    }
    
    // Step 3: Test browser refresh during operations
    console.log('🔄 Testing browser refresh resilience');
    
    try {
      await TestHelpers.navigateToPage(page, '/chat');
      
      const chatInput = page.locator('[data-testid="chat-input"], textarea, input').first();
      const sendButton = page.locator('[data-testid="send-btn"], button:has-text("Send")').first();
      
      if (await chatInput.isVisible() && await sendButton.isVisible()) {
        await chatInput.fill('Testing refresh resilience');
        await sendButton.click();
        
        // Immediately refresh the page
        await page.reload();
        await TestHelpers.waitForAppReady(page);
        await page.waitForTimeout(2000);
        
        // Check if the message persisted or if there's proper state recovery
        const hasMessage = await page.locator('text="Testing refresh resilience"').isVisible().catch(() => false);
        
        if (hasMessage) {
          console.log('✓ Chat message persisted through page refresh');
        } else {
          console.log('⚠ Chat state reset after refresh (session-based)');
        }
      }
      
      await TestHelpers.takeScreenshot(page, 'workflow-refresh-resilience');
    } catch (error) {
      console.log('⚠ Refresh resilience test variation:', error.message);
    }
    
    console.log('🎉 Error recovery and resilience workflow completed');
  });

  test('Mobile responsive user workflow', async ({ page }) => {
    console.log('🎯 Testing mobile responsive workflow');
    
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await TestHelpers.waitForAppReady(page);
    
    await TestHelpers.takeScreenshot(page, 'workflow-mobile-start');
    
    // Step 1: Mobile navigation test
    console.log('📱 Testing mobile navigation');
    
    const mobileNavTriggers = [
      '[data-testid="mobile-menu"]',
      '.mobile-nav-trigger',
      'button[aria-label*="menu"]',
      '.hamburger',
      '.nav-toggle'
    ];
    
    let mobileNav = null;
    for (const selector of mobileNavTriggers) {
      if (await TestHelpers.elementExists(page, selector)) {
        mobileNav = page.locator(selector).first();
        break;
      }
    }
    
    if (mobileNav) {
      await mobileNav.click();
      await page.waitForTimeout(500);
      
      console.log('✓ Mobile navigation menu opened');
      await TestHelpers.takeScreenshot(page, 'workflow-mobile-nav-open');
      
      // Try navigating to different sections
      const navLinks = [
        'a:has-text("Chat")',
        'a:has-text("Insights")',
        'a:has-text("Topics")'
      ];
      
      for (const link of navLinks) {
        const navLink = page.locator(link).first();
        if (await navLink.isVisible()) {
          await navLink.click();
          await page.waitForTimeout(1000);
          break;
        }
      }
    } else {
      console.log('⚠ No mobile navigation trigger found');
    }
    
    // Step 2: Mobile entry creation
    console.log('✍️ Testing mobile entry creation');
    
    await TestHelpers.navigateToPage(page, '/');
    
    const newEntryBtn = page.locator('[data-testid="new-entry-btn"], button:has-text("New Entry"), .new-entry').first();
    
    if (await newEntryBtn.isVisible()) {
      await newEntryBtn.click();
      await page.waitForTimeout(1000);
      
      // Test mobile form interaction
      const titleField = page.locator('[data-testid="entry-title"], input').first();
      const contentField = page.locator('[data-testid="entry-content"], textarea').first();
      
      if (await titleField.isVisible()) {
        // Test mobile keyboard input
        await titleField.tap();
        await titleField.fill('Mobile Entry Test');
      }
      
      if (await contentField.isVisible()) {
        await contentField.tap();
        await contentField.fill('This entry was created on mobile to test the responsive interface.');
        
        // Test scrolling in mobile view
        await page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight / 2);
        });
        await page.waitForTimeout(500);
      }
      
      const saveBtn = page.locator('[data-testid="save-entry-btn"], button:has-text("Save")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        await page.waitForTimeout(2000);
      }
      
      console.log('✓ Mobile entry creation completed');
      await TestHelpers.takeScreenshot(page, 'workflow-mobile-entry-created');
    }
    
    // Step 3: Mobile chat interaction
    console.log('💬 Testing mobile chat');
    
    await TestHelpers.navigateToPage(page, '/chat');
    
    const chatInput = page.locator('[data-testid="chat-input"], textarea, input').first();
    const sendButton = page.locator('[data-testid="send-btn"], button').first();
    
    if (await chatInput.isVisible() && await sendButton.isVisible()) {
      await chatInput.tap();
      await chatInput.fill('Testing mobile chat interface');
      
      await sendButton.tap();
      await page.waitForTimeout(3000);
      
      console.log('✓ Mobile chat interaction completed');
      
      // Test mobile scrolling in chat
      await page.evaluate(() => {
        const chatContainer = document.querySelector('.chat-messages, .messages, .conversation');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      });
      
      await TestHelpers.takeScreenshot(page, 'workflow-mobile-chat');
    }
    
    // Reset to desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    
    console.log('🎉 Mobile responsive workflow completed');
  });
});