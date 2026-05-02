import { useEffect, useState } from 'react'
import { getHealth, getSummary } from '../services/api'

export function DashboardPage() {
  const [summary, setSummary] = useState<any>(null)
  const [health, setHealth] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getSummary(), getHealth()])
      .then(([summaryResult, healthResult]) => {
        setSummary(summaryResult.summary)
        setHealth(healthResult.health)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [])

  return (
    <section>
      <div className="page-header">
        <h1>系统概览</h1>
        <p>先看基础状态，再进入具体操作。</p>
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="card-grid">
        <article className="panel stat-card"><h3>系统状态</h3><strong>{health?.status ?? '-'}</strong></article>
        <article className="panel stat-card"><h3>玩家总数</h3><strong>{summary?.players_total ?? '-'}</strong></article>
        <article className="panel stat-card"><h3>封禁玩家</h3><strong>{summary?.players_banned ?? '-'}</strong></article>
        <article className="panel stat-card"><h3>登录闸门</h3><strong>{summary?.login_gate_enabled ? '已开启' : '已关闭'}</strong></article>
        <article className="panel stat-card"><h3>白名单数量</h3><strong>{summary?.ops_whitelist_count ?? '-'}</strong></article>
        <article className="panel stat-card"><h3>活跃记录数</h3><strong>{summary?.players_active_recent ?? '-'}</strong></article>
      </div>
    </section>
  )
}
