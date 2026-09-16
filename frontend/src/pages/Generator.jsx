import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import { streamPost } from "@/lib/stream";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Zap, Cpu, Layers, Code2, Route } from "lucide-react";

const stages = [
  { icon: Layers, label: "Parsing ontology", marker: '"core_insight"' },
  { icon: Cpu, label: "Synthesizing architecture", marker: '"system_blueprint"' },
  { icon: Zap, label: "Mapping leverage points", marker: '"leverage_point"' },
  { icon: Route, label: "Roadmap, risks, monetization", marker: '"roadmap"' },
  { icon: Code2, label: "Generating executable assets", marker: '"executable_output"' },
];

const examples = [
  "A creator-owned newsletter platform where audiences can invest in individual writers.",
  "A B2B tool that turns customer support tickets into product roadmap decisions.",
  "A marketplace connecting indie game studios with QA testers by playstyle.",
];

export default function Generator() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [budget, setBudget] = useState("");
  const [timeline, setTimeline] = useState("");
  const [scale, setScale] = useState("");
  const [generating, setGenerating] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [finalizing, setFinalizing] = useState(false);

  const stage = stages.reduce((acc, s, i) => (streamText.includes(s.marker) ? i : acc), 0);

  const submit = async (e) => {
    e.preventDefault();
    if (idea.trim().length < 8) {
      toast.error("Give me a little more to work with (at least 8 chars).");
      return;
    }
    setGenerating(true);
    setStreamText("");
    setFinalizing(false);
    try {
      await streamPost(
        "/blueprints/stream",
        {
          idea: idea.trim(),
          industry: industry || null,
          budget: budget || null,
          timeline: timeline || null,
          scale: scale || null,
        },
        (ev) => {
          if (ev.type === "token") setStreamText((t) => t + ev.content);
          else if (ev.type === "done") {
            setFinalizing(true);
            toast.success("Blueprint ready.");
            navigate(`/blueprint/${ev.blueprint.id}`);
          } else if (ev.type === "error") {
            throw new Error(ev.detail || "Generation failed.");
          }
        }
      );
    } catch (err) {
      toast.error(err.message || "Generation failed.");
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-24 pb-16 px-4 sm:px-8 max-w-5xl mx-auto">
        {!generating ? (
          <>
            <div className="mb-10">
              <div className="eyebrow mb-3">// new blueprint</div>
              <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight">
                Drop your idea. Get a system.
              </h1>
              <p className="mt-2 text-slate-400 max-w-2xl">
                One paragraph. Optionally constrain by industry, budget, and
                timeline. The architect handles the rest.
              </p>
            </div>

            <form
              onSubmit={submit}
              className="rounded-2xl border border-slate-800/80 bg-[#0D131E] p-6 sm:p-8"
            >
              <Label htmlFor="idea" className="text-slate-200 font-mono text-xs tracking-widest uppercase">
                // Your idea
              </Label>
              <Textarea
                id="idea"
                data-testid="idea-prompt-input"
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="e.g., A marketplace where indie devs sell reusable game mechanics as licensed modules..."
                className="mt-2 min-h-[160px] bg-[#070A0F] border-slate-800 focus:border-cyan-500 text-slate-100 text-base leading-relaxed"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                {examples.map((ex, i) => (
                  <button
                    type="button"
                    key={i}
                    data-testid={`example-chip-${i}`}
                    onClick={() => setIdea(ex)}
                    className="text-xs px-3 py-1.5 rounded-full border border-slate-800 bg-[#0d131e] text-slate-400 hover:border-cyan-500/40 hover:text-cyan-300 transition-colors"
                  >
                    {ex.slice(0, 44)}…
                  </button>
                ))}
              </div>

              <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-6 border-t border-slate-800/80">
                <Field
                  label="Industry"
                  testid="industry-input"
                  value={industry}
                  onChange={setIndustry}
                  placeholder="Fintech, SaaS..."
                />
                <Field
                  label="Budget"
                  testid="budget-input"
                  value={budget}
                  onChange={setBudget}
                  placeholder="Bootstrapped, $50k..."
                />
                <Field
                  label="Timeline"
                  testid="timeline-input"
                  value={timeline}
                  onChange={setTimeline}
                  placeholder="4 weeks, 6 months..."
                />
                <Field
                  label="Scale"
                  testid="scale-input"
                  value={scale}
                  onChange={setScale}
                  placeholder="10k users, national..."
                />
              </div>

              <div className="mt-8 flex items-center justify-between gap-4">
                <p className="text-xs font-mono text-slate-500 tracking-wide">
                  powered by claude sonnet 5
                </p>
                <Button
                  type="submit"
                  data-testid="submit-blueprint-btn"
                  className="h-12 px-6 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold shadow-[0_0_30px_rgba(245,158,11,0.35)]"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Generate Blueprint
                </Button>
              </div>
            </form>
          </>
        ) : (
          <GeneratingState stage={stage} streamText={streamText} finalizing={finalizing} />
        )}
      </main>
    </div>
  );
}

