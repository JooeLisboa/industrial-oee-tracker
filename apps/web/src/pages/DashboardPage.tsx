import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import api from '../lib/api'
import { MonthlyReportResponse } from '../types/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/feedback/States'

export function DashboardPage() {
  const { token } = useAuth()
  const today = new Date()

  const monthly = useQuery({
    queryKey: ['monthly', today.getFullYear(), today.getMonth() + 1],
    enabled: Boolean(token),
    queryFn: async () =>
      (
        await api.get<MonthlyReportResponse>(`/reports/monthly?year=${today.getFullYear()}&month=${today.getMonth() + 1}`)
      ).data,
  })

  if (monthly.isLoading) return <LoadingState text="Carregando dashboard..." />
  if (monthly.isError) {
    return (
      <ErrorState
        text="Falha ao carregar relatório mensal."
        action={
          <button type="button" onClick={() => monthly.refetch()}>
            Tentar novamente
          </button>
        }
      />
    )
  }
  if (!monthly.data?.items.length) {
    return (
      <EmptyState
        text="Sem execuções no período selecionado."
        action={<Link to="/leader" className="text-slate-900 underline">Iniciar operação no painel do líder</Link>}
      />
    )
  }

  const chart = monthly.data.items.map((item, idx) => ({ name: `Run ${idx + 1}`, oee: Number((item.oee * 100).toFixed(2)) }))

  return (
    <div className="card">
      <h1 className="text-xl font-bold">Dashboard Supervisor</h1>
      <p className="text-slate-600">OEE do mês por execução</p>
      <div style={{ width: '100%', height: 320 }} className="mt-4">
        <ResponsiveContainer>
          <BarChart data={chart}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="oee" fill="#0f172a" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
