import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import { api, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Copy,
  Download,
  Zap,
  ShieldAlert,
  TrendingUp,
  Layers,
  Cpu,
  Code2,
  ArrowLeft,
  Route,
  Coins,
} from "lucide-react";

export default function BlueprintDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [bp, setBp] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get(`/blueprints/${id}`)
      .then((r) => setBp(r.data))
      .catch((e) => {
        toast.error(formatApiError(e.response?.data?.detail) || "Not found");
        navigate("/dashboard");
      })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070A0F]">
        <Header />
        <div className="pt-24 px-8 max-w-6xl mx-auto">
          <div className="h-64 rounded-2xl shimmer border border-slate-800/80" />
        </div>
      </div>
    );
  }
  if (!bp) return null;

  const c = bp.content || {};

  const copyJSON = async () => {
    await navigator.clipboard.writeText(JSON.stringify(c, null, 2));
    toast.success("Blueprint JSON copied to clipboard.");
  };

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(bp, null, 2)], { type: "application/json" });
    triggerDownload(blob, `${slug(bp.title)}.json`);
    toast.success("JSON downloaded.");
  };

  const downloadMD = () => {
    const md = toMarkdown(bp);
    const blob = new Blob([md], { type: "text/markdown" });
    triggerDownload(blob, `${slug(bp.title)}.md`);
    toast.success("Markdown downloaded.");
  };

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-24 pb-24 px-4 sm:px-8 max-w-6xl mx-auto">
        <Button
          variant="ghost"
          size="sm"
          data-testid="back-to-vault-btn"
          onClick={() => navigate("/dashboard")}
          className="mb-4 text-slate-400 hover:text-slate-200 -ml-3"
        >
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Vault
        </Button>

        {/* HERO */}
        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-[#0D131E] to-[#070A0F] p-8 sm:p-10 relative overflow-hidden">
          <div className="absolute inset-0 blueprint-mesh opacity-30" />
          <div className="relative">
            <div className="eyebrow mb-3">// blueprint</div>
            <h1
              data-testid="blueprint-title"
              className="font-heading text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-50 leading-tight"
            >
              {bp.title}
            </h1>
            {c.tagline && (
              <p className="mt-3 text-lg text-cyan-400/90">{c.tagline}</p>
            )}
            <p className="mt-5 text-slate-400 text-sm max-w-3xl leading-relaxed">
              <span className="font-mono text-xs tracking-widest uppercase text-slate-500 block mb-1">
                // original idea
              </span>
              {bp.idea}
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              <Button
                data-testid="copy-json-btn"
                size="sm"
                onClick={copyJSON}
                variant="outline"
                className="bg-transparent border-slate-700 hover:bg-slate-800/60 text-slate-200"
              >
                <Copy className="w-4 h-4 mr-1.5" /> Copy JSON
              </Button>
              <Button
                data-testid="export-markdown-btn"
                size="sm"
                onClick={downloadMD}
                variant="outline"
                className="bg-transparent border-slate-700 hover:bg-slate-800/60 text-slate-200"
              >
                <Download className="w-4 h-4 mr-1.5" /> .md
              </Button>
              <Button
                data-testid="export-json-btn"
                size="sm"
                onClick={downloadJSON}
                variant="outline"
                className="bg-transparent border-slate-700 hover:bg-slate-800/60 text-slate-200"
              >
                <Download className="w-4 h-4 mr-1.5" /> .json
              </Button>
            </div>
          </div>
        </div>

        {/* CORE INSIGHT */}
        <Section icon={Layers} eyebrow="// core insight" title="The hidden structure">
          <p className="text-slate-200 text-base sm:text-lg leading-relaxed">
            {c.core_insight}
          </p>
        </Section>

        {/* LEVERAGE POINT — highlighted */}
        {c.leverage_point && (
          <div className="mt-8 rounded-2xl border border-amber-500/40 bg-gradient-to-br from-amber-500/10 to-transparent p-8 glow-amber">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-md bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                <Zap className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="font-mono text-[10px] tracking-[0.3em] uppercase text-amber-400/90">
                  // leverage point — highest ROI
                </div>
                <div className="font-heading text-xl font-bold text-slate-100 mt-0.5">
                  The one move
                </div>
              </div>
            </div>
            <p className="font-heading text-xl sm:text-2xl font-bold text-amber-100 leading-snug">
              {c.leverage_point.the_move}
            </p>
            <p className="mt-3 text-slate-300 leading-relaxed">
              {c.leverage_point.why_it_works}
            </p>
            {c.leverage_point.impact_effort && (
              <div className="mt-5 flex gap-6 font-mono text-xs tracking-widest uppercase">
                <span className="text-emerald-400">
                  Impact: {c.leverage_point.impact_effort.impact}/10
                </span>
                <span className="text-cyan-400">
                  Effort: {c.leverage_point.impact_effort.effort}/10
                </span>
              </div>
            )}
          </div>
        )}

        {/* SYSTEM BLUEPRINT — tabs */}
        <Section icon={Cpu} eyebrow="// system blueprint" title="Architecture, stack, and data">
          <Tabs defaultValue="arch">
            <TabsList className="bg-[#070A0F] border border-slate-800 mb-4">
              <TabsTrigger value="arch" data-testid="tab-architecture">Architecture</TabsTrigger>
              <TabsTrigger value="stack" data-testid="tab-stack">Tech Stack</TabsTrigger>
              <TabsTrigger value="models" data-testid="tab-models">Data Models</TabsTrigger>
            </TabsList>
            <TabsContent value="arch" className="space-y-4">
              <p className="text-slate-300 leading-relaxed">
                {c.system_blueprint?.architecture}
              </p>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(c.system_blueprint?.components || []).map((cmp, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-slate-800 bg-[#070A0F]"
                  >
                    <div className="font-heading font-semibold text-slate-100">
                      {cmp.name}
                    </div>
                    <div className="text-xs text-slate-500 font-mono mt-0.5">
                      {cmp.tech}
                    </div>
                    <p className="text-sm text-slate-400 mt-2">{cmp.role}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="stack">
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(c.system_blueprint?.tech_stack || {}).map(
                  ([k, v]) => (
                    <div
                      key={k}
                      className="p-4 rounded-lg border border-slate-800 bg-[#070A0F]"
                    >
                      <div className="font-mono text-[10px] tracking-widest uppercase text-cyan-400 mb-1">
                        {k}
                      </div>
                      <div className="text-slate-100">{v}</div>
                    </div>
                  )
                )}
              </div>
            </TabsContent>
            <TabsContent value="models" className="space-y-4">
              {(c.system_blueprint?.data_models || []).map((m, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-slate-800 bg-[#070A0F] overflow-hidden"
                >
                  <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <span className="font-heading font-semibold text-slate-100">
                      {m.name}
                    </span>
                    <Badge className="bg-cyan-500/10 text-cyan-300 border-cyan-500/30 font-mono text-[10px]">
                      {(m.fields || []).length} fields
                    </Badge>
                  </div>
                  <div className="divide-y divide-slate-800/60">
                    {(m.fields || []).map((f, j) => (
                      <div
                        key={j}
                        className="px-4 py-2.5 grid grid-cols-12 gap-3 font-mono text-xs"
                      >
                        <span className="col-span-4 text-slate-200">
                          {f.name}
                        </span>
                        <span className="col-span-3 text-cyan-400">
                          {f.type}
                        </span>
                        <span className="col-span-5 text-slate-500">
                          {f.note}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </Section>

        {/* ROADMAP */}
        {c.roadmap?.length > 0 && (
          <Section icon={Route} eyebrow="// execution roadmap" title="Phased delivery">
            <div className="grid md:grid-cols-2 gap-4">
              {c.roadmap.map((p, i) => (
                <div
                  key={i}
                  className="p-5 rounded-lg border border-slate-800 bg-[#0D131E]"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-heading font-bold text-slate-100">
                      {p.phase}
                    </span>
                    <span className="font-mono text-[10px] tracking-widest uppercase text-cyan-400">
                      {p.weeks}
                    </span>
                  </div>
                  <ul className="space-y-1.5">
                    {(p.deliverables || []).map((d, j) => (
                      <li key={j} className="text-sm text-slate-400 flex gap-2">
                        <span className="text-cyan-400 mt-0.5">▸</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* RISKS */}
        {c.risks?.length > 0 && (
          <Section icon={ShieldAlert} eyebrow="// risk matrix" title="Systemic vulnerabilities">
            <div className="space-y-3">
              {c.risks.map((r, i) => (
                <div
                  key={i}
                  className="p-5 rounded-lg border border-slate-800 bg-[#0D131E] flex gap-4"
                >
                  <SeverityDot severity={r.severity} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-heading font-bold text-slate-100">
                        {r.risk}
                      </span>
                      <Badge
                        className={`font-mono text-[10px] ${severityClass(
                          r.severity
                        )}`}
                      >
                        {r.severity}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-sm text-slate-400">
                      <span className="text-cyan-400 font-mono text-xs uppercase tracking-widest mr-2">
                        mitigation:
                      </span>
                      {r.mitigation}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* MONETIZATION */}
        {c.monetization && (
          <Section icon={Coins} eyebrow="// monetization engine" title="Revenue mechanics">
            <div className="grid lg:grid-cols-3 gap-4">
              <div className="p-5 rounded-lg border border-slate-800 bg-[#0D131E]">
                <div className="eyebrow mb-2">Model</div>
                <div className="font-heading font-bold text-slate-100">
                  {c.monetization.model}
                </div>
                <p className="mt-3 text-sm text-slate-400">
                  {c.monetization.unit_economics}
                </p>
              </div>
              <div className="lg:col-span-2 space-y-2">
                {(c.monetization.pricing_tiers || []).map((t, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-slate-800 bg-[#0D131E] flex items-start gap-4"
                  >
                    <div className="min-w-[120px]">
                      <div className="font-heading font-bold text-slate-100">
                        {t.name}
                      </div>
                      <div className="text-cyan-400 font-mono text-sm">
                        {t.price}
                      </div>
                    </div>
                    <ul className="text-sm text-slate-400 flex-1 space-y-1">
                      {(t.includes || []).map((it, j) => (
                        <li key={j} className="flex gap-2">
                          <span className="text-emerald-400">✓</span>
                          <span>{it}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
            {c.monetization.growth_loops?.length > 0 && (
              <div className="mt-4 p-5 rounded-lg border border-cyan-500/25 bg-cyan-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <span className="eyebrow">// growth loops</span>
                </div>
                <ul className="space-y-1.5">
                  {c.monetization.growth_loops.map((g, i) => (
                    <li key={i} className="text-slate-300 flex gap-2">
                      <span className="text-cyan-400">▸</span>
                      <span>{g}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Section>
        )}

        {/* EXECUTABLE OUTPUT */}
        {c.executable_output && (
          <Section icon={Code2} eyebrow="// executable output" title="Ship this today">
            <p className="text-slate-300 mb-6">
              {c.executable_output.summary}
            </p>
            <div className="space-y-4">
              {(c.executable_output.artifacts || []).map((a, i) => (
                <ArtifactBlock key={i} artifact={a} />
              ))}
            </div>
          </Section>
        )}
      </main>
    </div>
  );
}

function Section({ icon: Icon, eyebrow, title, children }) {
  return (
    <section className="mt-12">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-md border border-cyan-500/30 bg-cyan-500/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-cyan-400" />
        </div>
        <div>
          <div className="eyebrow">{eyebrow}</div>
          <div className="font-heading text-xl sm:text-2xl font-bold text-slate-100">
            {title}
          </div>
        </div>
      </div>
      <div>{children}</div>
    </section>
  );
}

function ArtifactBlock({ artifact }) {
  const copy = async () => {
    await navigator.clipboard.writeText(artifact.content || "");
    toast.success(`${artifact.filename || "Artifact"} copied.`);
  };
  return (
    <div className="rounded-lg border border-slate-800 bg-[#05070B] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-[#0D131E]">
        <div className="flex items-center gap-3">
          <Badge className="bg-cyan-500/10 text-cyan-300 border-cyan-500/30 font-mono text-[10px] uppercase">
            {artifact.kind}
          </Badge>
          <span className="font-mono text-xs text-slate-300">
            {artifact.filename}
          </span>
          <span className="font-mono text-[10px] text-slate-500">
            {artifact.language}
          </span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={copy}
          data-testid={`copy-artifact-${artifact.filename}`}
          className="text-slate-400 hover:text-cyan-300 h-8"
        >
          <Copy className="w-3.5 h-3.5 mr-1" /> Copy
        </Button>
      </div>
      <pre className="p-5 overflow-x-auto text-xs font-mono text-slate-300 leading-relaxed max-h-[420px]">
        <code>{artifact.content}</code>
      </pre>
    </div>
  );
}

function SeverityDot({ severity }) {
  const map = {
    High: "bg-rose-500",
    Medium: "bg-amber-500",
    Low: "bg-emerald-500",
  };
  return (
    <div className="pt-2">
      <span className={`w-3 h-3 rounded-full block ${map[severity] || "bg-slate-500"}`} />
    </div>
  );
}
function severityClass(s) {
  if (s === "High") return "bg-rose-500/10 text-rose-300 border-rose-500/30";
  if (s === "Medium") return "bg-amber-500/10 text-amber-300 border-amber-500/30";
  return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
}

function slug(t = "blueprint") {
  return t
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
}

function triggerDownload(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function toMarkdown(bp) {
  const c = bp.content || {};
  const lines = [];
  lines.push(`# ${bp.title}`);
  if (c.tagline) lines.push(`\n> ${c.tagline}\n`);
  lines.push(`\n**Original idea:** ${bp.idea}\n`);
  lines.push(`\n## Core Insight\n${c.core_insight || ""}`);
  if (c.leverage_point) {
    lines.push(`\n## Leverage Point\n**The move:** ${c.leverage_point.the_move}\n\n${c.leverage_point.why_it_works}`);
  }
  if (c.system_blueprint) {
    lines.push(`\n## System Blueprint`);
    lines.push(`\n### Architecture\n${c.system_blueprint.architecture || ""}`);
    lines.push(`\n### Components`);
    (c.system_blueprint.components || []).forEach((cmp) =>
      lines.push(`- **${cmp.name}** (${cmp.tech}) — ${cmp.role}`)
    );
    lines.push(`\n### Tech Stack`);
    Object.entries(c.system_blueprint.tech_stack || {}).forEach(([k, v]) =>
      lines.push(`- **${k}**: ${v}`)
    );
    lines.push(`\n### Data Models`);
    (c.system_blueprint.data_models || []).forEach((m) => {
      lines.push(`\n#### ${m.name}`);
      (m.fields || []).forEach((f) =>
        lines.push(`- \`${f.name}\`: ${f.type} — ${f.note || ""}`)
      );
    });
  }
  if (c.roadmap) {
    lines.push(`\n## Execution Roadmap`);
    c.roadmap.forEach((p) => {
      lines.push(`\n### ${p.phase} (${p.weeks})`);
      (p.deliverables || []).forEach((d) => lines.push(`- ${d}`));
    });
  }
  if (c.risks) {
    lines.push(`\n## Risks`);
    c.risks.forEach((r) =>
      lines.push(`- **[${r.severity}] ${r.risk}** — ${r.mitigation}`)
    );
  }
  if (c.monetization) {
    lines.push(`\n## Monetization`);
    lines.push(`**Model:** ${c.monetization.model}`);
    lines.push(`\n**Unit economics:** ${c.monetization.unit_economics}`);
    lines.push(`\n### Pricing Tiers`);
    (c.monetization.pricing_tiers || []).forEach((t) => {
      lines.push(`\n**${t.name}** — ${t.price}`);
      (t.includes || []).forEach((it) => lines.push(`- ${it}`));
    });
  }
  if (c.executable_output) {
    lines.push(`\n## Executable Output\n${c.executable_output.summary}\n`);
    (c.executable_output.artifacts || []).forEach((a) => {
      lines.push(`\n### ${a.filename} (${a.kind})`);
      lines.push("```" + (a.language || ""));
      lines.push(a.content || "");
      lines.push("```");
    });
  }
  return lines.join("\n");
}
