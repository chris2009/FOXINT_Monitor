"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

export default function PagesDashboard() {
  const queryClient = useQueryClient();
  const [fbPageId, setFbPageId] = useState("");
  const [pollInterval, setPollInterval] = useState(300);
  const [error, setError] = useState<string | null>(null);

  const pagesQuery = useQuery({ queryKey: ["pages"], queryFn: api.listPages });

  const registerMutation = useMutation({
    mutationFn: api.registerPage,
    onSuccess: () => {
      setFbPageId("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Páginas monitoreadas</h1>
      <p className="text-gray-500 mb-6">
        Solo se aceptan Páginas públicas de Facebook — los perfiles personales se rechazan automáticamente.
      </p>

      <form
        className="flex gap-2 mb-2"
        onSubmit={(e) => {
          e.preventDefault();
          registerMutation.mutate({ fb_page_id: fbPageId, poll_interval: pollInterval });
        }}
      >
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="ID de la página de Facebook"
          value={fbPageId}
          onChange={(e) => setFbPageId(e.target.value)}
          required
        />
        <input
          type="number"
          className="border rounded px-3 py-2 w-32"
          value={pollInterval}
          onChange={(e) => setPollInterval(Number(e.target.value))}
          min={60}
        />
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={registerMutation.isPending}
        >
          {registerMutation.isPending ? "Validando..." : "Registrar"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-6">{error}</p>}

      {pagesQuery.isLoading && <p>Cargando...</p>}
      {pagesQuery.error && <p className="text-red-600">Error cargando páginas</p>}

      <ul className="divide-y border rounded">
        {pagesQuery.data?.map((page) => (
          <li key={page.id} className="p-4 flex justify-between items-center">
            <div>
              <Link href={`/pages/${page.id}`} className="font-medium hover:underline">
                {page.name}
              </Link>
              <p className="text-sm text-gray-500">
                {page.category} · {page.fan_count ?? "?"} fans · cada {page.poll_interval}s
              </p>
            </div>
            <span
              className={`text-xs px-2 py-1 rounded ${
                page.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
              }`}
            >
              {page.is_active ? "activa" : "pausada"}
            </span>
          </li>
        ))}
        {pagesQuery.data?.length === 0 && <li className="p-4 text-gray-500">Aún no hay páginas registradas.</li>}
      </ul>
    </main>
  );
}
