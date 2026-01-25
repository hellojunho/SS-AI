import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

type QuizItem = {
  id: number
  title: string
  question: string
  source_user_id: string
}

const PAGE_SIZE = 10

type SortKey = 'id' | 'title' | 'source_user_id' | 'question'

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

  useEffect(() => {
    if (status !== 'allowed') return
    const load = async () => {
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
    load()
  }, [status])

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
        // numeric sort for id
        const na = Number((a as any).id ?? 0)
        const nb = Number((b as any).id ?? 0)
        return (na - nb) * multiplier
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

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>이전</button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>홈</button>
      </div>
      <h1>퀴즈 대시보드</h1>
      <p>생성된 퀴즈 목록을 확인하고 특정 사용자의 퀴즈를 검토할 수 있습니다.</p>
      <AdminNav />

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
            <span>INDEX</span>
            <button type="button" className="admin-sort" onClick={() => handleSort('id')}>ID {renderSortIndicator('id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('title')}>제목 {renderSortIndicator('title')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('source_user_id')}>생성 사용자 {renderSortIndicator('source_user_id')}</button>
            <button type="button" className="admin-sort" onClick={() => handleSort('question')}>문항 {renderSortIndicator('question')}</button>
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
                <button type="button" className="link-button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>
                  {normalizeText(q.title)}
                </button>
                <span>{q.source_user_id || '-'}</span>
                <span>{normalizeText(q.question)}</span>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={() => navigate(`/admin/quizzes/${q.id}`)}>상세</button>
                  <button
                    type="button"
                    onClick={async () => {
                      if (!confirm('이 퀴즈를 삭제하시겠습니까?')) return
                      setDeletingId(q.id)
                      try {
                        const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/${q.id}`, { method: 'DELETE' })
                        if (!res.ok) throw new Error('삭제 실패')
                        setQuizzes((prev) => prev.filter((it) => it.id !== q.id))
                      } catch (err) {
                        setError('퀴즈를 삭제하지 못했습니다.')
                      } finally {
                        setDeletingId(null)
                      }
                    }}
                    disabled={deletingId === q.id}
                  >
                    {deletingId === q.id ? '삭제 중...' : '삭제'}
                  </button>
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
