import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, setOpsToken } from '../services/api'

export function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await login(username, password)
      setOpsToken(result.token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form className="panel login-card" onSubmit={handleSubmit}>
        <h1>线上运维系统</h1>
        <p className="muted">使用运维账号登录后进入后台。</p>
        <label>
          用户名
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label>
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error ? <div className="error-box">{error}</div> : null}
        <button className="primary" type="submit" disabled={loading}>{loading ? '登录中...' : '登录'}</button>
      </form>
    </div>
  )
}
