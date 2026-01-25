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
          🏠
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
          <h2>퀴즈 생성</h2>
          <p>사용자 대화 기록을 기반으로 퀴즈를 생성합니다.</p>
        </button>
        <button type="button" className="card admin-link-card" onClick={() => navigate('/admin/users')}>
          <h2>사용자 대시보드</h2>
          <p>사용자 계정 정보를 검색하고 수정할 수 있습니다.</p>
        </button>
      </div>
    </section>
  )
}

export default AdminHomePage
