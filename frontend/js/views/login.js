// US1 — sign in / create account (FR-01, FR-02).
import { post, session } from '../api.js';
import { h, clear, field, showFieldErrors } from '../ui.js';
import { go, themeButton } from '../app.js';

const SAMPLE = [
  { score: 90, title: 'STRIDE threat model', level: 'Critical', indent: 0 },
  { score: 74, title: 'SDD report draft', level: 'High', indent: 24 },
  { score: 32, title: 'Normalization exercises', level: 'Low', indent: 48 },
];

export function renderLogin({ root, mode = 'login' }) {
  const isRegister = mode === 'register';
  document.title = `${isRegister ? 'Create account' : 'Sign in'} · StudyFlow`;
  const errorBox = h('div', { class: 'form-error', role: 'alert', hidden: true });

  const form = h('form', { class: 'auth-form', novalidate: true, style: { display: 'flex', flexDirection: 'column', gap: '16px' } },
    isRegister ? field({ label: 'Full name', name: 'name', autocomplete: 'name', placeholder: 'Your name' }) : null,
    field({ label: 'Email', name: 'email', type: 'email', autocomplete: 'email', placeholder: 'you@example.com' }),
    field({ label: 'Password', name: 'password', type: 'password',
      autocomplete: isRegister ? 'new-password' : 'current-password',
      placeholder: isRegister ? 'At least 8 characters' : '' }),
    h('button', { class: 'btn btn-primary', type: 'submit', style: { height: '50px', marginTop: '6px' } },
      isRegister ? 'Create account' : 'Sign in'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBox.hidden = true;
    const data = Object.fromEntries(new FormData(form).entries());
    const button = form.querySelector('button[type=submit]');
    button.disabled = true;
    try {
      const res = await post(isRegister ? '/auth/register' : '/auth/login', data);
      session.save(res.token, res.user);
      go(res.user.role === 'admin' ? '/admin' : '/dashboard');
    } catch (err) {
      if (!showFieldErrors(form, err.fields)) {
        errorBox.textContent = err.message;
        errorBox.hidden = false;
      }
    } finally {
      button.disabled = false;
    }
  });

  const tab = (label, target, selected) => h('a', {
    href: `#/${target}`, role: 'tab', 'aria-selected': selected ? 'true' : 'false',
    class: 'btn btn-sm', style: selected
      ? { background: 'var(--accent)', color: 'var(--onAccent)', border: '0', height: '40px' }
      : { border: '0', height: '40px', color: 'var(--muted)' },
  }, label);

  clear(root, h('div', { class: 'auth' },
    h('section', { class: 'auth-aside', 'aria-label': 'About StudyFlow' },
      h('div', {},
        h('div', { class: 'brand' }, h('span', { class: 'brand-mark', 'aria-hidden': 'true' }, 'S'),
          h('span', { class: 'brand-name', style: { fontSize: '20px' } }, 'StudyFlow')),
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '14px' } },
          h('h1', { class: 'auth-hero' }, 'Know what to work on next.'),
          h('p', { class: 'muted', style: { fontSize: '17px', lineHeight: '1.55' } },
            'Add your assignments, exams and projects. StudyFlow weighs deadline, difficulty and time, and puts the right task first.')),
        h('div', { class: 'auth-sample', 'aria-hidden': 'true' }, SAMPLE.map((s) =>
          h('div', { style: { marginLeft: `${s.indent}px` } },
            h('span', { class: 'mono', style: { fontWeight: '700', fontSize: '20px', width: '36px' } }, String(s.score)),
            h('span', { style: { flex: '1', fontWeight: '600' } }, s.title),
            h('span', { class: `badge ${s.level}` }, s.level)))))),
    h('section', { class: 'auth-main', 'aria-label': isRegister ? 'Create account' : 'Sign in' },
      h('div', { class: 'auth-box' },
        h('div', { style: { display: 'flex', justifyContent: 'flex-end' } }, themeButton()),
        h('div', { class: 'seg', role: 'tablist', 'aria-label': 'Account' },
          tab('Sign in', 'login', !isRegister), tab('Create account', 'register', isRegister)),
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '6px' } },
          h('h2', { style: { fontSize: '28px' } }, isRegister ? 'Create your account' : 'Welcome back'),
          h('p', { class: 'muted' }, isRegister ? 'It takes less than a minute.' : 'Sign in to see today’s plan.')),
        errorBox,
        form,
        h('p', { class: 'small muted', style: { textAlign: 'center' } }, 'Your tasks are private to your account.')))));
  form.querySelector('input').focus();
}
