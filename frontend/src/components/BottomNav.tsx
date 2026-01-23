import { NavLink } from 'react-router-dom'

const BottomNav = () => {
  return (
    <nav className="bottom-nav">
      <NavLink to="/chat" className={({ isActive }) => (isActive ? 'active' : '')}>
        Chat
      </NavLink>
      <NavLink to="/quiz" className={({ isActive }) => (isActive ? 'active' : '')}>
        Quiz
      </NavLink>
      <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')}>
        Home
      </NavLink>
    </nav>
  )
}

export default BottomNav
