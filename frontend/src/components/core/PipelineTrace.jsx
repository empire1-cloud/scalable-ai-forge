import { GitBranch, Cpu, ShieldCheck, Activity, AlertTriangle } from "lucide-react";

const STAGES = [
  { key: "routing", label: "Routing", icon: GitBranch },
  { key: "strategy", label: "Engine", icon: Cpu },
  { key: "canon", label: "Canon", icon: ShieldCheck },
  { key: "drift", label: "Drift", icon: Activity },
];

export default function PipelineTrace({ running, activeStage, result }) {
  const failedStage = result?.error ? result.stage : null;
  const failedIdx = STAGES.findIndex((s) => s.key === failedStage);

  return (
    <div
      data-testid="pipeline-trace"
      className="rounded-xl border border-slate-800/80 bg-[#0D131E] px-5 py-4 flex items-center gap-2 overflow-x-auto"
    >
      {STAGES.map((s, i) => {
        let state = "idle";
        if (running) state = i < activeStage ? "done" : i === activeStage ? "active" : "idle";
        else if (result && !result.error) state = "done";
        else if (result && result.error) state = i < failedIdx ? "done" : i === failedIdx ? "failed" : "idle";
        const Icon = state === "failed" ? AlertTriangle : s.icon;
        return (
          <div key={s.key} className="flex items-center gap-2 shrink-0">
            <div
              data-testid={`pipeline-stage-${s.key}`}
              data-state={state}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border font-mono text-[11px] tracking-widest uppercase transition-colors ${cls(state)}`}
            >
              <Icon className={`w-3.5 h-3.5 ${state === "active" ? "pulse-dot" : ""}`} />
              {s.label}
            </div>
            {i < STAGES.length - 1 && (
              <div className={`w-8 h-px ${state === "done" ? "bg-emerald-500/60" : "bg-slate-800"}`} />
            )}
          </div>
        );
      })}
      {result && !result.error && (
        <span className="ml-auto font-mono text-[11px] text-slate-500 shrink-0">
          {result.latency_ms} ms
        </span>
      )}
    </div>
  );
}

function cls(state) {
  if (state === "done") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (state === "active") return "border-cyan-500/50 bg-cyan-500/10 text-cyan-300";
  if (state === "failed") return "border-rose-500/50 bg-rose-500/10 text-rose-300";
  return "border-slate-800 text-slate-500";
}
