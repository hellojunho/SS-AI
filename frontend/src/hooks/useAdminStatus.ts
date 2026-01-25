import { useEffect, useState } from 'react'

import { authorizedFetch } from '../api'
import { API_BASE_URL } from '../config'

type AdminStatus = 'loading' | 'allowed' | 'forbidden'

type UserInfo = {
  role?: string
}

export const useAdminStatus = () => {
  const [status, setStatus] = useState<AdminStatus>('loading')

  useEffect(() => {
    const loadUser = async () => {
      try {
        const response = await authorizedFetch(`${API_BASE_URL}/auth/me`)
        if (!response.ok) {
          throw new Error('사용자 정보를 불러오지 못했습니다.')
        }
        const data = (await response.json()) as UserInfo
        if (data.role === 'admin') {
          setStatus('allowed')
        } else {
          setStatus('forbidden')
        }
      } catch (error) {
        setStatus('forbidden')
      }
    }
    loadUser()
  }, [])

  return status
}
