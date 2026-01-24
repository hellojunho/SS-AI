import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import BottomNav from './components/BottomNav'
import { isAuthenticated } from './auth'
import ChatPage from './pages/ChatPage'
import HomePage from './pages/HomePage'
import MyPage from './pages/MyPage'
import AdminPage from './pages/AdminPage'
import QuizPage from './pages/QuizPage'
import SignupPage from './pages/SignupPage'

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated())

  useEffect(() => {
    const handleAuthChange = () => setIsLoggedIn(isAuthenticated())
    window.addEventListener('authchange', handleAuthChange)
    window.addEventListener('storage', handleAuthChange)
    return () => {
      window.removeEventListener('authchange', handleAuthChange)
      window.removeEventListener('storage', handleAuthChange)
    }
  }, [])

  return (
    <div className="app-shell">
      <main className="content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/mypage" element={isLoggedIn ? <MyPage /> : <Navigate to="/" />} />
          <Route path="/chat" element={isLoggedIn ? <ChatPage /> : <Navigate to="/" />} />
          <Route path="/quiz" element={isLoggedIn ? <QuizPage /> : <Navigate to="/" />} />
          <Route path="/admin" element={isLoggedIn ? <AdminPage /> : <Navigate to="/" />} />
        </Routes>
      </main>
      {isLoggedIn && <BottomNav />}
    </div>
  )
}

export default App
