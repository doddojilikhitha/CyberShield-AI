import { useState } from "react";
import { useLocation } from "wouter";
import { Shield, Lock, Mail, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Hardcoded credentials requirement
    if (email === "security@organization.com" && password === "CyberShield@123") {
      setTimeout(() => {
        sessionStorage.setItem("cybershield_auth", "true");
        setLoading(false);
        setLocation("/"); // Redirect to dashboard
      }, 800);
    } else {
      setTimeout(() => {
        setError("Invalid organization credentials. Please check your email and password.");
        setLoading(false);
      }, 600);
    }
  };

  return (
    <div className="min-h-screen bg-black text-foreground relative overflow-hidden flex items-center justify-center p-6">
      {/* Decorative Blur Glows */}
      <div className="absolute top-[20%] left-[20%] w-[300px] h-[300px] bg-primary/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[20%] w-[300px] h-[300px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Cyber Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#151515_1px,transparent_1px),linear-gradient(to_bottom,#151515_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      <Card className="w-full max-w-md bg-card/40 border-border/50 backdrop-blur-md relative z-10 p-2 shadow-2xl">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <Shield className="w-6 h-6 animate-pulse" />
            </div>
          </div>
          <CardTitle className="text-xl font-mono font-bold tracking-tight uppercase text-foreground">
            Identity Verification
          </CardTitle>
          <CardDescription className="text-xs font-mono uppercase text-muted-foreground">
            Sign In with your Corporate Security Credentials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-mono uppercase text-muted-foreground">Corporate Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  placeholder="security@organization.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="pl-9 bg-card border-border/50 text-xs font-mono focus-visible:ring-primary/40 focus-visible:border-primary/50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-mono uppercase text-muted-foreground">Access Key / Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pl-9 bg-card border-border/50 text-xs font-mono focus-visible:ring-primary/40 focus-visible:border-primary/50"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded flex items-start gap-2 text-destructive font-mono text-[11px] uppercase">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full font-mono text-xs uppercase tracking-wider h-10 mt-6"
            >
              {loading ? "Authenticating..." : "Establish Secure Session"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
