import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import { api, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Plus,
  Search,
  Layers,
  Trash2,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAuth } from "@/context/AuthContext";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  const fetchList = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/blueprints");
      setItems(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  const remove = async (id) => {
    try {
      await api.delete(`/blueprints/${id}`);
      setItems((s) => s.filter((b) => b.id !== id));
      toast.success("Blueprint deleted.");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const filtered = items.filter((b) => {
    const s = q.trim().toLowerCase();
    if (!s) return true;
    return (
      (b.title || "").toLowerCase().includes(s) ||
      (b.idea || "").toLowerCase().includes(s) ||
      (b.tagline || "").toLowerCase().includes(s)
    );
  });

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-24 pb-16 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-12">
          <div>
            <div className="eyebrow mb-3">// blueprint vault</div>
            <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight">
              Welcome back, {user?.name?.split(" ")[0] || "Architect"}.
            </h1>
            <p className="mt-2 text-slate-400 max-w-xl">
              Every system you've drafted, ready to deploy or evolve.
            </p>
          </div>
          <Button
            data-testid="dashboard-new-btn"
            onClick={() => navigate("/generator")}
            className="h-11 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold shadow-[0_0_25px_rgba(245,158,11,0.35)]"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Blueprint
          </Button>
        </div>

        <div className="mb-8 relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            data-testid="dashboard-search-input"
            placeholder="Search blueprints..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="pl-10 h-11 bg-[#0D131E] border-slate-800 focus:border-cyan-500"
          />
        </div>

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-48 rounded-xl border border-slate-800/80 bg-[#0D131E] shimmer"
              />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState onCreate={() => navigate("/generator")} hasQuery={!!q} />
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((b) => (
              <div
                key={b.id}
                data-testid={`blueprint-card-${b.id}`}
                className="group relative rounded-xl border border-slate-800/80 bg-[#0D131E] p-6 hover:border-cyan-500/50 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-9 h-9 rounded-md bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                    <Layers className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="font-mono text-[10px] tracking-widest uppercase text-slate-500">
                    {new Date(b.created_at).toLocaleDateString()}
                  </div>
                </div>
                <h3
                  className="font-heading text-lg font-bold text-slate-100 leading-snug line-clamp-2 cursor-pointer"
                  onClick={() => navigate(`/blueprint/${b.id}`)}
                >
                  {b.title}
                </h3>
                {b.tagline && (
                  <p className="mt-1.5 text-sm text-cyan-400/80 line-clamp-1">
                    {b.tagline}
                  </p>
                )}
                <p className="mt-3 text-sm text-slate-400 line-clamp-3 leading-relaxed">
                  {b.core_insight_snippet || b.idea}
                </p>

                <div className="mt-5 flex items-center justify-between">
                  <Button
                    data-testid={`open-blueprint-${b.id}`}
                    size="sm"
                    variant="ghost"
                    onClick={() => navigate(`/blueprint/${b.id}`)}
                    className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 -ml-3"
                  >
                    Open <ArrowRight className="ml-1 w-3 h-3" />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        data-testid={`delete-blueprint-${b.id}`}
                        size="sm"
                        variant="ghost"
                        className="text-slate-500 hover:text-rose-400 hover:bg-rose-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-[#0D131E] border-slate-800">
                      <AlertDialogHeader>
                        <AlertDialogTitle className="font-heading">
                          Delete this blueprint?
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                          This will permanently remove "{b.title}" from your
                          vault. This cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel className="bg-transparent border-slate-700 text-slate-300">
                          Cancel
                        </AlertDialogCancel>
                        <AlertDialogAction
                          data-testid={`confirm-delete-${b.id}`}
                          onClick={() => remove(b.id)}
                          className="bg-rose-500 hover:bg-rose-400 text-slate-900"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function EmptyState({ onCreate, hasQuery }) {
  return (
    <div
      data-testid="dashboard-empty-state"
      className="rounded-2xl border border-dashed border-slate-800 bg-[#0D131E]/50 p-16 text-center"
    >
      <div className="w-14 h-14 rounded-xl border border-cyan-500/30 bg-cyan-500/10 mx-auto flex items-center justify-center mb-6">
        <Sparkles className="w-6 h-6 text-cyan-400" />
      </div>
      <h3 className="font-heading text-2xl font-bold text-slate-100">
        {hasQuery ? "No matching blueprints." : "The vault is empty."}
      </h3>
      <p className="mt-2 text-slate-400 max-w-md mx-auto">
        {hasQuery
          ? "Try a different search term."
          : "Drop an idea into the generator and receive a complete system in under a minute."}
      </p>
      {!hasQuery && (
        <Button
          onClick={onCreate}
          className="mt-6 h-11 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold"
        >
          Create your first blueprint
          <ArrowRight className="ml-2 w-4 h-4" />
        </Button>
      )}
    </div>
  );
}
