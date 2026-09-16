import { History, AlertTriangle } from "lucide-react";
import { ENGINE_META } from "@/components/core/CoreTaskForm";

export default function RunHistory({ runs, onOpen }) {
  return (
    <div data-testid="run-history" className="rounded-xl border border-slate-800/80 bg-[#0D131E] overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
        <History className="w-4 h-4 text-cyan-400" />
        <span className="eyebrow">// run history</span>
        <span className="ml-auto font-mono text-[10px] text-slate-500">{runs.length}</span>
      </div>
      {runs.length === 0 ? (
        <p data-testid="run-history-empty" className="px-5 py-8 text-sm text-slate-500 text-center">
          No runs yet. Send a task through the Core.
        </p>
      ) : (
        <ul className="divide-y divide-slate-800/60 max-h-[520px] overflow-y-auto">
          {runs.map((r) => {
            const meta = ENGINE_META[r.engine] || {};
            return (
              <li key={r.id}>
                <button
                  data-testid={`run-item-${r.id}`}
                  onClick={() => onOpen(r.id)}
                  className="w-full text-left px-5 py-3 hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    {r.error ? (
                      <span className="font-mono text-[10px] uppercase tracking-widest text-rose-300 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> error
                      </span>
                    ) : (
                      <span className={`font-mono text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded border ${meta.color || "text-slate-400 border-slate-700"}`}>
                        {meta.label || r.engine}
                      </span>
                    )}
                    <span className="ml-auto font-mono text-[10px] text-slate-500">
                      {r.latency_ms ? `${(r.latency_ms / 1000).toFixed(1)}s` : ""}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 line-clamp-2">{r.task}</p>
                  <div className="mt-1 font-mono text-[10px] text-slate-500 flex gap-3">
                    <span>{r.model || "—"}</span>
                    {r.drift_flags > 0 && <span className="text-amber-400">{r.drift_flags} drift</span>}
                    <span className="ml-auto">{new Date(r.created_at).toLocaleTimeString()}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
