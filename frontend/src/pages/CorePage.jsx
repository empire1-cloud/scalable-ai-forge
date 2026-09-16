import { useEffect, useState } from "react";
import { toast } from "sonner";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import CoreTaskForm from "@/components/core/CoreTaskForm";
import PipelineTrace from "@/components/core/PipelineTrace";
import CoreResult from "@/components/core/CoreResult";
import RunHistory from "@/components/core/RunHistory";
import DriftPanel from "@/components/core/DriftPanel";
import PlaybookDrawer from "@/components/core/PlaybookDrawer";

export default function CorePage() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [runs, setRuns] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [activeStage, setActiveStage] = useState(-1);

  const refresh = async () => {
    const [r, m] = await Promise.all([api.get("/core/runs"), api.get("/core/metrics")]);
    setRuns(r.data);
    setMetrics(m.data);
  };

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  useEffect(() => {
    if (!running) return;
    setActiveStage(0);
    const t = setInterval(() => setActiveStage((s) => Math.min(s + 1, 3)), 2200);
    return () => clearInterval(t);
  }, [running]);

  const run = async (task, engineOverride) => {
    setRunning(true);
    setResult(null);
    try {
      const { data } = await api.post("/core/run", {
        task,
        engine_override: engineOverride || null,
      });
      setResult(data);
      toast.success(`Routed to ${data.engine_name} · ${data.model}`);
    } catch (err) {
      const body = err.response?.data;
      if (body && body.error) {
        setResult(body);
        toast.error(`${body.type} @ ${body.stage}: ${body.message}`);
      } else {
        setResult({ error: true, type: "system_error", message: err.message, stage: "orchestrator" });
        toast.error("Core request failed.");
      }
    } finally {
      setRunning(false);
      setActiveStage(-1);
      refresh().catch(() => {});
    }
  };

  const openRun = async (id) => {
    const { data } = await api.get(`/core/runs/${id}`);
    setResult(data.error ? data.error : { ...data, run_id: data.id });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-24 pb-24 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-10">
          <div>
            <div className="eyebrow mb-3">// hybrid intelligence core</div>
            <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight">
              One task in. The right engine answers.
            </h1>
            <p className="mt-2 text-slate-400 max-w-2xl">
              Routing → Engine → Canon → Drift. Claude for strategy, GPT for code,
              Gemini for speed. Every response is clean JSON.
            </p>
          </div>
          <PlaybookDrawer />
        </div>

        <div className="grid lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <CoreTaskForm onRun={run} running={running} />
            <PipelineTrace running={running} activeStage={activeStage} result={result} />
            {result && <CoreResult result={result} />}
          </div>
          <aside className="lg:col-span-4 space-y-6">
            <DriftPanel metrics={metrics} />
            <RunHistory runs={runs} onOpen={openRun} />
          </aside>
        </div>
      </main>
    </div>
  );
}
