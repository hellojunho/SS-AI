import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

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
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [answerStatus, setAnswerStatus] = useState<'correct' | 'wrong' | null>(null)
  const [activeModal, setActiveModal] = useState<'correct' | 'wrong' | 'finished' | null>(null)
  const [finishedMessage, setFinishedMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const generateQuiz = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/generate`, {
        method: 'POST',
      })
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

  const handleNextQuiz = async () => {
    if (!quiz) return
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
        <button type="button" onClick={generateQuiz} disabled={loading}>
          {loading ? (
            <span className="button-with-spinner">
              <span className="spinner" />
              불러오는 중
            </span>
          ) : (
            '퀴즈 불러오기'
          )}
        </button>
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
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
