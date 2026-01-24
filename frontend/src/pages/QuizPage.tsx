import { useState, type FormEvent } from 'react'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type Quiz = {
  id: number
  title: string
  question: string
  correct: string
  wrong: string
  explanation: string
  reference: string
  has_correct_attempt: boolean
  has_wrong_attempt: boolean
  answer_history: string[]
  tried_at: string | null
  solved_at: string | null
}

const QuizPage = () => {
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resultMessage, setResultMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const generateQuiz = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/generate`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error('퀴즈를 생성하지 못했습니다.')
      }
      const data = await response.json()
      setQuiz(data)
      setAnswer('')
      setResultMessage(null)
    } catch (error) {
      setQuiz(null)
      setErrorMessage('퀴즈를 가져오지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async () => {
    if (!quiz) return
    setSubmitting(true)
    setErrorMessage(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/quiz/${quiz.id}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer }),
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
      setResultMessage(data.is_correct ? '정답이에요!' : '틀렸어요. 다시 도전해보세요!')
    } catch (error) {
      setResultMessage('답안을 제출하는 데 문제가 발생했습니다.')
      setErrorMessage('답안을 제출하지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setSubmitting(false)
      setAnswer('')
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submitAnswer()
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

  return (
    <section className="page">
      <h1>Quiz</h1>
      <p>요약된 대화를 바탕으로 퀴즈를 풀어보세요.</p>
      <div className="card">
        <button type="button" onClick={generateQuiz} disabled={loading}>
          {loading ? '생성 중' : '퀴즈 생성'}
        </button>
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      </div>
      {quiz && (
        <div className="card">
          <div className="quiz-header">
            <h2>{quiz.title}</h2>
            {stickerText && <span className={stickerClass}>{stickerText}</span>}
          </div>
          <p className="question">{quiz.question}</p>
          <form onSubmit={handleSubmit}>
            <label className="label">
              답안 입력
              <input
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                placeholder="답을 입력하세요"
              />
            </label>
            <button type="submit" disabled={submitting || !answer}>
              {submitting ? '제출 중' : '답 제출'}
            </button>
          </form>
          {resultMessage && <p className="result-message">{resultMessage}</p>}
          <div>
            <strong>정답:</strong> {quiz.correct}
          </div>
          <div>
            <strong>오답:</strong> {quiz.wrong}
          </div>
          <div>
            <strong>해설:</strong> {quiz.explanation}
          </div>
          <div>
            <strong>추가 자료:</strong> {quiz.reference}
          </div>
          {quiz.answer_history.length > 0 && (
            <div className="answer-history">
              <strong>입력한 답:</strong>
              <ul>
                {quiz.answer_history.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default QuizPage
