import { ensureAccessToken } from './auth'

export const authorizedFetch = async (input: RequestInfo, init?: RequestInit) => {
  const token = await ensureAccessToken()
  if (!token) {
    throw new Error('로그인이 필요합니다.')
  }
  const headers = new Headers(init?.headers)
  headers.set('Authorization', `Bearer ${token}`)
  return fetch(input, { ...init, headers })
}
