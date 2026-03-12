import { useEffect, useState } from 'react'
import api, { setToken } from './api'
import AuthPage from './authpage'
import DashboardPage from './dashboard'
import HistoryPage from './historypage'
import SettingsPage from './settingspage'

const TABS = ['dashboard', 'history', 'settings']

export default function App() {
  const [user, setUser] = useState(null)
  const [tab, setTab] = useState('dashboard')

  console.log('App component rendering')

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const response = await api.get('/me')
        setUser(response.data.user)
      } catch {
        setToken(null)
      }
    }
    bootstrap()
  }, [])

  const handleAuth = (token, authUser) => {
    setToken(token)
    setUser(authUser)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  if (!user) {
    return <AuthPage onAuthenticated={handleAuth} />
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Driver AI Co-Pilot</h1>
        <p className="driver-id">Driver ID: {user.driverId}</p>
        {TABS.map((item) => (
          <button
            key={item}
            className={tab === item ? 'active' : ''}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
        <button onClick={logout}>Logout</button>
      </aside>
      <main className="content">
        {tab === 'dashboard' && <DashboardPage user={user} />}
        {tab === 'history' && <HistoryPage />}
        {tab === 'settings' && <SettingsPage user={user} onUserUpdate={setUser} />}
      </main>
    </div>
  )
}
