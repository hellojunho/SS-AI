import { useMemo, useState, type ReactNode } from 'react'

export type DirectoryUser = {
  id: number
  user_id: string
  user_name: string
  email: string
  role: string
  created_at: string
  last_logined: string | null
  is_active: boolean
}

type SortKey = 'user_id' | 'user_name' | 'email' | 'role' | 'created_at' | 'last_logined'

type SortConfig = {
  key: SortKey
  direction: 'asc' | 'desc'
}

type Props = {
  users: DirectoryUser[]
  loading: boolean
  error?: string | null
  emptyMessage: string
  roleOptions?: string[]
  pageSize?: number
  onRowClick?: (user: DirectoryUser) => void
  rowAction?: (user: DirectoryUser) => ReactNode
}

const DEFAULT_PAGE_SIZE = 10

const formatDate = (value: string | null) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ko-KR')
}

const UserDirectoryTable = ({
  users,
  loading,
  error,
  emptyMessage,
  roleOptions,
  pageSize = DEFAULT_PAGE_SIZE,
  onRowClick,
  rowAction,
}: Props) => {
  const [searchId, setSearchId] = useState('')
  const [searchEmail, setSearchEmail] = useState('')
  const [searchRole, setSearchRole] = useState('')
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'created_at',
    direction: 'desc',
  })
  const [page, setPage] = useState(1)

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
    const { key, direction } = sortConfig
    const multiplier = direction === 'asc' ? 1 : -1
    return [...filteredUsers].sort((a, b) => {
      const valueA = a[key]
      const valueB = b[key]
      if (key === 'created_at' || key === 'last_logined') {
        const dateA = valueA ? new Date(valueA).getTime() : 0
        const dateB = valueB ? new Date(valueB).getTime() : 0
        return (dateA - dateB) * multiplier
      }
      return String(valueA).localeCompare(String(valueB), 'ko', { sensitivity: 'base' }) * multiplier
    })
  }, [filteredUsers, sortConfig])

  const totalPages = Math.max(1, Math.ceil(sortedUsers.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const pagedUsers = sortedUsers.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      }
      return { key, direction: 'asc' }
    })
  }

  const renderSortIndicator = (key: SortKey) => {
    if (sortConfig.key !== key) return null
    return sortConfig.direction === 'asc' ? '▲' : '▼'
  }

  return (
    <>
      <div className="card admin-filters">
        <label className="label">
          사용자 ID 검색
          <input
            value={searchId}
            onChange={(event) => {
              setSearchId(event.target.value)
              setPage(1)
            }}
            placeholder="아이디를 입력하세요"
          />
        </label>
        <label className="label">
          이메일 검색
          <input
            value={searchEmail}
            onChange={(event) => {
              setSearchEmail(event.target.value)
              setPage(1)
            }}
            placeholder="이메일을 입력하세요"
          />
        </label>
        <label className="label">
          역할 검색
          <select
            value={searchRole}
            onChange={(event) => {
              setSearchRole(event.target.value)
              setPage(1)
            }}
          >
            <option value="">전체</option>
            {(roleOptions ?? ['general', 'coach', 'admin']).map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="label" style={{ alignItems: 'flex-end' }}>
        <button
          type="button"
          onClick={() => {
            setSearchId('')
            setSearchEmail('')
            setSearchRole('')
            setPage(1)
          }}
        >
          초기화
        </button>
      </label>

      <div className="admin-dashboard admin-compact">
        <div className="card admin-table admin-users-table">
          <div className={`admin-table-row admin-table-header admin-user-row ${rowAction ? "with-action" : ""}`}>
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
            <button type="button" className="admin-sort" onClick={() => handleSort('created_at')}>
              가입일 {renderSortIndicator('created_at')}
            </button>
            <button type="button" className="admin-sort" onClick={() => handleSort('last_logined')}>
              최근 로그인 {renderSortIndicator('last_logined')}
            </button>
            <span>상태</span>
            {rowAction && <span>액션</span>}
          </div>
          {loading ? (
            <div className="admin-table-empty">사용자 정보를 불러오는 중...</div>
          ) : pagedUsers.length === 0 ? (
            <div className="admin-table-empty">{emptyMessage}</div>
          ) : (
            pagedUsers.map((user, idx) => (
              <div key={user.id} className={`admin-table-row admin-user-row ${rowAction ? "with-action" : ""}`}>
                <span>{(currentPage - 1) * pageSize + idx + 1}</span>
                {onRowClick ? (
                  <button type="button" className="link-button" onClick={() => onRowClick(user)}>
                    {user.user_id}
                  </button>
                ) : (
                  <span>{user.user_id}</span>
                )}
                <span>{user.user_name}</span>
                <span>{user.email}</span>
                <span>{user.role}</span>
                <span>{formatDate(user.created_at)}</span>
                <span>{formatDate(user.last_logined)}</span>
                <span>{user.is_active ? '활성' : '탈퇴'}</span>
                {rowAction && <div>{rowAction(user)}</div>}
              </div>
            ))
          )}
          {error && <p className="helper-text error-text">{error}</p>}
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
    </>
  )
}

export default UserDirectoryTable
