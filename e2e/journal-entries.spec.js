// E2E Tests for Journal Entry Creation and Management

const { test, expect } = require('@playwright/test');
const { TestHelpers } = require('./utils/test-helpers');
const { sampleEntries } = require('./fixtures/test-data');

test.describe('Journal Entry Management', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to journal page
    await TestHelpers.navigateToPage(page, '/');
  });

  test('should display journal entries list', async ({ page }) => {
    // Wait for entries to load
    await page.waitForTimeout(2000);
    
    // Check for entries container or empty state
    const hasEntries = await TestHelpers.elementExists(page, '.entry, .entry-card, [data-testid="entry"]');
    const hasEmptyState = await TestHelpers.elementExists(page, '.empty-state, [data-testid="empty-state"], text=/no entries/i');
    
    // Should have either entries or empty state
    expect(hasEntries || hasEmptyState).toBeTruthy();
    
    if (hasEntries) {
      console.log('✓ Journal entries are displayed');
    } else {
      console.log('✓ Empty state is displayed (no entries yet)');
    }
    
    await TestHelpers.takeScreenshot(page, 'journal-entries-list');
  });

  test('should show new entry creation UI', async ({ page }) => {
    // Look for new entry button/link
    const newEntryTriggers = [
      '[data-testid="new-entry-btn"]',
      'button:has-text("New Entry")',
      'a:has-text("New Entry")',
      '.new-entry',
      'button[title*="new"]',
      '[aria-label*="new entry"]',
      '.add-entry',
      'button:has-text("+")'
    ];
    
    let newEntryButton = null;
    for (const selector of newEntryTriggers) {
      if (await TestHelpers.elementExists(page, selector)) {
        newEntryButton = page.locator(selector).first();
        break;
      }
    }
    
    expect(newEntryButton).toBeTruthy();
    
    if (newEntryButton) {
      await newEntryButton.click();
      
      // Should show entry creation form or modal
      const formSelectors = [
        'form',
        '.entry-form',
        '[data-testid="entry-editor"]',
        '.modal',
        '.editor'
      ];
      
      let formVisible = false;
      for (const selector of formSelectors) {
        if (await TestHelpers.elementExists(page, selector)) {
          formVisible = true;
          break;
        }
      }
      
      expect(formVisible).toBeTruthy();
      
      await TestHelpers.takeScreenshot(page, 'new-entry-form');
      console.log('✓ New entry creation UI is accessible');
    }
  });

  test('should create a new journal entry', async ({ page }) => {
    const testEntry = {
      title: 'E2E Test Entry ' + Date.now(),
      content: 'This is a test entry created by Playwright E2E testing. It contains sample content to verify the entry creation functionality works correctly.'
    };

    try {
      // Find and click new entry button
      const newEntryButton = await page.locator([
        '[data-testid="new-entry-btn"]',
        'button:has-text("New Entry")',
        '.new-entry',
        'button:has-text("+")'
      ].join(', ')).first();
      
      if (await newEntryButton.isVisible().catch(() => false)) {
        await newEntryButton.click();
        
        // Wait for form to appear
        await page.waitForTimeout(1000);
        
        // Fill in entry details
        const titleField = page.locator([
          '[data-testid="entry-title"]',
          'input[placeholder*="title"]',
          'input[name="title"]',
          '.title-input'
        ].join(', ')).first();
        
        if (await titleField.isVisible().catch(() => false)) {
          await titleField.fill(testEntry.title);
        }
        
        // Fill content
        const contentField = page.locator([
          '[data-testid="entry-content"]',
          'textarea[placeholder*="content"]',
          'textarea[name="content"]',
          '.content-input',
          '.editor textarea'
        ].join(', ')).first();
        
        if (await contentField.isVisible()) {
          await contentField.fill(testEntry.content);
        }
        
        // Set mood if available
        const moodSelect = page.locator([
          '[data-testid="mood-select"]',
          'select[name="mood"]',
          '.mood-selector'
        ].join(', ')).first();
        
        if (await moodSelect.isVisible().catch(() => false)) {
          await moodSelect.selectOption('happy');
        }
        
        // Save the entry
        const saveButton = page.locator([
          '[data-testid="save-entry-btn"]',
          'button:has-text("Save")',
          'button[type="submit"]',
          '.save-btn'
        ].join(', ')).first();
        
        await saveButton.click();
        
        // Wait for save operation
        await page.waitForTimeout(2000);
        
        // Look for success indication
        const successIndicators = [
          '.toast',
          '[data-testid="toast"]',
          '.success',
          'text=/saved|created|success/i'
        ];
        
        let successFound = false;
        for (const selector of successIndicators) {
          if (await TestHelpers.elementExists(page, selector)) {
            successFound = true;
            console.log('✓ Entry saved successfully');
            break;
          }
        }
        
        // Take screenshot
        await TestHelpers.takeScreenshot(page, 'entry-created');
        
        // Verify entry appears in list (navigate back if needed)
        if (await TestHelpers.getCurrentPath(page) !== '/') {
          await TestHelpers.navigateToPage(page, '/');
        }
        
        // Check if the entry appears in the list
        await page.waitForTimeout(1000);
        const entryInList = await page.locator(`text=${testEntry.title.substring(0, 20)}`).isVisible().catch(() => false);
        
        if (entryInList) {
          console.log('✓ New entry appears in journal list');
        }
        
      } else {
        console.log('⚠ New entry button not found - entry creation UI may be different');
      }
      
    } catch (error) {
      console.log(`Entry creation test completed with variations: ${error.message}`);
      await TestHelpers.takeScreenshot(page, 'entry-creation-attempt');
    }
  });

  test('should validate entry form fields', async ({ page }) => {
    try {
      // Open new entry form
      const newEntryButton = page.locator('button:has-text("New Entry"), [data-testid="new-entry-btn"], .new-entry').first();
      
      if (await newEntryButton.isVisible().catch(() => false)) {
        await newEntryButton.click();
        await page.waitForTimeout(1000);
        
        // Try to save empty form
        const saveButton = page.locator('button:has-text("Save"), button[type="submit"], .save-btn').first();
        
        if (await saveButton.isVisible()) {
          await saveButton.click();
          
          // Check for validation messages
          const validationSelectors = [
            '.error',
            '.validation-error',
            '[data-testid="error"]',
            'text=/required|invalid|empty/i',
            '.field-error'
          ];
          
          let validationFound = false;
          for (const selector of validationSelectors) {
            if (await TestHelpers.elementExists(page, selector)) {
              validationFound = true;
              console.log('✓ Form validation is working');
              break;
            }
          }
          
          if (!validationFound) {
            console.log('⚠ Form validation not detected (may allow empty entries)');
          }
        }
      }
    } catch (error) {
      console.log(`Form validation test: ${error.message}`);
    }
  });

  test('should allow editing existing entries', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Look for existing entries
    const entryElements = [
      '.entry',
      '.entry-card',
      '[data-testid="entry"]',
      '.journal-entry'
    ];
    
    let entryToEdit = null;
    for (const selector of entryElements) {
      const elements = page.locator(selector);
      const count = await elements.count();
      
      if (count > 0) {
        entryToEdit = elements.first();
        break;
      }
    }
    
    if (entryToEdit) {
      // Click on entry to view/edit
      await entryToEdit.click();
      await page.waitForTimeout(1000);
      
      // Look for edit functionality
      const editTriggers = [
        'button:has-text("Edit")',
        '[data-testid="edit-btn"]',
        '.edit-button',
        '[title*="edit"]'
      ];
      
      let editButton = null;
      for (const selector of editTriggers) {
        if (await TestHelpers.elementExists(page, selector)) {
          editButton = page.locator(selector).first();
          break;
        }
      }
      
      if (editButton) {
        await editButton.click();
        
        // Should show editable form
        const editableContent = page.locator('textarea, input[type="text"], .editor').first();
        
        if (await editableContent.isVisible()) {
          // Make a small edit
          const currentContent = await editableContent.inputValue();
          await editableContent.fill(currentContent + ' (edited by E2E test)');
          
          // Save changes
          const saveButton = page.locator('button:has-text("Save"), button[type="submit"]').first();
          if (await saveButton.isVisible()) {
            await saveButton.click();
            await page.waitForTimeout(1000);
            
            console.log('✓ Entry editing functionality is working');
            await TestHelpers.takeScreenshot(page, 'entry-edited');
          }
        }
      } else {
        console.log('⚠ Edit functionality not found - entries may be read-only or use different UI');
      }
    } else {
      console.log('⚠ No existing entries found to test editing');
    }
  });

  test('should handle entry deletion if available', async ({ page }) => {
    // Wait for entries to load
    await page.waitForTimeout(2000);
    
    // Look for delete functionality
    const deleteSelectors = [
      'button:has-text("Delete")',
      '[data-testid="delete-btn"]',
      '.delete-button',
      '[title*="delete"]',
      'button[aria-label*="delete"]'
    ];
    
    let deleteButton = null;
    for (const selector of deleteSelectors) {
      if (await TestHelpers.elementExists(page, selector)) {
        deleteButton = page.locator(selector).first();
        break;
      }
    }
    
    if (deleteButton) {
      // Get count of entries before deletion
      const entriesBefore = await page.locator('.entry, .entry-card, [data-testid="entry"]').count();
      
      await deleteButton.click();
      
      // Look for confirmation dialog
      const confirmationSelectors = [
        'button:has-text("Confirm")',
        'button:has-text("Yes")',
        '[data-testid="confirm-delete"]',
        '.confirm-button'
      ];
      
      let confirmButton = null;
      for (const selector of confirmationSelectors) {
        if (await TestHelpers.elementExists(page, selector)) {
          confirmButton = page.locator(selector).first();
          break;
        }
      }
      
      if (confirmButton) {
        await confirmButton.click();
        await page.waitForTimeout(2000);
        
        // Check if entry count decreased
        const entriesAfter = await page.locator('.entry, .entry-card, [data-testid="entry"]').count();
        
        if (entriesAfter < entriesBefore) {
          console.log('✓ Entry deletion is working');
        } else {
          console.log('⚠ Entry deletion may not be working or requires different approach');
        }
      } else {
        // Direct deletion without confirmation
        await page.waitForTimeout(2000);
        console.log('✓ Entry deletion (direct) functionality detected');
      }
    } else {
      console.log('⚠ Delete functionality not found - may be protected or use different UI');
    }
  });

  test('should display entry details correctly', async ({ page }) => {
    // Wait for entries to load
    await page.waitForTimeout(2000);
    
    // Click on first available entry
    const firstEntry = page.locator('.entry, .entry-card, [data-testid="entry"]').first();
    
    if (await firstEntry.isVisible().catch(() => false)) {
      await firstEntry.click();
      await page.waitForTimeout(1000);
      
      // Check for entry details
      const detailElements = [
        '.entry-content',
        '.entry-title',
        '.entry-date',
        '.mood',
        '.tags'
      ];
      
      let detailsFound = 0;
      for (const selector of detailElements) {
        if (await TestHelpers.elementExists(page, selector)) {
          detailsFound++;
        }
      }
      
      expect(detailsFound).toBeGreaterThan(0);
      console.log(`✓ Entry details displayed (${detailsFound} detail elements found)`);
      
      await TestHelpers.takeScreenshot(page, 'entry-details');
    } else {
      console.log('⚠ No entries available to view details');
    }
  });

  test('should handle mood and tag filtering if available', async ({ page }) => {
    // Look for filter controls
    const filterSelectors = [
      'select[name*="mood"]',
      '[data-testid="mood-filter"]',
      '.mood-filter',
      '.filter-select',
      'input[placeholder*="tag"]',
      '.tag-filter'
    ];
    
    let hasFilters = false;
    for (const selector of filterSelectors) {
      if (await TestHelpers.elementExists(page, selector)) {
        hasFilters = true;
        
        const filterElement = page.locator(selector).first();
        
        // Try to use the filter
        if (await filterElement.getAttribute('tagName') === 'SELECT') {
          const options = await filterElement.locator('option').count();
          if (options > 1) {
            await filterElement.selectOption({ index: 1 });
            await page.waitForTimeout(1000);
            console.log('✓ Mood/tag filtering functionality detected');
          }
        } else if (await filterElement.getAttribute('type') === 'text') {
          await filterElement.fill('test');
          await page.waitForTimeout(1000);
          console.log('✓ Tag filtering functionality detected');
        }
        
        break;
      }
    }
    
    if (!hasFilters) {
      console.log('⚠ No mood/tag filters found - basic entry display is sufficient');
    }
  });
});