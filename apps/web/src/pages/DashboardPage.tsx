import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import api from '../lib/api'

export function DashboardPage() {
  const { data } = useQuery({ queryKey: ['monthly'], queryFn: async () => (await api.get('/reports/monthly?year=2026&month=1')).data })
  const chart = (data?.items || []).map((i: any, idx: number) => ({ name: `Run ${idx + 1}`, oee: Number((i.oee * 100).toFixed(2)) }))
  return <div className="card"><h1 className="text-xl font-bold">Dashboard Supervisor</h1><div style={{ width: '100%', height: 320 }}>
    <ResponsiveContainer><BarChart data={chart}><XAxis dataKey="name" /><YAxis /><Bar dataKey="oee" fill="#0f172a" /></BarChart></ResponsiveContainer>
  </div></div>
}
