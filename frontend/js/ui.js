// Shared UI building blocks. User data is only ever inserted as text (no innerHTML),
// so task titles etc. cannot inject markup (XSS). Icons are fixed strings in this file.

export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key === 'text') el.textContent = value;
    else if (key === 'style' && typeof value === 'object') Object.assign(el.style, value);
    else if (key.startsWith('on') && typeof value === 'function') el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'value') el.value = value;
    else if (key === 'checked' || key === 'disabled' || key === 'selected') el[key] = Boolean(value);
    else el.setAttribute(key, value === true ? '' : String(value));
  }
  append(el, children);
  return el;
}

function append(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

export function clear(el, ...children) {
  el.replaceChildren();
  append(el, children);
  return el;
}

const PATHS = {
  dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  tasks: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
  calendar: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>',
  sort: '<path d="M7 4v16M3 8l4-4 4 4M17 20V4M13 16l4 4 4-4"/>',
  back: '<path d="M15 18l-6-6 6-6"/>',
  alert: '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  minus: '<path d="M5 12h14"/>',
};

export function icon(name, size = 18, strokeWidth = 2) {
  const t = document.createElement('template');
  t.innerHTML = `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round">${PATHS[name] || ''}</svg>`;
  return t.content.firstChild;
}

export function badge(level, text) {
  return h('span', { class: `badge ${level || ''}` }, h('span', { class: 'dot' }), text || level);
}

export function levelBadge(task) {
  if (task.completed) return h('span', { class: 'badge' }, 'Done');
  return badge(task.priority.level, `${task.priority.level} · ${task.priority.score}`);
}

export const LEVEL_COLORS = { Critical: 'var(--crit)', High: 'var(--high)', Medium: 'var(--med)', Low: 'var(--low)' };
export const LEVEL_BG = { Critical: 'var(--critBg)', High: 'var(--highBg)', Medium: 'var(--medBg)', Low: 'var(--lowBg)' };

export function ring(score, level) {
  const t = document.createElement('template');
  const len = Math.round((339.3 * Math.max(0, Math.min(100, score))) / 100);
  t.innerHTML = `<svg role="img" aria-label="Priority score ${score} out of 100" width="120" height="120" viewBox="0 0 132 132">
    <circle class="ring-track" cx="66" cy="66" r="54" fill="none" stroke-width="12"/>
    <circle class="ring-value-arc ${['Critical', 'High', 'Medium', 'Low'].includes(level) ? level : ''}" cx="66" cy="66" r="54" fill="none" stroke-width="12"
      stroke-linecap="round" stroke-dasharray="${len} 340" transform="rotate(-90 66 66)"/></svg>`;
  return h('div', { class: 'ring' }, t.content.firstChild,
    h('div', { class: 'ring-label' }, h('span', { class: 'ring-value' }, String(score)), h('span', { class: 'small muted' }, 'of 100')));
}

export function toast(message, kind = 'info') {
  const region = document.getElementById('toasts');
  const el = h('div', { class: `toast ${kind}` }, message);
  region.append(el);
  setTimeout(() => el.remove(), kind === 'error' ? 6000 : 3500);
}

/** Accessible confirm dialog (native <dialog>). Resolves true/false. */
export function confirmDialog({ title, text, confirmLabel = 'Confirm', danger = false }) {
  return new Promise((resolve) => {
    const dialog = h('dialog', { class: 'modal', 'aria-labelledby': 'dlg-title' },
      h('h2', { id: 'dlg-title' }, title),
      h('p', { class: 'muted' }, text),
      h('div', { class: 'actions' },
        h('button', { class: 'btn', type: 'button', value: 'cancel', onClick: () => dialog.close('cancel') }, 'Cancel'),
        h('button', { class: `btn ${danger ? 'btn-primary' : 'btn-primary'}`, type: 'button', 'data-confirm': '',
          style: danger ? { background: 'var(--crit)', borderColor: 'var(--crit)', color: '#fff' } : {},
          onClick: () => dialog.close('ok') }, confirmLabel)));
    dialog.addEventListener('close', () => { resolve(dialog.returnValue === 'ok'); dialog.remove(); });
    document.body.append(dialog);
    dialog.showModal();
  });
}

/** Show server field errors next to inputs; returns true if any were shown. */
export function showFieldErrors(form, fields = {}) {
  form.querySelectorAll('.field-error[data-for]').forEach((el) => { el.textContent = ''; el.hidden = true; });
  form.querySelectorAll('[aria-invalid="true"]').forEach((el) => el.setAttribute('aria-invalid', 'false'));
  let first = null;
  for (const [name, message] of Object.entries(fields)) {
    const slot = form.querySelector(`.field-error[data-for="${name}"]`);
    const input = form.querySelector(`[name="${name}"]`);
    if (slot) { slot.textContent = message; slot.hidden = false; }
    if (input) { input.setAttribute('aria-invalid', 'true'); first = first || input; }
  }
  if (first) first.focus();
  return Object.keys(fields).length > 0;
}

export function field({ label, name, type = 'text', value = '', placeholder = '', autocomplete, hint, attrs = {} }) {
  const id = `f-${name}`;
  return h('div', { class: 'field' },
    h('label', { class: 'label', for: id }, label),
    h('input', { class: 'input', id, name, type, value, placeholder, autocomplete,
      'aria-describedby': `${id}-err`, 'aria-invalid': 'false', ...attrs }),
    hint ? h('span', { class: 'hint' }, hint) : null,
    h('span', { class: 'field-error', id: `${id}-err`, 'data-for': name, hidden: true }));
}
