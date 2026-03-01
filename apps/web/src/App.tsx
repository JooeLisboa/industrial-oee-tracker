import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { LeaderPage } from './pages/LeaderPage'
import { DashboardPage } from './pages/DashboardPage'
import { AdminPage } from './pages/AdminPage'
import { ReportsPage } from './pages/ReportsPage'

export function App() {
  const logged = Boolean(localStorage.getItem('token'))
  return (
    <div>
      <header className="bg-slate-900 text-white p-3 flex gap-3">
        <strong>OEE Line Monitor</strong>
        {logged && (
          <>
            <Link to="/leader">Leader</Link><Link to="/dashboard">Dashboard</Link><Link to="/admin">Admin</Link><Link to="/reports">Reports</Link>
          </>
        )}
      </header>
      <main className="p-4">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/leader" element={logged ? <LeaderPage /> : <Navigate to="/login" />} />
          <Route path="/dashboard" element={logged ? <DashboardPage /> : <Navigate to="/login" />} />
          <Route path="/admin" element={logged ? <AdminPage /> : <Navigate to="/login" />} />
          <Route path="/reports" element={logged ? <ReportsPage /> : <Navigate to="/login" />} />
          <Route path="*" element={<Navigate to={logged ? '/leader' : '/login'} />} />
        </Routes>
      </main>
    </div>
  )
}
