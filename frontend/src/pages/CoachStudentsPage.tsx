import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authorizedFetch } from '../api'
import UserDirectoryTable, { type DirectoryUser } from '../components/UserDirectoryTable'
import { API_BASE_URL } from '../config'

type CoachStatus = 'loading' | 'allowed' | 'forbidden'

type MyInfo = {
  role?: string
}

const CoachStudentsPage = () => {
  const navigate = useNavigate()
  const [status, setStatus] = useState<CoachStatus>('loading')
  const [students, setStudents] = useState<DirectoryUser[]>([])
  const [studentsLoading, setStudentsLoading] = useState(false)
  const [studentsError, setStudentsError] = useState<string | null>(null)
  const [studentIdInput, setStudentIdInput] = useState('')
  const [studentSearchInput, setStudentSearchInput] = useState('')
  const [studentSearchResults, setStudentSearchResults] = useState<DirectoryUser[]>([])
  const [studentSearchLoading, setStudentSearchLoading] = useState(false)
  const [studentSearchError, setStudentSearchError] = useState<string | null>(null)
  const [selectedStudents, setSelectedStudents] = useState<DirectoryUser[]>([])
  const [batchRegisterLoading, setBatchRegisterLoading] = useState(false)
  const [batchRegisterMessage, setBatchRegisterMessage] = useState<string | null>(null)
  const [registerLoading, setRegisterLoading] = useState(false)
  const [registerMessage, setRegisterMessage] = useState<string | null>(null)

  const registeredIds = useMemo(() => new Set(students.map((student) => student.user_id)), [students])
  const selectedIds = useMemo(() => new Set(selectedStudents.map((student) => student.user_id)), [selectedStudents])

  const loadStudents = async () => {
    setStudentsLoading(true)
    setStudentsError(null)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/coach/students`)
      if (!response.ok) {
        throw new Error('학생 목록을 불러오지 못했습니다.')
      }
      const data = (await response.json()) as DirectoryUser[]
      setStudents(data)
    } catch (error) {
      setStudentsError('학생 목록을 불러오지 못했습니다.')
    } finally {
      setStudentsLoading(false)
    }
  }

  useEffect(() => {
    const loadRole = async () => {
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/me`)
        if (!response.ok) {
          throw new Error('사용자 정보를 확인할 수 없습니다.')
        }
        const data = (await response.json()) as MyInfo
        if (data.role === 'coach') {
          setStatus('allowed')
          loadStudents()
        } else {
          setStatus('forbidden')
        }
      } catch (error) {
        setStatus('forbidden')
      }
    }
    loadRole()
  }, [])

  const registerStudentRequest = async (studentUserId: string) => {
    if (!studentUserId.trim()) return
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/coach/students`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_user_id: studentUserId.trim() }),
      })
      if (!response.ok) {
        const errorData = (await response.json().catch(() => null)) as { detail?: string } | null
        return { status: 'error', message: errorData?.detail || '학생 등록에 실패했습니다.' } as const
      }
      const created = (await response.json()) as DirectoryUser
      return { status: 'ok', user: created } as const
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : '학생 등록에 실패했습니다.',
      } as const
    }
  }

  const handleRegisterStudent = async () => {
    if (!studentIdInput.trim() || registerLoading) return
    setRegisterLoading(true)
    setRegisterMessage(null)
    const result = await registerStudentRequest(studentIdInput.trim())
    if (!result) {
      setRegisterMessage('학생 등록에 실패했습니다.')
      setRegisterLoading(false)
      return
    }
    if (result.status === 'ok') {
      setStudents((prev) => [result.user, ...prev])
      setStudentIdInput('')
      setRegisterMessage('학생 등록이 완료되었습니다.')
    } else {
      setRegisterMessage(result.message)
    }
    setRegisterLoading(false)
  }

  const handleRemoveStudent = async (studentUserId: string) => {
    if (!confirm(`학생(${studentUserId}) 등록을 해제할까요?`)) return
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/auth/coach/students/${studentUserId}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        const errorData = (await response.json().catch(() => null)) as { detail?: string } | null
        throw new Error(errorData?.detail || '학생 해제에 실패했습니다.')
      }
      setStudents((prev) => prev.filter((student) => student.user_id !== studentUserId))
      setRegisterMessage('학생 등록이 해제되었습니다.')
    } catch (error) {
      setRegisterMessage(error instanceof Error ? error.message : '학생 해제에 실패했습니다.')
    }
  }

  const handleSearchStudent = async () => {
    const keyword = studentSearchInput.trim()
    if (!keyword) {
      setStudentSearchError('검색어를 입력해주세요.')
      setStudentSearchResults([])
      return
    }
    setStudentSearchLoading(true)
    setStudentSearchError(null)
    try {
      const response = await authorizedFetch(
        `${API_BASE_URL}/auth/coach/students/search?keyword=${encodeURIComponent(keyword)}`,
      )
      if (!response.ok) {
        throw new Error('학생 검색에 실패했습니다.')
      }
      const data = (await response.json()) as DirectoryUser[]
      setStudentSearchResults(data)
    } catch (error) {
      setStudentSearchError(error instanceof Error ? error.message : '학생 검색에 실패했습니다.')
    } finally {
      setStudentSearchLoading(false)
    }
  }

  const handleResetStudentSearch = () => {
    setStudentSearchInput('')
    setStudentSearchResults([])
    setStudentSearchError(null)
  }

  const handleSelectStudent = (student: DirectoryUser) => {
    if (registeredIds.has(student.user_id)) {
      setBatchRegisterMessage('이미 등록된 학생입니다.')
      return
    }
    if (selectedIds.has(student.user_id)) return
    setSelectedStudents((prev) => [student, ...prev])
    setBatchRegisterMessage(null)
  }

  const handleRemoveSelectedStudent = (studentUserId: string) => {
    setSelectedStudents((prev) => prev.filter((student) => student.user_id !== studentUserId))
  }

  const handleBatchRegister = async () => {
    if (selectedStudents.length === 0 || batchRegisterLoading) return
    setBatchRegisterLoading(true)
    setBatchRegisterMessage(null)

    const results = await Promise.all(
      selectedStudents.map((student) => registerStudentRequest(student.user_id)),
    )

    const successUsers: DirectoryUser[] = []
    const failedIds = new Set<string>()
    let alreadyCount = 0

    results.forEach((result, index) => {
      const student = selectedStudents[index]
      if (!result) {
        failedIds.add(student.user_id)
        return
      }
      if (result.status === 'ok') {
        successUsers.push(result.user)
        return
      }
      if (result.message?.includes('이미 등록된 학생')) {
        alreadyCount += 1
        return
      }
      failedIds.add(student.user_id)
    })

    if (successUsers.length > 0) {
      setStudents((prev) => {
        const existing = new Set(prev.map((item) => item.user_id))
        const merged = successUsers.filter((user) => !existing.has(user.user_id))
        return [...merged, ...prev]
      })
    }

    setSelectedStudents((prev) => prev.filter((student) => failedIds.has(student.user_id)))

    const messages: string[] = []
    if (successUsers.length > 0) {
      messages.push(`${successUsers.length}명 등록 완료`)
    }
    if (alreadyCount > 0) {
      messages.push(`${alreadyCount}명은 이미 등록됨`)
    }
    if (failedIds.size > 0) {
      messages.push(`${failedIds.size}명 등록 실패`)
    }
    setBatchRegisterMessage(messages.join(' · ') || '등록할 학생이 없습니다.')
    setBatchRegisterLoading(false)
  }

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>학생 등록</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>학생 등록</h1>
        <p>코치만 접근할 수 있습니다.</p>
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

      <div className="coach-students-hero card">
        <div>
          <h1>학생 등록 대시보드</h1>
          <p>학생 아이디를 검색해 내 수업 학생으로 등록하고, 학습 대상자를 빠르게 관리하세요.</p>
        </div>
        <div className="coach-students-register">
          <label className="label">
            학생 아이디 검색
            <input
              value={studentIdInput}
              onChange={(event) => setStudentIdInput(event.target.value)}
              placeholder="예: student01"
            />
          </label>
          <button type="button" onClick={handleRegisterStudent} disabled={registerLoading || !studentIdInput.trim()}>
            {registerLoading ? '등록 중...' : '학생 등록'}
          </button>
        </div>
        {registerMessage && <p className="helper-text">{registerMessage}</p>}
      </div>

      <div className="card coach-students-search">
        <label className="label">
          학생 검색
          <input
            value={studentSearchInput}
            onChange={(event) => setStudentSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                handleSearchStudent()
              }
            }}
            placeholder="아이디/이름/이메일로 검색하세요"
          />
        </label>
        <button type="button" onClick={handleSearchStudent} disabled={studentSearchLoading}>
          {studentSearchLoading ? '검색 중...' : '학생 검색'}
        </button>
        <button type="button" className="secondary" onClick={handleResetStudentSearch} disabled={studentSearchLoading}>
          검색 초기화
        </button>
      </div>

      <UserDirectoryTable
        users={studentSearchResults}
        loading={studentSearchLoading}
        error={studentSearchError}
        emptyMessage="검색 결과가 없습니다."
        roleOptions={['general']}
        showDateColumns={false}
        rowClickable
        onRowClick={handleSelectStudent}
        tableClassName="admin-users-table--compact"
      />

      <div className="coach-students-selected">
        <div className="coach-students-selected-header">
          <div>
            <h2>등록 대기 학생</h2>
            <p>검색 결과에서 학생을 클릭하면 여기에 추가됩니다.</p>
          </div>
        </div>
        {batchRegisterMessage && <p className="helper-text">{batchRegisterMessage}</p>}
        <UserDirectoryTable
          users={selectedStudents}
          loading={false}
          emptyMessage="등록 대기 학생이 없습니다."
          roleOptions={['general']}
          showDateColumns={false}
          tableClassName="admin-users-table--compact"
          rowAction={(student) => (
            <button
              type="button"
              className="ghost"
              onClick={() => handleRemoveSelectedStudent(student.user_id)}
            >
              제거
            </button>
          )}
        />
        <div className="coach-students-selected-actions">
          <button
            type="button"
            onClick={handleBatchRegister}
            disabled={batchRegisterLoading || selectedStudents.length === 0}
          >
            {batchRegisterLoading ? '등록 중...' : '등록'}
          </button>
        </div>
      </div>

      <UserDirectoryTable
        users={students}
        loading={studentsLoading}
        error={studentsError}
        emptyMessage="등록된 학생이 없습니다. 학생 아이디로 먼저 등록해보세요."
        roleOptions={['general']}
        showDateColumns={false}
        tableClassName="admin-users-table--compact"
        rowAction={(student) => (
          <button
            type="button"
            className="ghost"
            onClick={() => handleRemoveStudent(student.user_id)}
          >
            등록 해제
          </button>
        )}
      />
    </section>
  )
}

export default CoachStudentsPage
