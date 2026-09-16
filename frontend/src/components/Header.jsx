import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Cpu, LogOut, Plus, LayoutGrid, GitBranch, Sparkles, Crown } from "lucide-react";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-slate-800/80 bg-[#070A0F]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto h-full px-4 sm:px-8 flex items-center justify-between">
        <Link
          to={user ? "/dashboard" : "/"}
          data-testid="brand-link"
          className="flex items-center gap-3 group"
        >
          <div className="relative w-8 h-8 rounded-md border border-cyan-500/40 bg-cyan-500/10 flex items-center justify-center group-hover:glow-cyan transition-all">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full pulse-dot" />
          </div>
          <div className="leading-tight">
            <div className="font-heading font-extrabold text-slate-100 text-sm tracking-tight">
              EMERGENT
            </div>
            <div className="font-mono text-[10px] tracking-[0.25em] text-cyan-400/80 -mt-0.5">
              // ARCHITECT
            </div>
          </div>
        </Link>

        <nav className="flex items-center gap-2">
          {user ? (
            <>
              <Button
                data-testid="nav-dashboard-btn"
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
                className="text-slate-300 hover:text-slate-100 hover:bg-slate-800/60"
              >
                <LayoutGrid className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Vault</span>
              </Button>
              <Button
                data-testid="nav-core-btn"
                variant="ghost"
                size="sm"
                onClick={() => navigate("/core")}
                className="text-slate-300 hover:text-cyan-300 hover:bg-cyan-500/10"
              >
                <GitBranch className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Core</span>
              </Button>
              {user.plan && user.plan !== "free" ? (
                <span
                  data-testid="plan-badge"
                  onClick={() => navigate("/pricing")}
                  className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-amber-500/40 bg-amber-500/10 text-amber-300 text-[10px] font-mono tracking-widest uppercase cursor-pointer"
                >
                  <Crown className="w-3 h-3" />
                  {user.plan}
                </span>
              ) : (
                <Button
                  data-testid="nav-upgrade-btn"
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate("/pricing")}
                  className="text-amber-300 hover:text-amber-200 hover:bg-amber-500/10"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Upgrade</span>
                </Button>
              )}
              <Button
                data-testid="nav-new-blueprint-btn"
                size="sm"
                onClick={() => navigate("/generator")}
                className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold shadow-[0_0_20px_rgba(245,158,11,0.35)]"
              >
                <Plus className="w-4 h-4 mr-1" />
                New Blueprint
              </Button>
              <Button
                data-testid="nav-logout-btn"
                variant="ghost"
                size="sm"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
                className="text-slate-400 hover:text-rose-400"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </>
          ) : (
            <Button
              data-testid="nav-signin-btn"
              size="sm"
              onClick={() => navigate("/auth")}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold"
            >
              Enter Console
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
}
