import { useState, type FormEvent } from 'react'
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
  const [showSuccessModal, setShowSuccessModal] = useState(false)

  const getErrorMessage = (responseBody: unknown) => {
    if (
      responseBody &&
      typeof responseBody === 'object' &&
      'detail' in responseBody &&
      Array.isArray(responseBody.detail)
    ) {
      const emailError = responseBody.detail.find(
        (item) =>
          item &&
          typeof item === 'object' &&
          'loc' in item &&
          Array.isArray(item.loc) &&
          item.loc.includes('email'),
      )
      if (emailError) {
        return '올바른 이메일 주소를 입력해주세요.'
      }
    }
    return '회원가입 정보를 확인해주세요.'
  }

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
        const responseBody = await response.json().catch(() => null)
        throw new Error(getErrorMessage(responseBody))
      }
      setMessage(null)
      setShowSuccessModal(true)
    } catch (error) {
      const errorMessage =
        error instanceof Error && error.message
          ? error.message
          : '회원가입 정보를 확인해주세요.'
      setMessage(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    handleSignup()
  }

  return (
    <section className="page">
      <h1>회원가입</h1>
      <p>간단한 정보 입력 후 바로 시작할 수 있어요.</p>
      <form className="card" onSubmit={handleSubmit}>
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
        <button type="submit" disabled={loading}>
          {loading ? '가입 중' : '회원가입'}
        </button>
        {message && <p className="helper-text">{message}</p>}
        <p className="helper-text">
          이미 계정이 있나요? <Link to="/">로그인</Link>
        </p>
      </form>
      {showSuccessModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <h2>회원가입 성공!</h2>
            <p>이제 로그인해서 서비스를 시작해보세요.</p>
            <button type="button" onClick={() => navigate('/')}>
              로그인 바로가기
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

export default SignupPage
