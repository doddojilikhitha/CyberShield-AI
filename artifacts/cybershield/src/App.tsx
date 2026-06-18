import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";

import Layout from "@/components/Layout";
import Dashboard from "@/pages/dashboard";
import Submit from "@/pages/submit";
import ReviewList from "@/pages/review-list";
import ReviewDetail from "@/pages/review-detail";
import Report from "@/pages/report";
import Audit from "@/pages/audit";

const queryClient = new QueryClient();

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/submit" component={Submit} />
        <Route path="/review" component={ReviewList} />
        <Route path="/review/:id" component={ReviewDetail} />
        <Route path="/report/:id" component={Report} />
        <Route path="/audit" component={Audit} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  // Enforce dark mode
  if (typeof document !== "undefined") {
    document.documentElement.classList.add("dark");
  }

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
