import { useEffect, useState } from 'react'
import { listAudit } from '../services/api'

export function AuditPage() {
  const [items, setItems] = useState<any[]>([])
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

  useEffect(() => {
    listAudit()
      .then((result) => setItems(result.items ?? []))
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [])

  return (
    <section>
      <div className="page-header">
        <h1>审计日志</h1>
        <p>所有写操作都应在这里可追溯。</p>
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="panel table-wrap">
        <table>
          <thead>
            <tr><th>时间</th><th>操作者</th><th>动作</th><th>结果</th><th>原因码</th></tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{formatShanghaiTime(item.created_at)}</td>
                <td>{item.operator_username || '-'}</td>
                <td>{item.action_type}</td>
                <td>{item.result}</td>
                <td>{item.reason_code || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
