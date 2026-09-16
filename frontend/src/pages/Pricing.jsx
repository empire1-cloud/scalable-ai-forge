import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Check, Zap, Coins, ArrowRight } from "lucide-react";

export default function Pricing() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [config, setConfig] = useState(null);
  const [yearly, setYearly] = useState(false);
  const [loadingKey, setLoadingKey] = useState(null);

  useEffect(() => {
    api
      .get("/billing/config")
      .then((r) => setConfig(r.data))
      .catch((e) => toast.error(formatApiError(e.response?.data?.detail)));
  }, []);

  const checkout = async (lookup_key) => {
    if (!user) {
      navigate("/auth");
      return;
    }
    setLoadingKey(lookup_key);
    try {
      const { data } = await api.post("/payments/checkout", {
        lookup_key,
        origin_url: window.location.origin,
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
      setLoadingKey(null);
    }
  };

  const currentPlan = user ? user.plan || "free" : null;

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-24 pb-24 px-4 sm:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <div className="eyebrow mb-3">// pricing</div>
          <h1 className="font-heading text-4xl sm:text-5xl font-extrabold tracking-tight">
            Build more. Ship faster.
          </h1>
          <p className="mt-3 text-slate-400 max-w-xl mx-auto">
            Start free. Upgrade when you need unlimited blueprints and the Hybrid
            Intelligence Core.
          </p>

          <div
            data-testid="billing-interval-toggle"
            className="mt-8 inline-flex items-center gap-1 rounded-full border border-slate-800 bg-[#0D131E] p-1"
          >
            <button
              data-testid="interval-monthly"
              onClick={() => setYearly(false)}
              className={`px-5 py-2 rounded-full text-sm font-mono tracking-wide transition-colors ${
                !yearly ? "bg-cyan-500 text-slate-900 font-semibold" : "text-slate-400"
              }`}
            >
              Monthly
            </button>
            <button
              data-testid="interval-yearly"
              onClick={() => setYearly(true)}
              className={`px-5 py-2 rounded-full text-sm font-mono tracking-wide transition-colors ${
                yearly ? "bg-cyan-500 text-slate-900 font-semibold" : "text-slate-400"
              }`}
            >
              Yearly <span className="text-amber-400">−20%</span>
            </button>
          </div>
        </div>

        {!config ? (
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-96 rounded-2xl border border-slate-800/80 bg-[#0D131E] shimmer" />
            ))}
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-3 gap-6">
              {config.plans.map((plan) => {
                const price = yearly ? plan.yearly : plan.monthly;
                const isFree = plan.id === "free";
                const isCurrent = currentPlan === plan.id;
                const lookup = yearly ? plan.lookup_yearly : plan.lookup_monthly;
                return (
                  <div
                    key={plan.id}
                    data-testid={`plan-card-${plan.id}`}
                    className={`relative rounded-2xl border p-7 flex flex-col transition-all ${
                      plan.highlighted
                        ? "border-cyan-500/60 bg-[#0D131E] shadow-[0_0_40px_rgba(6,182,212,0.15)]"
                        : "border-slate-800/80 bg-[#0D131E]"
                    }`}
                  >
                    {plan.highlighted && (
                      <div className="absolute -top-3 left-7 px-3 py-1 rounded-full bg-cyan-500 text-slate-900 text-[10px] font-mono font-bold tracking-widest uppercase">
                        Most popular
                      </div>
                    )}
                    <div className="font-mono text-[10px] tracking-widest uppercase text-cyan-400/80">
                      {plan.tagline}
                    </div>
                    <h3 className="mt-2 font-heading text-2xl font-extrabold text-slate-100">
                      {plan.name}
                    </h3>
                    <div className="mt-4 flex items-baseline gap-1">
                      <span className="font-heading text-4xl font-extrabold text-slate-100">
                        ${isFree ? "0" : yearly ? Math.round(price / 12) : price}
                      </span>
                      <span className="text-slate-500 text-sm">/mo</span>
                    </div>
                    {!isFree && yearly && (
                      <div className="mt-1 text-xs text-slate-500 font-mono">
                        ${price.toFixed(2)} billed yearly
                      </div>
                    )}

                    <ul className="mt-6 space-y-3 flex-1">
                      {plan.features.map((f, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                          <Check className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>

                    <div className="mt-7">
                      {isCurrent ? (
                        <Button
                          disabled
                          data-testid={`plan-current-${plan.id}`}
                          className="w-full h-11 bg-slate-800 text-slate-400 cursor-default"
                        >
                          Current plan
                        </Button>
                      ) : isFree ? (
                        <Button
                          onClick={() => navigate(user ? "/generator" : "/auth")}
                          data-testid="plan-free-cta"
                          variant="outline"
                          className="w-full h-11 border-slate-700 text-slate-300 hover:bg-slate-800"
                        >
                          {user ? "Start building" : "Get started"}
                        </Button>
                      ) : (
                        <Button
                          onClick={() => checkout(lookup)}
                          disabled={loadingKey === lookup}
                          data-testid={`plan-checkout-${plan.id}`}
                          className={`w-full h-11 font-semibold ${
                            plan.highlighted
                              ? "bg-cyan-500 hover:bg-cyan-400 text-slate-900"
                              : "bg-amber-500 hover:bg-amber-400 text-slate-900"
                          }`}
                        >
                          {loadingKey === lookup ? "Redirecting…" : `Upgrade to ${plan.name}`}
                          <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-14">
              <div className="flex items-center gap-3 mb-6">
                <Coins className="w-5 h-5 text-amber-400" />
                <h2 className="font-heading text-xl font-bold text-slate-100">
                  Or top up with credits
                </h2>
                <span className="text-sm text-slate-500">
                  One-time. Each credit = one extra blueprint.
                </span>
              </div>
              <div className="grid sm:grid-cols-2 gap-5 max-w-2xl">
                {config.credit_packs.map((pack) => (
                  <div
                    key={pack.id}
                    data-testid={`credit-pack-${pack.id}`}
                    className="rounded-xl border border-slate-800/80 bg-[#0D131E] p-6 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-heading text-lg font-bold text-slate-100">
                        {pack.name}
                      </div>
                      <div className="text-sm text-slate-400">
                        ${pack.price} · {pack.credits} blueprints
                      </div>
                    </div>
                    <Button
                      onClick={() => checkout(pack.lookup_key)}
                      disabled={loadingKey === pack.lookup_key}
                      data-testid={`credit-checkout-${pack.id}`}
                      className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold"
                    >
                      <Zap className="w-4 h-4 mr-1.5" />
                      {loadingKey === pack.lookup_key ? "…" : "Buy"}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
