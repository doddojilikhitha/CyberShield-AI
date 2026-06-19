import { Link, useLocation } from "wouter";
import { Shield, Activity, FileText, ClipboardCheck, ScrollText, LogOut } from "lucide-react";

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useLocation();

  const navItems = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/submit", label: "Submit Incident", icon: Shield },
    { href: "/review", label: "Review Hub", icon: ClipboardCheck },
    { href: "/audit", label: "Audit Logs", icon: ScrollText },
  ];

  const handleLogout = () => {
    sessionStorage.removeItem("cybershield_auth");
    setLocation("/home");
  };

  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      <aside className="w-64 border-r border-border bg-card flex flex-col justify-between">
        <div className="flex flex-col flex-1">
          <div className="p-4 border-b border-border flex items-center gap-2 text-primary">
            <Shield className="w-6 h-6" />
            <span className="font-mono font-bold uppercase tracking-wider text-sm">CyberShield</span>
          </div>
          <nav className="flex-1 overflow-y-auto py-4">
            <ul className="space-y-1 px-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      location === item.href
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="p-4 border-t border-border bg-card/30">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-mono text-xs uppercase font-medium transition-all text-destructive hover:text-destructive hover:bg-destructive/10 border border-transparent hover:border-destructive/20 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            Disconnect Session
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto relative">{children}</main>
    </div>
  );
}
