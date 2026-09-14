const API_BASE = "";
const API_KEY = (import.meta.env.VITE_API_KEY as string) || "dev-local-key-change-me";

export interface ComplianceEvent {
  id: number;
  session_id: string;
  zone: string;
  person_track_id: number;
  helmet_detected: boolean;
  vest_detected: boolean;
  is_compliant: boolean;
  missing_items: string;
  timestamp: string;
}

export interface AnalysisSession {
  id: string;
  source_filename: string;
  zone: string;
  total_people: number;
  compliant_count: number;
  non_compliant_count: number;
  status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_people_checked: number;
  compliance_rate_pct: number;
  non_compliant_events: number;
  total_sessions: number;
}

function authHeaders(): HeadersInit {
  return { "X-API-Key": API_KEY };
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json();
}

async function downloadFile(url: string, filename: string) {
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

export const api = {
  health: () => fetch(`${API_BASE}/api/health`).then((r) => json<{ status: string }>(r)),
  summary: () =>
    fetch(`${API_BASE}/api/dashboard/summary`, { headers: authHeaders() }).then((r) => json<DashboardSummary>(r)),
  events: () => fetch(`${API_BASE}/api/events`, { headers: authHeaders() }).then((r) => json<ComplianceEvent[]>(r)),
  exportEvents: () => downloadFile(`${API_BASE}/api/events/export`, "ppe_events.csv"),

  runDemo: (zone: string) => {
    const form = new FormData();
    form.set("zone", zone);
    return fetch(`${API_BASE}/api/analyze/demo`, { method: "POST", headers: authHeaders(), body: form }).then((r) =>
      json<AnalysisSession>(r)
    );
  },

  analyzeImage: (file: File, zone: string) => {
    const form = new FormData();
    form.set("file", file);
    form.set("zone", zone);
    return fetch(`${API_BASE}/api/analyze/image`, { method: "POST", headers: authHeaders(), body: form }).then((r) =>
      json<AnalysisSession>(r)
    );
  },
};
