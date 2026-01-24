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

const AdminPage = () => {
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'allowed' | 'forbidden'>('loading')
  const [targetUserId, setTargetUserId] = useState('')
  const [quiz, setQuiz] = useState<AdminQuiz | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

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
        } else {
          setStatus('forbidden')
        }
      } catch (error) {
        setStatus('forbidden')
      }
    }
    loadUser()
  }, [])

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
          {loading ? '생성 중' : '퀴즈 생성'}
        </button>
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      </form>
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
