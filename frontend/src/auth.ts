import { API_BASE_URL } from './config'

const ACCESS_TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const ACCESS_EXP_KEY = 'accessTokenExpiresAt'
const REFRESH_EXP_KEY = 'refreshTokenExpiresAt'
const SESSION_MINUTES = 10080

type TokenResponse = {
  access_token: string
  refresh_token: string
}

const getNumber = (value: string | null) => (value ? Number(value) : 0)

export const saveTokens = (accessToken: string, refreshToken: string) => {
  const expiresAt = Date.now() + SESSION_MINUTES * 60 * 1000
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  localStorage.setItem(ACCESS_EXP_KEY, String(expiresAt))
  localStorage.setItem(REFRESH_EXP_KEY, String(expiresAt))
  window.dispatchEvent(new Event('authchange'))
}

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(ACCESS_EXP_KEY)
  localStorage.removeItem(REFRESH_EXP_KEY)
  window.dispatchEvent(new Event('authchange'))
}

export const isAccessTokenValid = () => {
  const expiresAt = getNumber(localStorage.getItem(ACCESS_EXP_KEY))
  return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY)) && Date.now() < expiresAt
}

export const isRefreshTokenValid = () => {
  const expiresAt = getNumber(localStorage.getItem(REFRESH_EXP_KEY))
  return Boolean(localStorage.getItem(REFRESH_TOKEN_KEY)) && Date.now() < expiresAt
}

export const isAuthenticated = () => isAccessTokenValid() || isRefreshTokenValid()

const requestRefreshToken = async () => {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) return null
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!response.ok) {
    return null
  }
  return (await response.json()) as TokenResponse
}

export const ensureAccessToken = async () => {
  if (isAccessTokenValid()) {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  }
  if (!isRefreshTokenValid()) {
    clearTokens()
    return null
  }
  try {
    const tokens = await requestRefreshToken()
    if (!tokens) {
      clearTokens()
      return null
    }
    saveTokens(tokens.access_token, tokens.refresh_token)
    return tokens.access_token
  } catch (error) {
    clearTokens()
    return null
  }
}
