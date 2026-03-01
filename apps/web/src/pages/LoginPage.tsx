import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

export function LoginPage() {
  const nav = useNavigate()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')

  async function submit(e: FormEvent) {
    e.preventDefault()
    try {
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', res.data.access_token)
      nav('/leader')
    } catch {
      setError('Credenciais inválidas')
    }
  }

  return <form className="card max-w-md mx-auto flex flex-col gap-2" onSubmit={submit}><h1 className="font-bold text-xl">Login</h1>
    <input value={email} onChange={(e) => setEmail(e.target.value)} />
    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
    {error && <p className="text-red-600">{error}</p>}
    <button type="submit">Entrar</button>
  </form>
}
