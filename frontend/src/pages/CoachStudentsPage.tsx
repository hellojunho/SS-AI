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
  const [registerLoading, setRegisterLoading] = useState(false)
  const [registerMessage, setRegisterMessage] = useState<string | null>(null)

  const registeredIds = useMemo(() => new Set(students.map((student) => student.user_id)), [students])

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

  const registerStudentById = async (studentUserId: string) => {
    if (!studentUserId.trim() || registerLoading) return
    setRegisterLoading(true)
    setRegisterMessage(null)

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
        throw new Error(errorData?.detail || '학생 등록에 실패했습니다.')
      }
      const created = (await response.json()) as DirectoryUser
      setStudents((prev) => [created, ...prev])
      setStudentIdInput('')
      setRegisterMessage('학생 등록이 완료되었습니다.')
    } catch (error) {
      setRegisterMessage(error instanceof Error ? error.message : '학생 등록에 실패했습니다.')
    } finally {
      setRegisterLoading(false)
    }
  }

  const handleRegisterStudent = async () => {
    await registerStudentById(studentIdInput.trim())
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
        rowAction={(student) => {
          if (registeredIds.has(student.user_id)) {
            return <span className="helper-text">등록됨</span>
          }
          return (
            <button
              type="button"
              className="ghost"
              onClick={() => registerStudentById(student.user_id)}
              disabled={registerLoading}
            >
              등록
            </button>
          )
        }}
      />

      <UserDirectoryTable
        users={students}
        loading={studentsLoading}
        error={studentsError}
        emptyMessage="등록된 학생이 없습니다. 학생 아이디로 먼저 등록해보세요."
        roleOptions={['general']}
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
