import { ReactNode } from 'react'

export function LoadingState({ text = 'Carregando...' }: { text?: string }) {
  return <div className="card">{text}</div>
}

export function ErrorState({ text = 'Erro ao carregar dados.', action }: { text?: string; action?: ReactNode }) {
  return (
    <div className="card border border-red-300 text-red-700">
      <p>{text}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  )
}

export function EmptyState({
  text = 'Sem dados disponíveis.',
  action,
}: {
  text?: string
  action?: ReactNode
}) {
  return (
    <div className="card text-slate-500">
      <p>📭 {text}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  )
}
