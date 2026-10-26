// US2 — add / edit task with live priority preview (FR-04..FR-06, FR-10, FR-35).
// The preview asks the server (POST /priority/preview): the formula lives only there.
import { get, post, put } from '../api.js';
import { h, clear, icon, toast, showFieldErrors } from '../ui.js';
import { toLocalInput, fromLocalInput } from '../format.js';
import { go, themeButton } from '../app.js';

const DIFFS = [['Easy', 20], ['Medium', 50], ['Hard', 80], ['Very Hard', 100]];

function defaultDeadline() {
  const d = new Date(Date.now() + 3 * 24 * 3600 * 1000);
  d.setHours(12, 0, 0, 0);
  return d.toISOString();
}

export async function renderTaskForm({ root, id }) {
  const editing = Boolean(id);
  const [task, list] = await Promise.all([
    editing ? get(`/tasks/${id}`) : Promise.resolve(null),
    get('/tasks?status=all'),
  ]);
  const values = task || { title: '', subject: '', deadline: defaultDeadline(), difficulty: 'Medium', estimated_hours: 2 };
  let difficulty = values.difficulty;

  const err = (name) => h('span', { class: 'field-error', 'data-for': name, id: `err-${name}`, hidden: true });
  const titleInput = h('input', { class: 'input', id: 'title', name: 'title', value: values.title, maxlength: '200',
    placeholder: 'e.g. Security lab: STRIDE threat model', 'aria-describedby': 'err-title', required: true });
  const subjectInput = h('input', { class: 'input', id: 'subject', name: 'subject', value: values.subject, maxlength: '100',
    list: 'subject-list', placeholder: 'e.g. Software Design', 'aria-describedby': 'err-subject', required: true });
  const deadlineInput = h('input', { class: 'input', id: 'deadline', name: 'deadline', type: 'datetime-local',
    value: toLocalInput(values.deadline), 'aria-describedby': 'err-deadline', required: true });
  const hoursInput = h('input', { class: 'input', id: 'estimated_hours', name: 'estimated_hours', type: 'number',
    min: '0.5', max: '1000', step: '0.5', inputmode: 'decimal', value: String(values.estimated_hours),
    'aria-describedby': 'err-estimated_hours hours-hint', required: true });

  const diffGroup = h('div', { class: 'diff-grid', role: 'radiogroup', 'aria-labelledby': 'diff-legend' });
  function renderDiffs() {
    clear(diffGroup, DIFFS.map(([name, pts]) => h('button', {
      class: 'diff-opt', type: 'button', role: 'radio', 'aria-checked': difficulty === name ? 'true' : 'false',
      tabindex: difficulty === name ? '0' : '-1', 'data-value': name,
      onClick: () => { difficulty = name; renderDiffs(); diffGroup.querySelector('[aria-checked="true"]').focus(); preview(); },
    }, h('span', { style: { fontWeight: '600' } }, name), h('span', { class: 'small muted mono' }, `${pts} pts`))));
  }
  diffGroup.addEventListener('keydown', (e) => {   // arrow keys move between radio options
    const i = DIFFS.findIndex(([n]) => n === difficulty);
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!step) return;
    e.preventDefault();
    difficulty = DIFFS[(i + step + DIFFS.length) % DIFFS.length][0];
    renderDiffs();
    diffGroup.querySelector('[aria-checked="true"]').focus();
    preview();
  });
  renderDiffs();

  const stepHours = (delta) => {
    const v = Math.max(0.5, Math.min(1000, (parseFloat(hoursInput.value) || 0) + delta));
    hoursInput.value = String(v);
    preview();
  };

  // ---- live preview ----
  const scoreEl = h('span', { class: 'mono' }, '–');
  const levelEl = h('span', { class: 'badge' }, '…');
  const marker = h('div', { style: { left: '0%' } });
  const rows = { d: h('span', { class: 'mono' }, '–'), f: h('span', { class: 'mono' }, '–'), t: h('span', { class: 'mono' }, '–'), exact: h('span', { class: 'mono' }, '–') };
  const labels = { d: h('span', { class: 'muted' }), f: h('span', { class: 'muted' }), t: h('span', { class: 'muted' }) };
  const previewNote = h('p', { class: 'small muted', 'aria-live': 'polite' }, '');
  let timer;
  let firstPreview = true;
  function preview() {
    clearTimeout(timer);
    const delay = firstPreview ? 0 : 200;
    firstPreview = false;
    timer = setTimeout(async () => {
      try {
        const p = await post('/priority/preview', { deadline: fromLocalInput(deadlineInput.value),
          difficulty, estimated_hours: hoursInput.value === '' ? null : Number(hoursInput.value) });
        scoreEl.textContent = String(p.score);
        levelEl.className = `badge ${p.level}`;
        clear(levelEl, h('span', { class: 'dot' }), p.level);
        marker.style.left = `${Math.min(100, p.exact)}%`;
        labels.d.textContent = ` ${p.deadline_score} × 0.50`;
        labels.f.textContent = ` ${p.difficulty_score} × 0.30`;
        labels.t.textContent = ` ${p.time_score} × 0.20`;
        rows.d.textContent = p.deadline_part.toFixed(1);
        rows.f.textContent = p.difficulty_part.toFixed(1);
        rows.t.textContent = p.time_part.toFixed(1);
        rows.exact.textContent = Number(p.exact).toFixed(1);
        previewNote.textContent = p.overdue ? 'This deadline has already passed, so the task will be overdue.'
          : p.days_left === 0 ? `Less than 24 hours left → deadline score ${p.deadline_score}.`
            : `Counted as ${p.days_left} day${p.days_left === 1 ? '' : 's'} (time left rounded up) → deadline score ${p.deadline_score}.`;
      } catch (e) {
        scoreEl.textContent = '–';
        clear(levelEl, 'Fill in deadline and hours');
        levelEl.className = 'badge';
        previewNote.textContent = '';
      }
    }, delay);
  }
  [deadlineInput, hoursInput].forEach((el) => el.addEventListener('input', preview));

  const subjects = h('datalist', { id: 'subject-list' }, list.subjects.map((s) => h('option', { value: s })));

  const form = h('form', { class: 'card lg form-card', novalidate: true },
    h('div', { class: 'field' }, h('label', { class: 'label', for: 'title' }, 'Title'), titleInput, err('title')),
    h('div', { class: 'form-grid' },
      h('div', { class: 'field' }, h('label', { class: 'label', for: 'subject' }, 'Subject'), subjectInput, subjects, err('subject')),
      h('div', { class: 'field' }, h('label', { class: 'label', for: 'deadline' }, 'Deadline'), deadlineInput, err('deadline'))),
    h('fieldset', {}, h('legend', { id: 'diff-legend' }, 'Difficulty'), diffGroup, err('difficulty')),
    h('div', { class: 'field' },
      h('label', { class: 'label', for: 'estimated_hours' }, 'Estimated hours'),
      h('div', { class: 'stepper' },
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Decrease hours', onClick: () => stepHours(-1) }, icon('minus')),
        hoursInput,
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Increase hours', onClick: () => stepHours(1) }, icon('plus')),
        h('span', { class: 'hint', id: 'hours-hint' }, 'More than 0; halves allowed')),
      err('estimated_hours')),
    h('div', { class: 'form-actions' },
      h('button', { class: 'btn btn-primary', type: 'submit' }, editing ? 'Save changes' : 'Save task'),
      h('a', { class: 'btn', href: editing ? `#/tasks/${id}` : '#/tasks' }, 'Cancel')));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = { title: titleInput.value, subject: subjectInput.value, deadline: fromLocalInput(deadlineInput.value),
      difficulty, estimated_hours: hoursInput.value === '' ? null : Number(hoursInput.value) };
    const button = form.querySelector('button[type=submit]');
    button.disabled = true;
    try {
      const saved = editing ? await put(`/tasks/${id}`, body) : await post('/tasks', body);
      toast(editing ? 'Changes saved.' : `“${saved.title}” added · ${saved.priority ? `${saved.priority.level} ${saved.priority.score}` : 'Done'}.`);
      go(`/tasks/${saved.id}`);
    } catch (err2) {
      if (!showFieldErrors(form, err2.fields)) toast(err2.message, 'error');
    } finally {
      button.disabled = false;
    }
  });

  clear(root, h('div', { class: 'narrow-page', style: { display: 'flex', flexDirection: 'column', gap: '22px' } },
    h('header', { class: 'page-head' },
      h('div', { class: 'titles' },
        h('a', { class: 'back', href: editing ? `#/tasks/${id}` : '#/tasks' }, icon('back', 16), editing ? 'Back to task' : 'Back to tasks'),
        h('h1', { class: 'h1' }, editing ? 'Edit task' : 'New task'),
        h('p', { class: 'muted' }, 'Five fields. The priority is calculated for you as you type.')),
      themeButton()),
    h('div', { class: 'form-wrap' },
      form,
      h('aside', { class: 'card lg preview-card', 'aria-label': 'Priority preview' },
        h('span', { class: 'eyebrow', style: { color: 'var(--muted)' } }, 'Live priority'),
        h('div', { class: 'big-score' }, scoreEl, levelEl),
        h('div', { role: 'img', 'aria-label': 'Score scale from 0 to 100' },
          h('div', { class: 'scale' }, h('div', { class: 'bg-lowSoft', style: { flex: '40' } }), h('div', { class: 'bg-medSoft', style: { flex: '20' } }),
            h('div', { class: 'bg-highSoft', style: { flex: '20' } }), h('div', { class: 'bg-critSoft', style: { flex: '20' } })),
          h('div', { class: 'scale-marker' }, marker),
          h('div', { class: 'scale-labels mono' }, ['0', '40', '60', '80', '100'].map((x) =>
            h('span', { style: { left: `${x}%` } }, x)))),
        h('div', { class: 'breakdown' },
          h('div', {}, h('span', {}, 'Deadline', labels.d), rows.d),
          h('div', {}, h('span', {}, 'Difficulty', labels.f), rows.f),
          h('div', {}, h('span', {}, 'Time', labels.t), rows.t),
          h('div', { class: 'total' }, h('span', {}, 'Priority score'), rows.exact)),
        previewNote,
        h('p', { class: 'small muted' }, 'Deadline counts 50%, difficulty 30%, estimated time 20%. The shown score is rounded half up; the level follows the shown score.')))));
  preview();
  titleInput.focus();
}
