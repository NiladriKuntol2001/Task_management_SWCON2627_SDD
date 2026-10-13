// US5 — dashboard and "What should I work on today?" (FR-19, FR-20).
import { get, patch } from '../api.js';
import { h, clear, icon, ring, toast } from '../ui.js';
import { dateTime, dayParts, timeOnly, greeting, todayLabel, num, dueLabel } from '../format.js';
import { go, themeButton, setCounts } from '../app.js';

const LEVELS = [['Critical', 'crit', 'Critical · 80+'], ['High', 'high', 'High · 60–79'],
  ['Medium', 'med', 'Medium · 40–59'], ['Low', 'low', 'Low · 0–39']];

function header(user) {
  const search = h('form', { class: 'search', role: 'search' },
    icon('search', 16),
    h('label', { class: 'sr-only', for: 'dash-search' }, 'Search tasks'),
    h('input', { id: 'dash-search', type: 'search', placeholder: 'Search tasks', name: 'q' }));
  search.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = search.q.value.trim();
    go(q ? `/tasks?q=${encodeURIComponent(q)}` : '/tasks');
  });
  return h('header', { class: 'page-head' },
    h('div', { class: 'titles' },
      h('span', { class: 'muted' }, todayLabel()),
      h('h1', { class: 'h1' }, `${greeting()}, ${user.name.split(' ')[0]}`)),
    search,
    themeButton(),
    h('a', { class: 'btn btn-primary', href: '#/tasks/new' }, icon('plus', 16, 2.4), 'New task'));
}

function recommendation(task, reload) {
  if (!task) {
    return h('section', { class: 'card lg empty', 'aria-label': 'Recommendation' },
      h('span', { class: 'eyebrow' }, 'What should I work on today?'),
      h('h3', {}, 'Nothing left to do'),
      h('p', { class: 'muted' }, 'You have no incomplete tasks. Add one to get a recommendation.'),
      h('a', { class: 'btn btn-primary', href: '#/tasks/new' }, icon('plus', 16, 2.4), 'Add a task'));
  }
  const p = task.priority;
  const bar = (label, part, raw) => h('div', { class: 'bar-row' },
    h('div', { class: 'bar-head' }, h('span', {}, label), h('span', { class: 'mono' }, part.toFixed(1))),
    h('div', { class: 'track' }, h('div', { style: { width: `${raw}%` } })));
  const due = dueLabel(task);
  return h('section', { class: 'card lg rec', 'aria-labelledby': 'rec-title' },
    h('div', { class: 'rec-main' },
      h('span', { class: 'eyebrow' }, 'What should I work on today?'),
      h('h2', { class: 'rec-title', id: 'rec-title' }, h('a', { href: `#/tasks/${task.id}` }, task.title)),
      h('div', { class: 'tags' },
        h('span', { class: `badge ${p.level}` }, h('span', { class: 'dot' }), p.level),
        h('span', { class: 'pill' }, task.subject),
        h('span', { class: 'pill' }, `${due.kind === 'over' ? 'Was due' : 'Due'} ${dateTime(task.deadline)}`),
        h('span', { class: 'pill' }, `${task.difficulty} · ${num(task.estimated_hours)} h`)),
      h('div', { class: 'actions' },
        h('a', { class: 'btn btn-primary', href: `#/tasks/${task.id}` }, 'Open task'),
        h('button', { class: 'btn', type: 'button', onClick: async () => {
          try {
            await patch(`/tasks/${task.id}/complete`, { completed: true });
            toast(`“${task.title}” marked complete.`);
            reload();
          } catch (err) { toast(err.message, 'error'); }
        } }, 'Mark complete'))),
    h('div', { class: 'rec-why' },
      ring(p.score, p.level),
      h('div', { class: 'bars' },
        h('span', { class: 'small muted' }, 'Why this task'),
        bar('Deadline · 50%', p.deadline_part, p.deadline_score),
        bar('Difficulty · 30%', p.difficulty_part, p.difficulty_score),
        bar('Time · 20%', p.time_part, p.time_score))));
}

