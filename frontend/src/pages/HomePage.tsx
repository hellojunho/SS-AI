import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { isAuthenticated, saveTokens } from '../auth'
import { API_BASE_URL } from '../config'

const HomePage = () => {
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated())
  const [userId, setUserId] = useState('')
  const [rememberId, setRememberId] = useState(false)
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const handleAuthChange = () => setIsLoggedIn(isAuthenticated())
    window.addEventListener('authchange', handleAuthChange)
    window.addEventListener('storage', handleAuthChange)
    return () => {
      window.removeEventListener('authchange', handleAuthChange)
      window.removeEventListener('storage', handleAuthChange)
    }
  }, [])

  useEffect(() => {
    const saved = localStorage.getItem('rememberedUserId')
    if (saved) {
      setUserId(saved)
      setRememberId(true)
    }
  }, [])

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
      if (rememberId) {
        localStorage.setItem('rememberedUserId', userId)
      } else {
        localStorage.removeItem('rememberedUserId')
      }
      setIsLoggedIn(true)
      navigate('/')
    } catch (error) {
      setErrorMessage('로그인 정보를 확인해주세요.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    handleLogin()
  }

  return (
    <section className="page">
      <div className="hero">
        <p className="hero-title">
          SS-AI
          <br />
          created by hellojunho
        </p>
        <p className="hero-subtitle">스포츠 과학 학습을 한 곳에서 관리하세요.</p>
      </div>
      {isLoggedIn ? (
        <div className="banner-grid">
          <Link to="/chat" className="banner-card">
            <span className="banner-title">채팅 바로가기</span>
            <span className="banner-desc">AI 코치와 대화를 시작해보세요.</span>
          </Link>
          <Link to="/quiz" className="banner-card banner-accent">
            <span className="banner-title">퀴즈 도전하기</span>
            <span className="banner-desc">오늘의 실력을 빠르게 점검해요.</span>
          </Link>
          <Link to="/mypage" className="banner-card banner-dark">
            <span className="banner-title">마이페이지 보기</span>
            <span className="banner-desc">학습 기록과 성과를 확인하세요.</span>
          </Link>
        </div>
      ) : (
        <form className="card login-card" onSubmit={handleSubmit}>
          <h2>로그인</h2>
          <label className="label">
            아이디
            <input
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="아이디를 입력하세요"
            />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={rememberId} onChange={(e) => setRememberId(e.target.checked)} />
            <span style={{ fontSize: 13 }}>아이디 기억하기</span>
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
            {loading ? '로그인 중' : '로그인'}
          </button>
          {errorMessage && <p className="helper-text error-text">{errorMessage}</p>}
          <p className="helper-text">
            계정이 없나요? <Link to="/signup">signup</Link>
          </p>
        </form>
      )}
    </section>
  )
}

export default HomePage
