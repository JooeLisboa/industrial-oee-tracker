import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export function AdminPage() {
  const { data: products, refetch } = useQuery({ queryKey: ['products'], queryFn: async () => (await api.get('/products')).data })
  async function addProduct() {
    await api.post('/products', { name: 'Nova Placa', sku: 'NEW', plates_per_min: 45 })
    refetch()
  }
  return <div className="space-y-4"><div className="card"><h1 className="font-bold text-xl">Admin Panel</h1><button onClick={addProduct}>Adicionar placa exemplo</button></div>
    <div className="card"><h2 className="font-semibold">Produtos</h2><ul>{products?.map((p: any) => <li key={p.id}>{p.name} ({p.plates_per_min} p/min)</li>)}</ul></div></div>
}
