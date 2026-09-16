import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Loader2, ArrowRight } from "lucide-react";

const MAX_POLLS = 15;

export default function PaymentSuccess() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState("checking"); // checking | success | timeout | error
  const pollsRef = useRef(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (!sessionId) {
      setStatus("error");
      return;
    }
    let cancelled = false;

    const poll = async () => {
      if (cancelled) return;
      if (pollsRef.current >= MAX_POLLS) {
        setStatus("timeout");
        return;
      }
      pollsRef.current += 1;
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (data.payment_status === "paid") {
          await refreshUser().catch(() => {});
          setStatus("success");
          return;
        }
        if (["failed", "expired", "refunded"].includes(data.payment_status)) {
          setStatus("error");
          return;
        }
      } catch (_) {
        /* keep polling */
      }
      setTimeout(poll, 2000);
    };
    poll();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-32 pb-24 px-4 flex items-center justify-center">
        <div
          data-testid="payment-success-card"
          className="w-full max-w-md rounded-2xl border border-slate-800/80 bg-[#0D131E] p-10 text-center"
        >
          {status === "checking" && (
            <>
              <Loader2 className="w-12 h-12 text-cyan-400 mx-auto animate-spin" />
              <h1 className="mt-6 font-heading text-2xl font-extrabold text-slate-100">
                Confirming your payment…
              </h1>
              <p className="mt-2 text-slate-400 text-sm">
                Hang tight, this only takes a moment.
              </p>
            </>
          )}
          {status === "success" && (
            <>
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
              <h1 className="mt-6 font-heading text-2xl font-extrabold text-slate-100">
                You&apos;re all set.
              </h1>
              <p className="mt-2 text-slate-400 text-sm">
                Your account has been upgraded. Time to build.
              </p>
              <Button
                data-testid="success-go-generator"
                onClick={() => navigate("/generator")}
                className="mt-6 w-full h-11 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold"
              >
                Start a blueprint <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </>
          )}
          {status === "timeout" && (
            <>
              <Loader2 className="w-12 h-12 text-amber-400 mx-auto" />
              <h1 className="mt-6 font-heading text-2xl font-extrabold text-slate-100">
                Still processing…
              </h1>
              <p className="mt-2 text-slate-400 text-sm">
                Your payment is taking longer than usual. It will apply automatically
                once confirmed.
              </p>
              <Button
                onClick={() => navigate("/dashboard")}
                className="mt-6 w-full h-11 bg-slate-800 hover:bg-slate-700 text-slate-200"
              >
                Back to vault
              </Button>
            </>
          )}
          {status === "error" && (
            <>
              <XCircle className="w-12 h-12 text-rose-400 mx-auto" />
              <h1 className="mt-6 font-heading text-2xl font-extrabold text-slate-100">
                Something went wrong.
              </h1>
              <p className="mt-2 text-slate-400 text-sm">
                We couldn&apos;t confirm this payment. You were not charged if it failed.
              </p>
              <Button
                onClick={() => navigate("/pricing")}
                className="mt-6 w-full h-11 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold"
              >
                Back to pricing
              </Button>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
