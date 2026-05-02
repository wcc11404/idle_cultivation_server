import { useEffect, useMemo, useState } from 'react'
import { confirmMails, listGrantItemOptions, previewMails } from '../services/api'

type AttachmentRow = {
  item_id: string
  count: number
}

type ItemOption = {
  item_id: string
  item_name: string
}

const EMPTY_ATTACHMENT: AttachmentRow = {
  item_id: '',
  count: 1,
}

export function GrantPage() {
  const [accountIds, setAccountIds] = useState('')
  const [allAccounts, setAllAccounts] = useState(false)
  const [mailTitle, setMailTitle] = useState('系统邮件')
  const [mailContent, setMailContent] = useState('这里填写邮件内容')
  const [attachments, setAttachments] = useState<AttachmentRow[]>([{ ...EMPTY_ATTACHMENT }])
  const [mailPreviewToken, setMailPreviewToken] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [itemOptions, setItemOptions] = useState<ItemOption[]>([])

  const parsedAccountIds = useMemo(
    () => accountIds.split(/[,\n]/).map((row) => row.trim()).filter(Boolean),
    [accountIds],
  )

  useEffect(() => {
    async function loadItemOptions() {
      try {
        const result = await listGrantItemOptions()
        setItemOptions(result.items ?? [])
        setAttachments((current) => {
          if (current.some((row) => row.item_id)) {
            return current
          }
          const first = result.items?.[0]?.item_id || ''
          return [{ item_id: first, count: 1 }]
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载附件物品失败')
      }
    }
    loadItemOptions()
  }, [])

  function updateAttachment(index: number, patch: Partial<AttachmentRow>) {
    setAttachments((current) => current.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)))
  }

  function addAttachmentRow() {
    setAttachments((current) => [
      ...current,
      { item_id: itemOptions[0]?.item_id || '', count: 1 },
    ])
  }

  function removeAttachmentRow(index: number) {
    setAttachments((current) => (current.length <= 1 ? current : current.filter((_, rowIndex) => rowIndex !== index)))
  }

  async function handleMailPreview() {
    setError('')
    const sanitizedAttachments = attachments
      .map((row) => ({ item_id: row.item_id, count: Number(row.count) }))
      .filter((row) => row.item_id && row.count > 0)
    try {
      const result = await previewMails({
        account_ids: parsedAccountIds,
        all_accounts: allAccounts,
        title: mailTitle,
        content: mailContent,
        attachments: sanitizedAttachments,
      })
      setMailPreviewToken(result.confirm_token)
      setMessage(`邮件预览成功，目标 ${result.preview.target_count} 人，附件 ${sanitizedAttachments.length} 项`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '邮件预览失败')
    }
  }

  async function handleMailConfirm() {
    setError('')
    try {
      const result = await confirmMails(mailPreviewToken)
      setMessage(`邮件发放完成：成功 ${result.reason_data.sent_count} 人`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '邮件发放失败')
    }
  }

  return (
    <section>
      <div className="page-header">
        <h1>发放中心</h1>
        <p>这里只允许发送带附件邮件，不允许直接把物品塞进玩家背包。</p>
      </div>
      {message ? <div className="success-box">{message}</div> : null}
      {error ? <div className="error-box">{error}</div> : null}
      <div className="panel form-grid">
        <label>
          目标账号ID
          <textarea rows={4} value={accountIds} onChange={(e) => setAccountIds(e.target.value)} placeholder="多个账号用逗号或换行分隔" />
        </label>
        <label className="checkbox-row">
          <input type="checkbox" checked={allAccounts} onChange={(e) => setAllAccounts(e.target.checked)} />
          全服所有玩家
        </label>
        <label>
          邮件标题
          <input value={mailTitle} onChange={(e) => setMailTitle(e.target.value)} />
        </label>
        <label>
          邮件正文
          <textarea rows={4} value={mailContent} onChange={(e) => setMailContent(e.target.value)} />
        </label>
      </div>
      <div className="panel form-grid">
        <div className="page-header compact">
          <h2>附件列表</h2>
          <button className="ghost" onClick={addAttachmentRow}>新增附件</button>
        </div>
        {attachments.map((row, index) => (
          <div key={index} className="attachment-row">
            <label>
              物品
              <select value={row.item_id} onChange={(e) => updateAttachment(index, { item_id: e.target.value })}>
                {itemOptions.map((option) => (
                  <option key={option.item_id} value={option.item_id}>
                    {option.item_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              数量
              <input type="number" min={1} value={row.count} onChange={(e) => updateAttachment(index, { count: Number(e.target.value) || 1 })} />
            </label>
            <button className="ghost" onClick={() => removeAttachmentRow(index)} disabled={attachments.length <= 1}>移除</button>
          </div>
        ))}
      </div>
      <div className="grant-grid">
        <div className="panel">
          <h2>邮件发放</h2>
          <div className="button-row">
            <button className="primary" onClick={handleMailPreview}>预览邮件</button>
            <button className="danger" onClick={handleMailConfirm} disabled={!mailPreviewToken}>确认发邮件</button>
          </div>
          <p className="muted">确认令牌：{mailPreviewToken || '尚未生成'}</p>
        </div>
      </div>
    </section>
  )
}
