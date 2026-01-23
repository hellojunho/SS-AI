import { useState } from 'react'

import { API_BASE_URL } from '../config'

type Quiz = {
  id: number
  title: string
  question: string
  correct: string
  wrong: string
  explanation: string
  reference: string
}

const QuizPage = () => {
  const [token, setToken] = useState('')
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [loading, setLoading] = useState(false)

  const generateQuiz = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/quiz/generate`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (!response.ok) {
        throw new Error('퀴즈를 생성하지 못했습니다.')
      }
      const data = await response.json()
      setQuiz(data)
    } catch (error) {
      setQuiz(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <h1>Quiz</h1>
      <p>요약된 대화를 바탕으로 퀴즈를 풀어보세요.</p>
      <div className="card">
        <label className="label">
          Access Token
          <input
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="JWT 토큰을 입력하세요"
          />
        </label>
        <button type="button" onClick={generateQuiz} disabled={loading}>
          {loading ? '생성 중' : '퀴즈 생성'}
        </button>
      </div>
      {quiz && (
        <div className="card">
          <h2>{quiz.title}</h2>
          <p className="question">{quiz.question}</p>
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
        </div>
      )}
    </section>
  )
}

export default QuizPage
