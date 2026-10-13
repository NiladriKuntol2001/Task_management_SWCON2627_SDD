// End-to-end run-through with a real browser (task T038).
// Needs a server started with sample data:  python run.py --reset --seed --port 8765
// Then:  cd e2e && npm install && node e2e.mjs http://127.0.0.1:8765
// Saves screenshots to e2e/screenshots/ and exits non-zero if any check fails.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = join(dirname(fileURLToPath(import.meta.url)), 'screenshots');
mkdirSync(OUT, { recursive: true });

const results = [];
const check = (name, ok, detail = '') => {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`);
};

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

async function newPage(width, height, theme) {
  const context = await browser.newContext({ viewport: { width, height }, colorScheme: theme });
  const page = await context.newPage();
  page.errors = [];
  page.on('pageerror', (e) => page.errors.push(e.message));
  page.on('console', (m) => {
    if (m.type() === 'error' && !/fonts\.(googleapis|gstatic)|ERR_|Failed to load resource/.test(m.text())) page.errors.push(m.text());
  });
  return page;
}

async function login(page, email, password) {
  await page.goto(`${BASE}/#/login`);
  await page.fill('#f-email', email);
  await page.fill('#f-password', password);
  await page.click('button[type=submit]');
  await page.waitForSelector('main#main h1');
}

async function noHorizontalScroll(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
}

const shot = (page, name) => page.screenshot({ path: join(OUT, `${name}.png`), fullPage: true });

// ---------------------------------------------------------------- admin (runs first: needs untouched sample data)
for (const [width, height, theme, tag] of [[1280, 1000, 'dark', 'dark-1280'], [390, 844, 'light', 'light-390']]) {
  const page = await newPage(width, height, theme);
  await login(page, 'admin123@gmail.com', 'admin@123');
  check(`FR-26 admin lands on the admin overview (${tag})`, page.url().includes('#/admin'));
  await page.waitForSelector('.trend');
  if (tag === 'dark-1280') {
    const stats = await page.$$eval('.stat .stat-value', (els) => els.map((e) => e.textContent));
    check('FR-27 overview: 6 students, 39 tasks, 23%, 4 critical, 3 overdue',
      JSON.stringify(stats) === JSON.stringify(['6', '39', '23%', '4', '3']), stats.join(','));
    check('FR-27 attention list starts with Mikael', (await page.textContent('.att-item')).includes('Mikael Lindqvist'));
  }
  await shot(page, `07-admin-overview-${tag}`);
  check(`FR-34 admin overview has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  await page.goto(`${BASE}/#/admin/users`);
  await page.waitForSelector('.ugrid:not(.uhead)');
  if (tag === 'dark-1280') {
    await page.fill('#user-search', 'aino');
    await page.waitForFunction(() => document.querySelectorAll('.ugrid:not(.uhead)').length === 1);
    await page.click('button:text-is("Deactivate")');
    await page.waitForSelector('button:text-is("Activate")');
    check('FR-30 admin deactivates a student', (await page.textContent('.ugrid:not(.uhead) .u-status')).includes('Deactivated'));
    await page.click('button:text-is("Activate")');
    await page.waitForSelector('button:text-is("Deactivate")');
    check('FR-30 admin reactivates the student', (await page.textContent('.ugrid:not(.uhead) .u-status')).includes('Active'));
    await page.fill('#user-search', '1');
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll('.ugrid:not(.uhead)');
      return rows.length === 1 && rows[0].querySelector('.u-id').textContent === '#1';
    });
    check('FR-26 main admin row is protected', (await page.textContent('.ugrid:not(.uhead)')).includes('Main admin, protected'));
    await page.fill('#user-search', '');
    await page.waitForFunction(() => document.querySelectorAll('.ugrid:not(.uhead)').length >= 7);
  }
  await shot(page, `08-admin-users-${tag}`);
  check(`FR-34 admin users has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  await page.goto(`${BASE}/#/admin/tasks?owner=6`);
  await page.waitForSelector('.agrid:not(.ahead)');
  if (tag === 'dark-1280') {
    const rows = await page.$$eval('.agrid:not(.ahead) .a-owner', (els) => els.map((e) => e.textContent));
    check('FR-31 all tasks filtered by student', rows.length === 3 && rows.every((r) => r.startsWith('Mikael')), rows.join(' | '));
  }
  await shot(page, `09-admin-tasks-${tag}`);
  check(`no JavaScript errors (admin ${tag})`, page.errors.length === 0, page.errors.join(' | '));
  await page.context().close();
}

