"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function RulesPage() {
  const queryClient = useQueryClient();
  const [label, setLabel] = useState("");
  const [keywords, setKeywords] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [error, setError] = useState<string | null>(null);

  const rulesQuery = useQuery({ queryKey: ["rules"], queryFn: api.listRules });

  const createMutation = useMutation({
    mutationFn: api.createRule,
    onSuccess: () => {
      setLabel("");
      setKeywords("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => api.updateRule(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rules"] }),
  });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Reglas de keywords</h1>
      <p className="text-gray-500 mb-6">Disparan una detección y una alerta cuando un post nuevo las contiene.</p>

      <form
        className="grid grid-cols-[1fr_1fr_auto_auto] gap-2 mb-2"
        onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate({
            label,
            keywords: keywords
              .split(",")
              .map((k) => k.trim())
              .filter(Boolean),
            match_type: "any",
            severity,
            notify_channels: ["telegram"],
            is_active: true,
          });
        }}
      >
        <input
          className="border rounded px-3 py-2"
          placeholder="Etiqueta"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          required
        />
        <input
          className="border rounded px-3 py-2"
          placeholder="keywords separadas por coma"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          required
        />
        <select className="border rounded px-3 py-2" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={createMutation.isPending}
        >
          Crear
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-6">{error}</p>}

      <ul className="divide-y border rounded">
        {rulesQuery.data?.map((rule) => (
          <li key={rule.id} className="p-4 flex justify-between items-center">
            <div>
              <p className="font-medium">
                {rule.label} <span className="text-xs text-gray-400">({rule.severity})</span>
              </p>
              <p className="text-sm text-gray-500">{rule.keywords.join(", ")}</p>
            </div>
            <button
              className="text-xs px-2 py-1 rounded border"
              onClick={() => toggleMutation.mutate({ id: rule.id, is_active: !rule.is_active })}
            >
              {rule.is_active ? "desactivar" : "activar"}
            </button>
          </li>
        ))}
        {rulesQuery.data?.length === 0 && <li className="p-4 text-gray-500">No hay reglas todavía.</li>}
      </ul>
    </main>
  );
}
