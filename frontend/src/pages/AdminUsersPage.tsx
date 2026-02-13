import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import UserDirectoryTable, { type DirectoryUser } from '../components/UserDirectoryTable'
import AdminNav from '../components/AdminNav'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

const AdminUsersPage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [users, setUsers] = useState<DirectoryUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const createSectionRef = useRef<HTMLDivElement | null>(null)
  const [createForm, setCreateForm] = useState({
    user_id: '',
    user_name: '',
    email: '',
    password: '',
    role: 'general',
  })

  useEffect(() => {
    if (status !== 'allowed') return
    const loadUsers = async () => {
      setUsersLoading(true)
      setUsersError(null)
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users`)
        if (!response.ok) {
          throw new Error('사용자 정보를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as DirectoryUser[]
        setUsers(data)
      } catch (error) {
        setUsersError('사용자 정보를 불러오지 못했습니다.')
      } finally {
        setUsersLoading(false)
      }
    }
    loadUsers()
  }, [status])

  const handleCreateUser = async () => {
    if (createLoading) return
    setCreateLoading(true)
    setCreateError(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createForm),
      })
      if (!response.ok) {
        throw new Error('사용자 생성을 완료하지 못했습니다.')
      }
      const created = (await response.json()) as DirectoryUser
      setUsers((prev) => [created, ...prev])
      setCreateForm({
        user_id: '',
        user_name: '',
        email: '',
        password: '',
        role: 'general',
      })
    } catch (error) {
      setCreateError('사용자 생성을 완료하지 못했습니다. 입력값을 확인해주세요.')
    } finally {
      setCreateLoading(false)
    }
  }

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>사용자 대시보드</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>사용자 대시보드</h1>
        <p>접근 권한이 없습니다.</p>
        <button type="button" onClick={() => navigate('/')}>홈으로 이동</button>
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
      <div className="admin-users-header">
        <div>
          <h1>사용자 대시보드</h1>
          <p>사용자 정보를 검색하고 계정 정보를 관리할 수 있습니다.</p>
        </div>
        <button
          type="button"
          className="secondary"
          onClick={() => createSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
        >
          사용자 추가
        </button>
      </div>
      <AdminNav />
      <div ref={createSectionRef} className="card admin-user-create">
        <h2>사용자 생성</h2>
        <div className="admin-user-create-grid">
          <label className="label">
            사용자 ID
            <input
              value={createForm.user_id}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, user_id: event.target.value }))}
              placeholder="아이디"
            />
          </label>
          <label className="label">
            이름
            <input
              value={createForm.user_name}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, user_name: event.target.value }))}
              placeholder="이름"
            />
          </label>
          <label className="label">
            이메일
            <input
              value={createForm.email}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="example@domain.com"
            />
          </label>
          <label className="label">
            비밀번호
            <input
              type="password"
              value={createForm.password}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="비밀번호"
            />
          </label>
          <label className="label">
            역할
            <select
              value={createForm.role}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, role: event.target.value }))}
            >
              <option value="general">general</option>
              <option value="coach">coach</option>
              <option value="admin">admin</option>
            </select>
          </label>
        </div>
        <div className="admin-user-create-actions">
          <button type="button" onClick={handleCreateUser} disabled={createLoading}>
            {createLoading ? '생성 중...' : '사용자 생성'}
          </button>
        </div>
        {createError && <p className="helper-text error-text">{createError}</p>}
      </div>

      <UserDirectoryTable
        users={users}
        loading={usersLoading}
        error={usersError}
        emptyMessage="조건에 맞는 사용자가 없습니다."
        onRowClick={(user) => navigate(`/admin/users/${user.id}`)}
      />
    </section>
  )
}

export default AdminUsersPage