// ---------------------------------------------------------------- student journey
{
  const page = await newPage(1280, 900, 'light');
  await page.goto(BASE);
  await page.waitForSelector('.auth');
  check('US1 unauthenticated visitor lands on sign-in', page.url().includes('#/login'));
  await shot(page, '01-login-light-1280');

  // register a new student (FR-01)
  const email = `e2e${Date.now()}@test.fi`;
  await page.click('a[href="#/register"]');
  await page.fill('#f-name', 'Eeva Tester');
  await page.fill('#f-email', email);
  await page.fill('#f-password', 'short');
  await page.click('button[type=submit]');
  await page.waitForSelector('.field-error:not([hidden])');
  check('FR-01 short password rejected with message',
    (await page.textContent('[data-for="password"]')).includes('at least 8 characters'));
  await page.fill('#f-password', 'Password123');
  await page.click('button[type=submit]');
  await page.waitForSelector('main#main h1');
  check('FR-01 registration signs in and opens dashboard', page.url().includes('#/dashboard'));
  check('FR-20 empty state when there are no tasks', (await page.textContent('main')).includes('Nothing left to do'));

  // add a task with live preview (FR-04, FR-35)
  await page.click('a[href="#/tasks/new"]');
  await page.waitForSelector('form.form-card');
  await page.click('button[type=submit]');
  await page.waitForSelector('[data-for="title"]:not([hidden])');
  check('FR-10 empty title shows "Title can\'t be empty."', (await page.textContent('[data-for="title"]')).includes("Title can't be empty."));
  await page.fill('#title', 'Security lab: STRIDE threat model');
  await page.fill('#subject', 'Software Security');
  const deadline = await page.evaluate(() => {
    const d = new Date(Date.now() + 14.5 * 3600e3);
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
  });
  await page.fill('#deadline', deadline);
  await page.click('.diff-opt[data-value="Hard"]');
  await page.fill('#estimated_hours', '8');
  await page.waitForFunction(() => document.querySelector('.big-score .mono').textContent === '90');
  check('FR-35 live preview shows 90 Critical', (await page.textContent('.big-score')).includes('Critical'));
  await shot(page, '04-task-form-light-1280');
  await page.click('button[type=submit]');
  await page.waitForURL(/#\/tasks\/\d+$/);
  check('FR-04 task saved and details shown (FR-09)', (await page.textContent('h1')).includes('STRIDE'));
  check('FR-09 breakdown shows deadline part 50.0', (await page.textContent('.breakdown')).includes('50.0'));
  await shot(page, '05-task-detail-light-1280');

  // complete it (FR-08)
  await page.click('text=Mark complete');
  await page.waitForSelector('.badge.ok');
  check('FR-08 task marked complete', (await page.textContent('.tags')).includes('Completed'));
  await page.goto(`${BASE}/#/completed`);
  await page.waitForSelector('.tgrid.is-done');
  check('FR-15 completed view lists the task', (await page.textContent('main')).includes('STRIDE'));

  // theme switch is instant and remembered (FR-33)
  const before = await page.getAttribute('html', 'data-theme');
  await page.click('[data-theme-toggle]');
  const after = await page.getAttribute('html', 'data-theme');
  await page.reload();
  await page.waitForSelector('main#main h1');
  check('FR-33 theme toggles and persists after reload',
    before !== after && (await page.getAttribute('html', 'data-theme')) === after, `${before} -> ${after}`);

  // sign out revokes (FR-03)
  await page.click('.userbox button[aria-label="Log out"]');
  await page.waitForSelector('.auth');
  check('FR-03 sign out returns to sign-in', page.url().includes('#/login'));
  check('no JavaScript errors (new student journey)', page.errors.length === 0, page.errors.join(' | '));
  await page.context().close();
}

// ---------------------------------------------------------------- sample student, all widths
for (const [width, height, theme, tag] of [[1280, 900, 'light', 'light-1280'], [1280, 900, 'dark', 'dark-1280'],
  [768, 1024, 'dark', 'dark-768'], [390, 844, 'light', 'light-390'], [390, 844, 'dark', 'dark-390']]) {
  const page = await newPage(width, height, theme);
  const t0 = Date.now();
  await login(page, 'niladri@student.test', 'Student@123');
  await page.waitForSelector('.rec');
  const loadMs = Date.now() - t0;
  const text = await page.textContent('main');
  if (tag === 'light-1280') {
    check('NFR-02 dashboard ready in under 2 s', loadMs < 2000, `${loadMs} ms incl. sign-in`);
    const stats = await page.$$eval('.stat .stat-value', (els) => els.map((e) => e.textContent));
    check('US5 sample dashboard counts 13 / 4 / 6 / 1', JSON.stringify(stats) === JSON.stringify(['13', '4', '6', '1']), stats.join(','));
    check('FR-20 recommends STRIDE threat model (90)', text.includes('Security lab: STRIDE threat model') && (await page.textContent('.ring-value')) === '90');
  }
  await shot(page, `02-dashboard-${tag}`);
  check(`FR-34 dashboard has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  if (width <= 600) {
    const pos = await page.$eval('.links', (el) => getComputedStyle(el).position);
    check(`FR-34 navigation is a bottom bar at ${width}px`, pos === 'fixed');
  }
  await page.goto(`${BASE}/#/tasks`);
  await page.waitForSelector('.tgrid:not(.thead)');
  if (tag === 'light-1280') {
    const first = await page.$$eval('.tgrid:not(.thead) .t-title', (els) => els.slice(0, 3).map((e) => e.textContent));
    check('FR-14/16 list sorted by priority', first[0] === 'Security lab: STRIDE threat model' && first[1] === 'Algorithms problem set 4', first.join(' | '));
    await page.click('.chip:has-text("Thesis")');
    await page.waitForFunction(() => [...document.querySelectorAll('.tgrid:not(.thead) .t-sub')].every((e) => e.textContent.startsWith('Thesis')));
    const thesis = await page.$$eval('.tgrid:not(.thead) .t-title', (els) => els.map((e) => e.textContent));
    check('FR-15 subject filter', thesis.length === 2, thesis.join(' | '));
    await page.click('.chip:has-text("All subjects")');
    await page.click('button:has-text("Sort:")');
    await page.waitForFunction(() => document.querySelector('button.push').textContent.includes('Deadline'));
    const byDeadline = await page.$$eval('.tgrid:not(.thead) .t-title', (els) => els[0].textContent);
    check('FR-16 sort by deadline puts the overdue task first', byDeadline === 'Scalability quiz reflection', byDeadline);
  }
  await shot(page, `03-tasks-${tag}`);
  check(`FR-34 task list has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  await page.goto(`${BASE}/#/upcoming`);
  await page.waitForSelector('section[aria-label="Tasks"] .tgrid:not(.thead), section[aria-label="Tasks"] .empty');
  if (tag === 'light-1280') {
    const up = await page.$$eval('.tgrid:not(.thead)', (els) => els.length);
    check('FR-17 upcoming shows 7 tasks for the next 7 days', up === 7, String(up));
  }
  await page.goto(`${BASE}/#/profile`);
  await page.waitForSelector('#pw-rules');
  if (tag === 'light-1280') {
    check('FR-22 profile shows ID 2 and 17 tasks', (await page.textContent('main')).includes('ID 2') && (await page.textContent('.facts')).includes('17'));
    const pwForm = page.locator('form[aria-labelledby="pw-title"]');
    await pwForm.locator('[name=current_password]').fill('Student@123');
    await pwForm.locator('[name=new_password]').fill('Student@123');
    const ruleClass = await page.$eval('#pw-rules li:nth-child(2)', (el) => el.className);
    check('FR-24 live rule flags "same as current password"', ruleClass === 'bad', ruleClass);
  }
  await shot(page, `06-profile-${tag}`);
  check(`FR-34 profile has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  await page.goto(`${BASE}/#/tasks/new`);
  await page.waitForSelector('form.form-card');
  await shot(page, `04-task-form-${tag}`);
  check(`FR-34 task form has no horizontal scroll at ${width}px`, await noHorizontalScroll(page));
  check(`no JavaScript errors (${tag})`, page.errors.length === 0, page.errors.join(' | '));
  await page.context().close();
}

// ---------------------------------------------------------------- isolation through the UI
{
  const page = await newPage(1280, 900, 'light');
  await login(page, 'zahra@student.test', 'Student@123');
  await page.goto(`${BASE}/#/tasks/1`);   // task 1 belongs to Niladri
  await page.waitForSelector('main h1');
  check('FR-21 another student\'s task shows "Task not found"', (await page.textContent('main h1')) === 'Task not found');
  await page.goto(`${BASE}/#/admin`);
  await page.waitForSelector('main h1');
  check('FR-32 student is kept out of the admin panel', page.url().includes('#/dashboard'));
  await page.context().close();
}

{
  const page = await newPage(390, 844, 'dark');
  await page.goto(`${BASE}/#/login`);
  await page.waitForSelector('.auth');
  await shot(page, '01-login-dark-390');
  check('FR-34 sign-in has no horizontal scroll at 390px', await noHorizontalScroll(page));
  await page.context().close();
}

await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed. Screenshots: ${OUT}`);
process.exit(failed.length ? 1 : 0);
