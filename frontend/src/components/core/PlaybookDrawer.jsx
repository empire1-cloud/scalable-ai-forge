import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { BookOpen, Copy, Download } from "lucide-react";

export default function PlaybookDrawer() {
  const [pb, setPb] = useState(null);

  useEffect(() => {
    api.get("/core/playbook").then((r) => setPb(r.data)).catch(() => {});
  }, []);

  const copy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(pb, null, 2));
    toast.success("Playbook JSON copied.");
  };
  const download = () => {
    const blob = new Blob([JSON.stringify(pb, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "hybrid-intelligence-core-playbook.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button data-testid="open-playbook-btn" variant="outline" className="bg-transparent border-slate-700 text-slate-200 hover:bg-slate-800/60">
          <BookOpen className="w-4 h-4 mr-2" /> Integration Playbook
        </Button>
      </SheetTrigger>
      <SheetContent data-testid="playbook-sheet" className="bg-[#0D131E] border-slate-800 w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="font-heading text-slate-100">Hybrid Intelligence Core — Playbook</SheetTitle>
        </SheetHeader>
        {!pb ? (
          <div className="mt-6 h-40 shimmer rounded-lg" />
        ) : (
          <div className="mt-6 space-y-6 text-sm">
            <Block title="execution pipeline">
              <div className="flex flex-wrap gap-2 font-mono text-[11px]">
                {pb.pipeline.map((p, i) => (
                  <span key={p} className="px-2 py-1 rounded border border-cyan-500/30 bg-cyan-500/5 text-cyan-300">
                    {i + 1}. {p}
                  </span>
                ))}
              </div>
            </Block>
            <Block title="routing logic">
              <table className="w-full text-xs">
                <tbody className="divide-y divide-slate-800/60">
                  {pb.routing_logic.map((r) => (
                    <tr key={r.engine}>
                      <td className="py-2 pr-2 text-slate-300">{r.signal}</td>
                      <td className="py-2 pr-2 font-mono text-cyan-300">{r.engine}</td>
                      <td className="py-2 font-mono text-slate-500">{r.model}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 font-mono text-[10px] text-slate-500">
                router: {pb.router.model} · fallback: {pb.router.fallback}
              </p>
            </Block>
            <Block title="role assignments">
              <ul className="space-y-2">
                {Object.entries(pb.engines).map(([k, e]) => (
                  <li key={k} className="p-3 rounded border border-slate-800 bg-[#070A0F]">
                    <div className="font-heading font-semibold text-slate-100">{e.name}</div>
                    <div className="font-mono text-[10px] text-cyan-400">{e.provider} / {e.model}</div>
                    <p className="text-slate-400 mt-1">{e.role}</p>
                  </li>
                ))}
              </ul>
            </Block>
            <Block title="canon rules">
              <ul className="list-disc pl-5 text-slate-300 space-y-1">
                {pb.canon_rules.map((r) => <li key={r}>{r}</li>)}
              </ul>
            </Block>
            <Block title="formatting standards">
              <ul className="list-disc pl-5 text-slate-300 space-y-1">
                {pb.formatting_standards.map((r) => <li key={r}>{r}</li>)}
              </ul>
            </Block>
            <Block title="drift prevention">
              <p className="text-slate-300">{pb.drift_prevention.policy}</p>
              <p className="font-mono text-[11px] text-slate-500 mt-1">
                tracked: {pb.drift_prevention.tracked.join(", ")}
              </p>
              <p className="font-mono text-[11px] text-slate-500">{pb.drift_prevention.storage}</p>
            </Block>
            <Block title="error format">
              <pre className="p-3 rounded bg-[#05070B] border border-slate-800 text-xs font-mono text-slate-400 overflow-x-auto">
                {JSON.stringify(pb.error_format, null, 2)}
              </pre>
            </Block>
            <div className="flex gap-2 pt-2">
              <Button size="sm" variant="outline" data-testid="playbook-copy-btn" onClick={copy} className="bg-transparent border-slate-700 text-slate-200">
                <Copy className="w-3.5 h-3.5 mr-1.5" /> Copy JSON
              </Button>
              <Button size="sm" variant="outline" data-testid="playbook-download-btn" onClick={download} className="bg-transparent border-slate-700 text-slate-200">
                <Download className="w-3.5 h-3.5 mr-1.5" /> Download
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function Block({ title, children }) {
  return (
    <section>
      <div className="eyebrow mb-2">// {title}</div>
      {children}
    </section>
  );
}
