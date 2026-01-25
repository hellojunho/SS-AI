import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'
import ProgressBar from '../components/ProgressBar'
import useProgress from '../hooks/useProgress'

type QuizItem = {
  id: number
  title: string
  question: string
  source_user_id: string
  created_at: string
}

const PAGE_SIZE = 10

type SortKey = 'id' | 'title' | 'source_user_id' | 'question' | 'created_at'

type SortConfig = {
  key: SortKey
  direction: 'asc' | 'desc'
}

const AdminQuizzesPage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [quizzes, setQuizzes] = useState<QuizItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [searchTitle, setSearchTitle] = useState('')
  const [searchUser, setSearchUser] = useState('')
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'id', direction: 'desc' })
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [mixingAll, setMixingAll] = useState(false)
  const [deduping, setDeduping] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [targetUserId, setTargetUserId] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generatingAll, setGeneratingAll] = useState(false)
  const [generateMessage, setGenerateMessage] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const { progress, visible, finish, setProgressValue } = useProgress()
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobType, setJobType] = useState<'single' | 'all' | null>(null)

  const statusUrl = useMemo(() => {
    if (!jobId) return null
    return `${API_BASE_URL}/quiz/admin/generate/status/${jobId}`
  }, [jobId])

  const fetchQuizzes = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/list`)
      if (!res.ok) throw new Error('퀴즈를 불러오지 못했습니다.')
      const data = (await res.json()) as QuizItem[]
      setQuizzes(data)
    } catch (err) {
      setError('퀴즈를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (status !== 'allowed') return
    fetchQuizzes()
  }, [status])

  useEffect(() => {
    if (!statusUrl || !jobType) return
    let cancelled = false
    const poll = async () => {
      try {
        const response = await authorizedFetch(statusUrl)
        if (!response.ok) {
          throw new Error('퀴즈 생성 상태를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as {
          status: 'pending' | 'running' | 'completed' | 'failed'
          progress: number
          result?: { created: number; failed: { user_id: string; reason: string }[] } | QuizItem
          error?: string
        }
        if (cancelled) return
        setProgressValue(data.progress ?? 0)
        if (data.status === 'completed') {
          if (jobType === 'single' && data.result) {
            const result = data.result as QuizItem
            setGenerateMessage(`사용자 ${result.source_user_id || '해당'} 대상 퀴즈를 생성했습니다.`)
            setTargetUserId('')
            fetchQuizzes()
          }
          if (jobType === 'all' && data.result) {
            const result = data.result as { created: number; failed: { user_id: string; reason: string }[] }
            const failedCount = result.failed?.length ?? 0
            setGenerateMessage(`전체 퀴즈 ${result.created}개 생성, 실패 ${failedCount}개`)
            fetchQuizzes()
          }
          setGenerating(false)
          setGeneratingAll(false)
          setJobId(null)
          setJobType(null)
          finish()
        }
        if (data.status === 'failed') {
          setGenerateError(data.error || '퀴즈를 생성하지 못했습니다.')
          setGenerating(false)
          setGeneratingAll(false)
          setJobId(null)
          setJobType(null)
          finish()
        }
      } catch (err) {
        if (cancelled) return
        setGenerateError('퀴즈 생성 상태를 불러오지 못했습니다.')
        setGenerating(false)
        setGeneratingAll(false)
        setJobId(null)
        setJobType(null)
        finish()
      }
    }
    poll()
    const intervalId = window.setInterval(poll, 1000)
    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [finish, jobType, setProgressValue, statusUrl])

  useEffect(() => {
    setPage(1)
  }, [sortConfig, searchTitle, searchUser])

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => (prev.key === key ? { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' } : { key, direction: 'asc' }))
  }

  const renderSortIndicator = (key: SortKey) => {
    if (sortConfig.key !== key) return null
    return sortConfig.direction === 'asc' ? '▲' : '▼'
  }

  const normalizeText = (value: string) => {
    if (!value) return value
    const stripped = value
      .replace(/```json\s*([\s\S]*?)```/gi, '$1')
      .replace(/```\s*([\s\S]*?)```/g, '$1')
    return stripped.trim()
  }

  const formatDate = (value: string) => {
    if (!value) return '-'
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return value
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} - ${pad(
      d.getHours()
    )}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  const truncateText = (value: string, length = 5) => {
    if (!value) return value
    if (value.length <= length) return value
    return value.slice(0, length) + ' ...'
  }

  const filtered = useMemo(() => {
    const titleQuery = searchTitle.trim().toLowerCase()
    const userQuery = searchUser.trim().toLowerCase()
    const filteredItems = quizzes.filter((quiz) => {
      const title = normalizeText(quiz.title).toLowerCase()
      const userId = (quiz.source_user_id || '').toLowerCase()
      const matchesTitle = titleQuery ? title.includes(titleQuery) : true
      const matchesUser = userQuery ? userId.includes(userQuery) : true
      return matchesTitle && matchesUser
    })
    const multiplier = sortConfig.direction === 'asc' ? 1 : -1
    const arr = [...filteredItems].sort((a, b) => {
      const key = sortConfig.key
      if (key === 'id') {
        const na = Number((a as any).id ?? 0)
        const nb = Number((b as any).id ?? 0)
        return (na - nb) * multiplier
      }
      if (key === 'created_at') {
        const da = new Date((a as any).created_at).getTime() || 0
        const db = new Date((b as any).created_at).getTime() || 0
        return (da - db) * multiplier
      }
      const valueA = normalizeText(String(a[sortConfig.key as keyof QuizItem] ?? ''))
      const valueB = normalizeText(String(b[sortConfig.key as keyof QuizItem] ?? ''))
      return valueA.localeCompare(valueB, 'ko', { sensitivity: 'base' }) * multiplier
    })
    return arr
  }, [quizzes, searchTitle, searchUser, sortConfig])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>퀴즈 대시보드</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>퀴즈 대시보드</h1>
        <p>접근 권한이 없습니다.</p>
        <button type="button" onClick={() => navigate('/')}>홈으로 이동</button>
      </section>
    )
  }

  console.log('quizzes:', quizzes);

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>이전</button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>홈</button>
      </div>
      <h1>퀴즈 대시보드</h1>
      <p>생성된 퀴즈 목록을 확인하고 특정 사용자의 퀴즈를 검토할 수 있습니다.</p>
      <AdminNav />

      <form
        className="card admin-actions"
        onSubmit={async (event) => {
          event.preventDefault()
          const trimmed = targetUserId.trim()
          if (!trimmed) {
            setGenerateError('사용자 아이디를 입력해주세요.')
            return
          }
          setProgressValue(0)
          setGenerating(true)
          setGenerateMessage(null)
          setGenerateError(null)
          try {
            const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/generate`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ user_id: trimmed }),
            })
            if (!res.ok) {
              const data = (await res.json().catch(() => null)) as { detail?: string } | null
              throw new Error(data?.detail || '퀴즈를 생성하지 못했습니다.')
            }
            const data = (await res.json()) as { job_id: string }
            setJobId(data.job_id)
            setJobType('single')
          } catch (err) {
            const message = err instanceof Error ? err.message : '퀴즈를 생성하지 못했습니다.'
            setGenerateError(message)
            setGenerating(false)
            finish()
          }
        }}
      >
        <div>
          <h3>퀴즈 생성</h3>
          <p className="helper-text">사용자 대화 기록으로 새로운 퀴즈를 생성합니다.</p>
        </div>
        <label className="label">
          사용자 ID
          <input
            value={targetUserId}
            onChange={(event) => setTargetUserId(event.target.value)}
            placeholder="사용자 아이디를 입력하세요"
          />
        </label>
        <div className="admin-actions-buttons">
          <button type="submit" disabled={generating || generatingAll}>
            {generating ? (
              <span className="button-with-spinner">
                <span className="spinner" aria-label="퀴즈 생성 중" />
                생성 중
              </span>
            ) : (
              '퀴즈 생성'
            )}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={async () => {
              setProgressValue(0)
              setGeneratingAll(true)
              setGenerateMessage(null)
              setGenerateError(null)
              try {
                const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/generate-all`, { method: 'POST' })
                if (!res.ok) {
                  const data = (await res.json().catch(() => null)) as { detail?: string } | null
                  throw new Error(data?.detail || '퀴즈를 생성하지 못했습니다.')
                }
                const data = (await res.json()) as { job_id: string }
                setJobId(data.job_id)
                setJobType('all')
              } catch (err) {
                const message = err instanceof Error ? err.message : '퀴즈를 생성하지 못했습니다.'
                setGenerateError(message)
                setGeneratingAll(false)
                finish()
              }
            }}
            disabled={generating || generatingAll}
          >
            {generatingAll ? (
              <span className="button-with-spinner">
                <span className="spinner" aria-label="전체 퀴즈 생성 중" />
                전체 생성 중
              </span>
            ) : (
              '전체 생성'
            )}
          </button>
        </div>
        {visible && <ProgressBar value={progress} label="퀴즈 생성 진행률" />}
        {generateMessage && <p className="helper-text">{generateMessage}</p>}
        {generateError && <p className="helper-text error-text">{generateError}</p>}
      </form>

      <div className="card admin-actions">
        <div>
          <h3>전체 관리</h3>
          <p className="helper-text">모든 퀴즈의 보기를 섞거나 유사 문항을 정리합니다.</p>
        </div>
        <div className="admin-actions-buttons">
          <button
            type="button"
            onClick={async () => {
              setMixingAll(true)
              setActionMessage(null)
              setError(null)
              try {
                const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/mix-all`, { method: 'POST' })
                if (!res.ok) throw new Error('mix-all 실패')
                const data = (await res.json()) as { mixed: number }
                setActionMessage(`모든 퀴즈 보기 ${data.mixed}개를 섞었습니다.`)
              } catch (err) {
                setError('전체 보기를 섞지 못했습니다.')
              } finally {
                setMixingAll(false)
              }
            }}
            disabled={mixingAll}
          >
            {mixingAll ? 'Mix All 진행 중...' : 'Mix All'}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={async () => {
              if (!confirm('모든 퀴즈에서 유사한 문제를 제거할까요?')) return
              setDeduping(true)
              setActionMessage(null)
              setError(null)
              try {
                const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/dedupe`, { method: 'POST' })
                if (!res.ok) throw new Error('dedupe 실패')
                const data = (await res.json()) as { removed: number; removed_ids: number[] }
                setQuizzes((prev) => prev.filter((item) => !data.removed_ids.includes(item.id)))
                setActionMessage(`중복/유사 문항 ${data.removed}개를 정리했습니다.`)
              } catch (err) {
                setError('중복 문항을 제거하지 못했습니다.')
              } finally {
                setDeduping(false)
              }
            }}
            disabled={deduping}
          >
            {deduping ? '중복 제거 중...' : '중복 제거'}
          </button>
          <button
            type="button"
            className="ghost"
            onClick={() => {
              fetchQuizzes()
              setActionMessage(null)
            }}
          >
            목록 새로고침
          </button>
        </div>
        {actionMessage && <p className="helper-text">{actionMessage}</p>}
      </div>

      <div className="card admin-filters">
        <label className="label">
          퀴즈 제목 검색
          <input
            value={searchTitle}
            onChange={(event) => setSearchTitle(event.target.value)}
            placeholder="퀴즈 제목을 입력하세요"
          />
        </label>
        <label className="label">
          생성 사용자 검색
          <input
            value={searchUser}
            onChange={(event) => setSearchUser(event.target.value)}
            placeholder="사용자 아이디를 입력하세요"
          />
        </label>
      </div>
      <label className="label" style={{ alignItems: 'flex-end' }}>
        <button type="button" onClick={() => {
          setSearchTitle('')
          setSearchUser('')
        }}>
          초기화
        </button>
      </label>

      <div className="admin-dashboard admin-compact">
        <div className="card admin-table">
          <div className="admin-table-row admin-table-header">
            <button type="button" className="admin-sort" onClick={() => handleSort('id')}>ID {renderSortIndicator('id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('title')}>제목 {renderSortIndicator('title')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('source_user_id')}>생성 사용자 {renderSortIndicator('source_user_id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('question')}>문항 {renderSortIndicator('question')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('created_at')}>생성일 {renderSortIndicator('created_at')}</button>
            <span>관리</span>
          </div>

          {loading ? (
            <div className="admin-table-empty">퀴즈 정보를 불러오는 중...</div>
          ) : paged.length === 0 ? (
            <div className="admin-table-empty">조건에 맞는 퀴즈가 없습니다.</div>
          ) : (
            paged.map((q, idx) => (
              <div key={q.id} className="admin-table-row">
                <span>{q.id}</span>
                <button type="button" className="link-button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>
                  {normalizeText(q.title)}
                </button>
                <span>{q.source_user_id || '-'}</span>
                <span>{truncateText(normalizeText(q.question))}</span>
                <span className="created-at">{formatDate(q.created_at)}</span>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>상세</button>
                </div>
              </div>
            ))
          )}

          {error && <p className="helper-text error-text">{error}</p>}
        </div>

        <div className="admin-pagination">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}>이전</button>
          <span>{currentPage} / {totalPages}</span>
          <button type="button" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>다음</button>
        </div>
      </div>
    </section>
  )
}

export default AdminQuizzesPage
