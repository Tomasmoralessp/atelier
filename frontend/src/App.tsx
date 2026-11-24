import { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/lib/theme";
import GridPage from "@/pages/GridPage";
import DetailPage from "@/pages/DetailPage";
import { loadConfig } from "@/lib/config";
import { setApiBase } from "@/lib/api";
import { isTauri } from "@/lib/utils";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  const [configLoaded, setConfigLoaded] = useState(false);
  useEffect(() => {
    if (isTauri) {
      loadConfig().then((config) => {
        setApiBase(config.apiBase);
        setConfigLoaded(true);
      });
    } else {
      setConfigLoaded(true);
    }
  }, []);
  if (!configLoaded) return null;
  return (
    <ThemeProvider>
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
    </ThemeProvider>
  );
}
