import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

type QuizItem = {
  id: number
  user_id: string
  created_at: string
  summary: string
  title: string | null
}

const PAGE_SIZE = 10

type SortKey = 'id' | 'user_id' | 'title' | 'created_at'

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
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'created_at', direction: 'desc' })

  useEffect(() => {
    if (status !== 'allowed') return
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await authorizedFetch(`${API_BASE_URL}/admin/quizzes`)
        if (!res.ok) throw new Error('퀴즈를 불러오지 못했습니다.')
        const data = (await res.json()) as QuizItem[]
        setQuizzes(data)
      } catch (err) {
        setError('퀴즈를 불러오지 못했습니다.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [status])

  useEffect(() => {
    setPage(1)
  }, [sortConfig])

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => (prev.key === key ? { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' } : { key, direction: 'asc' }))
  }

  const renderSortIndicator = (key: SortKey) => {
    if (sortConfig.key !== key) return null
    return sortConfig.direction === 'asc' ? '▲' : '▼'
  }

  const filtered = useMemo(() => {
    const multiplier = sortConfig.direction === 'asc' ? 1 : -1
    const arr = [...quizzes].sort((a, b) => {
      const va: any = a[sortConfig.key as keyof QuizItem] ?? ''
      const vb: any = b[sortConfig.key as keyof QuizItem] ?? ''
      if (sortConfig.key === 'created_at') {
        return (new Date(va).getTime() - new Date(vb).getTime()) * multiplier
      }
      return String(va).localeCompare(String(vb), 'ko', { sensitivity: 'base' }) * multiplier
    })
    return arr
  }, [quizzes, sortConfig])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const formatDate = (value: string) => {
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return value
    return d.toLocaleString('ko-KR')
  }

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

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>이전</button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>홈</button>
      </div>
      <h1>퀴즈 대시보드</h1>
      <p>생성된 퀴즈 목록을 확인하고 특정 사용자의 퀴즈를 검토할 수 있습니다.</p>
      <AdminNav />

      <div className="admin-dashboard admin-compact">
        <div className="card admin-table">
          <div className="admin-table-row admin-table-header">
            <span>INDEX</span>
            <button type="button" className="admin-sort" onClick={() => handleSort('id')}>ID {renderSortIndicator('id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('user_id')}>사용자 {renderSortIndicator('user_id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('title')}>제목 {renderSortIndicator('title')}</button>
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
                <span>{(currentPage - 1) * PAGE_SIZE + idx + 1}</span>
                <span>{q.id}</span>
                <span>{q.user_id}</span>
                <button type="button" className="link-button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>
                  {q.title ?? q.summary}
                </button>
                <span>{formatDate(q.created_at)}</span>
                <button type="button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>상세</button>
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
