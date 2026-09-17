import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { api, DashboardSummary, ComplianceEvent, AnalysisSession } from "../lib/api";
import KpiCard from "../components/KpiCard";

const ZONES = ["construction", "mining", "warehouse"];

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<ComplianceEvent[]>([]);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [zone, setZone] = useState("construction");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<AnalysisSession | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([api.summary(), api.events()]);
      setSummary(s);
      setEvents(e);
    } catch {
      /* offline */
    }
  }, []);

  useEffect(() => {
    api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
    refresh();
  }, [refresh]);

  const runDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      setSession(await api.runDemo(zone));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      setSession(await api.analyzeImage(file, zone));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Helmet>
        <title>Dashboard — PPE Guardian</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>

      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-500" />
          PPE Guardian
        </Link>
        <span className="flex items-center gap-2 text-xs">
          <span className={`inline-block h-2 w-2 rounded-full ${apiOnline ? "bg-emerald-500" : "bg-red-500"}`} />
          {apiOnline === null ? "Checking..." : apiOnline ? "Backend online" : "Backend offline"}
        </span>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <h1 className="sr-only">PPE Guardian compliance dashboard</h1>
        {!apiOnline && apiOnline !== null && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm">
            Can't reach the backend at <code>/api</code>. Start it with <code>uvicorn app.main:app --reload</code>.
          </div>
        )}

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="font-semibold mb-4">Check a site</h2>
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm capitalize"
            >
              {ZONES.map((z) => (
                <option key={z} value={z}>{z}</option>
              ))}
            </select>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"
            />
            <button
              disabled={!file || loading}
              onClick={runUpload}
              className="rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
            >
              {loading ? "Analyzing..." : "Analyze image"}
            </button>
            <span className="text-slate-500 text-sm">or</span>
            <button
              disabled={loading}
              onClick={runDemo}
              className="rounded-lg border border-slate-700 hover:border-slate-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
            >
              {loading ? "Running..." : "Run demo clip"}
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
          {session && (
            <p className="mt-4 text-sm text-slate-400">
              Session <code>{session.id}</code>: {session.total_people} people, {session.compliant_count} compliant,{" "}
              {session.non_compliant_count} non-compliant
            </p>
          )}
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard label="People checked" value={summary?.total_people_checked ?? "-"} />
          <KpiCard label="Compliance rate" value={summary ? `${summary.compliance_rate_pct}%` : "-"} />
          <KpiCard label="Non-compliant events" value={summary?.non_compliant_events ?? "-"} accent="alert" />
          <KpiCard label="Sessions analyzed" value={summary?.total_sessions ?? "-"} />
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Event history</h2>
            <button onClick={() => api.exportEvents()} className="text-sm rounded-lg border border-slate-700 hover:border-slate-500 transition px-3 py-1.5">
              Export CSV
            </button>
          </div>
          {events.length === 0 ? (
            <p className="text-sm text-slate-500">No events yet — run the demo or analyze an image above.</p>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="py-2 pr-4">Person</th>
                  <th className="py-2 pr-4">Zone</th>
                  <th className="py-2 pr-4">Helmet</th>
                  <th className="py-2 pr-4">Vest</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Time</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id} className="border-b border-slate-800/60">
                    <td className="py-2 pr-4">#{e.person_track_id}</td>
                    <td className="py-2 pr-4 capitalize">{e.zone}</td>
                    <td className="py-2 pr-4">{e.helmet_detected ? "✓" : "✗"}</td>
                    <td className="py-2 pr-4">{e.vest_detected ? "✓" : "✗"}</td>
                    <td className="py-2 pr-4">
                      {e.is_compliant ? (
                        <span className="text-emerald-500">Compliant</span>
                      ) : (
                        <span className="text-red-500">Missing {e.missing_items}</span>
                      )}
                    </td>
                    <td className="py-2 pr-4 text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
