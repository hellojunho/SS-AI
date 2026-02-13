import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import BottomNav from './components/BottomNav'
import { isAuthenticated } from './auth'
import ChatPage from './pages/ChatPage'
import HomePage from './pages/HomePage'
import MyPage from './pages/MyPage'
import WrongNotesPage from './pages/WrongNotesPage'
import AdminHomePage from './pages/AdminHomePage'
import AdminQuizDetailPage from './pages/AdminQuizDetailPage'
import AdminQuizzesPage from './pages/AdminQuizzesPage'
import AdminUsersPage from './pages/AdminUsersPage'
import AdminUserEditPage from './pages/AdminUserEditPage'
import AllQuizPage from './pages/AllQuizPage'
import QuizPage from './pages/QuizPage'
import SignupPage from './pages/SignupPage'
import AdminDocsPage from './pages/AdminDocsPage'
import AdminLlmTokensPage from './pages/AdminLlmTokensPage'
import CoachStudentsPage from './pages/CoachStudentsPage'

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

  useEffect(() => {
    const handleButtonClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null
      const button = target?.closest('button')
      if (!button || button.disabled) return
      if (button.classList.contains('button-click-spinner')) return
      if (button.querySelector('.spinner')) return
      button.classList.add('button-click-spinner')
      window.setTimeout(() => {
        button.classList.remove('button-click-spinner')
      }, 600)
    }
    document.addEventListener('click', handleButtonClick)
    return () => {
      document.removeEventListener('click', handleButtonClick)
    }
  }, [])

  return (
    <div className="app-shell">
      <main className="content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/mypage" element={isLoggedIn ? <MyPage /> : <Navigate to="/" />} />
          <Route
            path="/mypage/wrong-notes"
            element={isLoggedIn ? <WrongNotesPage /> : <Navigate to="/" />}
          />
          <Route path="/chat" element={isLoggedIn ? <ChatPage /> : <Navigate to="/" />} />
          <Route path="/quiz" element={isLoggedIn ? <QuizPage /> : <Navigate to="/" />} />
          <Route path="/quiz/all" element={isLoggedIn ? <AllQuizPage /> : <Navigate to="/" />} />
          <Route path="/admin" element={isLoggedIn ? <AdminHomePage /> : <Navigate to="/" />} />
          <Route
            path="/admin/quizzes"
            element={isLoggedIn ? <AdminQuizzesPage /> : <Navigate to="/" />}
          />
          <Route
            path="/admin/quizzes/:id"
            element={isLoggedIn ? <AdminQuizDetailPage /> : <Navigate to="/" />}
          />
          <Route
            path="/admin/users"
            element={isLoggedIn ? <AdminUsersPage /> : <Navigate to="/" />}
          />
          <Route path="/admin/users/:id" element={isLoggedIn ? <AdminUserEditPage /> : <Navigate to="/" />} />
          <Route path="/admin/docs" element={isLoggedIn ? <AdminDocsPage /> : <Navigate to="/" />} />
          <Route path="/admin/llm" element={isLoggedIn ? <AdminLlmTokensPage /> : <Navigate to="/" />} />
          <Route path="/coach/students" element={isLoggedIn ? <CoachStudentsPage /> : <Navigate to="/" />} />
        </Routes>
      </main>
      {isLoggedIn && <BottomNav />}
    </div>
  )
}

export default App
