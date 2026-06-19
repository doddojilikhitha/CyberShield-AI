import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";

import { useEffect } from "react";
import { useLocation } from "wouter";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/dashboard";
import Submit from "@/pages/submit";
import ReviewList from "@/pages/review-list";
import ReviewDetail from "@/pages/review-detail";
import Report from "@/pages/report";
import Audit from "@/pages/audit";
import Home from "@/pages/home";
import Login from "@/pages/login";

const queryClient = new QueryClient();

function Router() {
  const [location, setLocation] = useLocation();
  const isLoggedIn = sessionStorage.getItem("cybershield_auth") === "true";
  const isPublicRoute = location === "/home" || location === "/login";

  useEffect(() => {
    // If not logged in and trying to access a protected page, redirect to home
    if (!isLoggedIn && !isPublicRoute) {
      setLocation("/home");
    }
    // If logged in and trying to access landing/login pages, redirect to dashboard
    if (isLoggedIn && isPublicRoute) {
      setLocation("/");
    }
  }, [isLoggedIn, isPublicRoute, location, setLocation]);

  if (isPublicRoute) {
    return (
      <Switch>
        <Route path="/home" component={Home} />
        <Route path="/login" component={Login} />
        <Route component={NotFound} />
      </Switch>
    );
  }

  // Render Layout with Protected Routes only if authenticated
  if (!isLoggedIn) {
    return null; // Prevents layout flicker during redirects
  }

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
