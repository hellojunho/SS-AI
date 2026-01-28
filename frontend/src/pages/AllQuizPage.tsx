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
  link: string
  has_correct_attempt: boolean
  has_wrong_attempt: boolean
  answer_history: string[]
  tried_at: string | null
  solved_at: string | null
  current_index: number | null
  total_count: number | null
}

type QuizSummary = {
  total_count: number
  correct_count: number
  wrong_count: number
  accuracy_rate: number
}

const AllQuizPage = () => {
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [answerStatus, setAnswerStatus] = useState<'correct' | 'wrong' | null>(null)
  const [activeModal, setActiveModal] = useState<'correct' | 'wrong' | 'finished' | null>(null)
  const [finishedMessage, setFinishedMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [quizSummary, setQuizSummary] = useState<QuizSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [quizIndex, setQuizIndex] = useState<number | null>(null)
  const [quizTotal, setQuizTotal] = useState<number | null>(null)

  const loadQuiz = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/all/first`)
      if (!response.ok) {
        throw new Error('퀴즈를 가져오지 못했습니다.')
      }
      const data = await response.json()
      setQuiz(data)
      setQuizIndex(1)
      setQuizTotal(data.total_count ?? null)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
      setQuizSummary(null)
    } catch (error) {
      setQuiz(null)
      setQuizIndex(null)
      setQuizTotal(null)
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
        await handleNextQuiz()
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

  const handlePrevQuiz = async () => {
    if (!quiz) return
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/all/prev?current_id=${quiz.id}`)
      if (!response.ok) {
        setErrorMessage('이전 문제를 불러오지 못했습니다.')
        return
      }
      const data = await response.json()
      setQuiz(data)
      setQuizIndex((prev) => (prev ? Math.max(prev - 1, 1) : 1))
      setQuizTotal(data.total_count ?? null)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
      setQuizSummary(null)
    } catch (error) {
      setErrorMessage('이전 문제를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleNextQuiz = async () => {
    if (!quiz) return
    if (quizIndex && quizTotal && quizIndex + 1 > quizTotal) {
      setFinishedMessage('전체 문제를 모두 풀었어요!')
      setActiveModal('finished')
      await loadQuizSummary('all')
      return
    }
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/all/next?current_id=${quiz.id}`)
      if (!response.ok) {
        setErrorMessage('다음 문제를 불러오지 못했습니다.')
        return
      }
      const data = await response.json()
      setQuiz(data)
      setQuizIndex((prev) => (prev ? prev + 1 : 1))
      setQuizTotal(data.total_count ?? null)
      setAnswerStatus(null)
      setActiveModal(null)
      setFinishedMessage(null)
      setQuizSummary(null)
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

  const loadQuizSummary = async (scope: 'user' | 'all') => {
    setSummaryLoading(true)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/summary?scope=${scope}`)
      if (!response.ok) {
        throw new Error('결과를 불러오지 못했습니다.')
      }
      const data = (await response.json()) as QuizSummary
      setQuizSummary(data)
    } catch (error) {
      setQuizSummary(null)
    } finally {
      setSummaryLoading(false)
    }
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

  const renderQuestionLink = (link: string) => {
    if (!link.trim()) return null
    return (
      <a href={link} target="_blank" rel="noreferrer">
        출처 바로가기
      </a>
    )
  }

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>
          이전
        </button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>홈</button>
      </div>
      <h1>전체 문제 풀기</h1>
      <p>모든 사용자의 퀴즈를 한 번에 풀 수 있어요.</p>
      <div className="card">
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
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
        {finishedMessage && <p className="helper-text">{finishedMessage}</p>}
      </div>
      {quiz && (
        <div className="card">
          <div className="quiz-header">
            <div className="quiz-header-left">
              {stickerText && <span className={stickerClass}>{stickerText}</span>}
            </div>
            {quizIndex && quizTotal && (
              <span className="quiz-progress">
                {quizIndex} / {quizTotal}
              </span>
            )}
          </div>
          <div className="quiz-question">
            <div className="quiz-question-heading">
              <p className="question">Q{quizIndex ?? 1}. {quiz.question}</p>
              {answerStatus && (
                <span className={`quiz-result-mark ${answerStatus}`}>
                  {answerStatus === 'correct' ? 'O' : 'X'}
                </span>
              )}
            </div>
            {quiz.link && (
              <div className="quiz-question-source">
                {renderQuestionLink(quiz.link)}
              </div>
            )}
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
            <button type="button" className="secondary" onClick={handlePrevQuiz} disabled={loading}>
              이전 문제
            </button>
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
            {summaryLoading && <p className="helper-text">결과를 불러오는 중...</p>}
            {quizSummary && (
              <ul className="quiz-summary-list">
                <li>
                  <span>총 문제 수</span>
                  <strong>{quizSummary.total_count}</strong>
                </li>
                <li>
                  <span>맞힌 문제 수</span>
                  <strong>{quizSummary.correct_count}</strong>
                </li>
                <li>
                  <span>틀린 문제 수</span>
                  <strong>{quizSummary.wrong_count}</strong>
                </li>
                <li>
                  <span>정답률</span>
                  <strong>{quizSummary.accuracy_rate}%</strong>
                </li>
              </ul>
            )}
            <div className="modal-actions">
              <button type="button" onClick={handleFinish}>
                홈
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

export default AllQuizPage
