export type OpsUser = {
  id: string
  username: string
  role: string
  permissions: string[]
  is_active: boolean
  last_login_at: string | null
}

const TOKEN_KEY = 'ops_token'
const API_BASE = '/ops/api'

export function getOpsToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setOpsToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearOpsToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function request(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  const token = getOpsToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || data.reason_code || '请求失败')
  }
  return data
}

export async function login(username: string, password: string) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function logout() {
  return request('/auth/logout', { method: 'POST' })
}

export async function getMe() {
  return request('/auth/me')
}

export async function getSummary() {
  return request('/system/summary')
}

export async function getHealth() {
  return request('/system/health')
}

export async function listPlayers(q = '', page = 1, pageSize = 20) {
  const params = new URLSearchParams({ q, page: String(page), page_size: String(pageSize) })
  return request(`/players?${params.toString()}`)
}

export async function getPlayer(accountId: string) {
  return request(`/players/${accountId}`)
}

export async function banPlayer(accountId: string) {
  return request('/players/ban', { method: 'POST', body: JSON.stringify({ account_id: accountId }) })
}

export async function unbanPlayer(accountId: string) {
  return request('/players/unban', { method: 'POST', body: JSON.stringify({ account_id: accountId }) })
}

export async function kickPlayer(accountId: string) {
  return request('/players/kick', { method: 'POST', body: JSON.stringify({ account_id: accountId }) })
}

export async function previewMails(payload: unknown) {
  return request('/grant/mails/preview', { method: 'POST', body: JSON.stringify(payload) })
}

export async function confirmMails(confirmToken: string) {
  return request('/grant/mails/confirm', { method: 'POST', body: JSON.stringify({ confirm_token: confirmToken }) })
}

export async function listGrantItemOptions() {
  return request('/grant/item-options')
}

export async function listAudit(actionType = '', operatorUsername = '', page = 1, pageSize = 20) {
  const params = new URLSearchParams({
    action_type: actionType,
    operator_username: operatorUsername,
    page: String(page),
    page_size: String(pageSize),
  })
  return request(`/audit/list?${params.toString()}`)
}

export async function listWhitelist() {
  return request('/system/whitelist')
}

export async function updateWhitelist(action: 'add' | 'remove', accountId: string, note = '') {
  return request('/system/whitelist', {
    method: 'POST',
    body: JSON.stringify({ action, account_id: accountId, note }),
  })
}

export async function updateLoginGate(enabled: boolean, note = '') {
  return request('/system/login-gate', {
    method: 'POST',
    body: JSON.stringify({ enabled, note }),
  })
}

export async function kickAllPlayers(note = '') {
  return request('/system/kick-all', {
    method: 'POST',
    body: JSON.stringify({ note }),
  })
}
