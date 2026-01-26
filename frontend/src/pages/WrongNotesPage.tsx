import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type WrongNoteQuestion = {
  quiz_id: number
  question_id: number
  question: string
  choices: string[]
  correct: string
  wrong: string[]
  explanation: string
  reference: string
  link: string
}

const WrongNotesPage = () => {
  const navigate = useNavigate()
  const [wrongNotes, setWrongNotes] = useState<WrongNoteQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [answerStatus, setAnswerStatus] = useState<'correct' | 'wrong' | null>(null)
  const [activeModal, setActiveModal] = useState<'correct' | 'wrong' | 'finished' | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const currentQuestion = wrongNotes[currentIndex]

  const loadWrongNotes = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/wrong-notes`)
      if (!response.ok) {
        throw new Error('오답노트를 불러오지 못했습니다.')
      }
      const data = (await response.json()) as WrongNoteQuestion[]
      setWrongNotes(data)
      setCurrentIndex(0)
      setAnswerStatus(null)
      setActiveModal(null)
    } catch (error) {
      setWrongNotes([])
      setErrorMessage('오답노트를 불러오지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWrongNotes()
  }, [])

  const submitAnswer = async (selectedAnswer: string) => {
    if (!currentQuestion) return
    setSubmitting(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/${currentQuestion.quiz_id}/answer`, {
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

  const handlePrevNote = () => {
    if (currentIndex === 0) return
    setCurrentIndex((prev) => Math.max(prev - 1, 0))
    setAnswerStatus(null)
    setActiveModal(null)
  }

  const handleNextNote = () => {
    if (currentIndex + 1 >= wrongNotes.length) {
      setActiveModal('finished')
      return
    }
    setCurrentIndex((prev) => Math.min(prev + 1, wrongNotes.length - 1))
    setAnswerStatus(null)
    setActiveModal(null)
  }

  const handleCloseModal = () => {
    setActiveModal(null)
  }

  const handleRetry = () => {
    setAnswerStatus(null)
    setActiveModal(null)
  }

  const handleFinish = () => {
    setActiveModal(null)
    navigate('/mypage')
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

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>
          이전
        </button>
        <button type="button" className="chat-nav-button" onClick={() => navigate('/mypage')}>
          마이페이지
        </button>
      </div>
      <h1>오답노트</h1>
      <p>틀렸던 문제를 다시 풀어보며 약점을 보완해요.</p>
      {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      {!loading && wrongNotes.length === 0 && (
        <div className="card">
          <p className="helper-text">아직 기록된 오답이 없어요.</p>
        </div>
      )}
      {currentQuestion && (
        <div className="card">
          <div className="quiz-header">
            <div className="quiz-header-left">
              <span className="sticker">오답 노트</span>
            </div>
            <span className="quiz-progress">
              {currentIndex + 1} / {wrongNotes.length}
            </span>
          </div>
          <div className="quiz-question">
            <div className="quiz-question-heading">
              <p className="question">
                Q{currentIndex + 1}. {currentQuestion.question}
              </p>
              {answerStatus && (
                <span className={`quiz-result-mark ${answerStatus}`}>
                  {answerStatus === 'correct' ? 'O' : 'X'}
                </span>
              )}
            </div>
            {currentQuestion.link && (
              <div className="quiz-question-source">
                <a href={currentQuestion.link} target="_blank" rel="noreferrer">
                  출처 바로가기
                </a>
              </div>
            )}
          </div>
          <ol className="quiz-options">
            {currentQuestion.choices.map((choice, index) => (
              <li key={`${currentQuestion.quiz_id}-${choice}-${index}`}>
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
            <button type="button" className="secondary" onClick={handlePrevNote} disabled={currentIndex === 0}>
              이전 문제
            </button>
          </div>
          {currentQuestion.explanation && (
            <div className="quiz-explanation">
              <span className="quiz-explanation-label">해설</span>
              <p className="quiz-explanation-content">{currentQuestion.explanation}</p>
            </div>
          )}
          {currentQuestion.reference && (
            <div className="quiz-reference">
              <span className="quiz-reference-label">참고자료</span>
              <p className="quiz-reference-content">{renderReference(currentQuestion.reference)}</p>
            </div>
          )}
        </div>
      )}
      {activeModal === 'correct' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>정답입니다!</h3>
            <p>다음 오답 문제로 넘어가볼까요?</p>
            <div className="modal-actions">
              <button type="button" className="secondary" onClick={handleCloseModal}>
                닫기
              </button>
              <button type="button" onClick={handleNextNote}>
                다음 문제
              </button>
            </div>
          </div>
        </div>
      )}
      {activeModal === 'wrong' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>틀렸습니다!</h3>
            <p>다시 풀어보며 확인해보세요.</p>
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
            <p>오답노트의 모든 문제를 풀었어요.</p>
            <div className="modal-actions">
              <button type="button" onClick={handleFinish}>
                마이페이지로
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

export default WrongNotesPage
