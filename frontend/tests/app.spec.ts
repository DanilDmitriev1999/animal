import { test, expect } from '@playwright/test';

test.describe('App Navigation and Core Features', () => {

  test('should navigate from landing to tracks page', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('Будущее обучения, персонализированное с помощью ИИ');

    await page.getByRole('button', { name: 'Начать бесплатно' }).click();

    await expect(page).toHaveURL('/tracks');
    await expect(page.locator('h1')).toContainText('Your Tracks');
  });

  test('progress bar should animate on view', async ({ page }) => {
    await page.goto('/tracks');

    const trackCard = page.locator('a[href="/tracks/intro-to-neural-networks"]');
    await expect(trackCard).toBeVisible();

    // The progress bar is a motion.div, let's find it.
    const progressBar = trackCard.locator('div.bg-primary');

    // It starts at 0% width
    await expect(progressBar).toHaveCSS('width', '0px');
    
    // Scroll into view to trigger animation
    await trackCard.scrollIntoViewIfNeeded();

    // After animation, it should have a width corresponding to 25%
    // We wait for the animation to complete. Playwright's toHaveCSS will retry.
    // The parent width is needed to calculate the percentage.
    const parentDiv = progressBar.locator('..');
    const parentWidth = (await parentDiv.boundingBox())?.width ?? 0;
    const expectedWidth = parentWidth * 0.25;

    // Use a custom expectation to check the width with a tolerance
    await expect(async () => {
      const bb = await progressBar.boundingBox();
      expect(bb?.width).toBeGreaterThan(expectedWidth * 0.9);
      expect(bb?.width).toBeLessThan(expectedWidth * 1.1);
    }).toPass({
        timeout: 2000 // Wait up to 2 seconds for animation
    });
  });

}); 