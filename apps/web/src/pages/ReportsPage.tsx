import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import { YearlyReportResponse } from '../types/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/feedback/States'

export function ReportsPage() {
  const { token } = useAuth()
  const year = new Date().getFullYear()

  const yearly = useQuery({
    queryKey: ['yearly', year],
    enabled: Boolean(token),
    queryFn: async () => (await api.get<YearlyReportResponse>(`/reports/yearly?year=${year}`)).data,
  })

  if (yearly.isLoading) return <LoadingState text="Carregando relatórios anuais..." />
  if (yearly.isError) {
    return (
      <ErrorState
        text="Falha ao buscar relatório anual."
        action={
          <button type="button" onClick={() => yearly.refetch()}>
            Tentar novamente
          </button>
        }
      />
    )
  }
  if (!yearly.data?.items.length) {
    return (
      <EmptyState
        text="Nenhuma execução encontrada neste ano."
        action={<Link to="/leader" className="text-slate-900 underline">Gerar novas execuções</Link>}
      />
    )
  }

  return (
    <div className="grid gap-4">
      <div className="card">
        <h1 className="font-bold text-xl">Relatórios</h1>
        <p className="text-slate-600">Total de runs no ano: {yearly.data.items.length}</p>
      </div>
      <div className="card">
        <h2 className="font-semibold">Ranking por OEE</h2>
        <ol className="list-decimal ml-6 mt-2">
          {yearly.data.items
            .slice()
            .sort((a, b) => b.oee - a.oee)
            .map((item) => (
              <li key={item.run_id}>Run #{item.run_id} - {(item.oee * 100).toFixed(2)}%</li>
            ))}
        </ol>
      </div>
    </div>
  )
}
