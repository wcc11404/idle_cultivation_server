import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearOpsToken, logout } from '../services/api'

const links = [
  ['dashboard', '概览'],
  ['players', '玩家管理'],
  ['grant', '发放中心'],
  ['audit', '审计日志'],
  ['system', '系统维护'],
] as const

export function Layout() {
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await logout()
    } finally {
      clearOpsToken()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">修仙挂机运维台</div>
        <nav className="nav">
          {links.map(([path, label]) => (
            <NavLink key={path} to={`/${path}`} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              {label}
            </NavLink>
          ))}
        </nav>
        <button className="danger ghost" onClick={handleLogout}>退出登录</button>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
