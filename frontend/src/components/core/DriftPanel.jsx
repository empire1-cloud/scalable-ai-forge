import { Activity } from "lucide-react";
import { ENGINE_META } from "@/components/core/CoreTaskForm";

export default function DriftPanel({ metrics }) {
  return (
    <div data-testid="drift-panel" className="rounded-xl border border-slate-800/80 bg-[#0D131E] overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
        <Activity className="w-4 h-4 text-cyan-400" />
        <span className="eyebrow">// drift monitor</span>
      </div>
      <ul className="divide-y divide-slate-800/60">
        {Object.entries(ENGINE_META).map(([k, meta]) => {
          const m = metrics?.[k];
          const empty = !m || !m.samples;
          return (
            <li key={k} data-testid={`drift-row-${k}`} className="px-5 py-3 flex items-center gap-3">
              <span className={`font-mono text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded border ${meta.color}`}>
                {meta.label}
              </span>
              {empty ? (
                <span className="ml-auto font-mono text-[10px] text-slate-600">no samples</span>
              ) : (
                <div className="ml-auto flex items-center gap-4 font-mono text-[10px]">
                  <span className="text-slate-400">{m.samples} runs</span>
                  <span className="text-slate-400">{m.avg_tokens} tok</span>
                  <span className={m.avg_compliance >= 0.95 ? "text-emerald-400" : "text-amber-400"}>
                    {Math.round(m.avg_compliance * 100)}%
                  </span>
                  <span className={m.drift_events ? "text-amber-400" : "text-slate-600"}>
                    {m.drift_events} drift
                  </span>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
