// US7 — admin panel: overview, users, all tasks (FR-26..FR-31).
import { get, post, patch, session } from '../api.js';
import { h, clear, icon, toast, field, showFieldErrors } from '../ui.js';
import { dueLabel, initials, num, dateTime } from '../format.js';
import { go, themeButton } from '../app.js';

const LEVELS = [['Critical', 'crit'], ['High', 'high'], ['Medium', 'med'], ['Low', 'low']];

function head(title) {
  return h('header', { class: 'page-head' },
    h('div', { class: 'titles' }, h('span', { class: 'eyebrow admin' }, 'Admin'), h('h1', { class: 'h1' }, title)),
    themeButton());
}

// ---------- overview (FR-27) ----------
export async function renderAdminOverview({ root }) {
  const o = await get('/admin/overview');
  const stat = (label, value, note, cls, href) => h(href ? 'a' : 'div', { class: 'stat', href },
    h('span', { class: 'stat-label' }, label), h('span', { class: `stat-value ${cls || ''}` }, String(value)),
    h('span', { class: 'stat-note' }, note));
  const maxDay = Math.max(1, ...o.trend.map((d) => Math.max(d.created, d.completed)));
  const maxLevel = Math.max(1, ...Object.values(o.by_level));
  const created = o.trend.reduce((s, d) => s + d.created, 0);
  const completed = o.trend.reduce((s, d) => s + d.completed, 0);

  clear(root,
    head('Overview'),
    h('section', { class: 'stats', 'aria-label': 'Platform summary' },
      stat('Students', o.students.total, `${o.students.active} active · ${o.students.deactivated} deactivated`, '', '#/admin/users'),
      stat('Tasks', o.tasks.total, `${o.tasks.open} open · ${o.tasks.completed} completed`, '', '#/admin/tasks'),
      stat('Completion rate', `${o.completion_rate}%`, 'across all students'),
      stat('Critical open', o.critical_open, 'score 80 or more', 'c-crit', '#/admin/tasks?level=Critical'),
      stat('Overdue', o.overdue.tasks, `${o.overdue.students} student${o.overdue.students === 1 ? '' : 's'} affected`, 'c-crit')),
    h('div', { class: 'two-col' },
      h('section', { class: 'card wide', 'aria-labelledby': 'trend-title', style: { display: 'flex', flexDirection: 'column', gap: '14px' } },
        h('div', { class: 'toolbar' },
          h('h2', { class: 'section-title', id: 'trend-title', style: { marginRight: 'auto' } }, 'Last 14 days'),
          h('span', { class: 'legend' }, h('i', { class: 'bg-accent' }), `Created (${created})`),
          h('span', { class: 'legend' }, h('i', { class: 'bg-low' }), `Completed (${completed})`)),
        h('div', { class: 'trend', role: 'img', 'aria-label': `Tasks created and completed per day over the last 14 days: ${created} created, ${completed} completed` },
          o.trend.map((d) => h('div', { class: 'trend-day', title: `${d.date}: ${d.created} created, ${d.completed} completed` },
            h('div', { class: 'bg-accent', style: { height: `${(d.created / maxDay) * 100}%` } }),
            h('div', { class: 'bg-low', style: { height: d.completed ? `${(d.completed / maxDay) * 100}%` : '2px' } })))),
        h('div', { class: 'trend-labels', 'aria-hidden': 'true' }, o.trend.map((d) => h('span', {}, String(Number(d.date.slice(8))))))),
      h('section', { class: 'card narrow', 'aria-labelledby': 'split-title', style: { display: 'flex', flexDirection: 'column', gap: '14px' } },
        h('h2', { class: 'section-title', id: 'split-title' }, 'Open tasks by priority'),
        LEVELS.map(([level, cls]) => h('a', { class: 'bar-row', href: `#/admin/tasks?level=${level}`, style: { color: 'var(--text)', textDecoration: 'none' } },
          h('div', { class: 'bar-head', style: { fontSize: '14px' } }, h('span', {}, level), h('span', { class: 'mono', style: { fontWeight: '700' } }, String(o.by_level[level]))),
          h('div', { class: 'track thick' }, h('div', { class: `bg-${cls}`, style: { width: `${(o.by_level[level] / maxLevel) * 100}%` } })))),
        h('p', { class: 'small muted', style: { marginTop: 'auto' } },
          `Top subjects: ${o.top_subjects.map((s) => `${s.subject} ${s.count}`).join(' · ') || '—'}`))),
    h('section', { class: 'card', 'aria-labelledby': 'att-title' },
      h('h2', { class: 'section-title', id: 'att-title', style: { marginBottom: '6px' } }, 'Students who need attention'),
      o.attention.length ? o.attention.map((a) => h('div', { class: 'att-item' },
        h('span', { class: 'avatar', 'aria-hidden': 'true' }, initials(a.name)),
        h('div', { style: { flex: '1 1 200px', minWidth: '0', display: 'flex', flexDirection: 'column', gap: '2px' } },
          h('span', { style: { fontWeight: '600' } }, a.name, ' ', h('span', { class: 'small muted mono' }, `ID ${a.id}`)),
          h('span', { class: 'small muted' }, `${a.task.title} is overdue (${a.task.level}, ${a.task.score}) · ${a.open} open tasks`)),
        h('span', { class: 'badge warn' }, `${a.overdue} overdue`),
        h('a', { class: 'btn btn-sm', href: `#/admin/tasks?owner=${a.id}` }, 'View tasks')))
        : h('p', { class: 'muted', style: { padding: '12px 0', borderTop: '1px solid var(--border)' } }, 'No student has overdue tasks.')));
}

