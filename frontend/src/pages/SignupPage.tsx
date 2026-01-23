import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { API_BASE_URL } from '../config'

const SignupPage = () => {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [userName, setUserName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSignup = async () => {
    if (!userId || !userName || !email || !password) return
    setLoading(true)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          user_name: userName,
          email,
          password,
        }),
      })
      if (!response.ok) {
        throw new Error('회원가입에 실패했습니다.')
      }
      setMessage('회원가입이 완료되었습니다. 로그인해주세요.')
      setTimeout(() => navigate('/'), 800)
    } catch (error) {
      setMessage('회원가입 정보를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <h1>회원가입</h1>
      <p>간단한 정보 입력 후 바로 시작할 수 있어요.</p>
      <div className="card">
        <label className="label">
          아이디
          <input
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            placeholder="아이디를 입력하세요"
          />
        </label>
        <label className="label">
          이름
          <input
            value={userName}
            onChange={(event) => setUserName(event.target.value)}
            placeholder="이름을 입력하세요"
          />
        </label>
        <label className="label">
          이메일
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="example@mail.com"
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
        <button type="button" onClick={handleSignup} disabled={loading}>
          {loading ? '가입 중' : '회원가입'}
        </button>
        {message && <p className="helper-text">{message}</p>}
        <p className="helper-text">
          이미 계정이 있나요? <Link to="/">로그인</Link>
        </p>
      </div>
    </section>
  )
}

export default SignupPage
