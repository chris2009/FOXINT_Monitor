"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Post } from "@/lib/api";

function PostRow({ post }: { post: Post }) {
  const detectionsQuery = useQuery({
    queryKey: ["detections", post.id],
    queryFn: () => api.listDetections(post.id),
  });

  return (
    <li className="p-4 border-b">
      <p className="text-sm text-gray-500">
        {post.type} · {post.published_at ? new Date(post.published_at).toLocaleString() : "sin fecha"}
        {post.is_live && <span className="ml-2 text-red-600 font-semibold">● LIVE</span>}
      </p>
      <p className="mt-1">{post.message ?? <em className="text-gray-400">sin texto</em>}</p>
      {post.transcript && (
        <div className="mt-2 text-sm bg-amber-50 border border-amber-200 rounded p-2">
          <span className="font-medium text-amber-700">🎙️ Transcripción:</span> {post.transcript}
        </div>
      )}
      {post.permalink && (
        <a
          href={post.permalink}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          Ver publicación original
        </a>
      )}

      {detectionsQuery.data && detectionsQuery.data.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {detectionsQuery.data.map((d) => (
            <span key={d.id} className="text-xs bg-gray-100 rounded px-2 py-1">
              {d.analyzer}
              {d.score !== null && `: ${d.score.toFixed(2)}`}
            </span>
          ))}
        </div>
      )}
    </li>
  );
}

export default function PageDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const pageId = Number(id);

  const postsQuery = useQuery({ queryKey: ["posts", pageId], queryFn: () => api.listPosts(pageId) });

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Timeline de publicaciones</h1>

      {postsQuery.isLoading && <p>Cargando...</p>}
      {postsQuery.data?.length === 0 && (
        <p className="text-gray-500">Aún no se ha capturado ningún post de esta página.</p>
      )}

      <ul className="border rounded">
        {postsQuery.data?.map((post) => (
          <PostRow key={post.id} post={post} />
        ))}
      </ul>
    </main>
  );
}
