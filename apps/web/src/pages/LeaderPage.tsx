import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import { ApiListResponse, LineOverviewItem } from '../types/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/feedback/States'

export function LeaderPage() {
  const { token } = useAuth()
  const overview = useQuery({
    queryKey: ['overview'],
    enabled: Boolean(token),
    refetchInterval: 4000,
    queryFn: async () => (await api.get<ApiListResponse<LineOverviewItem>>('/status/overview')).data,
  })

  if (overview.isLoading) return <LoadingState text="Carregando status das linhas..." />
  if (overview.isError) {
    return (
      <ErrorState
        text="Não foi possível carregar o painel ao vivo."
        action={
          <button type="button" onClick={() => overview.refetch()}>
            Tentar novamente
          </button>
        }
      />
    )
  }
  if (!overview.data?.items.length) {
    return (
      <EmptyState
        text="Nenhuma linha cadastrada para monitoramento."
        action={<Link to="/admin" className="text-slate-900 underline">Ir para Admin e cadastrar linha</Link>}
      />
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Painel ao vivo do Líder</h1>
      {overview.data.items.map((line) => (
        <section key={line.line.id} className="card">
          <h2 className="font-semibold text-lg">{line.line.name}</h2>
          {!line.machines.length ? (
            <EmptyState
              text="Sem máquinas associadas a esta linha."
              action={<Link to="/admin" className="text-slate-900 underline">Associar máquinas</Link>}
            />
          ) : (
            <div className="grid md:grid-cols-3 gap-3 mt-3">
              {line.machines.map((entry) => (
                <article className="rounded border bg-white p-3" key={entry.machine.id}>
                  <p className="font-medium">{entry.machine.name}</p>
                  <p className="text-sm text-slate-600">Status atual: {entry.state.status}</p>
                  <p className="text-xs text-slate-500 mt-1">Desde: {new Date(entry.state.since_at).toLocaleString()}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  )
}
