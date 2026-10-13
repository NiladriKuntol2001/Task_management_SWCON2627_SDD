// Boot, hash router and the layout shell (sidebar / top bar / bottom bar).
import { session, setUnauthorizedHandler, post } from './api.js';
import { h, clear, icon, toast } from './ui.js';
import { initials } from './format.js';
import { renderLogin } from './views/login.js';
import { renderDashboard } from './views/dashboard.js';
import { renderTasks } from './views/tasks.js';
import { renderTaskForm } from './views/task-form.js';
import { renderTaskDetail } from './views/task-detail.js';
import { renderProfile } from './views/profile.js';
import { renderAdminOverview, renderAdminUsers, renderAdminTasks } from './views/admin.js';

const root = document.getElementById('app');
export const shellState = { counts: null };

// ---------- theme (FR-33) ----------
export function currentTheme() { return document.documentElement.getAttribute('data-theme') || 'light'; }
export function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('studyflow.theme', next); } catch (e) { /* ignore */ }
  document.querySelectorAll('[data-theme-toggle]').forEach(updateThemeButton);
}
function updateThemeButton(btn) {
  const dark = currentTheme() === 'dark';
  btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
  btn.setAttribute('title', dark ? 'Light mode' : 'Dark mode');
  btn.replaceChildren(icon(dark ? 'sun' : 'moon'));
}
export function themeButton() {
  const btn = h('button', { class: 'icon-btn', type: 'button', 'data-theme-toggle': '', onClick: toggleTheme });
  updateThemeButton(btn);
  return btn;
}

// ---------- routing ----------
const routes = [
  { re: /^\/login$/, view: renderLogin, public: true },
  { re: /^\/register$/, view: (ctx) => renderLogin({ ...ctx, mode: 'register' }), public: true },
  { re: /^\/dashboard$/, view: renderDashboard, nav: 'dashboard' },
  { re: /^\/tasks$/, view: (ctx) => renderTasks({ ...ctx, preset: 'all' }), nav: 'tasks' },
  { re: /^\/upcoming$/, view: (ctx) => renderTasks({ ...ctx, preset: 'upcoming' }), nav: 'upcoming' },
  { re: /^\/overdue$/, view: (ctx) => renderTasks({ ...ctx, preset: 'overdue' }), nav: 'overdue' },
  { re: /^\/completed$/, view: (ctx) => renderTasks({ ...ctx, preset: 'completed' }), nav: 'completed' },
  { re: /^\/tasks\/new$/, view: renderTaskForm, nav: 'tasks' },
  { re: /^\/tasks\/(\d+)\/edit$/, view: (ctx) => renderTaskForm({ ...ctx, id: Number(ctx.match[1]) }), nav: 'tasks' },
  { re: /^\/tasks\/(\d+)$/, view: (ctx) => renderTaskDetail({ ...ctx, id: Number(ctx.match[1]) }), nav: 'tasks' },
  { re: /^\/profile$/, view: renderProfile, nav: 'profile' },
  { re: /^\/admin$/, view: renderAdminOverview, nav: 'admin', admin: true },
  { re: /^\/admin\/users$/, view: renderAdminUsers, nav: 'admin-users', admin: true },
  { re: /^\/admin\/tasks$/, view: renderAdminTasks, nav: 'admin-tasks', admin: true },
];

export function go(path) {
  if (location.hash === `#${path}`) route();
  else location.hash = `#${path}`;
}

function homeFor(user) { return user && user.role === 'admin' ? '/admin' : '/dashboard'; }