function Field({ label, testid, value, onChange, placeholder }) {
  return (
    <div>
      <Label className="text-xs font-mono tracking-widest uppercase text-slate-400">
        {label}
      </Label>
      <Input
        data-testid={testid}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1.5 bg-[#070A0F] border-slate-800 focus:border-cyan-500 h-10"
      />
    </div>
  );
}

function GeneratingState({ stage, streamText, finalizing }) {
  const preRef = useRef(null);
  useEffect(() => {
    if (preRef.current) preRef.current.scrollTop = preRef.current.scrollHeight;
  }, [streamText]);
  const chars = streamText.length;
  return (
    <div
      data-testid="generating-state"
      className="rounded-2xl border border-cyan-500/30 bg-[#0D131E] p-8 sm:p-12 relative overflow-hidden"
    >
      <div className="absolute inset-0 blueprint-mesh opacity-40" />
      <div className="relative">
        <div className="eyebrow mb-3">// architect running — live stream</div>
        <h2 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100">
          {finalizing ? "Sealing the blueprint..." : "Composing your system..."}
        </h2>
        <p className="mt-2 text-slate-400 text-sm">
          Claude Sonnet 5 is streaming architecture, leverage, and executable
          outputs token by token. Do not refresh.
        </p>

        <div className="mt-10 grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2 space-y-3">
            {stages.map((s, i) => {
              const done = i < stage || finalizing;
              const active = i === stage && !finalizing;
              return (
                <div
                  key={i}
                  data-testid={`gen-stage-${i}`}
                  className={`flex items-center gap-4 p-3.5 rounded-lg border transition-all ${
                    active
                      ? "border-cyan-500/50 bg-cyan-500/5"
                      : done
                      ? "border-emerald-500/30 bg-emerald-500/5"
                      : "border-slate-800 bg-[#070A0F]"
                  }`}
                >
                  <div
                    className={`w-9 h-9 rounded-md flex items-center justify-center ${
                      active
                        ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40"
                        : done
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-slate-800 text-slate-500"
                    }`}
                  >
                    <s.icon className={`w-4 h-4 ${active ? "pulse-dot" : ""}`} />
                  </div>
                  <div
                    className={`flex-1 font-mono text-xs tracking-widest uppercase ${
                      active ? "text-cyan-300" : done ? "text-emerald-300" : "text-slate-500"
                    }`}
                  >
                    {s.label}
                    {active && <span className="ml-2 opacity-70">...</span>}
                    {done && <span className="ml-2">✓</span>}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="lg:col-span-3 rounded-lg border border-slate-800 bg-[#05070B] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-[#0D131E]">
              <span className="font-mono text-[10px] tracking-widest uppercase text-cyan-400">
                // raw stream
              </span>
              <span data-testid="stream-char-count" className="font-mono text-[10px] text-slate-500">
                {chars.toLocaleString()} chars
              </span>
            </div>
            <pre
              ref={preRef}
              data-testid="stream-output"
              className="p-4 text-[11px] leading-relaxed font-mono text-slate-400 overflow-y-auto h-[360px] whitespace-pre-wrap break-words"
            >
              {streamText || "awaiting first token..."}
              <span className="inline-block w-2 h-3 bg-cyan-400 ml-0.5 align-middle pulse-dot" />
            </pre>
          </div>
        </div>

        <div className="mt-8 h-1.5 rounded-full bg-slate-800 overflow-hidden">
          <div
            className="h-full bg-cyan-500 transition-all duration-500"
            style={{ width: `${finalizing ? 100 : Math.min(95, 8 + (stage / stages.length) * 80)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
