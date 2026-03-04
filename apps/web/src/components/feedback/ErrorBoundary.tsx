import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-100 p-6">
          <div className="card max-w-lg">
            <h1 className="font-bold text-xl">Ops! Algo deu errado na interface.</h1>
            <p className="text-slate-600 mt-2">Atualize a página ou faça login novamente.</p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
