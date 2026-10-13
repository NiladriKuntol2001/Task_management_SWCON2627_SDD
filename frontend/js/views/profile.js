// US6 — profile, change email, change password (FR-22..FR-25).
import { get, patch, session } from '../api.js';
import { h, clear, icon, toast, field, showFieldErrors } from '../ui.js';
import { dateOnly, initials } from '../format.js';
import { themeButton, logout } from '../app.js';

export async function renderProfile({ root }) {
  let me = await get('/me');
  const admin = me.role === 'admin';

  const summary = () => h('section', { class: 'card lg profile-head', 'aria-label': 'Account summary' },
    h('span', { class: `avatar lg${admin ? ' admin' : ''}`, 'aria-hidden': 'true' }, initials(me.name)),
    h('div', { style: { flex: '1 1 220px', display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '0' } },
      h('div', { class: 'tags' },
        h('h2', { style: { fontSize: '24px' } }, me.name),
        h('span', { class: 'badge mono' }, `ID ${me.id}`),
        h('span', { class: `badge ${admin ? 'High' : 'accent'}` }, admin ? (me.is_main_admin ? 'Main admin' : 'Admin') : 'Student')),
      h('span', { class: 'muted', style: { overflowWrap: 'anywhere' }, 'data-profile-email': '' }, me.email)),
    h('div', { class: 'facts', style: { flex: '1 1 300px' } },
      h('div', { class: 'fact' }, h('span', { class: 'k' }, 'Joined'), h('span', { class: 'v' }, dateOnly(me.created_at))),
      h('div', { class: 'fact' }, h('span', { class: 'k' }, 'Tasks'), h('span', { class: 'v mono' }, String(me.task_count))),
      h('div', { class: 'fact' }, h('span', { class: 'k' }, 'Completed'), h('span', { class: 'v mono' }, String(me.completed_count)))));
  const summaryHolder = h('div', {}, summary());

  // ---- change email (FR-23) ----
  const emailForm = h('form', { class: 'card lg', novalidate: true, 'aria-labelledby': 'em-title', style: { flex: '1 1 340px', minWidth: '0', display: 'flex', flexDirection: 'column', gap: '16px' } },
    h('div', {}, h('h2', { class: 'section-title', id: 'em-title' }, 'Change email'),
      h('p', { class: 'muted small' }, me.is_main_admin ? 'The main admin’s email is fixed and can’t be changed.' : 'You will use the new email to sign in.')),
    field({ label: 'New email', name: 'new_email', type: 'email', autocomplete: 'email', placeholder: 'name@example.com', attrs: { disabled: me.is_main_admin } }),
    field({ label: 'Current password', name: 'current_password', type: 'password', autocomplete: 'current-password', placeholder: 'Needed to confirm it’s you', attrs: { disabled: me.is_main_admin } }),
    h('button', { class: 'btn btn-primary', type: 'submit', style: { alignSelf: 'flex-start' }, disabled: me.is_main_admin }, 'Update email'));
  emailForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(emailForm).entries());
    try {
      me = await patch('/me/email', data);
      session.updateUser({ ...session.user, email: me.email });
      clear(summaryHolder, summary());
      emailForm.reset();
      showFieldErrors(emailForm, {});
      toast('Email updated.');
    } catch (err) {
      if (!showFieldErrors(emailForm, err.fields)) toast(err.message, 'error');
    }
  });

  // ---- change password (FR-24) with live rules ----
  const rulesList = h('ul', { class: 'rules', id: 'pw-rules', 'aria-label': 'Password rules' });
  const pwForm = h('form', { class: 'card lg', novalidate: true, 'aria-labelledby': 'pw-title', style: { flex: '1 1 340px', minWidth: '0', display: 'flex', flexDirection: 'column', gap: '16px' } },
    h('div', {}, h('h2', { class: 'section-title', id: 'pw-title' }, 'Change password'),
      h('p', { class: 'muted small' }, 'After changing it, the old password stops working.')),
    field({ label: 'Current password', name: 'current_password', type: 'password', autocomplete: 'current-password' }),
    field({ label: 'New password', name: 'new_password', type: 'password', autocomplete: 'new-password', attrs: { 'aria-describedby': 'f-new_password-err pw-rules' } }),
    field({ label: 'Confirm new password', name: 'confirm_password', type: 'password', autocomplete: 'new-password' }),
    rulesList,
    h('button', { class: 'btn btn-primary', type: 'submit', style: { alignSelf: 'flex-start' } }, 'Update password'));
  const renderRules = () => {
    const v = Object.fromEntries(new FormData(pwForm).entries());
    const rule = (ok, touched, label) => h('li', { class: ok ? 'met' : touched ? 'bad' : '' },
      h('span', { class: 'dot' }, icon(ok ? 'check' : touched ? 'x' : 'minus', 12, 3.4)), label,
      h('span', { class: 'sr-only' }, ok ? ' (met)' : ' (not met)'));
    clear(rulesList,
      rule(v.new_password.length >= 8, v.new_password.length > 0, 'At least 8 characters'),
      rule(v.new_password.length > 0 && v.new_password !== v.current_password, v.new_password.length > 0, 'Different from your current password'),
      rule(v.confirm_password.length > 0 && v.confirm_password === v.new_password, v.confirm_password.length > 0, 'Both new passwords match'));
  };
  pwForm.addEventListener('input', renderRules);
  pwForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await patch('/me/password', Object.fromEntries(new FormData(pwForm).entries()));
      pwForm.reset();
      showFieldErrors(pwForm, {});
      renderRules();
      toast('Password updated.');
    } catch (err) {
      if (!showFieldErrors(pwForm, err.fields)) toast(err.message, 'error');
    }
  });
  renderRules();

  clear(root,
    h('header', { class: 'page-head' },
      h('div', { class: 'titles' }, h('h1', { class: 'h1' }, 'Profile'), h('span', { class: 'muted' }, 'Your account details and sign-in settings.')),
      themeButton()),
    summaryHolder,
    h('div', { class: 'two-col' }, emailForm, pwForm),
    h('section', { class: 'card lg', 'aria-label': 'Session', style: { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '14px' } },
      h('div', { style: { flex: '1 1 240px' } }, h('p', { style: { fontWeight: '600' } }, 'Sign out'),
        h('p', { class: 'muted small' }, 'Your tasks stay saved and are here when you sign back in.')),
      h('button', { class: 'btn', type: 'button', onClick: logout }, icon('logout', 16), 'Log out')));
}
