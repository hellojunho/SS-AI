import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

type LearnStatus = {
  status: 'idle' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
}

const AdminDocsPage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [uploadMessage, setUploadMessage] = useState('')
  const [urlInput, setUrlInput] = useState('')
  const [urlMessage, setUrlMessage] = useState('')
  const [learnStatus, setLearnStatus] = useState<LearnStatus>({
    status: 'idle',
    progress: 0,
    message: '대기 중',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const isLearning = learnStatus.status === 'running'

  const loadLearnStatus = async () => {
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/admin/docs/learn/status`)
      if (!response.ok) {
        throw new Error('학습 상태를 불러오지 못했습니다.')
      }
      const data = (await response.json()) as LearnStatus
      setLearnStatus(data)
    } catch (error) {
      setLearnStatus((prev) => ({ ...prev, message: '학습 상태를 불러오지 못했습니다.' }))
    }
  }

  useEffect(() => {
    if (status !== 'allowed') return
    loadLearnStatus()
  }, [status])

  useEffect(() => {
    if (status !== 'allowed' || !isLearning) return
    const interval = window.setInterval(() => {
      loadLearnStatus()
    }, 1200)
    return () => window.clearInterval(interval)
  }, [status, isLearning])

  const acceptedTypes = useMemo(() => '.txt,.csv,.pdf,.md', [])

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setUploadMessage('업로드할 파일을 선택해주세요.')
      return
    }
    setIsSubmitting(true)
    setUploadMessage('')
    try {
      for (const file of Array.from(selectedFiles)) {
        const formData = new FormData()
        formData.append('file', file)
        const response = await authorizedFetch(`${API_BASE_URL}/admin/docs/upload`, {
          method: 'POST',
          body: formData,
        })
        if (!response.ok) {
          const detail = await response.json()
          throw new Error(detail.detail ?? '업로드 실패')
        }
      }
      setUploadMessage('업로드가 완료되었습니다.')
      setSelectedFiles(null)
    } catch (error) {
      setUploadMessage(error instanceof Error ? error.message : '업로드에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAddUrl = async () => {
    if (!urlInput.trim()) {
      setUrlMessage('추가할 URL을 입력해주세요.')
      return
    }
    setIsSubmitting(true)
    setUrlMessage('')
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/admin/docs/web`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput.trim() }),
      })
      if (!response.ok) {
        const detail = await response.json()
        throw new Error(detail.detail ?? 'URL 추가 실패')
      }
      setUrlMessage('웹 URL이 저장되었습니다.')
      setUrlInput('')
    } catch (error) {
      setUrlMessage(error instanceof Error ? error.message : 'URL 추가에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLearn = async () => {
    setIsSubmitting(true)
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/admin/docs/learn`, { method: 'POST' })
      if (!response.ok) {
        const detail = await response.json()
        throw new Error(detail.detail ?? '학습 시작 실패')
      }
      await loadLearnStatus()
    } catch (error) {
      setLearnStatus((prev) => ({
        ...prev,
        status: 'failed',
        message: error instanceof Error ? error.message : '학습 시작 실패',
      }))
    } finally {
      setIsSubmitting(false)
    }
  }

  if (status === 'loading') {
    return (
      <section className="page">
        <h1>문서 학습 관리</h1>
        <p>권한을 확인하고 있습니다.</p>
      </section>
    )
  }

  if (status === 'forbidden') {
    return (
      <section className="page">
        <h1>문서 학습 관리</h1>
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
      <h1>문서 학습 관리</h1>
      <p>문서를 업로드하고 학습을 실행할 수 있습니다.</p>
      <AdminNav />

      <div className="admin-docs-grid">
        <div className="card admin-docs-card">
          <h2>문서 업로드</h2>
          <p>지원 형식: txt / csv / pdf / md</p>
          <input
            type="file"
            accept={acceptedTypes}
            multiple
            onChange={(event) => setSelectedFiles(event.target.files)}
          />
          <button type="button" onClick={handleUpload} disabled={isSubmitting || isLearning}>
            파일 업로드
          </button>
          {uploadMessage && <p className="admin-docs-message">{uploadMessage}</p>}
        </div>

        <div className="card admin-docs-card">
          <h2>웹 URL 추가</h2>
          <p>웹 페이지는 URL을 저장한 뒤 학습 시 함께 반영됩니다.</p>
          <input
            type="text"
            placeholder="https://example.com/article"
            value={urlInput}
            onChange={(event) => setUrlInput(event.target.value)}
          />
          <button type="button" onClick={handleAddUrl} disabled={isSubmitting || isLearning}>
            URL 저장
          </button>
          {urlMessage && <p className="admin-docs-message">{urlMessage}</p>}
        </div>

        <div className="card admin-docs-card">
          <h2>학습 실행</h2>
          <p>문서 수집 → 청킹 → 임베딩 → 저장 순서로 진행됩니다.</p>
          <button type="button" onClick={handleLearn} disabled={isSubmitting || isLearning}>
            {isLearning ? '학습 진행 중' : '학습 시작'}
          </button>
          <div className="progress-bar-wrapper">
            <div className="progress-bar-header">
              <span>{learnStatus.message}</span>
              <span>{learnStatus.progress}%</span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${learnStatus.progress}%` }} />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default AdminDocsPage
