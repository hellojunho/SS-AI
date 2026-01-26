import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

type LlmUsageResponse = {
  provider: string
  model: string
  total_tokens: number
  used_tokens: number
  remaining_tokens: number
  prompt_tokens: number
  completion_tokens: number
  last_updated: string | null
}

const AdminLlmTokensPage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [usage, setUsage] = useState<LlmUsageResponse | null>(null)
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const loadUsage = async () => {
    setIsLoading(true)
    setMessage('')
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/admin/llm/usage`)
      if (!response.ok) {
        throw new Error('LLM 토큰 정보를 불러오지 못했습니다.')
      }
      const data = (await response.json()) as LlmUsageResponse
      setUsage(data)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'LLM 토큰 정보를 불러오지 못했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (status !== 'allowed') return
    loadUsage()
  }, [status])

  const formatTokens = (value: number) => value.toLocaleString('ko-KR')

  const usagePercent = useMemo(() => {
    if (!usage || usage.total_tokens <= 0) return 0
    return Math.min(Math.round((usage.used_tokens / usage.total_tokens) * 100), 100)
  }, [usage])

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>LLM 토큰 대시보드</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>LLM 토큰 대시보드</h1>
        <p>접근 권한이 없습니다.</p>
        <button type="button" onClick={() => navigate('/')}>
          홈으로 이동
        </button>
      </section>
    )
  }

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>
          이전
        </button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>
          홈
        </button>
      </div>
      <h1>LLM 토큰 대시보드</h1>
      <p>현재 연결된 LLM 토큰 사용량을 확인할 수 있습니다.</p>
      <AdminNav />

      <div className="card admin-token-summary">
        <div>
          <span className="admin-token-label">현재 연결된 LLM</span>
          <h2>{usage ? `${usage.provider} · ${usage.model}` : '불러오는 중'}</h2>
        </div>
        <div className="admin-token-actions">
          <button type="button" onClick={loadUsage} disabled={isLoading}>
            {isLoading ? '불러오는 중' : '새로고침'}
          </button>
          {message && <span className="admin-token-message">{message}</span>}
        </div>
      </div>

      <div className="admin-token-grid">
        <div className="card admin-token-card">
          <span className="admin-token-label">사용량</span>
          <strong className="admin-token-value">
            {usage ? formatTokens(usage.used_tokens) : '-'}
          </strong>
          <span className="admin-token-sub">누적 사용 토큰</span>
        </div>
        <div className="card admin-token-card">
          <span className="admin-token-label">잔여량</span>
          <strong className="admin-token-value">
            {usage ? formatTokens(usage.remaining_tokens) : '-'}
          </strong>
          <span className="admin-token-sub">남은 사용 가능 토큰</span>
        </div>
        <div className="card admin-token-card">
          <span className="admin-token-label">총 토큰</span>
          <strong className="admin-token-value">
            {usage ? formatTokens(usage.total_tokens) : '-'}
          </strong>
          <span className="admin-token-sub">전체 사용 가능한 토큰</span>
        </div>
      </div>

      <div className="card admin-token-bar">
        <div className="admin-token-bar-header">
          <span>토큰 사용률</span>
          <span>{usage ? `${usagePercent}%` : '-'}</span>
        </div>
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: `${usagePercent}%` }} />
        </div>
        <div className="admin-token-breakdown">
          <div>
            <span className="admin-token-label">프롬프트</span>
            <strong>{usage ? formatTokens(usage.prompt_tokens) : '-'}</strong>
          </div>
          <div>
            <span className="admin-token-label">응답</span>
            <strong>{usage ? formatTokens(usage.completion_tokens) : '-'}</strong>
          </div>
          <div>
            <span className="admin-token-label">업데이트</span>
            <strong>
              {usage?.last_updated
                ? new Date(usage.last_updated).toLocaleString('ko-KR')
                : '업데이트 기록 없음'}
            </strong>
          </div>
        </div>
      </div>
    </section>
  )
}

export default AdminLlmTokensPage
