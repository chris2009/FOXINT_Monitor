"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type SearchResult } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);

  const searchMutation = useMutation({
    mutationFn: (q: string) => api.search(q),
    onSuccess: (data) => setResults(data),
  });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Búsqueda semántica</h1>
      <p className="text-gray-500 mb-6">
        Busca por significado, no solo por palabras exactas, sobre todos los posts ya capturados de las páginas
        monitoreadas.
      </p>

      <form
        className="flex gap-2 mb-6"
        onSubmit={(e) => {
          e.preventDefault();
          if (query.trim()) searchMutation.mutate(query.trim());
        }}
      >
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="Ej: protestas, obras públicas, salud..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={searchMutation.isPending}
        >
          {searchMutation.isPending ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {results?.length === 0 && <p className="text-gray-500">Sin resultados. ¿Ya hay posts capturados?</p>}

      <ul className="space-y-3">
        {results?.map((result) => (
          <li key={result.post.id} className="border rounded p-4">
            <div className="flex justify-between items-start gap-4">
              <p>{result.post.message ?? <em className="text-gray-400">sin texto</em>}</p>
              <span className="text-xs bg-gray-100 rounded px-2 py-1 whitespace-nowrap">
                {(result.score * 100).toFixed(0)}%
              </span>
            </div>
            {result.post.permalink && (
              <a
                href={result.post.permalink}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                Ver publicación original
              </a>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
