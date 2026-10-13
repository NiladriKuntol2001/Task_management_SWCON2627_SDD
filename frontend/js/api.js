// Fetch wrapper: adds the session token, turns errors into ApiError (NFR-11).

const TOKEN_KEY = 'studyflow.token';
const USER_KEY = 'studyflow.user';

function store(key, value) {
  try { value == null ? localStorage.removeItem(key) : localStorage.setItem(key, value); } catch (e) { /* ignore */ }
}
function load(key) {
  try { return localStorage.getItem(key); } catch (e) { return null; }
}

export class ApiError extends Error {
  constructor(status, message, fields) {
    super(message);
    this.status = status;
    this.fields = fields || {};
  }
}

export const session = {
  get token() { return load(TOKEN_KEY); },
  get user() {
    try { return JSON.parse(load(USER_KEY) || 'null'); } catch (e) { return null; }
  },
  save(token, user) { store(TOKEN_KEY, token); store(USER_KEY, JSON.stringify(user)); },
  updateUser(user) { store(USER_KEY, JSON.stringify(user)); },
  clear() { store(TOKEN_KEY, null); store(USER_KEY, null); },
};

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

export async function api(method, path, body) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  let res;
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (e) {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch (e) { /* empty or non-JSON body */ }
  if (!res.ok) {
    const err = data && data.error ? data.error : {};
    const error = new ApiError(res.status, err.message || `Request failed (${res.status}).`, err.fields);
    if (res.status === 401 && !path.startsWith('/auth/')) onUnauthorized(error);
    throw error;
  }
  return data;
}

export const get = (path) => api('GET', path);
export const post = (path, body = {}) => api('POST', path, body);
export const put = (path, body) => api('PUT', path, body);
export const patch = (path, body) => api('PATCH', path, body);
export const del = (path) => api('DELETE', path);
