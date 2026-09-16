import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Send } from "lucide-react";

export const ENGINE_META = {
  strategy: { label: "Strategy", tier: "Claude Sonnet 4.5", color: "text-amber-300 border-amber-500/40 bg-amber-500/10" },
  plan_builder: { label: "Plan Builder", tier: "Claude Sonnet 4.5", color: "text-amber-300 border-amber-500/40 bg-amber-500/10" },
  analysis: { label: "Analysis", tier: "Claude Sonnet 4.5", color: "text-amber-300 border-amber-500/40 bg-amber-500/10" },
  code: { label: "Code", tier: "GPT-5.2", color: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10" },
  fast: { label: "Fast", tier: "Gemini 3 Flash", color: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10" },
};

const examples = [
  "Design a go-to-market strategy for a B2B analytics tool entering the EU mid-market.",
  "Write a Python function that dedupes a list of user records by fuzzy email match.",
  "Summarize the key differences between event sourcing and CRUD persistence.",
  "Analyze why a subscription app's month-2 retention dropped from 61% to 44%.",
];

export default function CoreTaskForm({ onRun, running }) {
  const [task, setTask] = useState("");
  const [engine, setEngine] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (task.trim().length < 4) return;
    onRun(task.trim(), engine);
  };

  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border border-slate-800/80 bg-[#0D131E] p-6 sm:p-8"
    >
      <Label htmlFor="core-task" className="text-slate-200 font-mono text-xs tracking-widest uppercase">
        // task
      </Label>
      <Textarea
        id="core-task"
        data-testid="core-task-input"
        value={task}
        onChange={(e) => setTask(e.target.value)}
        disabled={running}
        placeholder="Describe a strategy, plan, analysis, coding, or quick-lookup task..."
        className="mt-2 min-h-[120px] bg-[#070A0F] border-slate-800 focus:border-cyan-500 text-slate-100 text-base leading-relaxed"
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {examples.map((ex, i) => (
          <button
            type="button"
            key={i}
            data-testid={`core-example-${i}`}
            onClick={() => setTask(ex)}
            className="text-xs px-3 py-1.5 rounded-full border border-slate-800 bg-[#0d131e] text-slate-400 hover:border-cyan-500/40 hover:text-cyan-300 transition-colors"
          >
            {ex.slice(0, 48)}…
          </button>
        ))}
      </div>

      <div className="mt-6 pt-5 border-t border-slate-800/80">
        <Label className="text-xs font-mono tracking-widest uppercase text-slate-400">
          Engine routing
        </Label>
        <div className="mt-2 flex flex-wrap gap-2">
          <Chip active={engine === ""} onClick={() => setEngine("")} testid="engine-chip-auto">
            Auto (Gemini router)
          </Chip>
          {Object.entries(ENGINE_META).map(([k, m]) => (
            <Chip key={k} active={engine === k} onClick={() => setEngine(k)} testid={`engine-chip-${k}`}>
              {m.label} <span className="opacity-60 ml-1">· {m.tier}</span>
            </Chip>
          ))}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between gap-4">
        <p className="text-xs font-mono text-slate-500 tracking-wide">
          gpt-5.2 · claude-sonnet-4.5 · gemini-3-flash
        </p>
        <Button
          type="submit"
          data-testid="core-run-btn"
          disabled={running || task.trim().length < 4}
          className="h-11 px-6 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold shadow-[0_0_25px_rgba(6,182,212,0.35)]"
        >
          <Send className="w-4 h-4 mr-2" />
          {running ? "Orchestrating..." : "Run through Core"}
        </Button>
      </div>
    </form>
  );
}

function Chip({ active, onClick, children, testid }) {
  return (
    <button
      type="button"
      data-testid={testid}
      onClick={onClick}
      className={`text-xs px-3 py-1.5 rounded-md border font-mono transition-colors ${
        active
          ? "border-cyan-500/60 bg-cyan-500/10 text-cyan-200"
          : "border-slate-800 text-slate-400 hover:border-slate-600"
      }`}
    >
      {children}
    </button>
  );
}
