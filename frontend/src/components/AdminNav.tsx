import { NavLink } from 'react-router-dom'

const AdminNav = () => (
  <nav className="admin-nav">
    <NavLink to="/admin" end className={({ isActive }) => (isActive ? 'active' : '')}>
      관리자 홈
    </NavLink>
    <NavLink to="/admin/quizzes" className={({ isActive }) => (isActive ? 'active' : '')}>
      퀴즈 대시보드
    </NavLink>
    <NavLink to="/admin/users" className={({ isActive }) => (isActive ? 'active' : '')}>
      사용자 대시보드
    </NavLink>
    <NavLink to="/admin/docs" className={({ isActive }) => (isActive ? 'active' : '')}>
      문서 학습
    </NavLink>
    <NavLink to="/admin/llm" className={({ isActive }) => (isActive ? 'active' : '')}>
      LLM 토큰
    </NavLink>
  </nav>
)

export default AdminNav
