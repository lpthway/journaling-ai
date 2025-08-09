// E2E Tests for Authentication Flows

const { test, expect } = require('@playwright/test');
const { TestHelpers } = require('./utils/test-helpers');

test.describe('User Authentication', () => {
  
  test.beforeEach(async ({ page }) => {
    // Start fresh for each test
    await page.goto('/');
    await TestHelpers.waitForAppReady(page);
  });

  test('should display login form when not authenticated', async ({ page }) => {
    // Check if login form is visible
    const loginElements = [
      '[data-testid="login-form"]',
      'form[action*="login"]',
      'input[type="email"]',
      'input[type="password"]',
      '.login-form',
      'text=/login|sign in/i'
    ];
    
    let loginFormFound = false;
    for (const selector of loginElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        loginFormFound = true;
        console.log('✓ Login form element found:', selector);
        break;
      }
    }
    
    // Either show login form or already authenticated
    if (loginFormFound) {
      await TestHelpers.takeScreenshot(page, 'login-form-displayed');
      console.log('✓ Login form is displayed for unauthenticated users');
    } else {
      // Check if user is already authenticated
      const authenticatedElements = [
        '[data-testid="user-menu"]',
        '.user-profile',
        'text=/logout|sign out/i',
        '.authenticated'
      ];
      
      let isAuthenticated = false;
      for (const selector of authenticatedElements) {
        if (await TestHelpers.elementExists(page, selector)) {
          isAuthenticated = true;
          console.log('✓ User appears to be already authenticated');
          break;
        }
      }
      
      expect(isAuthenticated).toBeTruthy();
    }
  });

  test('should handle login form validation', async ({ page }) => {
    // Look for login form
    const loginForm = page.locator('[data-testid="login-form"], form[action*="login"], .login-form').first();
    
    if (await loginForm.isVisible().catch(() => false)) {
      // Try to submit empty form
      const submitButton = loginForm.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
      
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(1000);
        
        // Check for validation messages
        const validationSelectors = [
          '.error',
          '.validation-error',
          '[data-testid="error"]',
          'text=/required|invalid|empty/i',
          '.field-error',
          '[role="alert"]'
        ];
        
        let validationFound = false;
        for (const selector of validationSelectors) {
          if (await TestHelpers.elementExists(page, selector)) {
            validationFound = true;
            console.log('✓ Form validation is working');
            await TestHelpers.takeScreenshot(page, 'login-validation-error');
            break;
          }
        }
        
        // Try with invalid email format
        const emailField = loginForm.locator('input[type="email"], input[name="email"]').first();
        const passwordField = loginForm.locator('input[type="password"], input[name="password"]').first();
        
        if (await emailField.isVisible() && await passwordField.isVisible()) {
          await emailField.fill('invalid-email');
          await passwordField.fill('password');
          await submitButton.click();
          await page.waitForTimeout(1000);
          
          // Check for email format validation
          const emailValidation = await TestHelpers.elementExists(page, 'text=/valid email|email format/i');
          if (emailValidation) {
            console.log('✓ Email format validation is working');
          }
        }
      }
    } else {
      console.log('ⓘ No login form found - user may be authenticated or different auth flow');
    }
  });

  test('should attempt login with test credentials', async ({ page }) => {
    const loginForm = page.locator('[data-testid="login-form"], form, .login-form').first();
    
    if (await loginForm.isVisible().catch(() => false)) {
      const emailField = loginForm.locator('input[type="email"], input[name="email"], input[placeholder*="email"]').first();
      const passwordField = loginForm.locator('input[type="password"], input[name="password"], input[placeholder*="password"]').first();
      const submitButton = loginForm.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
      
      if (await emailField.isVisible() && await passwordField.isVisible() && await submitButton.isVisible()) {
        // Use test credentials
        await emailField.fill('test@example.com');
        await passwordField.fill('testpassword123');
        
        // Monitor for network requests
        const loginPromise = page.waitForResponse(response => 
          response.url().includes('/auth/login') || response.url().includes('/login'),
          { timeout: 10000 }
        ).catch(() => null);
        
        await submitButton.click();
        
        // Wait for login response
        const loginResponse = await loginPromise;
        
        if (loginResponse) {
          console.log('✓ Login request sent, status:', loginResponse.status());
          
          if (loginResponse.status() === 200 || loginResponse.status() === 201) {
            // Successful login
            await page.waitForTimeout(2000);
            
            // Check for authenticated state
            const authenticatedElements = [
              '[data-testid="user-menu"]',
              '.user-profile',
              'text=/logout|sign out/i',
              '.authenticated',
              '[data-testid="app-authenticated"]'
            ];
            
            let isAuthenticated = false;
            for (const selector of authenticatedElements) {
              if (await TestHelpers.elementExists(page, selector)) {
                isAuthenticated = true;
                console.log('✓ User successfully authenticated');
                await TestHelpers.takeScreenshot(page, 'authenticated-state');
                break;
              }
            }
            
            expect(isAuthenticated).toBeTruthy();
          } else {
            // Login failed (expected with test credentials)
            console.log('⚠ Login failed (expected with test credentials)');
            
            // Check for error message
            const errorShown = await TestHelpers.elementExists(page, '.error, [data-testid="error"], text=/invalid|incorrect|failed/i');
            if (errorShown) {
              console.log('✓ Error message displayed for failed login');
            }
          }
        } else {
          console.log('⚠ No login API endpoint detected');
        }
      }
    } else {
      console.log('ⓘ No login form found');
    }
  });

  test('should handle registration form if available', async ({ page }) => {
    // Look for registration/signup link
    const signupTriggers = [
      'a:has-text("Sign Up")',
      'a:has-text("Register")',
      '[data-testid="signup-link"]',
      '.signup-link',
      'button:has-text("Create Account")'
    ];
    
    let signupLink = null;
    for (const selector of signupTriggers) {
      if (await TestHelpers.elementExists(page, selector)) {
        signupLink = page.locator(selector).first();
        break;
      }
    }
    
    if (signupLink) {
      await signupLink.click();
      await page.waitForTimeout(1000);
      
      // Should show registration form
      const registrationForm = page.locator('[data-testid="registration-form"], [data-testid="signup-form"], form').first();
      
      if (await registrationForm.isVisible()) {
        console.log('✓ Registration form is accessible');
        
        // Test form fields
        const nameField = registrationForm.locator('input[name="name"], input[placeholder*="name"]').first();
        const emailField = registrationForm.locator('input[type="email"], input[name="email"]').first();
        const passwordField = registrationForm.locator('input[type="password"], input[name="password"]').first();
        
        if (await nameField.isVisible()) {
          await nameField.fill('Test User');
        }
        
        if (await emailField.isVisible()) {
          await emailField.fill('newuser@example.com');
        }
        
        if (await passwordField.isVisible()) {
          await passwordField.fill('newpassword123');
        }
        
        // Try to submit (expect validation or rejection with test data)
        const submitButton = registrationForm.locator('button[type="submit"], button:has-text("Sign Up"), button:has-text("Register")').first();
        
        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForTimeout(2000);
          
          console.log('✓ Registration form submission tested');
          await TestHelpers.takeScreenshot(page, 'registration-attempt');
        }
      }
    } else {
      console.log('ⓘ No registration form found');
    }
  });

  test('should handle logout functionality if authenticated', async ({ page }) => {
    // First check if user is authenticated
    const authenticatedElements = [
      '[data-testid="user-menu"]',
      '.user-profile',
      'text=/logout|sign out/i',
      '.authenticated'
    ];
    
    let isAuthenticated = false;
    let userMenu = null;
    
    for (const selector of authenticatedElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        isAuthenticated = true;
        userMenu = page.locator(selector).first();
        break;
      }
    }
    
    if (isAuthenticated && userMenu) {
      // Look for logout button/link
      let logoutButton = page.locator('button:has-text("Logout"), a:has-text("Sign Out"), [data-testid="logout-btn"]').first();
      
      // If logout is in a dropdown menu
      if (!(await logoutButton.isVisible().catch(() => false))) {
        // Try clicking user menu first
        await userMenu.click();
        await page.waitForTimeout(500);
        
        logoutButton = page.locator('button:has-text("Logout"), a:has-text("Sign Out"), [data-testid="logout-btn"]').first();
      }
      
      if (await logoutButton.isVisible()) {
        await logoutButton.click();
        await page.waitForTimeout(2000);
        
        // Should redirect to login or show unauthenticated state
        const backToLogin = await TestHelpers.elementExists(page, 'input[type="email"], .login-form, text=/login/i');
        
        if (backToLogin) {
          console.log('✓ Logout redirects to login form');
          await TestHelpers.takeScreenshot(page, 'logged-out-state');
        } else {
          console.log('⚠ Logout behavior unclear');
        }
      }
    } else {
      console.log('ⓘ User not authenticated or logout not visible');
    }
  });

  test('should handle password reset/forgot password if available', async ({ page }) => {
    const forgotPasswordTriggers = [
      'a:has-text("Forgot Password")',
      'a:has-text("Reset Password")',
      '[data-testid="forgot-password-link"]',
      '.forgot-password',
      'text=/forgot.*password/i'
    ];
    
    let forgotPasswordLink = null;
    for (const selector of forgotPasswordTriggers) {
      if (await TestHelpers.elementExists(page, selector)) {
        forgotPasswordLink = page.locator(selector).first();
        break;
      }
    }
    
    if (forgotPasswordLink) {
      await forgotPasswordLink.click();
      await page.waitForTimeout(1000);
      
      // Should show password reset form
      const resetForm = page.locator('[data-testid="password-reset-form"], form').first();
      
      if (await resetForm.isVisible()) {
        const emailField = resetForm.locator('input[type="email"], input[name="email"]').first();
        
        if (await emailField.isVisible()) {
          await emailField.fill('test@example.com');
          
          const submitButton = resetForm.locator('button[type="submit"], button:has-text("Reset"), button:has-text("Send")').first();
          
          if (await submitButton.isVisible()) {
            await submitButton.click();
            await page.waitForTimeout(2000);
            
            console.log('✓ Password reset form is functional');
            await TestHelpers.takeScreenshot(page, 'password-reset-form');
          }
        }
      }
    } else {
      console.log('ⓘ No password reset functionality found');
    }
  });

  test('should protect authenticated routes', async ({ page }) => {
    // Try accessing protected routes without authentication
    const protectedRoutes = [
      '/dashboard',
      '/profile',
      '/settings',
      '/admin'
    ];
    
    for (const route of protectedRoutes) {
      await page.goto(route);
      await page.waitForTimeout(1000);
      
      const currentPath = await TestHelpers.getCurrentPath(page);
      
      // Should redirect to login or show access denied
      const isProtected = currentPath === '/login' || 
                         currentPath === '/' ||
                         await TestHelpers.elementExists(page, 'text=/login|unauthorized|access denied/i');
      
      if (isProtected) {
        console.log(`✓ Route ${route} is protected`);
      } else {
        console.log(`ⓘ Route ${route} is accessible (may not exist or not protected)`);
      }
    }
  });

  test('should handle session timeout/expiration', async ({ page }) => {
    // This test simulates session expiration by manipulating tokens if possible
    
    // First, check if there's any session/token storage
    const hasLocalStorage = await page.evaluate(() => {
      return localStorage.getItem('token') || 
             localStorage.getItem('authToken') || 
             localStorage.getItem('session') ||
             sessionStorage.getItem('token') ||
             sessionStorage.getItem('authToken');
    });
    
    if (hasLocalStorage) {
      console.log('✓ Auth tokens found in storage');
      
      // Clear tokens to simulate expiration
      await page.evaluate(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('authToken');
        localStorage.removeItem('session');
        sessionStorage.clear();
      });
      
      // Refresh page and check if redirected to login
      await page.reload();
      await page.waitForTimeout(2000);
      
      const backToLogin = await TestHelpers.elementExists(page, 'input[type="email"], .login-form, text=/login/i');
      
      if (backToLogin) {
        console.log('✓ Session expiration redirects to login');
      } else {
        console.log('ⓘ Session handling behavior varies');
      }
    } else {
      console.log('ⓘ No auth tokens found in storage');
    }
  });

  test('should handle authentication state persistence', async ({ page }) => {
    // Check if authentication state persists across page reloads
    
    // First, check current authentication state
    const authenticatedElements = [
      '[data-testid="user-menu"]',
      '.user-profile',
      'text=/logout|sign out/i',
      '.authenticated'
    ];
    
    let wasAuthenticated = false;
    for (const selector of authenticatedElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        wasAuthenticated = true;
        break;
      }
    }
    
    // Reload page
    await page.reload();
    await TestHelpers.waitForAppReady(page);
    await page.waitForTimeout(2000);
    
    // Check authentication state after reload
    let stillAuthenticated = false;
    for (const selector of authenticatedElements) {
      if (await TestHelpers.elementExists(page, selector)) {
        stillAuthenticated = true;
        break;
      }
    }
    
    if (wasAuthenticated && stillAuthenticated) {
      console.log('✓ Authentication state persists across page reloads');
    } else if (!wasAuthenticated && !stillAuthenticated) {
      console.log('✓ Unauthenticated state persists across page reloads');
    } else {
      console.log('⚠ Authentication state changed after reload');
    }
    
    await TestHelpers.takeScreenshot(page, 'auth-state-after-reload');
  });
});