import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { clearTokens, isAuthenticated } from '../auth'
import { API_BASE_URL } from '../config'

const MyPage = () => {
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated())
  const [role, setRole] = useState<string | null>(null)

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
    if (!isLoggedIn) {
      setRole(null)
      return
    }
    const fetchRole = async () => {
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/me`)
        if (!response.ok) {
          throw new Error('사용자 정보를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as { role?: string }
        setRole(data.role ?? null)
      } catch (error) {
        setRole(null)
      }
    }
    fetchRole()
  }, [isLoggedIn])

  const handleLogout = () => {
    clearTokens()
    navigate('/', { replace: true })
  }

  const handleWithdraw = async () => {
    if (!confirm('정말로 회원 탈퇴를 진행하시겠습니까?')) return
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/withdraw`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error('회원 탈퇴 실패')
      }
      clearTokens()
      navigate('/', { replace: true })
    } catch (error) {
      alert('회원 탈퇴를 진행하지 못했습니다.')
    }
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
        onClick={() => navigate('/mypage/wrong-notes')}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            navigate('/mypage/wrong-notes')
          }
        }}
        role="button"
        tabIndex={0}
      >
        <h2>오답노트</h2>
        <p>내가 틀렸던 문제만 다시 풀어볼 수 있어요.</p>
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
          <div className="logout-actions">
            <button type="button" className="logout-button" onClick={handleLogout}>
              로그아웃
            </button>
            <button type="button" className="logout-button danger" onClick={handleWithdraw}>
              회원 탈퇴
            </button>
          </div>
        </div>
      )}
      {role === 'coach' && (
        <div
          className="card chat-preview"
          onClick={() => navigate('/coach/students')}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              navigate('/coach/students')
            }
          }}
          role="button"
          tabIndex={0}
        >
          <h2>학생 등록 페이지</h2>
          <p>학생 아이디를 검색하고 내 학생 목록을 관리할 수 있어요.</p>
        </div>
      )}
      {role === 'admin' && (
        <div
          className="card chat-preview"
          onClick={() => navigate('/admin')}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              navigate('/admin')
            }
          }}
          role="button"
          tabIndex={0}
        >
          <h2>관리자 페이지</h2>
          <p>사용자 대화 기록 기반 퀴즈를 생성할 수 있습니다.</p>
        </div>
      )}
    </section>
  )
}

export default MyPage
