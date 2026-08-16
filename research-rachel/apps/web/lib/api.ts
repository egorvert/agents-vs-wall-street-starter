const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type HealthResponse = {
  status: "ok";
};

export type DemoResponse = {
  id: string;
  input: string;
  status: "created";
  timestamp: string;
};

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, { cache: "no-store", signal });
  return readJson<HealthResponse>(response);
}

export async function createDemo(input: string): Promise<DemoResponse> {
  const response = await fetch(`${API_URL}/api/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });
  return readJson<DemoResponse>(response);
}
