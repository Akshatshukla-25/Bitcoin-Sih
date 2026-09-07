// API Client for FastAPI backend (Offline Air-Gapped)

const getBaseUrl = () => {
  if (typeof window !== "undefined") {
    // Client-side: use relative path proxied by Next.js rewrites
    return "";
  }
  // Server-side: call FastAPI directly
  return "http://127.0.0.1:8000";
};

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = getBaseUrl();
  const url = endpoint.startsWith("/") ? `${base}${endpoint}` : `${base}/${endpoint}`;
  
  const res = await fetch(url, {
    cache: "no-store",
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`API error ${res.status} on ${endpoint}: ${errorText}`);
  }

  return res.json();
}
