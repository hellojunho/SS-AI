import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { ensureAccessToken } from '../auth'

type Quiz = {
  id: number
  title: string
  question: string
  choices: string[]
  correct: string
  wrong: string[]
  explanation: string
  reference: string
  has_correct_attempt: boolean
  has_wrong_attempt: boolean
  answer_history: string[]
  tried_at: string | null
  solved_at: string | null
}

const QuizPage = () => {
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [adminTarget, setAdminTarget] = useState('')
  const [quizzesList, setQuizzesList] = useState<Quiz[]>([])
  const [listIndex, setListIndex] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [answerStatus, setAnswerStatus] = useState<'correct' | 'wrong' | null>(null)
  const [activeModal, setActiveModal] = useState<'correct' | 'wrong' | 'finished' | null>(null)
  const [finishedMessage, setFinishedMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadQuiz = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/latest`)
      if (!response.ok) {
        throw new Error('퀴즈를 가져오지 못했습니다.')
      }
      const data = await response.json()
      setQuiz(data)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
    } catch (error) {
      setQuiz(null)
      setErrorMessage('퀴즈를 가져오지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async (selectedAnswer: string) => {
    if (!quiz) return
    setSubmitting(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/${quiz.id}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer: selectedAnswer }),
      })
      if (!response.ok) {
        throw new Error('답안을 제출하지 못했습니다.')
      }
      const data = await response.json()
      setQuiz((prev) =>
        prev
          ? {
              ...prev,
              has_correct_attempt: data.has_correct_attempt,
              has_wrong_attempt: data.has_wrong_attempt,
              answer_history: data.answer_history,
              tried_at: data.tried_at,
              solved_at: data.solved_at,
            }
          : prev,
      )
      if (data.is_correct) {
        setAnswerStatus('correct')
        setActiveModal('correct')
      } else {
        setAnswerStatus('wrong')
        setActiveModal('wrong')
      }
    } catch (error) {
      setErrorMessage('답안을 제출하지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleChoiceClick = (choice: string) => {
    if (submitting || activeModal) return
    submitAnswer(choice)
  }

  useEffect(() => {
    ;(async () => {
      try {
        const token = await ensureAccessToken()
        if (!token) return
        const resp = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!resp.ok) return
        const data = await resp.json()
        setIsAdmin(data.role === 'admin')
      } catch {
        // ignore
      }
    })()
  }, [])

  const handlePrevQuiz = async () => {
    if (!quiz) return
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/prev?current_id=${quiz.id}`)
      if (!response.ok) {
        setErrorMessage('이전 문제를 불러오지 못했습니다.')
        return
      }
      const data = await response.json()
      setQuiz(data)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
    } catch (error) {
      setErrorMessage('이전 문제를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleNextQuiz = async () => {
    if (!quiz) return
    // Admin viewing list: navigate local list
    if (isAdmin && quizzesList.length > 0 && listIndex !== null) {
      const nxt = listIndex + 1
      if (nxt >= quizzesList.length) {
        setFinishedMessage('끝입니다. 더 이상 불러올 퀴즈가 없습니다.')
        setActiveModal('finished')
        return
      }
      setListIndex(nxt)
      setQuiz(quizzesList[nxt])
      setAnswerStatus(null)
      setActiveModal(null)
      return
    }

    // Normal user: request next from server
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/next?current_id=${quiz.id}`)
      if (!response.ok) {
        setFinishedMessage('오늘의 문제를 모두 풀었어요! 홈으로 이동합니다.')
        setActiveModal('finished')
        return
      }
      const data = await response.json()
      setQuiz(data)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
    } catch (error) {
      setErrorMessage('다음 문제를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    setAnswerStatus(null)
    setActiveModal(null)
  }

  const handleCloseModal = () => {
    setActiveModal(null)
  }

  const handleFinish = () => {
    setActiveModal(null)
    navigate('/')
  }

  const stickerText = quiz?.has_correct_attempt
    ? '전에 맞힌 문제에요!'
    : quiz?.has_wrong_attempt
      ? '전에 틀린 문제에요!'
      : null
  const stickerClass = quiz?.has_correct_attempt
    ? 'sticker sticker-success'
    : quiz?.has_wrong_attempt
      ? 'sticker sticker-danger'
      : ''

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
      <h1>Quiz</h1>
      <p>요약된 대화를 바탕으로 퀴즈를 풀어보세요.</p>
      <div className="card">
        {!isAdmin ? (
          <button type="button" onClick={loadQuiz} disabled={loading}>
            {loading ? (
              <span className="button-with-spinner">
                <span className="spinner" />
                불러오는 중
              </span>
            ) : (
              '퀴즈 불러오기'
            )}
          </button>
        ) : (
          <div className="admin-generate">
            <input
              type="text"
              placeholder="사용자 아이디 또는 all"
              value={adminTarget}
              onChange={(e) => setAdminTarget(e.target.value)}
            />
            &nbsp;
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                setErrorMessage(null)
                try {
                  const token = await ensureAccessToken()
                  if (!token) throw new Error('로그인이 필요합니다.')
                  if (adminTarget.trim().toLowerCase() === 'all') {
                    const resp = await fetch(`${API_BASE_URL}/quiz/admin/generate-all`, {
                      method: 'POST',
                      headers: { Authorization: `Bearer ${token}` },
                    })
                    if (!resp.ok) throw new Error('생성 실패')
                    const data = await resp.json()
                    setFinishedMessage(`생성 완료: ${data.created}개, 실패: ${data.failed.length}개`)
                  } else {
                    const resp = await fetch(`${API_BASE_URL}/quiz/admin/generate`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                      body: JSON.stringify({ user_id: adminTarget }),
                    })
                    if (!resp.ok) throw new Error('생성 실패')
                    const data = await resp.json()
                    setFinishedMessage(`생성 완료: ${data.id} (사용자: ${data.source_user_id})`)
                  }
                } catch (error) {
                  setErrorMessage('생성 중 오류가 발생했습니다.')
                } finally {
                  setLoading(false)
                }
              }}
            >
              {loading ? '생성중...' : '퀴즈 생성하기'}
            </button>
            &nbsp;
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                setErrorMessage(null)
                try {
                  const token = await ensureAccessToken()
                  if (!token) throw new Error('로그인이 필요합니다.')
                  const resp = await fetch(`${API_BASE_URL}/quiz/admin/list`, {
                    headers: { Authorization: `Bearer ${token}` },
                  })
                  if (!resp.ok) throw new Error('불러오기 실패')
                  const data = await resp.json()
                  if (Array.isArray(data) && data.length > 0) {
                    setQuizzesList(data)
                    setListIndex(0)
                    setQuiz(data[0])
                  } else {
                    setFinishedMessage('불러온 퀴즈가 없습니다.')
                  }
                } catch (error) {
                  setErrorMessage('퀴즈 목록을 불러오지 못했습니다.')
                } finally {
                  setLoading(false)
                }
              }}
            >
              모든 퀴즈 불러오기
            </button>
          </div>
        )}
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
        {finishedMessage && <p className="helper-text">{finishedMessage}</p>}
      </div>
      {quiz && (
        <div className="card">
          <div className="quiz-header">
            <h2>{quiz.title}</h2>
            {stickerText && <span className={stickerClass}>{stickerText}</span>}
          </div>
          <div className="quiz-question">
            <div className="quiz-index">
              <span className="quiz-index-label">Q1</span>
              {answerStatus && (
                <span className={`quiz-index-mark ${answerStatus}`}>
                  {answerStatus === 'correct' ? 'O' : 'X'}
                </span>
              )}
            </div>
            <p className="question">Q1. {quiz.question}</p>
          </div>
          <ol className="quiz-options">
            {quiz.choices.map((choice, index) => (
              <li key={`${choice}-${index}`}>
                <button
                  type="button"
                  className="quiz-option"
                  onClick={() => handleChoiceClick(choice)}
                  disabled={submitting}
                >
                  <span className="option-index">{index + 1}.</span>
                  <span>{choice}</span>
                </button>
              </li>
            ))}
          </ol>
          <div className="quiz-footer">
            {isAdmin && quizzesList.length > 0 ? (
              <>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    if (listIndex === null) return
                    const prev = listIndex - 1
                    if (prev < 0) return
                    setListIndex(prev)
                    setQuiz(quizzesList[prev])
                  }}
                  disabled={loading}
                >
                  이전 문제
                </button>
                &nbsp;
                <button
                  type="button"
                  onClick={() => {
                    if (listIndex === null) return
                    const nxt = listIndex + 1
                    if (nxt >= quizzesList.length) return
                    setListIndex(nxt)
                    setQuiz(quizzesList[nxt])
                  }}
                >
                  다음 문제
                </button>
              </>
            ) : (
              <button type="button" className="secondary" onClick={handlePrevQuiz} disabled={loading}>
                이전 문제
              </button>
            )}
          </div>
          {quiz.explanation && (
            <div className="quiz-explanation">
              <span className="quiz-explanation-label">해설</span>
              <p className="quiz-explanation-content">{quiz.explanation}</p>
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
      {activeModal === 'correct' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>정답입니다!</h3>
            <p>정답을 맞혔어요. 다음 문제를 풀어볼까요?</p>
            <div className="modal-actions">
              <button type="button" className="secondary" onClick={handleCloseModal}>
                닫기
              </button>
              <button type="button" onClick={handleNextQuiz} disabled={loading}>
                {loading ? (
                  <span className="button-with-spinner">
                    <span className="spinner" />
                    불러오는 중
                  </span>
                ) : (
                  '다음 문제'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      {activeModal === 'wrong' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>틀렸습니다!</h3>
            <p>다시 한 번 도전해볼까요?</p>
            <div className="modal-actions">
              <button type="button" className="secondary" onClick={handleCloseModal}>
                닫기
              </button>
              <button type="button" onClick={handleRetry}>
                다시 풀기
              </button>
            </div>
          </div>
        </div>
      )}
      {activeModal === 'finished' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>모두 완료!</h3>
            <p>{finishedMessage}</p>
            <div className="modal-actions">
              <button type="button" onClick={handleFinish}>
                🏠
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

export default QuizPage
