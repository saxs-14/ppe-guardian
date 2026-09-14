const API_BASE = "";

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

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json();
}

export const api = {
  health: () => fetch(`${API_BASE}/api/health`).then((r) => json<{ status: string }>(r)),
  summary: () => fetch(`${API_BASE}/api/dashboard/summary`).then((r) => json<DashboardSummary>(r)),
  events: () => fetch(`${API_BASE}/api/events`).then((r) => json<ComplianceEvent[]>(r)),
  exportCsvUrl: () => `${API_BASE}/api/events/export`,

  runDemo: (zone: string) => {
    const form = new FormData();
    form.set("zone", zone);
    return fetch(`${API_BASE}/api/analyze/demo`, { method: "POST", body: form }).then((r) => json<AnalysisSession>(r));
  },

  analyzeImage: (file: File, zone: string) => {
    const form = new FormData();
    form.set("file", file);
    form.set("zone", zone);
    return fetch(`${API_BASE}/api/analyze/image`, { method: "POST", body: form }).then((r) => json<AnalysisSession>(r));
  },
};
