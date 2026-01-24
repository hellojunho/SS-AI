import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type ChatEntry = {
  role: 'me' | 'gpt'
  content: string
}

type ChatHistoryResponse = {
  date: string
  entries: ChatEntry[]
  is_today: boolean
}

type ChatHistoryDatesResponse = {
  dates: string[]
  today: string
}

const ChatPage = () => {
  const [message, setMessage] = useState('')
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [historyDates, setHistoryDates] = useState<string[]>([])
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [today, setToday] = useState<string | null>(null)
  const [historySummaries, setHistorySummaries] = useState<Record<string, string>>({})
  const navigate = useNavigate()

  const isViewingToday = useMemo(() => {
    if (!selectedDate || !today) return true
    return selectedDate === today
  }, [selectedDate, today])

  const loadHistoryDates = async () => {
    const response = await authorizedFetch(`${API_BASE_URL}/chat/history`)
    if (!response.ok) {
      throw new Error('대화 기록을 불러오지 못했습니다.')
    }
    return (await response.json()) as ChatHistoryDatesResponse
  }

  const loadHistory = async (date: string) => {
    const response = await authorizedFetch(`${API_BASE_URL}/chat/history/${date}`)
    if (!response.ok) {
      throw new Error('대화 기록을 불러오지 못했습니다.')
    }
    return (await response.json()) as ChatHistoryResponse
  }

  useEffect(() => {
    const fetchHistory = async () => {
      setHistoryLoading(true)
      setErrorMessage(null)
      try {
        const data = await loadHistoryDates()
        setHistoryDates(data.dates)
        setToday(data.today)
        setSelectedDate(data.today)
        const histories = await Promise.all(
          data.dates.map(async (date) => {
            try {
              const history = await loadHistory(date)
              return { date, history }
            } catch (error) {
              return { date, history: null }
            }
          }),
        )
        const summaryMap: Record<string, string> = {}
        let todayHistory: ChatHistoryResponse | null = null
        histories.forEach(({ date, history }) => {
          if (!history) return
          const firstQuestion = history.entries.find((entry) => entry.role === 'me')?.content ?? ''
          if (firstQuestion) {
            summaryMap[date] = firstQuestion
          }
          if (date === data.today) {
            todayHistory = history
          }
        })
        setHistorySummaries(summaryMap)
        setEntries(todayHistory?.entries ?? [])
      } catch (error) {
        setErrorMessage('대화 기록을 불러오지 못했습니다. 로그인 상태를 확인해주세요.')
      } finally {
        setHistoryLoading(false)
      }
    }
    fetchHistory()
  }, [])

  const sendMessage = async () => {
    if (!message.trim()) return
    setLoading(true)
    setErrorMessage(null)
    setEntries((prev) => [...prev, { role: 'me', content: message }])
    if (today && !historySummaries[today]) {
      setHistorySummaries((prev) => ({ ...prev, [today]: message }))
    }
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      })
      if (!response.ok) {
        throw new Error('답변을 불러오지 못했습니다.')
      }
      const data = await response.json()
      setEntries((prev) => [...prev, { role: 'gpt', content: `${data.answer}\n출처: ${data.reference}` }])
      if (today && !historyDates.includes(today)) {
        setHistoryDates((prev) => [today, ...prev])
      }
    } catch (error) {
      setErrorMessage('오류가 발생했습니다. 로그인 상태를 확인해주세요.')
      setEntries((prev) => [
        ...prev,
        { role: 'gpt', content: '오류가 발생했습니다. 다시 시도해주세요.' },
      ])
    } finally {
      setLoading(false)
      setMessage('')
    }
  }

  const handleHistorySelect = async (date: string) => {
    setHistoryLoading(true)
    setErrorMessage(null)
    try {
      const history = await loadHistory(date)
      setEntries(history.entries)
      setSelectedDate(date)
      const firstQuestion = history.entries.find((entry) => entry.role === 'me')?.content ?? ''
      if (firstQuestion) {
        setHistorySummaries((prev) => ({ ...prev, [date]: firstQuestion }))
      }
    } catch (error) {
      setErrorMessage('대화 기록을 불러오지 못했습니다. 로그인 상태를 확인해주세요.')
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!isViewingToday) return
    sendMessage()
  }

  const formatQuestionPreview = (question: string) => {
    const chars = Array.from(question.trim())
    if (chars.length <= 5) return chars.join('')
    return `${chars.slice(0, 5).join('')} ...`
  }

  const formatHistoryLabel = (date: string) => {
    const question = historySummaries[date]
    if (!question) return date
    return `${date}: ${formatQuestionPreview(question)}`
  }

  return (
    <section className="page chat-page">
      <div className="chat-layout">
        <aside className="chat-sidebar">
          <h2>대화 기록</h2>
          {historyDates.length === 0 && (
            <p className="helper-text">{historyLoading ? '기록을 불러오는 중...' : '아직 기록이 없어요.'}</p>
          )}
          <div className="chat-date-list">
            {historyDates.map((date) => (
              <button
                key={date}
                type="button"
                className={`chat-date-button ${selectedDate === date ? 'active' : ''}`}
                onClick={() => handleHistorySelect(date)}
                disabled={historyLoading}
              >
                {formatHistoryLabel(date)}
              </button>
            ))}
          </div>
        </aside>
        <div className="chat-main">
          <div className="chat-header">
            <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>
              이전
            </button>
            <button type="button" className="chat-nav-button" onClick={() => navigate('/')}>
              홈
            </button>
          </div>
          <h1>Chat</h1>
          <p>스포츠 과학 지식을 대화로 학습하세요.</p>
          {selectedDate && !isViewingToday && (
            <p className="helper-text">이전 날짜의 대화 기록만 확인할 수 있어요.</p>
          )}
          {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
          <div className="chat-box">
            {entries.length === 0 && (
              <p className="helper-text">{historyLoading ? '대화를 불러오는 중...' : '대화를 시작해보세요.'}</p>
            )}
            {entries.map((entry, index) => (
              <div key={`${entry.role}-${index}`} className={`bubble ${entry.role}`}>
                {entry.content}
              </div>
            ))}
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="질문을 입력하세요"
              disabled={loading || !isViewingToday}
            />
            <button type="submit" disabled={loading || !isViewingToday}>
              {loading ? <span className="spinner" aria-label="답변 생성 중" /> : '전송'}
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}

export default ChatPage
