import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import AdminNav from '../components/AdminNav'
import { useAdminStatus } from '../hooks/useAdminStatus'

type AdminUser = {
  id: number
  user_id: string
  user_name: string
  email: string
  role: string
  created_at: string
  last_logined: string | null
  is_active: boolean
  deactivated_at: string | null
}

type SortKey = 'user_id' | 'user_name' | 'email' | 'role' | 'created_at' | 'last_logined'

type SortConfig = {
  key: SortKey
  direction: 'asc' | 'desc'
}

const PAGE_SIZE = 10

const AdminUsersPage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null)
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null)
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

  const [searchId, setSearchId] = useState('')
  const [searchEmail, setSearchEmail] = useState('')
  const [searchRole, setSearchRole] = useState('')
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'created_at',
    direction: 'desc',
  })
  const [page, setPage] = useState(1)

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
        const data = (await response.json()) as AdminUser[]
        setUsers(data)
      } catch (error) {
        setUsersError('사용자 정보를 불러오지 못했습니다.')
      } finally {
        setUsersLoading(false)
      }
    }
    loadUsers()
  }, [status])

  useEffect(() => {
    setPage(1)
  }, [searchId, searchEmail, searchRole])

  const handleUserChange = (
    userId: number,
    field: keyof Pick<AdminUser, 'user_name' | 'email' | 'role'>,
    value: string,
  ) => {
    setUsers((prev) =>
      prev.map((user) => (user.id === userId ? { ...user, [field]: value } : user)),
    )
  }

  const handleUserSave = async (user: AdminUser) => {
    setUpdatingUserId(user.id)
    setUsersError(null)
    try {
      // Only update role from dashboard; other fields are read-only here.
      const payload = {
        role: user.role,
      }
      const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        throw new Error('사용자 정보를 수정하지 못했습니다.')
      }
      const updated = (await response.json()) as AdminUser
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    } catch (error) {
      setUsersError('사용자 정보를 수정하지 못했습니다. 입력값을 확인해주세요.')
    } finally {
      setUpdatingUserId(null)
    }
  }

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
      const created = (await response.json()) as AdminUser
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

  const handleDeleteUser = async (user: AdminUser) => {
    if (deletingUserId) return
    const confirmed = window.confirm(`${user.user_id} 사용자를 삭제할까요?`)
    if (!confirmed) return
    setDeletingUserId(user.id)
    setUsersError(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/users/${user.id}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        throw new Error('사용자를 삭제하지 못했습니다.')
      }
      setUsers((prev) => prev.filter((item) => item.id !== user.id))
    } catch (error) {
      setUsersError('사용자를 삭제하지 못했습니다.')
    } finally {
      setDeletingUserId(null)
    }
  }

  const formatDate = (value: string | null) => {
    if (!value) return '-'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('ko-KR')
  }

  const filteredUsers = useMemo(() => {
    const idQuery = searchId.trim().toLowerCase()
    const emailQuery = searchEmail.trim().toLowerCase()
    const roleQuery = searchRole.trim().toLowerCase()
    return users.filter((user) => {
      const matchesId = idQuery ? user.user_id.toLowerCase().includes(idQuery) : true
      const matchesEmail = emailQuery ? user.email.toLowerCase().includes(emailQuery) : true
      const matchesRole = roleQuery ? user.role.toLowerCase() === roleQuery : true
      return matchesId && matchesEmail && matchesRole
    })
  }, [users, searchId, searchEmail, searchRole])

  const sortedUsers = useMemo(() => {
    if (!sortConfig) return filteredUsers
    const { key, direction } = sortConfig
    const multiplier = direction === 'asc' ? 1 : -1
    const sorted = [...filteredUsers].sort((a, b) => {
      const valueA = a[key]
      const valueB = b[key]
      if (key === 'created_at' || key === 'last_logined') {
        const dateA = valueA ? new Date(valueA).getTime() : 0
        const dateB = valueB ? new Date(valueB).getTime() : 0
        return (dateA - dateB) * multiplier
      }
      return String(valueA).localeCompare(String(valueB), 'ko', { sensitivity: 'base' }) * multiplier
    })
    return sorted
  }, [filteredUsers, sortConfig])

  const totalPages = Math.max(1, Math.ceil(sortedUsers.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pagedUsers = sortedUsers.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => {
      if (prev?.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      }
      return { key, direction: 'asc' }
    })
  }

  const renderSortIndicator = (key: SortKey) => {
    if (sortConfig.key !== key) return null
    return sortConfig.direction === 'asc' ? '▲' : '▼'
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
      <div className="card admin-filters">
        <label className="label">
          사용자 ID 검색
          <input
            value={searchId}
            onChange={(event) => setSearchId(event.target.value)}
            placeholder="아이디를 입력하세요"
          />
        </label>
        <label className="label">
          이메일 검색
          <input
            value={searchEmail}
            onChange={(event) => setSearchEmail(event.target.value)}
            placeholder="이메일을 입력하세요"
          />
        </label>
        <label className="label">
          역할 검색
          <select value={searchRole} onChange={(event) => setSearchRole(event.target.value)}>
            <option value="">전체</option>
            <option value="general">general</option>
            <option value="admin">admin</option>
          </select>
        </label>
      </div>
      <label className="label" style={{ alignItems: 'flex-end' }}>
        <button type="button" onClick={() => {
          setSearchId('')
          setSearchEmail('')
          setSearchRole('')
        }}>
          초기화
        </button>
      </label>
      <div className="admin-dashboard admin-compact">
        <div className="card admin-table admin-users-table">
          <div className="admin-table-row admin-table-header">
            <span>INDEX</span>
            <button type="button" className="admin-sort" onClick={() => handleSort('user_id')}>
              ID {renderSortIndicator('user_id')}
            </button>
            <button type="button" className="admin-sort" onClick={() => handleSort('user_name')}>
              이름 {renderSortIndicator('user_name')}
            </button>
            <button type="button" className="admin-sort" onClick={() => handleSort('email')}>
              이메일 {renderSortIndicator('email')}
            </button>
            <button type="button" className="admin-sort" onClick={() => handleSort('role')}>
              역할 {renderSortIndicator('role')}
            </button>
            <span>상태</span>
            <span>관리</span>
          </div>
          {usersLoading ? (
            <div className="admin-table-empty">사용자 정보를 불러오는 중...</div>
          ) : pagedUsers.length === 0 ? (
            <div className="admin-table-empty">조건에 맞는 사용자가 없습니다.</div>
          ) : (
            pagedUsers.map((user, idx) => (
              <div key={user.id} className="admin-table-row">
                <span>{(currentPage - 1) * PAGE_SIZE + idx + 1}</span>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => navigate(`/admin/users/${user.id}`)}
                >
                  {user.user_id}
                </button>
                <span>{user.user_name}</span>
                <span>{user.email}</span>
                <select
                  value={user.role}
                  onChange={(event) => handleUserChange(user.id, 'role', event.target.value)}
                >
                  <option value="general">general</option>
                  <option value="admin">admin</option>
                </select>
                <span>{user.is_active ? '활성' : '탈퇴'}</span>
                <div className="admin-user-actions">
                  <button
                    type="button"
                    onClick={() => handleUserSave(user)}
                    disabled={updatingUserId === user.id}
                  >
                    {updatingUserId === user.id ? (
                      <span className="button-with-spinner">
                        <span className="spinner" aria-label="사용자 업데이트 중" />
                        저장 중
                      </span>
                    ) : (
                      '저장'
                    )}
                  </button>
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => handleDeleteUser(user)}
                    disabled={deletingUserId === user.id}
                  >
                    {deletingUserId === user.id ? '삭제 중' : '삭제'}
                  </button>
                </div>
              </div>
            ))
          )}
          {usersError && <p className="helper-text error-text">{usersError}</p>}
        </div>
        <div className="admin-pagination">
          <button type="button" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={currentPage === 1}>
            이전
          </button>
          <span>
            {currentPage} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            다음
          </button>
        </div>
      </div>
    </section>
  )
}

export default AdminUsersPage
