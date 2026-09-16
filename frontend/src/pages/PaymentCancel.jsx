import { useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { XCircle } from "lucide-react";

export default function PaymentCancel() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#070A0F]">
      <Header />
      <main className="pt-32 pb-24 px-4 flex items-center justify-center">
        <div
          data-testid="payment-cancel-card"
          className="w-full max-w-md rounded-2xl border border-slate-800/80 bg-[#0D131E] p-10 text-center"
        >
          <XCircle className="w-12 h-12 text-slate-500 mx-auto" />
          <h1 className="mt-6 font-heading text-2xl font-extrabold text-slate-100">
            Checkout cancelled.
          </h1>
          <p className="mt-2 text-slate-400 text-sm">
            No charge was made. You can upgrade any time.
          </p>
          <div className="mt-6 flex gap-3">
            <Button
              data-testid="cancel-back-pricing"
              onClick={() => navigate("/pricing")}
              className="flex-1 h-11 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold"
            >
              Back to pricing
            </Button>
            <Button
              onClick={() => navigate("/dashboard")}
              variant="outline"
              className="flex-1 h-11 border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Vault
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
