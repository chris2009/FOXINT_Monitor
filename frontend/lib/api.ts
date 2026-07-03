const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Page {
  id: number;
  fb_page_id: string;
  name: string;
  category: string;
  platform: string;
  fan_count: number | null;
  followers_count: number | null;
  poll_interval: number;
  is_active: boolean;
  created_at: string;
}

export interface Post {
  id: number;
  page_id: number;
  platform_post_id: string;
  type: string;
  message: string | null;
  transcript: string | null;
  permalink: string | null;
  media_urls: string[] | null;
  is_live: boolean;
  live_status: string | null;
  published_at: string | null;
  captured_at: string;
}

export interface Detection {
  id: number;
  post_id: number;
  analyzer: string;
  result: Record<string, unknown>;
  score: number | null;
  created_at: string;
}

export interface KeywordRule {
  id: number;
  label: string;
  keywords: string[];
  match_type: string;
  severity: string;
  notify_channels: string[];
  is_active: boolean;
}

export interface Alert {
  id: number;
  post_id: number;
  rule_id: number | null;
  channel: string;
  status: string;
  sent_at: string;
}

export interface SearchResult {
  post: Post;
  score: number;
}

export interface ImageSearchResult {
  post: Post;
  image_url: string;
  score: number;
}

export interface EntityCount {
  text: string;
  type: string;
  count: number;
}

export interface FaceSearchResult {
  post: Post;
  image_url: string;
  bbox: number[] | null;
  score: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Error ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  listPages: () => request<Page[]>("/api/pages"),
  registerPage: (payload: { fb_page_id: string; platform?: string; poll_interval?: number }) =>
    request<Page>("/api/pages", { method: "POST", body: JSON.stringify(payload) }),

  listPosts: (pageId: number) => request<Post[]>(`/api/pages/${pageId}/posts`),
  listDetections: (postId: number) => request<Detection[]>(`/api/posts/${postId}/detections`),

  listRules: () => request<KeywordRule[]>("/api/rules"),
  createRule: (payload: Omit<KeywordRule, "id">) =>
    request<KeywordRule>("/api/rules", { method: "POST", body: JSON.stringify(payload) }),
  updateRule: (id: number, payload: Partial<Omit<KeywordRule, "id">>) =>
    request<KeywordRule>(`/api/rules/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  listAlerts: () => request<Alert[]>("/api/alerts"),

  search: (q: string, pageId?: number) => {
    const params = new URLSearchParams({ q });
    if (pageId !== undefined) params.set("page_id", String(pageId));
    return request<SearchResult[]>(`/api/search?${params.toString()}`);
  },

  listEntities: (entityType?: string) => {
    const params = new URLSearchParams();
    if (entityType) params.set("entity_type", entityType);
    return request<EntityCount[]>(`/api/entities?${params.toString()}`);
  },
  postsForEntity: (text: string) =>
    request<Post[]>(`/api/entities/posts?text=${encodeURIComponent(text)}`),

  searchImagesByText: (q: string, pageId?: number) => {
    const params = new URLSearchParams({ q });
    if (pageId !== undefined) params.set("page_id", String(pageId));
    return request<ImageSearchResult[]>(`/api/search/images?${params.toString()}`);
  },

  searchImagesByImage: async (file: File, pageId?: number) => {
    const params = new URLSearchParams();
    if (pageId !== undefined) params.set("page_id", String(pageId));
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API_URL}/api/search/images?${params.toString()}`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail ?? `Error ${response.status}`);
    }
    return (await response.json()) as ImageSearchResult[];
  },

  searchByFace: async (file: File, pageId?: number) => {
    const params = new URLSearchParams();
    if (pageId !== undefined) params.set("page_id", String(pageId));
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API_URL}/api/search/faces?${params.toString()}`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail ?? `Error ${response.status}`);
    }
    return (await response.json()) as FaceSearchResult[];
  },
};
