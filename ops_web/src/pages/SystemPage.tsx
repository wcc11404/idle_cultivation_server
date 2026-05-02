import { useEffect, useState } from 'react'
import { kickAllPlayers, listWhitelist, updateLoginGate, updateWhitelist } from '../services/api'

export function SystemPage() {
  const [enabled, setEnabled] = useState(false)
  const [accountId, setAccountId] = useState('')
  const [note, setNote] = useState('')
  const [items, setItems] = useState<any[]>([])
  const [message, setMessage] = useState('')

  async function loadWhitelist() {
    const result = await listWhitelist()
    setItems(result.items ?? [])
  }

  useEffect(() => {
    loadWhitelist()
  }, [])

  async function handleGate() {
    const result = await updateLoginGate(enabled, note)
    setMessage(`登录闸门已更新：${result.reason_data.login_gate_enabled ? '开启' : '关闭'}`)
  }

  async function handleWhitelistAdd() {
    const result = await updateWhitelist('add', accountId, note)
    setMessage(result.reason_code)
    await loadWhitelist()
  }

  async function handleWhitelistRemove(targetAccountId: string) {
    const result = await updateWhitelist('remove', targetAccountId)
    setMessage(result.reason_code)
    await loadWhitelist()
  }

  async function handleKickAll() {
    const result = await kickAllPlayers(note)
    setMessage(`全部踢下线完成：影响 ${result.reason_data.affected_count} 个账号`)
  }

  return (
    <section>
      <div className="page-header">
        <h1>系统维护</h1>
        <p>这里是一期开高危系统入口的地方，先把登录闸门和白名单打稳。</p>
      </div>
      {message ? <div className="success-box">{message}</div> : null}
      <div className="panel form-grid">
        <label className="checkbox-row">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          开启禁止登录
        </label>
        <label>
          备注
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="维护说明或操作备注" />
        </label>
        <button className="danger" onClick={handleGate}>更新登录闸门</button>
      </div>
      <div className="panel form-grid">
        <h2>全服踢下线</h2>
        <p className="muted">会统一提升所有玩家账号的 token_version，使现有玩家登录态全部失效。</p>
        <label>
          备注
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="例如：发版维护、热更新清场" />
        </label>
        <button className="danger" onClick={handleKickAll}>全部踢下线</button>
      </div>
      <div className="panel form-grid">
        <h2>白名单管理</h2>
        <label>
          账号ID / 用户名
          <input value={accountId} onChange={(e) => setAccountId(e.target.value)} placeholder="例如 test2 或 7b1291a7-..." />
        </label>
        <label>
          备注
          <input value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <button className="primary" onClick={handleWhitelistAdd}>加入白名单</button>
      </div>
      <div className="panel table-wrap">
        <table>
          <thead><tr><th>账号ID</th><th>用户名快照</th><th>备注</th><th>操作</th></tr></thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.account_id}</td>
                <td>{item.account_username_snapshot || '-'}</td>
                <td>{item.note || '-'}</td>
                <td><button className="ghost" onClick={() => handleWhitelistRemove(item.account_id)}>移除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
