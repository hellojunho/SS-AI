import { useState } from 'react'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type ChatEntry = {
  role: 'me' | 'gpt'
  content: string
}

const ChatPage = () => {
  const [message, setMessage] = useState('')
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const sendMessage = async () => {
    if (!message.trim()) return
    setLoading(true)
    setErrorMessage(null)
    setEntries((prev) => [...prev, { role: 'me', content: message }])
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

  return (
    <section className="page">
      <h1>Chat</h1>
      <p>스포츠 과학 지식을 대화로 학습하세요.</p>
      {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
      <div className="chat-box">
        {entries.map((entry, index) => (
          <div key={`${entry.role}-${index}`} className={`bubble ${entry.role}`}>
            {entry.content}
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="질문을 입력하세요"
        />
        <button type="button" onClick={sendMessage} disabled={loading}>
          {loading ? '전송 중' : '전송'}
        </button>
      </div>
    </section>
  )
}

export default ChatPage
