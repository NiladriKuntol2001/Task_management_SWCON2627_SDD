// Dates and labels. Server sends UTC ISO strings; everything is shown in local time.

const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const pad = (n) => String(n).padStart(2, '0');

export function dateTime(iso) {
  const d = new Date(iso);
  return `${DOW[d.getDay()]} ${d.getDate()} ${MON[d.getMonth()]}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function dateOnly(iso) {
  const d = new Date(iso);
  return `${d.getDate()} ${MON[d.getMonth()]} ${d.getFullYear()}`;
}

export function timeOnly(iso) {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function dayParts(iso) {
  const d = new Date(iso);
  return { dow: DOW[d.getDay()], day: String(d.getDate()) };
}

/** "In 14 hours", "In 4 days", "Overdue · 2 days". Returns {text, kind}. */
export function dueLabel(task) {
  if (task.completed) return { text: 'Completed', kind: '' };
  const ms = new Date(task.deadline).getTime() - Date.now();
  const hours = Math.abs(ms) / 3.6e6;
  const amount = hours < 48 ? `${Math.max(1, Math.round(hours))} hour${Math.round(hours) === 1 ? '' : 's'}`
    : `${Math.floor(hours / 24)} days`;
  if (ms < 0) return { text: `Overdue · ${amount}`, kind: 'over' };
  return { text: `In ${amount}`, kind: hours < 24 ? 'soon' : '' };
}

/** Value for <input type="datetime-local"> in local time. */
export function toLocalInput(iso) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Local datetime-local value -> ISO string with the browser's offset (stored as UTC by the server). */
export function fromLocalInput(value) {
  if (!value) return '';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '' : d.toISOString();
}

export function initials(name) {
  return (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('') || '?';
}

export function greeting() {
  const h = new Date().getHours();
  return h < 5 ? 'Good night' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

export function todayLabel() {
  const d = new Date();
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  return `${days[d.getDay()]}, ${d.getDate()} ${months[d.getMonth()]}`;
}

export const num = (n) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
