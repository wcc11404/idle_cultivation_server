import { useEffect, useState } from 'react'
import { banPlayer, getPlayer, kickPlayer, listPlayers, unbanPlayer } from '../services/api'

export function PlayersPage() {
  const [query, setQuery] = useState('')
  const [players, setPlayers] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [error, setError] = useState('')

  function formatShanghaiTime(value: string | null | undefined) {
    if (!value) return '-'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return new Intl.DateTimeFormat('zh-CN', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date).replace(/\//g, '-')
  }

  async function loadPlayers() {
    try {
      const result = await listPlayers(query)
      setPlayers(result.items ?? [])
      if ((result.items ?? []).length > 0 && !selected) {
        handleSelect(result.items[0].account_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    }
  }

  async function handleSelect(accountId: string) {
    try {
      const result = await getPlayer(accountId)
      setSelected(result.player)
    } catch (err) {
      setError(err instanceof Error ? err.message : '详情加载失败')
    }
  }

  async function runAction(action: 'ban' | 'unban' | 'kick') {
    if (!selected) return
    try {
      if (action === 'ban') await banPlayer(selected.account_id)
      if (action === 'unban') await unbanPlayer(selected.account_id)
      if (action === 'kick') await kickPlayer(selected.account_id)
      await loadPlayers()
      await handleSelect(selected.account_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    }
  }

  useEffect(() => {
    loadPlayers()
  }, [])

  return (
    <section className="players-layout">
      <div className="panel">
        <div className="page-header compact">
          <h1>玩家管理</h1>
        </div>
        <div className="toolbar">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="按用户名或昵称搜索" />
          <button className="primary" onClick={loadPlayers}>搜索</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>用户名</th><th>昵称</th><th>注册时间</th><th>境界</th><th>封禁</th></tr></thead>
            <tbody>
              {players.map((player) => (
                <tr key={player.account_id} onClick={() => handleSelect(player.account_id)}>
                  <td>{player.username}</td>
                  <td>{player.nickname || '-'}</td>
                  <td>{formatShanghaiTime(player.created_at)}</td>
                  <td>{player.realm || '-'} {player.realm_level || ''}</td>
                  <td>{player.is_banned ? '是' : '否'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="panel">
        <div className="page-header compact"><h1>玩家详情</h1></div>
        {error ? <div className="error-box">{error}</div> : null}
        {selected ? (
          <>
            <dl className="detail-grid">
              <div><dt>账号ID</dt><dd>{selected.account_id}</dd></div>
              <div><dt>用户名</dt><dd>{selected.username}</dd></div>
              <div><dt>昵称</dt><dd>{selected.nickname || '-'}</dd></div>
              <div><dt>区服</dt><dd>{selected.server_id}</dd></div>
              <div><dt>注册时间</dt><dd>{formatShanghaiTime(selected.created_at)}</dd></div>
              <div><dt>封禁</dt><dd>{selected.is_banned ? '是' : '否'}</dd></div>
              <div><dt>最近在线</dt><dd>{formatShanghaiTime(selected.last_online_at)}</dd></div>
              <div><dt>境界</dt><dd>{selected.summary?.realm || '-'} {selected.summary?.realm_level || ''}</dd></div>
            </dl>
            <div className="button-row">
              <button className="danger" onClick={() => runAction('ban')}>封禁</button>
              <button className="ghost" onClick={() => runAction('unban')}>解封</button>
              <button className="ghost" onClick={() => runAction('kick')}>强制下线</button>
            </div>
          </>
        ) : <p className="muted">请选择一名玩家。</p>}
      </div>
    </section>
  )
}
