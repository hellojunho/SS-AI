import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

const AdminUserEditPage = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [user, setUser] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [password, setPassword] = useState('')

  useEffect(() => {
    if (!id) return
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const resp = await authorizedFetch(`${API_BASE_URL}/auth/admin/users/${id}`)
        if (!resp.ok) throw new Error('불러오기 실패')
        const data = await resp.json()
        setUser(data)
      } catch (err) {
        setError('사용자 정보를 불러오지 못했습니다.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      const payload: any = {
        user_name: user.user_name,
        email: user.email,
        role: user.role,
      }
      if (password.trim()) payload.password = password
      const resp = await authorizedFetch(`${API_BASE_URL}/auth/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) throw new Error('저장 실패')
      const updated = await resp.json()
      setUser(updated)
      setPassword('')
    } catch (err) {
      setError('사용자 정보를 저장하지 못했습니다.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="page"><p>불러오는 중...</p></div>
  if (!user) return <div className="page"><p>{error ?? '사용자를 찾을 수 없습니다.'}</p></div>

  return (
    <section className="page">
      <div className="chat-header">
        <button type="button" className="chat-nav-button" onClick={() => navigate(-1)}>
          이전
        </button>
      </div>
      <h1>사용자 수정</h1>
      <form className="card" onSubmit={handleSubmit}>
        <label className="label">
          ID
          <input value={user.user_id} readOnly />
        </label>
        <label className="label">
          이름
          <input value={user.user_name} onChange={(e) => setUser({ ...user, user_name: e.target.value })} />
        </label>
        <label className="label">
          이메일
          <input value={user.email} onChange={(e) => setUser({ ...user, email: e.target.value })} />
        </label>
        <label className="label">
          역할
          <select value={user.role} onChange={(e) => setUser({ ...user, role: e.target.value })}>
            <option value="general">general</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <label className="label">
          상태
          <input value={user.is_active ? '활성' : '탈퇴'} readOnly />
        </label>
        <label className="label">
          탈퇴 일시
          <input value={user.deactivated_at ? new Date(user.deactivated_at).toLocaleString() : '-'} readOnly />
        </label>
        <label className="label">
          새 비밀번호
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="변경할 새 비밀번호" />
        </label>
        <label className="label">
            가입일
            <input value={new Date(user.created_at).toLocaleString()} readOnly />
        </label>
        <label className="label">
            마지막 로그인
            <input value={user.last_logined ? new Date(user.last_logined).toLocaleString() : '로그인 기록 없음'} readOnly />
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" disabled={saving}>{saving ? '저장 중' : '저장'}</button>
          <button type="button" onClick={() => navigate('/admin/users')}>취소</button>
        </div>
        {error && <p className="helper-text error-text">{error}</p>}
      </form>
    </section>
  )
}

export default AdminUserEditPage
