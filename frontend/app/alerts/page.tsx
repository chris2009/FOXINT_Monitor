"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function AlertsPage() {
  const alertsQuery = useQuery({ queryKey: ["alerts"], queryFn: api.listAlerts });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Historial de alertas</h1>

      {alertsQuery.isLoading && <p>Cargando...</p>}

      <ul className="divide-y border rounded">
        {alertsQuery.data?.map((alert) => (
          <li key={alert.id} className="p-4 flex justify-between">
            <span>
              Post #{alert.post_id} · canal {alert.channel}
            </span>
            <span className="text-sm text-gray-500">{new Date(alert.sent_at).toLocaleString()}</span>
          </li>
        ))}
        {alertsQuery.data?.length === 0 && <li className="p-4 text-gray-500">Sin alertas todavía.</li>}
      </ul>
    </main>
  );
}
