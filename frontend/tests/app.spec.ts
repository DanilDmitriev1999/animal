import { test, expect } from '@playwright/test';

test.describe('Навигация и базовые сценарии', () => {

  test('из лендинга к списку треков и в мастер создания', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('Будущее обучения');

    await page.getByRole('button', { name: 'Начать бесплатно' }).click();

    await expect(page).toHaveURL('/tracks');
    await expect(page.locator('h1')).toContainText('Ваши треки');

    await page.getByRole('button', { name: 'Создать трек' }).click();
    await expect(page).toHaveURL(/\/tracks\/create$/);
    await expect(page.getByText('Создание трека — шаг 1/2')).toBeVisible();
  });

  test('переход в трек из списка (пустое состояние — пока пропускаем)', async ({ page }) => {
    await page.goto('/tracks');
    await expect(page.locator('h1')).toContainText('Ваши треки');
  });

});