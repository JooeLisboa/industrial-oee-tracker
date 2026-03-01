import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export function LeaderPage() {
  const { data, refetch } = useQuery({ queryKey: ['overview'], queryFn: async () => (await api.get('/status/overview')).data, refetchInterval: 4000 })

  async function quick(runId: number, action: string) {
    if (action === 'close') await api.post('/runs/close', { run_id: runId })
    refetch()
  }

  return <div className="space-y-4"><h1 className="text-2xl font-bold">Painel ao vivo do Líder</h1>
    {data?.lines?.map((l: any) => <div key={l.line.id} className="card"><h2 className="font-semibold">{l.line.name}</h2>
      <div className="grid grid-cols-3 gap-3">{l.machines.map((m: any) => <div className="border rounded p-3" key={m.machine.id}><p>{m.machine.name}</p><p>Status: {m.state.status}</p>
        <button onClick={() => quick(m.state.current_run_id, 'close')}>Fechar run</button></div>)}</div></div>)}
  </div>
}
