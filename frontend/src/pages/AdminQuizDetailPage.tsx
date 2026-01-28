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
  link: string
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
  const [mixing, setMixing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formState, setFormState] = useState({
    title: '',
    question: '',
    choices: '',
    correct: '',
    wrong: '',
    explanation: '',
    reference: '',
    link: '',
  })

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

  const syncFormState = (data: AdminQuiz) => {
    setFormState({
      title: normalizeText(data.title),
      question: normalizeText(data.question),
      choices: data.choices.map((choice) => normalizeText(choice)).join('\n'),
      correct: normalizeText(data.correct),
      wrong: data.wrong.map((item) => normalizeText(item)).join('\n'),
      explanation: normalizeText(data.explanation),
      reference: normalizeText(data.reference),
      link: normalizeText(data.link),
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
        if (selected) {
          syncFormState(selected)
        }
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
        <div className="card admin-quiz-detail">
          <div className="admin-quiz-detail-header">
            <div>
              <span className="admin-quiz-detail-label">QUIZ</span>
              <input
                className="admin-quiz-title-input"
                value={formState.title}
                onChange={(event) => setFormState({ ...formState, title: event.target.value })}
              />
              <p className="admin-quiz-detail-meta">생성 사용자: {quiz.source_user_id || '-'}</p>
            </div>
            <div className="admin-quiz-detail-actions">
              <button
                type="button"
                onClick={async () => {
                  if (!quiz) return
                  setSaving(true)
                  setErrorMessage(null)
                  try {
                    const payload = {
                      title: formState.title,
                      question: formState.question,
                      choices: formState.choices
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                      correct: formState.correct,
                      wrong: formState.wrong
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                      explanation: formState.explanation,
                      reference: formState.reference,
                      link: formState.link,
                    }
                    const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/${quiz.id}`, {
                      method: 'PATCH',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                    if (!res.ok) throw new Error('수정 실패')
                    const data = (await res.json()) as AdminQuiz
                    setQuiz(data)
                    syncFormState(data)
                  } catch (err) {
                    setErrorMessage('퀴즈를 저장하지 못했습니다.')
                  } finally {
                    setSaving(false)
                  }
                }}
                disabled={saving}
              >
                {saving ? '저장 중...' : '저장'}
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (!quiz) return
                  setMixing(true)
                  setErrorMessage(null)
                  try {
                    const res = await authorizedFetch(`${API_BASE_URL}/quiz/admin/${quiz.id}/mix`, { method: 'POST' })
                    if (!res.ok) throw new Error('mix 실패')
                    const data = (await res.json()) as AdminQuiz
                    setQuiz(data)
                    syncFormState(data)
                  } catch (err) {
                    setErrorMessage('퀴즈를 섞지 못했습니다.')
                  } finally {
                    setMixing(false)
                  }
                }}
                disabled={mixing}
              >
                {mixing ? '섞는 중...' : 'Mix'}
              </button>
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
          <div className="admin-quiz-detail-question">
            <div className="admin-quiz-detail-chip">Q1</div>
            <textarea
              className="admin-quiz-textarea"
              value={formState.question}
              onChange={(event) => setFormState({ ...formState, question: event.target.value })}
            />
          </div>
          <div className="admin-quiz-detail-grid">
            <div className="admin-quiz-detail-block">
              <span className="admin-quiz-detail-block-label">보기</span>
              <textarea
                className="admin-quiz-textarea"
                value={formState.choices}
                onChange={(event) => setFormState({ ...formState, choices: event.target.value })}
              />
            </div>
            <div className="admin-quiz-detail-block">
              <span className="admin-quiz-detail-block-label">정답</span>
              <input
                className="admin-quiz-input"
                value={formState.correct}
                onChange={(event) => setFormState({ ...formState, correct: event.target.value })}
              />
              <span className="admin-quiz-detail-block-label">오답 보기</span>
              <textarea
                className="admin-quiz-textarea"
                value={formState.wrong}
                onChange={(event) => setFormState({ ...formState, wrong: event.target.value })}
              />
            </div>
          </div>
          <div className="admin-quiz-detail-block">
            <span className="admin-quiz-detail-block-label">해설</span>
            <textarea
              className="admin-quiz-textarea"
              value={formState.explanation}
              onChange={(event) => setFormState({ ...formState, explanation: event.target.value })}
            />
          </div>
          <div className="admin-quiz-detail-block">
            <span className="admin-quiz-detail-block-label">문항 출처</span>
            <textarea
              className="admin-quiz-textarea"
              value={formState.link}
              onChange={(event) => setFormState({ ...formState, link: event.target.value })}
            />
          </div>
          <div className="admin-quiz-detail-block">
            <span className="admin-quiz-detail-block-label">참고자료</span>
            <textarea
              className="admin-quiz-textarea"
              value={formState.reference}
              onChange={(event) => setFormState({ ...formState, reference: event.target.value })}
            />
          </div>
        </div>
      )}
    </section>
  )
}

export default AdminQuizDetailPage
