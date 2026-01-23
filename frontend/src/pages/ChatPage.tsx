import { useState } from 'react'

import { API_BASE_URL } from '../config'

type ChatEntry = {
  role: 'me' | 'gpt'
  content: string
}

const ChatPage = () => {
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('')
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!message.trim()) return
    setLoading(true)
    setEntries((prev) => [...prev, { role: 'me', content: message }])
    try {
      const response = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
      })
      if (!response.ok) {
        throw new Error('답변을 불러오지 못했습니다.')
      }
      const data = await response.json()
      setEntries((prev) => [...prev, { role: 'gpt', content: `${data.answer}\n출처: ${data.reference}` }])
    } catch (error) {
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
      <div className="card">
        <label className="label">
          Access Token
          <input
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="JWT 토큰을 입력하세요"
          />
        </label>
      </div>
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
