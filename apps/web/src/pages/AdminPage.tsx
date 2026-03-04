import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import { ApiListResponse } from '../types/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/feedback/States'

interface Product {
  id: number
  name: string
  plates_per_min: number
}

export function AdminPage() {
  const { token } = useAuth()
  const products = useQuery({
    queryKey: ['products'],
    enabled: Boolean(token),
    queryFn: async () => (await api.get<ApiListResponse<Product>>('/products')).data,
  })

  if (products.isLoading) return <LoadingState text="Carregando cadastros..." />
  if (products.isError) {
    return (
      <ErrorState
        text="Falha ao buscar produtos."
        action={
          <button type="button" onClick={() => products.refetch()}>
            Tentar novamente
          </button>
        }
      />
    )
  }
  if (!products.data?.items.length) {
    return (
      <EmptyState
        text="Nenhum produto cadastrado."
        action={<p className="text-xs">Use os endpoints de cadastro para inserir produtos iniciais.</p>}
      />
    )
  }

  return (
    <div className="card">
      <h1 className="font-bold text-xl">Admin Panel</h1>
      <p className="text-slate-600 mb-4">Gestão de placas/produtos cadastrados</p>
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b">
            <th className="py-2">Produto</th>
            <th className="py-2">Ritmo nominal</th>
          </tr>
        </thead>
        <tbody>
          {products.data.items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="py-2">{item.name}</td>
              <td className="py-2">{item.plates_per_min} placas/min</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