// ---------- users (FR-28..FR-30) ----------
export async function renderAdminUsers({ root }) {
  const me = session.user;
  let q = '';
  const listBox = h('section', { class: 'card flush', 'aria-label': 'Users' });
  const search = h('form', { class: 'search', role: 'search', style: { flex: '1 1 260px' } }, icon('search', 16),
    h('label', { class: 'sr-only', for: 'user-search' }, 'Search users by name, email or ID'),
    h('input', { id: 'user-search', type: 'search', name: 'q', placeholder: 'Search by name, email or ID' }));
  let timer;
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => { q = search.q.value.trim(); load(); }, 250); });
  search.addEventListener('submit', (e) => { e.preventDefault(); q = search.q.value.trim(); load(); });

  async function setActive(u, active) {
    try {
      await patch(`/admin/users/${u.id}`, { is_active: active });
      toast(`${u.name} ${active ? 'activated' : 'deactivated'}.`);
      load();
    } catch (err) { toast(err.message, 'error'); }
  }
  async function setRole(u, role) {
    try {
      await patch(`/admin/users/${u.id}`, { role });
      toast(`${u.name} is now ${role === 'admin' ? 'an admin' : 'a student'}.`);
      load();
    } catch (err) { toast(err.message, 'error'); }
  }

  function row(u) {
    const self = u.id === me.id;
    const locked = u.is_main_admin || self;
    return h('div', { class: 'ugrid' },
      h('span', { class: 'u-id mono muted', style: { fontWeight: '700' } }, `#${u.id}`),
      h('span', { class: 'u-name', style: { fontWeight: '600', minWidth: '0' } }, u.name),
      h('span', { class: 'u-email muted', style: { overflowWrap: 'anywhere', minWidth: '0' } }, u.email),
      h('span', { class: 'u-role' }, u.role === 'admin' ? 'Admin' : 'Student'),
      h('span', { class: 'u-status' }, h('span', { class: `badge ${u.is_active ? 'ok' : ''}` }, h('span', { class: 'dot' }), u.is_active ? 'Active' : 'Deactivated')),
      h('span', { class: 'u-open mono' }, String(u.open)),
      h('span', { class: 'u-done mono' }, String(u.completed)),
      h('span', { class: `u-over mono ${u.overdue ? 'c-crit' : ''}` }, String(u.overdue)),
      h('span', { class: 'u-sum small muted' }, `${u.role === 'admin' ? 'Admin' : 'Student'} · ${u.open} open · ${u.completed} done · ${u.overdue} overdue`),
      h('div', { class: 'u-act' }, locked
        ? h('span', { class: 'small muted', style: { display: 'inline-flex', alignItems: 'center', gap: '6px', height: '36px' } }, icon('lock', 14),
          u.is_main_admin ? 'Main admin, protected' : 'This is you')
        : [
          u.role === 'student' ? h('a', { class: 'btn btn-sm', href: `#/admin/tasks?owner=${u.id}` }, 'Tasks') : null,
          h('button', { class: 'btn btn-sm', type: 'button', onClick: () => setRole(u, u.role === 'admin' ? 'student' : 'admin') },
            u.role === 'admin' ? 'Make student' : 'Make admin'),
          h('button', { class: `btn btn-sm ${u.is_active ? 'btn-danger' : ''}`, type: 'button', style: u.is_active ? {} : { color: 'var(--low)' },
            onClick: () => setActive(u, !u.is_active) }, u.is_active ? 'Deactivate' : 'Activate')]));
  }

  async function load() {
    const { users } = await get(`/admin/users${q ? `?q=${encodeURIComponent(q)}` : ''}`);
    clear(listBox,
      h('div', { class: 'ugrid uhead thead', 'aria-hidden': 'true' },
        ['ID', 'Name', 'Email', 'Role', 'Status', 'Open', 'Done', 'Overdue'].map((x) => h('span', {}, x)), h('span', { style: { textAlign: 'right' } }, 'Actions')),
      users.length ? users.map(row) : h('div', { class: 'empty' }, h('h3', {}, 'No users found'), h('p', { class: 'muted' }, `Nothing matches “${q}”.`)));
  }

  function openAddUser() {
    const roleSel = h('select', { class: 'input', id: 'f-role', name: 'role' },
      h('option', { value: 'student' }, 'Student'), h('option', { value: 'admin' }, 'Admin'));
    const form = h('form', { novalidate: true, style: { display: 'flex', flexDirection: 'column', gap: '14px' } },
      field({ label: 'Full name', name: 'name', autocomplete: 'off' }),
      field({ label: 'Email', name: 'email', type: 'email', autocomplete: 'off' }),
      field({ label: 'Initial password', name: 'password', type: 'password', autocomplete: 'new-password', hint: 'At least 8 characters. Share it with the user safely.' }),
      h('div', { class: 'field' }, h('label', { class: 'label', for: 'f-role' }, 'Role'), roleSel,
        h('span', { class: 'field-error', 'data-for': 'role', hidden: true })),
      h('div', { class: 'actions', style: { justifyContent: 'flex-end' } },
        h('button', { class: 'btn', type: 'button', onClick: () => dialog.close() }, 'Cancel'),
        h('button', { class: 'btn btn-primary', type: 'submit' }, 'Create user')));
    const dialog = h('dialog', { class: 'modal', 'aria-labelledby': 'add-title' }, h('h2', { id: 'add-title' }, 'Add user'), form);
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const u = await post('/admin/users', Object.fromEntries(new FormData(form).entries()));
        dialog.close();
        toast(`${u.name} created with ID ${u.id}.`);
        load();
      } catch (err) {
        if (!showFieldErrors(form, err.fields)) toast(err.message, 'error');
      }
    });
    dialog.addEventListener('close', () => dialog.remove());
    document.body.append(dialog);
    dialog.showModal();
  }

  clear(root,
    head('Users'),
    h('div', { class: 'toolbar' }, search, h('button', { class: 'btn btn-primary', type: 'button', onClick: openAddUser }, icon('plus', 16, 2.4), 'Add user')),
    listBox,
    h('p', { class: 'small muted' }, 'Deactivated users can’t sign in, but their tasks are kept. The main admin (ID 1) can’t be demoted, deactivated or deleted.'));
  await load();
}

