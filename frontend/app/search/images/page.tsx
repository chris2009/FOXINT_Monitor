"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type ImageSearchResult } from "@/lib/api";

type Mode = "text" | "image";

export default function ImageSearchPage() {
  const [mode, setMode] = useState<Mode>("text");
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [results, setResults] = useState<ImageSearchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const searchMutation = useMutation({
    mutationFn: () =>
      mode === "text" ? api.searchImagesByText(query.trim()) : api.searchImagesByImage(file as File),
    onSuccess: (data) => {
      setResults(data);
      setError(null);
    },
    onError: (err: Error) => setError(err.message),
  });

  const canSubmit = mode === "text" ? query.trim().length > 0 : file !== null;

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Búsqueda visual</h1>
      <p className="text-gray-500 mb-6">
        Busca dentro de las <strong>imágenes</strong> de los posts capturados: por una descripción de texto, o
        subiendo una imagen de referencia para encontrar fotos parecidas.
      </p>

      <div className="flex gap-2 mb-4">
        <button
          className={`px-3 py-1 rounded text-sm border ${mode === "text" ? "bg-black text-white" : ""}`}
          onClick={() => setMode("text")}
        >
          Por texto
        </button>
        <button
          className={`px-3 py-1 rounded text-sm border ${mode === "image" ? "bg-black text-white" : ""}`}
          onClick={() => setMode("image")}
        >
          Por imagen
        </button>
      </div>

      <form
        className="flex gap-2 mb-6"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) searchMutation.mutate();
        }}
      >
        {mode === "text" ? (
          <input
            className="border rounded px-3 py-2 flex-1"
            placeholder="Ej: multitud, incendio, bandera, vehículo..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        ) : (
          <input
            type="file"
            accept="image/*"
            className="border rounded px-3 py-2 flex-1"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        )}
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={searchMutation.isPending || !canSubmit}
        >
          {searchMutation.isPending ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-6">{error}</p>}
      {results?.length === 0 && <p className="text-gray-500">Sin resultados. ¿Ya hay imágenes capturadas?</p>}

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
