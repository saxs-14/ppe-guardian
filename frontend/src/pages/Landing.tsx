import { Link } from "react-router-dom";

const FEATURES = [
  { title: "Person detection", desc: "Detects each worker in frame via OpenCV DNN." },
  { title: "PPE colour check", desc: "Flags presence of high-visibility helmet and vest colours per person." },
  { title: "Configurable zone rules", desc: "Different sites require different gear — construction, mining, warehouse." },
  { title: "Compliance dashboard", desc: "Live daily compliance percentage and event history." },
  { title: "Evidence & CSV export", desc: "Every non-compliance event is logged and exportable." },
  { title: "Demo mode", desc: "Run on a bundled worker-zone clip, no camera required." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-6 py-5 max-w-6xl mx-auto">
        <div className="flex items-center gap-2 font-semibold text-lg">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-500" />
          PPE Guardian
        </div>
        <Link to="/app" className="rounded-lg bg-amber-600 hover:bg-amber-500 transition px-4 py-2 text-sm font-medium">
          Open dashboard
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-6">
        <section className="py-16 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            Continuous <span className="text-amber-400">PPE compliance</span> monitoring
          </h1>
          <p className="mt-5 text-slate-400 max-w-2xl mx-auto text-lg">
            Camera footage in, compliance dashboard out — see who's missing a helmet or vest
            without walking the site.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/app" className="rounded-lg bg-amber-600 hover:bg-amber-500 transition px-5 py-3 font-medium">
              Try the live demo
            </Link>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            PPE presence is detected via colour analysis, not a PPE-specific trained model —
            see the README "Limitations" before relying on this for safety enforcement.
          </p>
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-slate-400">{f.desc}</p>
            </div>
          ))}
        </section>

        <section className="py-16 grid sm:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-bold mb-3">Who it's for</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Construction sites</li>
              <li>Mining operations</li>
              <li>Manufacturing plants</li>
              <li>Warehouses & logistics yards</li>
            </ul>
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-3">Pricing model</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Per-camera monthly subscription</li>
              <li>Site-wide subscription</li>
              <li>Enterprise multi-site licensing</li>
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        PPE Guardian — workplace safety MVP. Colour-based detection, not a certified safety system.
      </footer>
    </div>
  );
}