// ---------- all tasks (FR-31) ----------
export async function renderAdminTasks({ root, params }) {
  const state = { level: params.get('level') || '', owner: params.get('owner') || '', all: false };
  const chips = h('div', { class: 'chips', role: 'group', 'aria-label': 'Priority level' });
  const countEl = h('span', { class: 'muted push' });
  const listBox = h('section', { class: 'card flush', 'aria-label': 'All open tasks' });
  const ownerSlot = h('span');

  async function load() {
    const query = new URLSearchParams();
    if (state.level) query.set('level', state.level);
    if (state.owner) query.set('owner_id', state.owner);
    const data = await get(`/admin/tasks?${query}`);
    clear(chips, [['', 'All levels'], ...LEVELS.map(([l]) => [l, l])].map(([value, label]) =>
      h('button', { class: 'chip', type: 'button', 'aria-pressed': state.level === value ? 'true' : 'false',
        onClick: () => { state.level = value; state.all = false; load(); } }, label)));
    clear(ownerSlot, state.owner ? h('button', { class: 'chip', type: 'button', 'aria-pressed': 'true',
      onClick: () => { state.owner = ''; go(state.level ? `/admin/tasks?level=${state.level}` : '/admin/tasks'); } },
    `Student: ${data.owner_name || `#${state.owner}`} `, icon('x', 14, 2.4), h('span', { class: 'sr-only' }, 'Clear student filter')) : null);
    countEl.textContent = `${data.tasks.length} open task${data.tasks.length === 1 ? '' : 's'}`;
    const shown = state.all ? data.tasks : data.tasks.slice(0, 12);
    clear(listBox,
      h('div', { class: 'agrid ahead thead', 'aria-hidden': 'true' },
        ['Task', 'Student', 'Deadline', 'Difficulty · hours', 'Priority'].map((x) => h('span', {}, x))),
      shown.length ? shown.map((t) => {
        const due = dueLabel(t);
        return h('div', { class: 'agrid' },
          h('div', { class: 'a-task', style: { display: 'flex', flexDirection: 'column', gap: '2px', minWidth: '0' } },
            h('span', { style: { fontWeight: '600' } }, t.title), h('span', { class: 'small muted' }, t.subject)),
          h('span', { class: 'a-owner' }, t.owner_name, ' ', h('span', { class: 'small muted mono' }, `#${t.owner_id}`)),
          h('span', { class: `a-due due ${due.kind}`, title: dateTime(t.deadline) }, due.text),
          h('span', { class: 'a-diff' }, `${t.difficulty} · ${num(t.estimated_hours)} h`),
          h('span', { class: 'a-level' }, h('span', { class: `badge ${t.priority.level}` }, `${t.priority.level} · ${t.priority.score}`)));
      }) : h('div', { class: 'empty' }, h('h3', {}, 'No open tasks match'), h('p', { class: 'muted' }, 'Try another level or student.')),
      !state.all && data.tasks.length > shown.length
        ? h('button', { class: 'btn', type: 'button', style: { width: '100%', border: '0', borderRadius: '0', color: 'var(--accent)' },
          onClick: () => { state.all = true; load(); } }, `Show all ${data.tasks.length} tasks`) : null);
  }

  clear(root,
    head('All tasks'),
    h('div', { class: 'toolbar' }, chips, ownerSlot, countEl),
    listBox,
    h('p', { class: 'small muted' }, 'Open tasks across all students, in priority order (equal scores: earlier deadline first).'));
  await load();
}
