import { chromium } from 'playwright';

const browser = await chromium.connectOverCDP('http://localhost:9222');
const ctx = browser.contexts()[0];
const pages = ctx.pages();
const page = pages[0];

console.log('URL:', page.url());
console.log('Title:', await page.title());

// Check what inputs/fields exist
const fields = await page.evaluate(() => {
  const inputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable]'));
  return inputs.map(el => ({
    tag: el.tagName,
    type: el.type || 'n/a',
    name: el.name || '',
    placeholder: el.placeholder || '',
    ariaLabel: el.getAttribute('aria-label') || '',
    id: el.id || '',
    classes: el.className?.substring(0, 60) || '',
    contenteditable: el.getAttribute('contenteditable') || ''
  }));
});
console.log('Fields found:', JSON.stringify(fields, null, 2));

// Check for any "Gem" creation UI
const buttons = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(t => t);
});
console.log('Buttons:', buttons.join(', '));

await browser.close();
