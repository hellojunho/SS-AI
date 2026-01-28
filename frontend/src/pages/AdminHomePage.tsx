import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AdminNav from '../components/AdminNav'
import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'
import { useAdminStatus } from '../hooks/useAdminStatus'

type TrafficStats = {
  period: 'day' | 'week' | 'month' | 'year'
  buckets: {
    label: string
    signups: number
    logins: number
    withdrawals: number
  }[]
}

const AdminHomePage = () => {
  const navigate = useNavigate()
  const status = useAdminStatus()
  const [trafficStats, setTrafficStats] = useState<TrafficStats[]>([])
  const [trafficError, setTrafficError] = useState<string | null>(null)
  const [trafficLoading, setTrafficLoading] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState<TrafficStats['period']>('day')

  useEffect(() => {
    if (status !== 'allowed') return
    const loadTraffic = async () => {
      setTrafficLoading(true)
      setTrafficError(null)
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/admin/traffic`)
        if (!response.ok) {
          throw new Error('트래픽 정보를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as TrafficStats[]
        setTrafficStats(data)
      } catch (error) {
        setTrafficError('사용자 유입량 정보를 불러오지 못했습니다.')
      } finally {
        setTrafficLoading(false)
      }
    }
    loadTraffic()
  }, [status])

  const selectedStats = useMemo(
    () => trafficStats.find((stat) => stat.period === selectedPeriod),
    [trafficStats, selectedPeriod],
  )

  const maxTrafficValue = useMemo(() => {
    if (!selectedStats?.buckets.length) return 0
    return Math.max(
      ...selectedStats.buckets.flatMap((bucket) => [bucket.signups, bucket.logins, bucket.withdrawals]),
    )
  }, [selectedStats])

  const labelMap: Record<TrafficStats['period'], string> = {
    day: '일',
    week: '주',
    month: '월',
    year: '년',
  }

  const trafficSeries = [
    { type: 'signup', label: '신규', key: 'signups' },
    { type: 'login', label: '로그인', key: 'logins' },
    { type: 'withdrawal', label: '탈퇴', key: 'withdrawals' },
  ] as const

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
      <div className="card admin-traffic-card">
        <div className="admin-traffic-header">
          <div className="admin-traffic-title">
            <h2>사용자 유입량</h2>
            <p>일/주/월/년 단위 신규 가입, 로그인, 탈퇴 수를 확인하세요.</p>
            <div className="admin-traffic-tabs" role="tablist" aria-label="유입량 기간 선택">
              {(Object.keys(labelMap) as TrafficStats['period'][]).map((period) => {
                const isActive = selectedPeriod === period
                return (
                  <button
                    key={period}
                    id={`traffic-tab-${period}`}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    aria-controls={`traffic-panel-${period}`}
                    className={`admin-traffic-tab${isActive ? ' is-active' : ''}`}
                    onClick={() => setSelectedPeriod(period)}
                  >
                    {labelMap[period]}
                  </button>
                )
              })}
            </div>
          </div>
          <div className="admin-traffic-legend">
            <span className="admin-traffic-legend-item">
              <span className="admin-traffic-dot admin-traffic-dot--signup" />
              신규 회원가입
            </span>
            <span className="admin-traffic-legend-item">
              <span className="admin-traffic-dot admin-traffic-dot--login" />
              로그인
            </span>
            <span className="admin-traffic-legend-item">
              <span className="admin-traffic-dot admin-traffic-dot--withdrawal" />
              회원 탈퇴
            </span>
          </div>
        </div>
        {trafficLoading && <p className="admin-traffic-message">유입량 데이터를 불러오는 중...</p>}
        {!trafficLoading && trafficError && <p className="admin-traffic-message error-text">{trafficError}</p>}
        {!trafficLoading && !trafficError && (
          <div
            className="admin-traffic-chart"
            role="tabpanel"
            id={`traffic-panel-${selectedPeriod}`}
            aria-labelledby={`traffic-tab-${selectedPeriod}`}
          >
            <div className="admin-traffic-columns">
              {(selectedStats?.buckets ?? []).map((bucket, index) => (
                <div key={`${bucket.label}-${index}`} className="admin-traffic-column">
                  <div className="admin-traffic-column-bars">
                    {trafficSeries.map((series) => {
                      const value = bucket[series.key]
                      const height = maxTrafficValue ? Math.max((value / maxTrafficValue) * 100, 6) : 6
                      return (
                        <div
                          key={series.type}
                          className={`admin-traffic-bar admin-traffic-bar--${series.type}`}
                          style={{ height: `${height}%` }}
                          title={`${bucket.label} ${series.label}: ${value}`}
                        />
                      )
                    })}
                  </div>
                  <span className="admin-traffic-column-label">{bucket.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
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
