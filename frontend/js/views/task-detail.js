// US2 — task details with score breakdown; complete / reopen / delete (FR-07..FR-09).
import { get, patch, del } from '../api.js';
import { h, clear, icon, ring, toast, confirmDialog } from '../ui.js';
import { dateTime, dueLabel, num } from '../format.js';
import { go, themeButton } from '../app.js';

export async function renderTaskDetail({ root, id }) {
  let task;
  try {
    task = await get(`/tasks/${id}`);
  } catch (err) {
    if (err.status !== 404) throw err;
    clear(root, h('div', { class: 'card empty' },
      h('h1', { class: 'h1' }, 'Task not found'),
      h('p', { class: 'muted' }, 'It may have been deleted, or it belongs to someone else.'),
      h('a', { class: 'btn', href: '#/tasks' }, 'Back to tasks')));
    return;
  }
  const render = () => {
    const due = dueLabel(task);
    const p = task.priority;
    const fact = (k, v, cls) => h('div', { class: 'fact' }, h('span', { class: 'k' }, k), h('span', { class: `v ${cls || ''}` }, v));
    const toggle = async () => {
      try {
        task = await patch(`/tasks/${task.id}/complete`, { completed: !task.completed });
        toast(task.completed ? 'Marked complete.' : 'Marked as not completed.');
        render();
      } catch (err) { toast(err.message, 'error'); }
    };
    const remove = async () => {
      if (!await confirmDialog({ title: 'Delete this task?', text: `“${task.title}” will be deleted for good.`, confirmLabel: 'Delete', danger: true })) return;
      try { await del(`/tasks/${task.id}`); toast('Task deleted.'); go('/tasks'); } catch (err) { toast(err.message, 'error'); }
    };
    clear(root, h('div', { class: 'narrow-page', style: { display: 'flex', flexDirection: 'column', gap: '22px' } },
      h('header', { class: 'page-head' },
        h('div', { class: 'titles' },
          h('a', { class: 'back', href: '#/tasks' }, icon('back', 16), 'Back to tasks'),
          h('h1', { class: 'h1', style: { overflowWrap: 'anywhere' } }, task.title),
          h('div', { class: 'tags' },
            task.completed ? h('span', { class: 'badge ok' }, h('span', { class: 'dot' }), 'Completed')
              : h('span', { class: `badge ${p.level}` }, h('span', { class: 'dot' }), `${p.level} · ${p.score}`),
            task.overdue ? h('span', { class: 'badge warn' }, 'Overdue') : null,
            h('span', { class: 'pill' }, task.subject))),
        themeButton()),
      h('div', { class: 'form-wrap' },
        h('section', { class: 'card lg form-card', 'aria-label': 'Details' },
          h('div', { class: 'facts' },
            fact('Deadline', dateTime(task.deadline)),
            fact(task.completed ? 'Status' : 'Time left', due.text, due.kind === 'over' ? 'c-crit' : due.kind === 'soon' ? 'c-high' : ''),
            fact('Difficulty', task.difficulty),
            fact('Estimated hours', `${num(task.estimated_hours)} h`),
            fact('Created', dateTime(task.created_at)),
            task.completed_at ? fact('Completed', dateTime(task.completed_at)) : null),
          h('div', { class: 'form-actions' },
            h('button', { class: `btn ${task.completed ? '' : 'btn-primary'}`, type: 'button', onClick: toggle },
              task.completed ? 'Mark as not completed' : [icon('check', 16, 2.4), 'Mark complete']),
            h('a', { class: 'btn', href: `#/tasks/${task.id}/edit` }, icon('edit', 16), 'Edit'),
            h('button', { class: 'btn btn-danger', type: 'button', onClick: remove }, icon('trash', 16), 'Delete'))),
        h('aside', { class: 'card lg preview-card', 'aria-label': 'Priority breakdown' },
          h('span', { class: 'eyebrow', style: { color: 'var(--muted)' } }, 'Priority breakdown'),
          task.completed
            ? h('p', { class: 'muted' }, 'Completed tasks have no priority score. Mark it as not completed to score it again.')
            : [
              h('div', { style: { display: 'flex', alignItems: 'center', gap: '18px', flexWrap: 'wrap' } },
                ring(p.score, p.level),
                h('p', { class: 'muted', style: { flex: '1 1 160px' } },
                  p.overdue ? 'The deadline has passed, so the deadline part counts in full.'
                    : p.days_left === 0 ? `Less than 24 hours left, so the deadline score is ${p.deadline_score}.`
                      : `The time left counts as ${p.days_left} day${p.days_left === 1 ? '' : 's'} (rounded up), so the deadline score is ${p.deadline_score}.`)),
              h('div', { class: 'breakdown' },
                h('div', {}, h('span', {}, 'Deadline ', h('span', { class: 'muted' }, `${p.deadline_score} × 0.50`)), h('span', { class: 'mono' }, p.deadline_part.toFixed(1))),
                h('div', {}, h('span', {}, 'Difficulty ', h('span', { class: 'muted' }, `${p.difficulty_score} × 0.30`)), h('span', { class: 'mono' }, p.difficulty_part.toFixed(1))),
                h('div', {}, h('span', {}, 'Time ', h('span', { class: 'muted' }, `${p.time_score} × 0.20`)), h('span', { class: 'mono' }, p.time_part.toFixed(1))),
                h('div', { class: 'total' }, h('span', {}, 'Exact score'), h('span', { class: 'mono' }, Number(p.exact).toFixed(1))),
                h('div', { class: 'total' }, h('span', {}, 'Shown score · level'), h('span', { class: 'mono' }, `${p.score} · ${p.level}`)))]))));
  };
  render();
}
