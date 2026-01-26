import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { useAdminStatus } from '../hooks/useAdminStatus'

const AdminHomePage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>관리자 페이지</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>관리자 페이지</h1>
        <p>접근 권한이 없습니다.</p>
        <button type="button" onClick={() => navigate('/')}>
          홈으로 이동
        </button>
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
      <h1>관리자 페이지</h1>
      <p>필요한 관리 기능을 선택하세요.</p>
      <AdminNav />
      <div className="admin-link-grid">
        <button
          type="button"
          className="card admin-link-card"
          onClick={() => navigate('/admin/quizzes')}
        >
          <h2>퀴즈 대시보드</h2>
          <p>생성된 퀴즈 목록을 확인하고 검토할 수 있습니다.</p>
        </button>
        <button type="button" className="card admin-link-card" onClick={() => navigate('/admin/users')}>
          <h2>사용자 대시보드</h2>
          <p>사용자 계정 정보를 검색하고 수정할 수 있습니다.</p>
        </button>
        <button type="button" className="card admin-link-card" onClick={() => navigate('/admin/docs')}>
          <h2>문서 학습</h2>
          <p>문서를 업로드하고 AI 학습을 실행할 수 있습니다.</p>
        </button>
        <button type="button" className="card admin-link-card" onClick={() => navigate('/admin/llm')}>
          <h2>LLM 토큰 대시보드</h2>
          <p>ChatGPT 토큰 사용량과 잔여량을 확인할 수 있습니다.</p>
        </button>
      </div>
    </section>
  )
}

export default AdminHomePage
