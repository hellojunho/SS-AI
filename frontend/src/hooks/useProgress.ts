import { useCallback, useEffect, useRef, useState } from 'react'

const MAX_BEFORE_COMPLETE = 90

const useProgress = (step = 6, intervalMs = 250) => {
  const [progress, setProgress] = useState(0)
  const [visible, setVisible] = useState(false)
  const intervalRef = useRef<number | null>(null)
  const timeoutRef = useRef<number | null>(null)

  const clearTimers = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const start = useCallback(() => {
    clearTimers()
    setVisible(true)
    setProgress(0)
    intervalRef.current = window.setInterval(() => {
      setProgress((prev) => (prev < MAX_BEFORE_COMPLETE ? Math.min(MAX_BEFORE_COMPLETE, prev + step) : prev))
    }, intervalMs)
  }, [clearTimers, intervalMs, step])

  const setProgressValue = useCallback(
    (value: number) => {
      clearTimers()
      setVisible(true)
      setProgress(Math.max(0, Math.min(100, value)))
    },
    [clearTimers]
  )

  const finish = useCallback(() => {
    clearTimers()
    setProgress(100)
    timeoutRef.current = window.setTimeout(() => {
      setVisible(false)
      setProgress(0)
    }, 500)
  }, [clearTimers])

  useEffect(() => {
    return () => {
      clearTimers()
    }
  }, [clearTimers])

  return { progress, visible, start, finish, setProgressValue }
}

export default useProgress
