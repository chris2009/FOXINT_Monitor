"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Post } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  persona: "bg-blue-100 text-blue-700",
  lugar: "bg-green-100 text-green-700",
  organización: "bg-purple-100 text-purple-700",
  otro: "bg-gray-100 text-gray-600",
};

export default function EntitiesPage() {
  const [selected, setSelected] = useState<string | null>(null);

  const entitiesQuery = useQuery({ queryKey: ["entities"], queryFn: () => api.listEntities() });
  const postsQuery = useQuery({
    queryKey: ["entity-posts", selected],
    queryFn: () => api.postsForEntity(selected as string),
    enabled: selected !== null,
  });

  return (
    <main className="min-h-screen p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Entidades detectadas</h1>
      <p className="text-gray-500 mb-6">
        Personas, lugares y organizaciones que el sistema encontró automáticamente en los posts. Haz clic en una
        para ver dónde se menciona.
      </p>

      <div className="grid grid-cols-[1fr_2fr] gap-6">
        <div>
          {entitiesQuery.isLoading && <p>Cargando...</p>}
          {entitiesQuery.data?.length === 0 && (
            <p className="text-gray-500">Aún no hay entidades. ¿Ya se procesaron posts con texto?</p>
          )}
          <ul className="border rounded divide-y">
            {entitiesQuery.data?.map((entity) => (
              <li key={`${entity.text}-${entity.type}`}>
                <button
                  className={`w-full text-left p-3 hover:bg-gray-50 flex justify-between items-center ${
                    selected === entity.text ? "bg-gray-100" : ""
                  }`}
                  onClick={() => setSelected(entity.text)}
                >
                  <span>
                    {entity.text}
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded ${TYPE_COLORS[entity.type] ?? ""}`}>
                      {entity.type}
                    </span>
                  </span>
                  <span className="text-sm text-gray-400">{entity.count}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          {selected === null && <p className="text-gray-400">Selecciona una entidad para ver sus menciones.</p>}
          {selected !== null && (
            <>
              <h2 className="font-medium mb-3">Menciones de &quot;{selected}&quot;</h2>
              {postsQuery.isLoading && <p>Cargando...</p>}
              <ul className="space-y-3">
                {postsQuery.data?.map((post: Post) => (
                  <li key={post.id} className="border rounded p-3">
                    <p>{post.message}</p>
                    {post.permalink && (
                      <a
                        href={post.permalink}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Ver publicación
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
