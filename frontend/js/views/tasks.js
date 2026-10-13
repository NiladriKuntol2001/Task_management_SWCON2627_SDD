// US4 — task list with filters, search and sort; Upcoming / Overdue / Completed views
// (FR-07, FR-08, FR-15..FR-18).
import { get, patch, del } from '../api.js';
import { h, clear, icon, levelBadge, toast, confirmDialog } from '../ui.js';
import { dateTime, dueLabel, num } from '../format.js';
import { themeButton, setCounts } from '../app.js';

const PRESETS = {
  all: { title: 'All tasks', query: {} },
  upcoming: { title: 'Upcoming', query: { view: 'upcoming' }, note: 'Incomplete tasks due in the next 7 days, earliest first.' },
  overdue: { title: 'Overdue', query: { view: 'overdue' }, note: 'Incomplete tasks whose deadline has passed.' },
  completed: { title: 'Completed', query: { status: 'completed' } },
};

export async function renderTasks({ root, preset, params }) {
  const conf = PRESETS[preset];
  const state = { status: 'active', subject: '', q: params.get('q') || '', sort: 'priority' };
  const isList = preset === 'all';

  const countLabel = h('span', { class: 'muted' });
  const listBox = h('section', { class: 'card flush', 'aria-label': 'Tasks' });
  const statusSeg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Status' });
  const chips = h('div', { class: 'chips scroll', role: 'group', 'aria-label': 'Subject', style: { flex: '1 1 100%' } });
  const sortBtn = h('button', { class: 'btn push', type: 'button', onClick: () => {
    state.sort = state.sort === 'priority' ? 'deadline' : 'priority';
    load();
  } });
  const searchForm = h('form', { class: 'search', role: 'search' }, icon('search', 16),
    h('label', { class: 'sr-only', for: 'task-search' }, 'Search by title'),
    h('input', { id: 'task-search', type: 'search', name: 'q', value: state.q, placeholder: 'Search by title' }));
  let searchTimer;
  searchForm.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { state.q = searchForm.q.value.trim(); load(); }, 250);
  });
  searchForm.addEventListener('submit', (e) => { e.preventDefault(); state.q = searchForm.q.value.trim(); load(); });

  function renderStatus() {
    clear(statusSeg, [['active', 'Active'], ['completed', 'Completed'], ['all', 'All']].map(([key, label]) =>
      h('button', { type: 'button', 'aria-pressed': state.status === key ? 'true' : 'false',
        onClick: () => { state.status = key; load(); } }, label)));
  }

  function renderChips(subjects) {
    const all = [['', 'All subjects'], ...subjects.map((s) => [s, s])];
    clear(chips, all.map(([value, label]) => h('button', { class: 'chip', type: 'button',
      'aria-pressed': state.subject.toLowerCase() === value.toLowerCase() ? 'true' : 'false',
      onClick: () => { state.subject = value; load(); } }, label)));
  }

  function row(task) {
    const due = dueLabel(task);
    const toggle = async () => {
      try {
        const updated = await patch(`/tasks/${task.id}/complete`, { completed: !task.completed });
        toast(updated.completed ? `“${task.title}” marked complete.` : `“${task.title}” is active again.`);
        load();
      } catch (err) { toast(err.message, 'error'); }
    };
    const remove = async () => {
      const ok = await confirmDialog({ title: 'Delete this task?', text: `“${task.title}” will be deleted for good.`,
        confirmLabel: 'Delete', danger: true });
      if (!ok) return;
      try { await del(`/tasks/${task.id}`); toast('Task deleted.'); load(); } catch (err) { toast(err.message, 'error'); }
    };
    return h('div', { class: `tgrid${task.completed ? ' is-done' : ''}` },
      h('button', { class: 'check c-check', type: 'button', 'aria-pressed': task.completed ? 'true' : 'false',
        'aria-label': `${task.completed ? 'Mark as not completed' : 'Mark as completed'}: ${task.title}`, onClick: toggle },
      h('span', { class: 'box' }, task.completed ? icon('check', 14, 3.2) : null)),
      h('div', { class: 'c-task', style: { display: 'flex', flexDirection: 'column', gap: '3px', minWidth: '0' } },
        h('a', { class: 't-title', href: `#/tasks/${task.id}` }, task.title),
        h('span', { class: 't-sub' }, `${task.subject} · ${task.difficulty} · ${num(task.estimated_hours)} h`)),
      h('div', { class: 't-dead c-dead' }, h('span', {}, dateTime(task.deadline)), h('span', { class: `due ${due.kind}` }, due.text)),
      h('span', { class: 'c-diff' }, task.difficulty),
      h('span', { class: 'mono c-hours' }, num(task.estimated_hours)),
      h('span', { class: 'c-level' }, levelBadge(task)),
      h('div', { class: 't-act' },
        h('a', { class: 'icon-btn plain', href: `#/tasks/${task.id}/edit`, 'aria-label': `Edit ${task.title}` }, icon('edit', 17)),
        h('button', { class: 'icon-btn plain', type: 'button', 'aria-label': `Delete ${task.title}`, onClick: remove }, icon('trash', 17))));
  }

  async function load() {
    const query = new URLSearchParams(conf.query);
    if (isList) query.set('status', state.status);
    if (state.subject) query.set('subject', state.subject);
    if (state.q) query.set('q', state.q);
    if (!conf.query.view) query.set('sort', state.sort);
    const data = await get(`/tasks?${query}`);
    setCounts(data.counts);
    countLabel.textContent = isList
      ? `${data.counts.active} active · ${data.counts.completed} completed`
      : `${data.tasks.length} task${data.tasks.length === 1 ? '' : 's'}`;
    if (isList) renderStatus();
    renderChips(data.subjects);
    clear(sortBtn, icon('sort', 16), `Sort: ${state.sort === 'priority' ? 'Priority' : 'Deadline'}`);
    clear(listBox,
      h('div', { class: 'tgrid thead', 'aria-hidden': 'true' },
        h('span'), h('span', {}, 'Task'), h('span', {}, 'Deadline'), h('span', { class: 'c-diff' }, 'Difficulty'),
        h('span', { class: 'c-hours' }, 'Hours'), h('span', {}, 'Priority'), h('span', { style: { textAlign: 'right' } }, 'Actions')),
      data.tasks.length ? data.tasks.map(row) : h('div', { class: 'empty' },
        h('h3', {}, state.q || state.subject ? 'No tasks match these filters' : emptyTitle(preset)),
        h('p', { class: 'muted' }, state.q || state.subject ? 'Try another subject or search.' : emptyText(preset)),
        preset === 'all' || preset === 'upcoming' ? h('a', { class: 'btn btn-primary', href: '#/tasks/new' }, icon('plus', 16, 2.4), 'New task') : null));
  }

  clear(root,
    h('header', { class: 'page-head' },
      h('div', { class: 'titles' }, h('h1', { class: 'h1' }, conf.title), countLabel),
      themeButton(),
      h('a', { class: 'btn btn-primary', href: '#/tasks/new' }, icon('plus', 16, 2.4), 'New task')),
    conf.note ? h('p', { class: 'muted' }, conf.note) : null,
    h('div', { class: 'toolbar' }, isList ? statusSeg : null, searchForm, conf.query.view ? null : sortBtn, chips),
    listBox,
    isList ? h('p', { class: 'small muted' }, 'Ties on score are broken by the earlier deadline. Scores update whenever deadline, difficulty or hours change.') : null);
  await load();
}

function emptyTitle(preset) {
  return { all: 'No active tasks', upcoming: 'Nothing due this week', overdue: 'Nothing overdue', completed: 'Nothing completed yet' }[preset];
}
function emptyText(preset) {
  return { all: 'Add your first assignment, exam or project.', upcoming: 'No incomplete tasks are due in the next 7 days.',
    overdue: 'Every incomplete task is still before its deadline.', completed: 'Tasks you mark complete show up here.' }[preset];
}