function parseHash() {
  const raw = location.hash.replace(/^#/, '') || '/';
  const [path, query = ''] = raw.split('?');
  return { path, params: new URLSearchParams(query) };
}

async function route() {
  const { path, params } = parseHash();
  const user = session.user;
  if (path === '/' || path === '') return go(user ? homeFor(user) : '/login');
  const match = routes.map((r) => ({ r, m: path.match(r.re) })).find((x) => x.m);
  if (!match) return go(user ? homeFor(user) : '/login');
  const { r, m } = match;
  if (!r.public && !user) return go('/login');
  if (r.public && user) return go(homeFor(user));
  if (r.admin && user.role !== 'admin') return go('/dashboard');

  window.scrollTo(0, 0);
  if (r.public) {
    clear(root);
    return r.view({ root, params });
  }
  const main = h('main', { class: 'main', id: 'main' });
  clear(root, h('div', { class: 'app' }, sidebar(user, r.nav), main));
  try {
    await r.view({ root: main, params, match: m, user });
    const heading = main.querySelector('h1');
    if (heading) document.title = `${heading.textContent} · StudyFlow`;
  } catch (err) {
    if (err.status === 401) return;
    clear(main, h('div', { class: 'card empty' }, h('h3', {}, 'Something went wrong'),
      h('p', { class: 'muted' }, err.message || 'Please try again.'),
      h('button', { class: 'btn', type: 'button', onClick: route }, 'Try again')));
  }
}

// ---------- shell ----------
function navLink(key, current, href, iconName, label, extra = {}) {
  return h('a', { class: `lnk${extra.extra ? ' extra' : ''}`, href: `#${href}`,
    'aria-current': key === current ? 'page' : null },
  icon(iconName), label,
  'count' in extra ? h('span', { class: `cnt${extra.alert ? ' alert' : ''}`, 'data-count': key }, extra.count == null ? '' : String(extra.count)) : null);
}

function sidebar(user, current) {
  const admin = user.role === 'admin';
  const c = shellState.counts;
  const links = admin ? [
    navLink('admin', current, '/admin', 'dashboard', 'Overview'),
    navLink('admin-users', current, '/admin/users', 'users', 'Users'),
    navLink('admin-tasks', current, '/admin/tasks', 'tasks', 'All tasks'),
    navLink('profile', current, '/profile', 'user', 'Profile'),
  ] : [
    navLink('dashboard', current, '/dashboard', 'dashboard', 'Dashboard'),
    navLink('tasks', current, '/tasks', 'tasks', 'Tasks', { count: c ? c.active : null }),
    navLink('upcoming', current, '/upcoming', 'calendar', 'Upcoming'),
    navLink('overdue', current, '/overdue', 'clock', 'Overdue', { extra: true, count: c ? c.overdue : null, alert: true }),
    navLink('completed', current, '/completed', 'check', 'Completed', { extra: true }),
    navLink('profile', current, '/profile', 'user', 'Profile'),
  ];
  return h('nav', { class: 'side', 'aria-label': admin ? 'Admin' : 'Main' },
    h('a', { class: 'brand', href: `#${homeFor(user)}` },
      h('span', { class: 'brand-mark', 'aria-hidden': 'true' }, 'S'),
      h('span', {}, h('span', { class: 'brand-name' }, 'StudyFlow'),
        h('span', { class: `brand-sub${admin ? ' admin' : ''}` }, admin ? 'Admin panel' : 'Smart task manager'))),
    h('div', { class: 'links' }, links),
    h('div', { class: 'userbox' },
      h('span', { class: `avatar${admin ? ' admin' : ''}`, 'aria-hidden': 'true' }, initials(user.name)),
      h('span', { class: 'userbox-text' },
        h('span', { class: 'userbox-name' }, user.name),
        h('span', { class: 'small muted' }, `${admin ? 'Admin' : 'Student'} · ID ${user.id}`)),
      h('button', { class: 'icon-btn plain', type: 'button', 'aria-label': 'Log out', title: 'Log out', onClick: logout }, icon('logout'))));
}

/** Refresh the task counters in the navigation after a change. */
export function setCounts(counts) {
  shellState.counts = counts;
  for (const [key, value] of [['tasks', counts.active], ['overdue', counts.overdue]]) {
    const el = document.querySelector(`[data-count="${key}"]`);
    if (el) el.textContent = String(value);
  }
}

export async function logout() {
  try { await post('/auth/logout'); } catch (e) { /* token may already be invalid */ }
  session.clear();
  shellState.counts = null;
  toast('You have signed out.');
  go('/login');
}

setUnauthorizedHandler((err) => {
  session.clear();
  shellState.counts = null;
  toast(err.message || 'Please sign in again.', 'error');
  go('/login');
});

window.addEventListener('hashchange', route);
route();
