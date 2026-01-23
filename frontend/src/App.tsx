import { Navigate, Route, Routes } from 'react-router-dom'

import BottomNav from './components/BottomNav'
import { isAuthenticated } from './auth'
import ChatPage from './pages/ChatPage'
import HomePage from './pages/HomePage'
import MyPage from './pages/MyPage'
import QuizPage from './pages/QuizPage'
import SignupPage from './pages/SignupPage'

const App = () => {
  const isLoggedIn = isAuthenticated()

  return (
    <div className="app-shell">
      <main className="content">
        <Routes>
          <Route path="/" element={isLoggedIn ? <Navigate to="/mypage" /> : <HomePage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/mypage" element={isLoggedIn ? <MyPage /> : <Navigate to="/" />} />
          <Route path="/chat" element={isLoggedIn ? <ChatPage /> : <Navigate to="/" />} />
          <Route path="/quiz" element={isLoggedIn ? <QuizPage /> : <Navigate to="/" />} />
        </Routes>
      </main>
      {isLoggedIn && <BottomNav />}
    </div>
  )
}

export default App