function stats(c) {
  const stat = (label, value, note, cls, href) => h('a', { class: 'stat', href },
    h('span', { class: 'stat-label' }, label),
    h('span', { class: `stat-value ${cls || ''}` }, String(value)),
    h('span', { class: 'stat-note' }, note));
  return h('section', { class: 'stats', 'aria-label': 'Summary' },
    stat('Incomplete', c.incomplete, `${c.due_this_week} due this week`, '', '#/tasks'),
    stat('Completed', c.completed, `${c.completion_percent}% of all tasks`, '', '#/completed'),
    stat('High priority', c.high_priority, `${c.critical} critical, ${c.high_priority - c.critical} high`, 'c-high', '#/tasks'),
    stat('Overdue', c.overdue, c.overdue ? 'Needs attention' : 'All on track', 'c-crit', '#/overdue'));
}

function upcomingList(items) {
  const body = items.length ? items.map((t) => {
    const d = dayParts(t.deadline);
    return h('a', { class: 'up-item', href: `#/tasks/${t.id}` },
      h('span', { class: 'datebox' }, h('span', { class: 'dow' }, d.dow), h('span', { class: 'day' }, d.day)),
      h('span', { class: 'up-text' },
        h('span', { class: 'up-title' }, t.title),
        h('span', { class: 'small muted' }, `${t.subject} · ${timeOnly(t.deadline)} · ${t.difficulty} · ${num(t.estimated_hours)} h`)),
      h('span', { class: `badge ${t.priority.level}` }, `${t.priority.level} · ${t.priority.score}`));
  }) : [h('p', { class: 'muted', style: { padding: '12px 2px', borderTop: '1px solid var(--border)' } },
    'Nothing due in the next 7 days.')];
  return h('section', { class: 'card wide', 'aria-labelledby': 'up-title' },
    h('div', { class: 'list-head' },
      h('h2', { class: 'section-title', id: 'up-title' }, 'Upcoming deadlines'),
      h('a', { href: '#/upcoming' }, 'View all')),
    body);
}

function mix(m, overdue) {
  const total = m.Critical + m.High + m.Medium + m.Low;
  const label = `Incomplete tasks: ${m.Critical} critical, ${m.High} high, ${m.Medium} medium, ${m.Low} low`;
  return h('section', { class: 'card narrow', 'aria-labelledby': 'mix-title', style: { display: 'flex', flexDirection: 'column', gap: '16px' } },
    h('h2', { class: 'section-title', id: 'mix-title' }, 'Priority mix'),
    h('div', { class: 'mixbar', role: 'img', 'aria-label': label },
      total ? LEVELS.filter(([k]) => m[k]).map(([k, cls]) => h('div', { class: `bg-${cls}`, style: { flex: String(m[k]) } })) : null),
    h('div', { class: 'mix-grid' }, LEVELS.map(([k, cls, text]) =>
      h('div', { class: `mix-cell bg-${cls}Soft` }, h('span', { class: `mono c-${cls}` }, String(m[k])), h('span', {}, text)))),
    overdue.length ? h('a', { class: 'notice', href: `#/tasks/${overdue[0].id}` },
      h('span', { class: 'c-crit' }, icon('alert')),
      h('span', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } },
        h('span', { style: { fontWeight: '600', fontSize: '14px' } },
          overdue.length === 1 ? `${overdue[0].title} is overdue` : `${overdue.length} tasks are overdue`),
        h('span', { class: 'small muted' }, `Was due ${dateTime(overdue[0].deadline)} · score ${overdue[0].priority.score}`))) : null);
}

export async function renderDashboard({ root, user }) {
  const load = async () => {
    const data = await get('/dashboard');
    setCounts({ active: data.counts.incomplete, overdue: data.counts.overdue });
    clear(root,
      header(user),
      recommendation(data.recommendation, load),
      stats(data.counts),
      h('div', { class: 'two-col' }, upcomingList(data.upcoming), mix(data.mix, data.overdue)));
  };
  await load();
}
