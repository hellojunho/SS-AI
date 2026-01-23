import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { clearTokens, isAuthenticated } from '../auth'

const MyPage = () => {
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated())

  useEffect(() => {
    const handleAuthChange = () => setIsLoggedIn(isAuthenticated())
    window.addEventListener('authchange', handleAuthChange)
    window.addEventListener('storage', handleAuthChange)
    return () => {
      window.removeEventListener('authchange', handleAuthChange)
      window.removeEventListener('storage', handleAuthChange)
    }
  }, [])

  const handleLogout = () => {
    clearTokens()
    navigate('/')
  }

  return (
    <section className="page">
      <h1>마이페이지</h1>
      <p>학습 기록과 퀴즈 성과를 확인하는 공간입니다.</p>
      <div className="card">
        <h2>오늘의 학습 요약</h2>
        <p>대화 기록을 요약해 퀴즈를 만들 수 있어요.</p>
      </div>
      <div
        className="card chat-preview"
        onClick={() => navigate('/chat')}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            navigate('/chat')
          }
        }}
        role="button"
        tabIndex={0}
      >
        <h2>채팅 시작하기</h2>
        <p>채팅 창을 눌러 스포츠 과학 질문을 이어가세요.</p>
      </div>
      {isLoggedIn && (
        <div className="card logout-card">
          <h2>계정</h2>
          <p>현재 계정에서 안전하게 로그아웃할 수 있어요.</p>
          <button type="button" className="logout-button" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      )}
    </section>
  )
}

export default MyPage
