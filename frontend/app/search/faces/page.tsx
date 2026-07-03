"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type FaceSearchResult } from "@/lib/api";

export default function FaceSearchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [results, setResults] = useState<FaceSearchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const searchMutation = useMutation({
    mutationFn: () => api.searchByFace(file as File),
    onSuccess: (data) => {
      setResults(data);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
      setResults(null);
    },
  });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Búsqueda facial</h1>
      <p className="text-gray-500 mb-2">
        Sube una imagen con una cara y encuentra fotos con caras parecidas <strong>entre lo que el sistema ya
        capturó</strong> de las páginas monitoreadas.
      </p>
      <p className="text-xs text-gray-400 mb-6">
        Es una búsqueda por similitud sobre el corpus capturado — no identifica personas ni busca en la web abierta.
      </p>

      <form
        className="flex gap-2 mb-6"
        onSubmit={(e) => {
          e.preventDefault();
          if (file) searchMutation.mutate();
        }}
      >
        <input
          type="file"
          accept="image/*"
          className="border rounded px-3 py-2 flex-1"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={searchMutation.isPending || !file}
        >
          {searchMutation.isPending ? "Buscando..." : "Buscar cara"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-6">{error}</p>}
      {results?.length === 0 && <p className="text-gray-500">Sin coincidencias entre las caras capturadas.</p>}

      <ul className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {results?.map((result, index) => (
          <li key={`${result.post.id}-${index}`} className="border rounded overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={result.image_url} alt="" className="w-full h-40 object-cover" />
            <div className="p-2 flex justify-between items-center text-sm">
              <span className="text-gray-500">Post #{result.post.id}</span>
              <span className="bg-gray-100 rounded px-2 py-0.5">{(result.score * 100).toFixed(0)}%</span>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
