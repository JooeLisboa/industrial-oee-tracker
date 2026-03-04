import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const nav = [
  { to: '/leader', label: 'Leader Live' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/admin', label: 'Admin' },
  { to: '/reports', label: 'Reports' },
]

export function AppShell({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  const { logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex min-h-screen">
        <aside className="w-64 bg-slate-900 text-white p-4 hidden md:block">
          <h1 className="font-bold text-xl mb-6">OEE Line Monitor</h1>
          <nav className="space-y-2">
            {nav.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`block rounded px-3 py-2 ${pathname === item.to ? 'bg-slate-700' : 'hover:bg-slate-800'}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex-1">
          <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Painel Industrial</h2>
            </div>
            <button onClick={logout} className="rounded-md bg-slate-900 px-3 py-2 text-white">Logout</button>
          </header>
          <main className="p-4">{children}</main>
        </div>
      </div>
    </div>
  )
}
