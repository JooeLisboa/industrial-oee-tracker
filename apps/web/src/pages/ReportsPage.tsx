import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export function ReportsPage() {
  const { data } = useQuery({ queryKey: ['yearly'], queryFn: async () => (await api.get('/reports/yearly?year=2026')).data })
  return <div className="card"><h1 className="font-bold text-xl">Relatórios</h1>
    <p>Total de runs no ano: {data?.items?.length || 0}</p>
  </div>
}
