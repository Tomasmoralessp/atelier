import { useCallback, useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { ThemeProvider } from "@/lib/theme";
import GridPage from "@/pages/GridPage";
import DetailPage from "@/pages/DetailPage";
import { loadConfig, saveConfig, currentConfig } from "@/lib/config";
import { connectBackend } from "@/lib/startup";
import { isTauri } from "@/lib/utils";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

type Status = { state: "starting" } | { state: "ready" } | { state: "error"; message: string };

function StartupScreen({ status, onRetry }: { status: Status; onRetry: () => void }) {
  const switchToLocal = async () => {
    await saveConfig({ ...currentConfig, mode: "local" });
    onRetry();
  };
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center text-foreground">
      {status.state === "starting" ? (
        <>
          <p className="text-lg">Starting Atelier…</p>
          <p className="text-sm text-muted-foreground">
            The first launch can take a minute or two.
          </p>
        </>
      ) : (
        status.state === "error" && (
          <>
            <p className="text-lg">Atelier could not start</p>
            <p className="max-w-md text-sm text-muted-foreground">{status.message}</p>
            <div className="flex gap-2">
              <Button onClick={onRetry}>Retry</Button>
              {currentConfig.mode === "remote" && (
                <Button variant="outline" onClick={switchToLocal}>
                  Use this computer instead
                </Button>
              )}
            </div>
          </>
        )
      )}
    </div>
  );
}

export default function App() {
  const [status, setStatus] = useState<Status>({ state: isTauri ? "starting" : "ready" });

  const connect = useCallback(() => {
    loadConfig()
      .then(connectBackend)
      .then(() => setStatus({ state: "ready" }))
      .catch((e) => setStatus({ state: "error", message: e instanceof Error ? e.message : String(e) }));
  }, []);

  const retry = () => {
    setStatus({ state: "starting" });
    connect();
  };

  useEffect(() => {
    if (isTauri) connect();
  }, [connect]);

  return (
    <ThemeProvider>
      {status.state !== "ready" ? (
        <StartupScreen status={status} onRetry={retry} />
      ) : (
        <QueryClientProvider client={queryClient}>
          <TooltipProvider delayDuration={200}>
            <HashRouter>
              <Routes>
                <Route path="/" element={<GridPage />} />
                <Route path="/artwork/:id" element={<DetailPage />} />
              </Routes>
            </HashRouter>
            <Toaster position="bottom-right" />
          </TooltipProvider>
        </QueryClientProvider>
      )}
    </ThemeProvider>
  );
}
