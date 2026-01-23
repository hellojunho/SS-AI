import { Route, Routes } from 'react-router-dom'

import BottomNav from './components/BottomNav'
import ChatPage from './pages/ChatPage'
import HomePage from './pages/HomePage'
import QuizPage from './pages/QuizPage'

const App = () => {
  return (
    <div className="app-shell">
      <main className="content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/quiz" element={<QuizPage />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  )
}

export default App
