export interface ApiListResponse<T> {
  items: T[]
}

export interface User {
  id: number
  name: string
  email: string
  role: 'ADMIN' | 'LEADER' | 'VIEWER'
}

export interface LoginResponse {
  access_token: string
  user: User
}

export interface MachineState {
  machine_id: number
  status: string
  since_at: string
  current_run_id: number | null
}

export interface LineOverviewItem {
  line: { id: number; name: string }
  machines: { machine: { id: number; name: string }; state: MachineState }[]
}

export interface OeeItem {
  run_id: number
  oee: number
  availability: number
  performance: number
  quality: number
}

export interface MonthlyReportResponse {
  year: number
  month: number
  items: OeeItem[]
}

export interface YearlyReportResponse {
  year: number
  items: OeeItem[]
}
