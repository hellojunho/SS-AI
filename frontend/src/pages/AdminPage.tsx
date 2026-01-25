import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type UserInfo = {
  role: string
}

type AdminQuiz = {
  id: number
  title: string
  question: string
  choices: string[]
  correct: string
  wrong: string[]
  explanation: string
  reference: string
  source_user_id: string
}

type AdminUser = {
  id: number
  user_id: string
  user_name: string
  email: string
  role: string
  created_at: string
  last_logined: string | null
}

const AdminPage = () => {
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'allowed' | 'forbidden'>('loading')
  const [targetUserId, setTargetUserId] = useState('')
  const [quiz, setQuiz] = useState<AdminQuiz | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/me`)
        if (!response.ok) {
          throw new Error('사용자 정보를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as UserInfo
        if (data.role === 'admin') {
          setStatus('allowed')
          await loadUsers()
        } else {
          setStatus('forbidden')
        }
      } catch (error) {
        setStatus('forbidden')
      }
    }
    loadUser()
  }, [])

  const loadUsers = async () => {
    setUsersLoading(true)
    setUsersError(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users`)
      if (!response.ok) {
        throw new Error('사용자 정보를 불러오지 못했습니다.')
      }
      const data = (await response.json()) as AdminUser[]
      setUsers(data)
    } catch (error) {
      setUsersError('사용자 정보를 불러오지 못했습니다.')
    } finally {
      setUsersLoading(false)
    }
  }

  const handleUserChange = (
    userId: number,
    field: keyof Pick<AdminUser, 'user_name' | 'email' | 'role'>,
    value: string,
  ) => {
    setUsers((prev) =>
      prev.map((user) => (user.id === userId ? { ...user, [field]: value } : user)),
    )
  }

  const handleUserSave = async (user: AdminUser) => {
    setUpdatingUserId(user.id)
    setUsersError(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: user.user_name,
          email: user.email,
          role: user.role,
        }),
      })
      if (!response.ok) {
        throw new Error('사용자 정보를 수정하지 못했습니다.')
      }
      const updated = (await response.json()) as AdminUser
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    } catch (error) {
      setUsersError('사용자 정보를 수정하지 못했습니다. 입력값을 확인해주세요.')
    } finally {
      setUpdatingUserId(null)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!targetUserId) return
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/admin/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: targetUserId }),
      })
      if (!response.ok) {
        throw new Error('퀴즈를 생성하지 못했습니다.')
      }
      const data = (await response.json()) as AdminQuiz
      setQuiz(data)
    } catch (error) {
      setQuiz(null)
      setErrorMessage('퀴즈를 생성하지 못했습니다. 사용자 아이디를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (value: string | null) => {
    if (!value) return '-'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('ko-KR')
  }

  const renderReference = (reference: string) => {
    if (!reference.trim()) return null
    const urlRegex = /(https?:\/\/[^\s]+)/g
    const parts = reference.split(urlRegex)
    return parts.map((part, index) => {
      if (/^https?:\/\//.test(part)) {
        return (
          <a key={`${part}-${index}`} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        )
      }
      return <span key={`${part}-${index}`}>{part}</span>
    })
  }

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>관리자 페이지</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>관리자 페이지</h1>
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
          🏠
        </button>
      </div>
      <h1>관리자 퀴즈 생성</h1>
      <p>사용자 대화 기록을 기반으로 퀴즈를 생성합니다.</p>
      <form className="card" onSubmit={handleSubmit}>
        <label className="label">
          사용자 ID
          <input
            value={targetUserId}
            onChange={(event) => setTargetUserId(event.target.value)}
            placeholder="사용자 아이디를 입력하세요"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? (
            <span className="button-with-spinner">
              <span className="spinner" aria-label="퀴즈 생성 중" />
              생성 중
            </span>
          ) : (
            '퀴즈 생성'
          )}
        </button>
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      </form>
      <div className="admin-dashboard">
        <h2>사용자 대시보드</h2>
        <p className="helper-text">
          전체 사용자 정보를 확인하고 역할이나 기본 정보를 수정할 수 있습니다.
        </p>
        <div className="card admin-table">
          <div className="admin-table-row admin-table-header">
            <span>ID</span>
            <span>이름</span>
            <span>이메일</span>
            <span>역할</span>
            <span>가입일</span>
            <span>마지막 로그인</span>
            <span>관리</span>
          </div>
          {usersLoading ? (
            <div className="admin-table-empty">사용자 정보를 불러오는 중...</div>
          ) : users.length === 0 ? (
            <div className="admin-table-empty">등록된 사용자가 없습니다.</div>
          ) : (
            users.map((user) => (
              <div key={user.id} className="admin-table-row">
                <span>{user.user_id}</span>
                <input
                  value={user.user_name}
                  onChange={(event) => handleUserChange(user.id, 'user_name', event.target.value)}
                />
                <input
                  value={user.email}
                  onChange={(event) => handleUserChange(user.id, 'email', event.target.value)}
                />
                <select
                  value={user.role}
                  onChange={(event) => handleUserChange(user.id, 'role', event.target.value)}
                >
                  <option value="general">general</option>
                  <option value="admin">admin</option>
                </select>
                <span>{formatDate(user.created_at)}</span>
                <span>{formatDate(user.last_logined)}</span>
                <button
                  type="button"
                  onClick={() => handleUserSave(user)}
                  disabled={updatingUserId === user.id}
                >
                  {updatingUserId === user.id ? (
                    <span className="button-with-spinner">
                      <span className="spinner" aria-label="사용자 업데이트 중" />
                      저장 중
                    </span>
                  ) : (
                    '저장'
                  )}
                </button>
              </div>
            ))
          )}
          {usersError && <p className="helper-text error-text">{usersError}</p>}
        </div>
      </div>
      {quiz && (
        <div className="card">
          <div className="quiz-header">
            <h2>{quiz.title}</h2>
            <span className="sticker">생성 대상: {quiz.source_user_id}</span>
          </div>
          <div className="quiz-question">
            <div className="quiz-index">
              <span className="quiz-index-label">Q1</span>
            </div>
            <p className="question">Q1. {quiz.question}</p>
          </div>
          <ol className="quiz-options">
            {quiz.choices.map((choice, index) => (
              <li key={`${choice}-${index}`}>
                <div className="quiz-option">
                  <span className="option-index">{index + 1}.</span>
                  <span>{choice}</span>
                </div>
              </li>
            ))}
          </ol>
          <div className="quiz-reference">
            <span className="quiz-reference-label">정답</span>
            <p className="quiz-reference-content">{quiz.correct}</p>
          </div>
          <div className="quiz-reference">
            <span className="quiz-reference-label">오답 보기</span>
            <ul className="quiz-reference-content">
              {quiz.wrong.map((choice, index) => (
                <li key={`${choice}-${index}`}>{choice}</li>
              ))}
            </ul>
          </div>
          {quiz.explanation && (
            <div className="quiz-reference">
              <span className="quiz-reference-label">해설</span>
              <p className="quiz-reference-content">{quiz.explanation}</p>
            </div>
          )}
          {quiz.reference && (
            <div className="quiz-reference">
              <span className="quiz-reference-label">참고자료</span>
              <p className="quiz-reference-content">{renderReference(quiz.reference)}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default AdminPage
