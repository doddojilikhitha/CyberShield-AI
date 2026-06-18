import { useGetReport } from "@workspace/api-client-react";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  FileText, Shield, User, Clock, AlertTriangle, Loader2, ArrowLeft, 
  Download, BookOpen, Layers, CheckCircle2 
} from "lucide-react";
import { Link } from "wouter";

export default function Report({ params }: { params: { id: string } }) {
  const incidentId = params.id;
  
  const { data: report, isLoading, error } = useGetReport(incidentId);

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="text-primary font-mono text-sm uppercase animate-pulse">Compiling Telemetry Report...</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-8 text-destructive font-mono flex items-center gap-2">
        <AlertTriangle /> Error loading report. Please verify incident is approved.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <Link href={`/review/${incidentId}`}>
          <a className="inline-flex items-center gap-1.5 text-xs font-mono uppercase text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-4 h-4" /> Back to Review Detail
          </a>
        </Link>
        
        {/* PDF Download Button pointing to the backend route */}
        <a 
          href={`/api/reports/${incidentId}/pdf`} 
          download
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-mono font-bold text-xs uppercase rounded transition-colors"
        >
          <Download className="w-4 h-4" /> Download PDF Report
        </a>
      </div>

      <div className="flex items-center gap-3 border-b-2 border-primary/30 pb-4">
        <FileText className="w-8 h-8 text-primary" />
        <div>
          <h1 className="text-2xl font-mono font-bold text-primary tracking-tight uppercase">
            Incident Telemetry Report
          </h1>
          <p className="text-xs font-mono text-muted-foreground uppercase">
            Incident ID: {incidentId}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card/30 border border-border/50 p-4 rounded flex items-center gap-3">
          <Shield className="w-5 h-5 text-blue-400" />
          <div>
            <div className="text-[10px] uppercase font-mono text-muted-foreground">Classification</div>
            <div className="text-sm font-semibold capitalize">{report.classification || "N/A"}</div>
          </div>
        </div>
        <div className="bg-card/30 border border-border/50 p-4 rounded flex items-center gap-3">
          <Layers className="w-5 h-5 text-orange-500" />
          <div>
            <div className="text-[10px] uppercase font-mono text-muted-foreground">Severity Tier</div>
            <div className="text-sm font-semibold uppercase">{report.severity || "N/A"}</div>
          </div>
        </div>
        <div className="bg-card/30 border border-border/50 p-4 rounded flex items-center gap-3">
          <User className="w-5 h-5 text-cyan-400" />
          <div>
            <div className="text-[10px] uppercase font-mono text-muted-foreground">Sign-off Analyst</div>
            <div className="text-sm font-medium">{report.analyst_name || "N/A"}</div>
          </div>
        </div>
        <div className="bg-card/30 border border-border/50 p-4 rounded flex items-center gap-3">
          <Clock className="w-5 h-5 text-yellow-500" />
          <div>
            <div className="text-[10px] uppercase font-mono text-muted-foreground">Approved Date</div>
            <div className="text-xs font-mono">
              {report.approved_at ? new Date(report.approved_at).toLocaleDateString() : "N/A"}
            </div>
          </div>
        </div>
      </div>

      {/* Incident Description */}
      <Card className="bg-card/40 border-border/50">
        <CardHeader>
          <CardTitle className="text-xs font-mono font-bold uppercase text-primary">Incident Summary Scope</CardTitle>
        </CardHeader>
        <CardContent className="font-mono text-xs leading-relaxed text-muted-foreground bg-muted/20 p-4 rounded mx-6 mb-6">
          {report.incident_summary}
        </CardContent>
      </Card>

      {/* Framework Mapping */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/40 border-border/50">
          <CardHeader>
            <CardTitle className="text-xs font-mono font-bold uppercase text-primary flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" /> NIST IR Phases
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {report.nist_mapping?.length ? (
              report.nist_mapping.map((p: any, i: any) => (
                <div key={i} className="text-xs font-medium bg-muted/50 p-1.5 rounded border border-border/40">• {p}</div>
              ))
            ) : (
              <div className="text-xs font-mono text-muted-foreground">No mappings found</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/40 border-border/50 col-span-2">
          <CardHeader>
            <CardTitle className="text-xs font-mono font-bold uppercase text-primary flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" /> MITRE ATT&CK & OWASP
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-[10px] uppercase font-mono text-muted-foreground mb-1">ATT&CK Techniques</h4>
              {report.mitre_mapping?.length ? (
                report.mitre_mapping.map((t: any, i: any) => (
                  <div key={i} className="text-xs font-mono text-foreground mb-1">• {t}</div>
                ))
              ) : (
                <div className="text-xs font-mono text-muted-foreground">No techniques identified</div>
              )}
            </div>
            <div>
              <h4 className="text-[10px] uppercase font-mono text-muted-foreground mb-1">OWASP Guidance</h4>
              {report.owasp_guidance?.length ? (
                report.owasp_guidance.map((o: any, i: any) => (
                  <div key={i} className="text-xs font-medium text-foreground mb-1">• {o}</div>
                ))
              ) : (
                <div className="text-xs font-mono text-muted-foreground">No items applicable</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Response Playbook */}
      <Card className="bg-card/40 border-border/50">
        <CardHeader className="border-b border-border/40">
          <CardTitle className="text-xs font-mono font-bold uppercase text-primary">Final Incident Response Playbook</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <MarkdownRenderer content={report.final_playbook || ""} />
        </CardContent>
      </Card>

      {/* Audit Log Timeline */}
      <Card className="bg-card/40 border-border/50">
        <CardHeader>
          <CardTitle className="text-xs font-mono font-bold uppercase text-primary">Execution Audit Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {report.audit_summary?.map((log: any, i: any) => (
              <div key={i} className="flex items-start justify-between p-3 rounded bg-muted/20 border border-border/30">
                <div>
                  <div className="font-mono text-xs text-primary font-bold">{log.agent_name}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{log.output_summary}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono text-muted-foreground">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                  {log.processing_time_ms && (
                    <div className="text-[9px] font-mono text-muted-foreground mt-0.5">
                      {log.processing_time_ms}ms
                    </div>
                  )}
                </div>
              </div>
            )) || <div className="text-center py-6 font-mono text-xs text-muted-foreground">No logs present</div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
