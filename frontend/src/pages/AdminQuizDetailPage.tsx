import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

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

const AdminQuizDetailPage = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const status = useAdminStatus()
  const [quiz, setQuiz] = useState<AdminQuiz | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const quizId = useMemo(() => {
    if (!id) return null
    const parsed = Number(id)
    return Number.isNaN(parsed) ? null : parsed
  }, [id])

  const normalizeText = (value: string) => {
    if (!value) return value
    const stripped = value
      .replace(/```json\s*([\s\S]*?)```/gi, '$1')
      .replace(/```\s*([\s\S]*?)```/g, '$1')
    return stripped.trim()
  }

  const formatReference = (value: string) => {
    const normalized = normalizeText(value)
    if (!normalized.trim()) return null
    const urlRegex = /(https?:\/\/[^\s]+)/g
    const parts = normalized.split(urlRegex)
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

  useEffect(() => {
    if (status !== 'allowed' || quizId === null) return
    const loadQuiz = async () => {
      setLoading(true)
      setErrorMessage(null)
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/quiz/admin/list`)
        if (!response.ok) {
          throw new Error('퀴즈를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as AdminQuiz[]
        const selected = data.find((item) => item.id === quizId) ?? null
        if (!selected) {
          setErrorMessage('해당 퀴즈를 찾을 수 없습니다.')
        }
        setQuiz(selected)
      } catch (error) {
        setErrorMessage('퀴즈를 불러오지 못했습니다.')
      } finally {
        setLoading(false)
      }
    }
    loadQuiz()
  }, [quizId, status])

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>퀴즈 상세</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>퀴즈 상세</h1>
        <p>접근 권한이 없습니다.</p>
        <button type="button" onClick={() => navigate('/')}>홈으로 이동</button>
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
      <h1>퀴즈 상세</h1>
      <p>선택한 퀴즈의 세부 정보를 확인할 수 있습니다.</p>
      <AdminNav />
      {loading && <div className="card">퀴즈 정보를 불러오는 중...</div>}
      {!loading && errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      {!loading && quiz && (
        <div className="card">
          <div className="quiz-header">
            <h2>{normalizeText(quiz.title)}</h2>
            <span className="sticker">생성 대상: {quiz.source_user_id || '-'}</span>
            <div style={{ marginLeft: 'auto' }}>
              <button
                type="button"
                onClick={async () => {
                  if (!quiz) return
                  if (!confirm('이 퀴즈를 삭제하시겠습니까?')) return
                  setDeleting(true)
                  try {
                    const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/${quiz.id}`, { method: 'DELETE' })
                    if (!res.ok) {
                      throw new Error('삭제 실패')
                    }
                    navigate('/admin/quizzes')
                  } catch (err) {
                    setErrorMessage('퀴즈를 삭제하지 못했습니다.')
                  } finally {
                    setDeleting(false)
                  }
                }}
                disabled={deleting}
              >
                {deleting ? '삭제 중...' : '삭제'}
              </button>
            </div>
          </div>
          <div className="quiz-question">
            <div className="quiz-index">
              <span className="quiz-index-label">Q1</span>
            </div>
            <p className="question">Q1. {normalizeText(quiz.question)}</p>
          </div>
          <ol className="quiz-options">
            {quiz.choices.map((choice, index) => (
              <li key={`${choice}-${index}`}>
                <div className="quiz-option">
                  <span className="option-index">{index + 1}.</span>
                  <span>{normalizeText(choice)}</span>
                </div>
              </li>
            ))}
          </ol>
          <div className="quiz-reference">
            <span className="quiz-reference-label">정답</span>
            <li><p className="quiz-reference-content">{normalizeText(quiz.correct)}</p></li>
          </div>
          <div className="quiz-reference">
            <span className="quiz-reference-label">오답 보기</span>
            <ul className="quiz-reference-content">
              {quiz.wrong.map((choice, index) => (
                <li key={`${choice}-${index}`}>{normalizeText(choice)}</li>
              ))}
            </ul>
          </div>
          {normalizeText(quiz.explanation) && (
            <div className="quiz-reference">
              <span className="quiz-reference-label">해설</span>
              <p className="quiz-reference-content">{normalizeText(quiz.explanation)}</p>
            </div>
          )}
          {normalizeText(quiz.reference) && (
            <div className="quiz-reference">
              <span className="quiz-reference-label">참고자료</span>
              <p className="quiz-reference-content">{formatReference(quiz.reference)}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default AdminQuizDetailPage
