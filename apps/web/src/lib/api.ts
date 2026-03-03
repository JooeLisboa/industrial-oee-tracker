import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:5000/api",
  headers: { "Content-Type": "application/json" },
});

// Interceptor: adiciona Authorization automaticamente
api.interceptors.request.use((config) => {
  const t1 = localStorage.getItem("token");
  const t2 = localStorage.getItem("access_token");
  const token = t1 ?? t2;

  // normaliza pra evitar “só pega depois do F5”
  if (!t1 && t2) localStorage.setItem("token", t2);

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

console.log("API.TS CARREGADO");

export default api;
