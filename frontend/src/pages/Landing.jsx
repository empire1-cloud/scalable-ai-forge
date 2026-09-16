import { useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Layers,
  Zap,
  Code2,
  Target,
  Cpu,
  TrendingUp,
} from "lucide-react";

const layers = [
  {
    n: "01",
    icon: Layers,
    title: "Core Insight",
    body: "Reveal the hidden structural truth underneath the idea.",
  },
  {
    n: "02",
    icon: Cpu,
    title: "System Blueprint",
    body: "Architecture, components, tech stack, and data models.",
  },
  {
    n: "03",
    icon: Zap,
    title: "Leverage Point",
    body: "The single move that creates exponential advantage.",
  },
  {
    n: "04",
    icon: Code2,
    title: "Executable Output",
    body: "Ship-ready code, schemas, prompts, and API specs.",
  },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#070A0F] text-slate-100 relative overflow-hidden">
      <Header />

      {/* HERO */}
      <section className="relative pt-32 pb-24 px-4 sm:px-8">
        <div className="absolute inset-0 blueprint-mesh opacity-40 pointer-events-none" />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 40% at 30% 20%, rgba(6,182,212,0.14), transparent 60%), radial-gradient(ellipse 50% 40% at 80% 60%, rgba(245,158,11,0.10), transparent 60%)",
          }}
        />

        <div className="relative max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7">
            <div className="eyebrow mb-6" data-testid="hero-eyebrow">
              // emergent-intelligence systems architect
            </div>
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] text-slate-50">
              Turn any idea into a{" "}
              <span className="text-cyan-400">scalable system</span>,
              <br />
              not a suggestion.
            </h1>
            <p className="mt-6 text-lg text-slate-300/90 max-w-2xl leading-relaxed">
              One prompt in. A complete blueprint out — architecture, leverage
              points, roadmap, monetization, and production‑ready code you can
              deploy today.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Button
                data-testid="hero-cta-primary"
                size="lg"
                onClick={() => navigate("/auth")}
                className="h-12 px-6 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold text-base shadow-[0_0_30px_rgba(245,158,11,0.4)]"
              >
                Build Your First System
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <Button
                data-testid="hero-cta-secondary"
                size="lg"
                variant="outline"
                onClick={() => {
                  document
                    .getElementById("engine")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
                className="h-12 px-6 bg-transparent border-slate-700 text-slate-200 hover:bg-slate-800/60 hover:text-slate-50"
              >
                See the Engine
              </Button>
            </div>

            <div className="mt-12 flex items-center gap-8 text-xs font-mono tracking-widest uppercase text-slate-500">
              <span className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
                Claude Sonnet 5
              </span>
              <span>Structured JSON</span>
              <span className="hidden sm:inline">Exports MD + JSON</span>
            </div>
          </div>

          {/* Wire diagram */}
          <div className="lg:col-span-5">
            <div className="relative aspect-square rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-[#0A1220] to-[#0d131e] p-6 glow-cyan overflow-hidden">
              <div className="absolute inset-0 grid-bg opacity-70" />
              <svg
                className="wire-anim relative w-full h-full"
                viewBox="0 0 400 400"
              >
                <defs>
                  <linearGradient id="wire" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="100%" stopColor="#f59e0b" />
                  </linearGradient>
                </defs>
                <g fill="none" stroke="url(#wire)" strokeWidth="1.2">
                  <path d="M60 60 L200 60 L200 200 L340 200 L340 340 L60 340 Z" />
                  <path d="M60 60 L340 340" />
                  <path d="M340 60 L60 340" />
                  <path d="M200 60 L200 340" />
                  <path d="M60 200 L340 200" />
                </g>
                {[
                  [60, 60],
                  [200, 60],
                  [340, 60],
                  [60, 200],
                  [200, 200],
                  [340, 200],
                  [60, 340],
                  [200, 340],
                  [340, 340],
                ].map(([x, y], i) => (
                  <g key={i}>
                    <circle cx={x} cy={y} r="6" fill="#06b6d4" />
                    <circle cx={x} cy={y} r="12" fill="#06b6d4" opacity="0.15" />
                  </g>
                ))}
                <circle cx="200" cy="200" r="10" fill="#f59e0b" />
                <circle cx="200" cy="200" r="22" fill="#f59e0b" opacity="0.2" />
              </svg>

              <div className="absolute bottom-4 left-4 right-4 flex justify-between font-mono text-[10px] tracking-widest uppercase text-slate-500">
                <span>ontology</span>
                <span className="text-amber-400">leverage</span>
                <span>outputs</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ENGINE */}
      <section id="engine" className="py-24 px-4 sm:px-8 border-t border-slate-800/60">
        <div className="max-w-7xl mx-auto">
          <div className="eyebrow mb-4">// the engine, in four layers</div>
          <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight max-w-3xl">
            A partner building a long‑term empire, not a short‑term answer
            machine.
          </h2>

          <div className="mt-14 grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {layers.map((l) => (
              <div
                key={l.n}
                className="group relative rounded-xl border border-slate-800/80 bg-[#0D131E] p-6 hover:border-cyan-500/40 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="flex items-center justify-between mb-6">
                  <span className="font-mono text-xs tracking-widest text-cyan-400/80">
                    {l.n}
                  </span>
                  <l.icon className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                </div>
                <div className="font-heading text-xl font-bold text-slate-100">
                  {l.title}
                </div>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                  {l.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MANIFESTO */}
      <section className="py-24 px-4 sm:px-8 border-t border-slate-800/60">
        <div className="max-w-5xl mx-auto grid md:grid-cols-5 gap-10">
          <div className="md:col-span-2">
            <div className="eyebrow mb-4">// operating canon</div>
            <h3 className="font-heading text-2xl sm:text-3xl font-bold text-slate-100 leading-tight">
              Every output reveals structure, proposes systems, and produces
              executable artifacts.
            </h3>
          </div>
          <div className="md:col-span-3 space-y-4">
            {[
              {
                icon: Target,
                t: "Ontology first",
                b: "We name the hidden structure of the problem before recommending anything.",
              },
              {
                icon: Layers,
                t: "System over suggestion",
                b: "You leave with an architecture, not an opinion.",
              },
              {
                icon: TrendingUp,
                t: "The highest-ROI move",
                b: "One leverage point that changes the slope of your growth curve.",
              },
              {
                icon: Code2,
                t: "Artifacts, not advice",
                b: "Runnable code, schemas, and prompts you can ship today.",
              },
            ].map((r, i) => (
              <div
                key={i}
                className="flex gap-4 p-5 rounded-lg border border-slate-800/80 bg-[#0D131E]/60"
              >
                <div className="w-10 h-10 rounded-md bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center flex-shrink-0">
                  <r.icon className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <div className="font-heading font-semibold text-slate-100">
                    {r.t}
                  </div>
                  <div className="text-sm text-slate-400 mt-1">{r.b}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="py-24 px-4 sm:px-8 border-t border-slate-800/60">
        <div className="max-w-3xl mx-auto text-center">
          <div className="eyebrow mb-4">// deploy the console</div>
          <h3 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight">
            Your next system is one prompt away.
          </h3>
          <p className="mt-4 text-slate-400">
            Create an account, drop your idea, and receive a complete blueprint
            in under a minute.
          </p>
          <Button
            data-testid="final-cta-btn"
            size="lg"
            onClick={() => navigate("/auth")}
            className="mt-8 h-12 px-8 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold text-base"
          >
            Enter the Console
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </div>
      </section>

      <footer className="border-t border-slate-800/60 py-8 px-4 text-center font-mono text-xs tracking-widest uppercase text-slate-600">
        // emergent // architect — clarity, power, momentum
      </footer>
    </div>
  );
}
