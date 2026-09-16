import "@/index.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Landing from "@/pages/Landing";
import AuthPage from "@/pages/AuthPage";
import Dashboard from "@/pages/Dashboard";
import Generator from "@/pages/Generator";
import BlueprintDetail from "@/pages/BlueprintDetail";
import CorePage from "@/pages/CorePage";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070A0F] text-slate-400">
        <div className="font-mono text-xs tracking-widest uppercase pulse-dot">
          Loading vault...
        </div>
      </div>
    );
  }
  if (!user) return <Navigate to="/auth" replace />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route
            path="/dashboard"
            element={
              <Protected>
                <Dashboard />
              </Protected>
            }
          />
          <Route
            path="/generator"
            element={
              <Protected>
                <Generator />
              </Protected>
            }
          />
          <Route
            path="/core"
            element={
              <Protected>
                <CorePage />
              </Protected>
            }
          />
          <Route
            path="/blueprint/:id"
            element={
              <Protected>
                <BlueprintDetail />
              </Protected>
            }
          />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="bottom-right" />
    </AuthProvider>
  );
}

export default App;
