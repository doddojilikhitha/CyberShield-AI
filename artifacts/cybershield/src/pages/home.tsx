import { Link } from "wouter";
import { Shield, ArrowRight, ShieldCheck, Database, ScrollText, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-foreground relative overflow-hidden flex flex-col justify-between">
      {/* Decorative Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Cyber Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#151515_1px,transparent_1px),linear-gradient(to_bottom,#151515_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Top Navbar */}
      <header className="border-b border-border/40 backdrop-blur-md bg-black/40 relative z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-primary">
            <Shield className="w-6 h-6" />
            <span className="font-mono font-bold uppercase tracking-wider text-sm">CyberShield AI</span>
          </div>
          <div>
            <Link href="/login">
              <Button variant="ghost" className="font-mono text-xs uppercase text-muted-foreground hover:text-foreground">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-20 flex-1 flex flex-col justify-center items-center text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-mono mb-8 animate-pulse">
          <ShieldCheck className="w-4 h-4" />
          <span>MILITARY-GRADE ORCHESTRATION</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-mono font-bold tracking-tight max-w-4xl leading-tight bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
          SECURE. ANALYZE. AUTOMATE.<br />
          <span className="text-primary">NEXT-GEN AI INCIDENT RESPONSE</span>
        </h1>

        <p className="text-muted-foreground text-sm md:text-base font-mono max-w-2xl mt-6 uppercase leading-relaxed">
          Powered by a multi-agent LangGraph engine and context-aware Enterprise RAG, CyberShield AI automates incident classification, framework mapping, and compliance verification.
        </p>

        <div className="mt-10 flex gap-4">
          <Link href="/login">
            <Button size="lg" className="font-mono text-xs uppercase tracking-wider gap-2">
              Launch Console <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl mt-20">
          <Card className="bg-card/30 border-border/40 backdrop-blur p-6 hover:border-primary/30 transition-all group">
            <CardContent className="p-0 space-y-4">
              <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-sm text-foreground uppercase tracking-wider">Multi-Agent Engine</h3>
              <p className="text-xs text-muted-foreground font-mono uppercase">
                LangGraph orchestrates specialized agents sequentially or conditionally for rapid, context-aware playbook generation.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/40 backdrop-blur p-6 hover:border-primary/30 transition-all group">
            <CardContent className="p-0 space-y-4">
              <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-sm text-foreground uppercase tracking-wider">Enterprise RAG Knowledge</h3>
              <p className="text-xs text-muted-foreground font-mono uppercase">
                Integrates ChromaDB to retrieve real-time threat intelligence mapping directly to NIST and MITRE ATT&CK standards.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/40 backdrop-blur p-6 hover:border-primary/30 transition-all group">
            <CardContent className="p-0 space-y-4">
              <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
                <ScrollText className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-sm text-foreground uppercase tracking-wider">Compliance Review</h3>
              <p className="text-xs text-muted-foreground font-mono uppercase">
                Dual-tier compliance tracing records audit logs securely to SQLite, delivering scores, gap analysis, and PDF exports.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/20 py-6 text-center text-xs font-mono text-muted-foreground uppercase relative z-10 bg-black/80">
        <span>© 2026 Organization Security Operations Center. All rights reserved.</span>
      </footer>
    </div>
  );
}
