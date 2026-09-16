import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Cpu, ArrowRight } from "lucide-react";

export default function AuthPage() {
  const { login, register, user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("signin");
  const [signIn, setSignIn] = useState({ email: "", password: "" });
  const [signUp, setSignUp] = useState({ name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  const handleSignIn = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(signIn.email, signIn.password);
      toast.success("Access granted. Entering console.");
      navigate("/dashboard");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await register(signUp.name, signUp.email, signUp.password);
      toast.success("Account provisioned.");
      navigate("/dashboard");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || "Sign up failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070A0F] grid lg:grid-cols-2">
      {/* LEFT — architectural art */}
      <div className="relative hidden lg:flex flex-col justify-between p-12 border-r border-slate-800/60 overflow-hidden">
        <div className="absolute inset-0 blueprint-mesh opacity-50" />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 60% at 30% 40%, rgba(6,182,212,0.15), transparent 70%)",
          }}
        />
        <div className="relative flex items-center gap-3">
          <div className="w-9 h-9 rounded-md border border-cyan-500/40 bg-cyan-500/10 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="font-heading font-extrabold tracking-tight text-slate-100">
              EMERGENT
            </div>
            <div className="font-mono text-[10px] tracking-[0.25em] text-cyan-400/80 -mt-0.5">
              // ARCHITECT
            </div>
          </div>
        </div>

        <div className="relative">
          <svg className="wire-anim w-full max-w-md" viewBox="0 0 400 300">
            <defs>
              <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#06b6d4" />
                <stop offset="100%" stopColor="#f59e0b" />
              </linearGradient>
            </defs>
            <g fill="none" stroke="url(#lg)" strokeWidth="1.2">
              <path d="M40 40 L200 40 L200 150 L360 150 L360 260 L40 260 Z" />
              <path d="M40 40 L360 260" />
              <path d="M200 40 L200 260" />
              <path d="M40 150 L360 150" />
            </g>
            {[
              [40, 40],
              [200, 40],
              [360, 40],
              [40, 150],
              [200, 150],
              [360, 150],
              [40, 260],
              [200, 260],
              [360, 260],
            ].map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r="5" fill="#06b6d4" />
            ))}
            <circle cx="200" cy="150" r="8" fill="#f59e0b" />
          </svg>
          <div className="mt-8 max-w-md">
            <div className="eyebrow mb-3">// canon</div>
            <p className="font-heading text-2xl font-bold text-slate-100 leading-tight">
              A partner building a long‑term empire, not a short‑term answer
              machine.
            </p>
          </div>
        </div>

        <div className="relative font-mono text-[10px] tracking-widest uppercase text-slate-600">
          clarity · power · momentum
        </div>
      </div>

      {/* RIGHT — form */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="eyebrow mb-3">// access console</div>
          <h1 className="font-heading text-3xl font-extrabold tracking-tight mb-8">
            Enter the workbench.
          </h1>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList
              className="grid grid-cols-2 bg-[#0D131E] border border-slate-800/80 h-11"
              data-testid="auth-tabs"
            >
              <TabsTrigger
                value="signin"
                data-testid="auth-tab-signin"
                className="data-[state=active]:bg-cyan-500 data-[state=active]:text-slate-900 font-mono text-xs tracking-widest uppercase"
              >
                Sign In
              </TabsTrigger>
              <TabsTrigger
                value="signup"
                data-testid="auth-tab-signup"
                className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900 font-mono text-xs tracking-widest uppercase"
              >
                Sign Up
              </TabsTrigger>
            </TabsList>

            <TabsContent value="signin">
              <form onSubmit={handleSignIn} className="space-y-5 mt-6">
                <div>
                  <Label htmlFor="si-email" className="text-slate-300">
                    Email
                  </Label>
                  <Input
                    id="si-email"
                    type="email"
                    data-testid="signin-email-input"
                    required
                    value={signIn.email}
                    onChange={(e) => setSignIn({ ...signIn, email: e.target.value })}
                    className="mt-1.5 bg-[#0D131E] border-slate-800 focus:border-cyan-500 h-11"
                  />
                </div>
                <div>
                  <Label htmlFor="si-pw" className="text-slate-300">
                    Password
                  </Label>
                  <Input
                    id="si-pw"
                    type="password"
                    data-testid="signin-password-input"
                    required
                    value={signIn.password}
                    onChange={(e) =>
                      setSignIn({ ...signIn, password: e.target.value })
                    }
                    className="mt-1.5 bg-[#0D131E] border-slate-800 focus:border-cyan-500 h-11"
                  />
                </div>
                <Button
                  type="submit"
                  data-testid="signin-submit-btn"
                  disabled={busy}
                  className="w-full h-11 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold"
                >
                  {busy ? "Authenticating..." : "Sign In"}
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-5 mt-6">
                <div>
                  <Label htmlFor="su-name" className="text-slate-300">
                    Name
                  </Label>
                  <Input
                    id="su-name"
                    data-testid="signup-name-input"
                    required
                    value={signUp.name}
                    onChange={(e) => setSignUp({ ...signUp, name: e.target.value })}
                    className="mt-1.5 bg-[#0D131E] border-slate-800 focus:border-amber-500 h-11"
                  />
                </div>
                <div>
                  <Label htmlFor="su-email" className="text-slate-300">
                    Email
                  </Label>
                  <Input
                    id="su-email"
                    type="email"
                    data-testid="signup-email-input"
                    required
                    value={signUp.email}
                    onChange={(e) => setSignUp({ ...signUp, email: e.target.value })}
                    className="mt-1.5 bg-[#0D131E] border-slate-800 focus:border-amber-500 h-11"
                  />
                </div>
                <div>
                  <Label htmlFor="su-pw" className="text-slate-300">
                    Password
                  </Label>
                  <Input
                    id="su-pw"
                    type="password"
                    data-testid="signup-password-input"
                    required
                    minLength={6}
                    value={signUp.password}
                    onChange={(e) =>
                      setSignUp({ ...signUp, password: e.target.value })
                    }
                    className="mt-1.5 bg-[#0D131E] border-slate-800 focus:border-amber-500 h-11"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Minimum 6 characters.
                  </p>
                </div>
                <Button
                  type="submit"
                  data-testid="signup-submit-btn"
                  disabled={busy}
                  className="w-full h-11 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold"
                >
                  {busy ? "Provisioning..." : "Create Account"}
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
