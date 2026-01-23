import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { saveTokens } from '../auth'
import { API_BASE_URL } from '../config'

const HomePage = () => {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    if (!userId || !password) return
    setLoading(true)
    setErrorMessage(null)
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId, password }),
      })
      if (!response.ok) {
        throw new Error('로그인에 실패했습니다.')
      }
      const data = await response.json()
      saveTokens(data.access_token, data.refresh_token)
      navigate('/mypage')
    } catch (error) {
      setErrorMessage('로그인 정보를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <h1>Sports Science</h1>
      <p>로그인 후 학습 기록과 퀴즈 성과를 확인할 수 있어요.</p>
      <div className="card">
        <h2>로그인</h2>
        <label className="label">
          아이디
          <input
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            placeholder="아이디를 입력하세요"
          />
        </label>
        <label className="label">
          비밀번호
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="비밀번호를 입력하세요"
          />
        </label>
        <button type="button" onClick={handleLogin} disabled={loading}>
          {loading ? '로그인 중' : '로그인'}
        </button>
        {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
        <p className="helper-text">
          계정이 없나요? <Link to="/signup">signup</Link>
        </p>
      </div>
    </section>
  )
}

export default HomePage
