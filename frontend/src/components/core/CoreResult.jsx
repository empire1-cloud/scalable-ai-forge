import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Download, AlertTriangle } from "lucide-react";
import { ENGINE_META } from "@/components/core/CoreTaskForm";
import JsonTree from "@/components/core/JsonTree";

export default function CoreResult({ result }) {
  if (result.error) return <ErrorCard err={result} />;

  const meta = ENGINE_META[result.engine] || {};
  const copy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(result.output, null, 2));
    toast.success("Engine JSON copied.");
  };
  const download = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `core-run-${result.run_id?.slice(0, 8) || "result"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div data-testid="core-result" className="rounded-2xl border border-cyan-500/25 bg-[#0D131E] overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center gap-3">
        <Badge data-testid="result-engine-badge" className={`font-mono text-[10px] uppercase ${meta.color || ""}`}>
          {result.engine_name || result.engine}
        </Badge>
        <span data-testid="result-model" className="font-mono text-xs text-slate-300">{result.model}</span>
        <span className="font-mono text-[10px] text-slate-500">
          via {result.routing?.method} · conf {Math.round((result.routing?.confidence || 0) * 100)}%
        </span>
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="outline" data-testid="core-copy-json-btn" onClick={copy} className="bg-transparent border-slate-700 text-slate-200 h-8">
            <Copy className="w-3.5 h-3.5 mr-1.5" /> Copy
          </Button>
          <Button size="sm" variant="outline" data-testid="core-download-json-btn" onClick={download} className="bg-transparent border-slate-700 text-slate-200 h-8">
            <Download className="w-3.5 h-3.5 mr-1.5" /> .json
          </Button>
        </div>
      </div>

      {result.routing?.rationale && (
        <p className="px-6 py-3 text-sm text-slate-400 border-b border-slate-800/60">
          <span className="font-mono text-[10px] uppercase tracking-widest text-cyan-400 mr-2">routing:</span>
          {result.routing.rationale}
        </p>
      )}

      <Tabs defaultValue="structured" className="p-6">
        <TabsList className="bg-[#070A0F] border border-slate-800 mb-4">
          <TabsTrigger value="structured" data-testid="tab-structured">Structured</TabsTrigger>
          <TabsTrigger value="raw" data-testid="tab-raw">Raw JSON</TabsTrigger>
          <TabsTrigger value="canon" data-testid="tab-canon">Canon</TabsTrigger>
          <TabsTrigger value="drift" data-testid="tab-drift">Drift</TabsTrigger>
        </TabsList>
        <TabsContent value="structured">
          <JsonTree data={result.output} />
        </TabsContent>
        <TabsContent value="raw">
          <pre data-testid="core-raw-json" className="p-4 rounded-lg bg-[#05070B] border border-slate-800 text-xs font-mono text-slate-300 overflow-auto max-h-[520px]">
            {JSON.stringify(result.output, null, 2)}
          </pre>
        </TabsContent>
        <TabsContent value="canon">
          <CanonView canon={result.canon} />
        </TabsContent>
        <TabsContent value="drift">
          <DriftView drift={result.drift} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ErrorCard({ err }) {
  return (
    <div data-testid="core-error" className="rounded-2xl border border-rose-500/40 bg-rose-500/5 p-6">
      <div className="flex items-center gap-3 mb-3">
        <AlertTriangle className="w-5 h-5 text-rose-400" />
        <span className="font-mono text-xs uppercase tracking-widest text-rose-300">
          {err.type} · stage: {err.stage}
        </span>
      </div>
      <p className="text-slate-200">{err.message}</p>
      <pre className="mt-4 p-3 rounded bg-[#05070B] border border-slate-800 text-xs font-mono text-slate-400">
        {JSON.stringify({ error: true, type: err.type, message: err.message, stage: err.stage }, null, 2)}
      </pre>
    </div>
  );
}

function CanonView({ canon }) {
  if (!canon) return null;
  return (
    <div className="space-y-3">
      <div data-testid="canon-status" className={`font-mono text-xs uppercase tracking-widest ${canon.compliant ? "text-emerald-300" : "text-amber-300"}`}>
        {canon.compliant ? "✓ fully compliant" : `${canon.violations.length} violation(s) normalized`}
      </div>
      <ul className="grid sm:grid-cols-2 gap-2">
        {canon.rules.map((r) => (
          <li key={r} className="text-sm text-slate-300 px-3 py-2 rounded border border-slate-800 bg-[#070A0F]">
            {r}
          </li>
        ))}
      </ul>
      {canon.violations.length > 0 && (
        <ul className="text-xs font-mono text-amber-300/80 space-y-1">
          {canon.violations.map((v, i) => (
            <li key={i}>{v.rule} @ {v.path}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DriftView({ drift }) {
  if (!drift) return null;
  const m = drift.metrics || {};
  return (
    <div className="space-y-4">
      <div data-testid="drift-status" className={`font-mono text-xs uppercase tracking-widest ${drift.stable ? "text-emerald-300" : "text-amber-300"}`}>
        {drift.stable ? "✓ stable — no drift detected" : `${drift.flags.length} drift flag(s)`}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Stat label="tokens" value={m.token_estimate} />
        <Stat label="depth" value={m.depth} />
        <Stat label="keys" value={(m.top_level_keys || []).length} />
        <Stat label="compliance" value={m.compliance != null ? `${Math.round(m.compliance * 100)}%` : "—"} />
      </div>
      {drift.baseline && (
        <p className="text-xs font-mono text-slate-500">
          baseline · {drift.baseline.samples} samples · avg {drift.baseline.avg_tokens} tokens · avg compliance {Math.round(drift.baseline.avg_compliance * 100)}%
        </p>
      )}
      {drift.flags.map((f, i) => (
        <div key={i} className="text-sm text-amber-200 px-3 py-2 rounded border border-amber-500/30 bg-amber-500/5">
          <span className="font-mono text-[10px] uppercase tracking-widest mr-2">{f.type}</span>
          {f.detail}
        </div>
      ))}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="p-3 rounded border border-slate-800 bg-[#070A0F]">
      <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">{label}</div>
      <div className="font-heading text-lg font-bold text-slate-100">{value ?? "—"}</div>
    </div>
  );
}
