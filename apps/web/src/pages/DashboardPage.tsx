import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import api from "../lib/api";

export function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["monthly", 2026, 1],
    queryFn: async () =>
      (await api.get("/reports/monthly?year=2026&month=1")).data,
    retry: false,
  });

  if (isLoading) return <div className="card">Carregando...</div>;
  if (isError) {
    return (
      <div className="card">
        Erro: {(error as any)?.response?.status} {(error as any)?.message}
      </div>
    );
  }

  const items = data?.items ?? [];
  const chart = items.map((i: any, idx: number) => ({
    name: `Run ${idx + 1}`,
    oee: Number(((i.oee ?? 0) * 100).toFixed(2)),
  }));

  return (
    <div className="card">
      <h1 className="text-xl font-bold">Dashboard Supervisor</h1>

      {chart.length === 0 ? (
        <p className="text-slate-600">
          Sem dados para 01/2026. Gere apontamentos/execuções para aparecer
          aqui.
        </p>
      ) : (
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={chart}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="oee" fill="#0f172a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
