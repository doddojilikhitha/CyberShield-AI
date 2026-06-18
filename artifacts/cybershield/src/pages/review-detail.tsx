import { useState } from "react";
import { useLocation } from "wouter";
import { 
  useGetIncident, 
  useGetPlaybook, 
  useApprovePlaybook, 
  useRejectPlaybook, 
  useRegeneratePlaybook 
} from "@workspace/api-client-react";
import { useToast } from "@/hooks/use-toast";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Shield, CheckCircle2, XCircle, AlertTriangle, Loader2, ArrowLeft, 
  ShieldAlert, BookOpen, ScrollText, Cpu, ExternalLink 
} from "lucide-react";
import { Link } from "wouter";

export default function ReviewDetail({ params }: { params: { id: string } }) {
  const incidentId = params.id;
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  
  const { data: incident, isLoading: loadingIncident, error: incidentErr } = useGetIncident(incidentId);
  const { data: playbook, isLoading: loadingPlaybook, error: playbookErr, refetch: refetchPlaybook } = useGetPlaybook(incidentId);
  
  const approvePlaybook = useApprovePlaybook();
  const rejectPlaybook = useRejectPlaybook();
  const regeneratePlaybook = useRegeneratePlaybook();

  const [feedback, setFeedback] = useState("");
  const [analystId, setAnalystId] = useState("analyst_01");
  const [showRejectForm, setShowRejectForm] = useState(false);

  if (loadingIncident || loadingPlaybook) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="text-primary font-mono text-sm uppercase animate-pulse">Retrieving Alert Scope...</span>
      </div>
    );
  }

  if (incidentErr || playbookErr || !incident || !playbook) {
    return (
      <div className="p-8 text-destructive font-mono flex items-center gap-2">
        <AlertTriangle /> Error retrieving records. Incident ID might be invalid.
      </div>
    );
  }

  const handleApprove = () => {
    approvePlaybook.mutate(
      { data: { incident_id: incidentId, analyst_id: analystId } },
      {
        onSuccess: () => {
          toast({ title: "Playbook Approved", description: "Successfully signed off on incident playbook." });
          refetchPlaybook();
        },
        onError: (err: any) => {
          toast({ title: "Approval Failed", description: err.detail || "Unknown error", variant: "destructive" });
        }
      }
    );
  };

  const handleReject = () => {
    if (!feedback.trim()) {
      toast({ title: "Feedback Required", description: "Please explain the revision requirements.", variant: "destructive" });
      return;
    }
    rejectPlaybook.mutate(
      { data: { incident_id: incidentId, analyst_id: analystId, feedback } },
      {
        onSuccess: () => {
          toast({ title: "Playbook Rejected", description: "Playbook set to rejected status." });
          // Automatically trigger regeneration
          regeneratePlaybook.mutate(
            { data: { incident_id: incidentId } },
            {
              onSuccess: () => {
                toast({ title: "Regeneration Initiated", description: "Agent pipeline is incorporating your feedback..." });
                setShowRejectForm(false);
                setFeedback("");
                refetchPlaybook();
              },
              onError: (err: any) => {
                toast({ title: "Regeneration Failed", description: err.detail || "Unknown error", variant: "destructive" });
              }
            }
          );
        },
        onError: (err: any) => {
          toast({ title: "Rejection Failed", description: err.detail || "Unknown error", variant: "destructive" });
        }
      }
    );
  };

  const isMutating = approvePlaybook.isPending || rejectPlaybook.isPending || regeneratePlaybook.isPending;

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <Link href="/review">
          <a className="inline-flex items-center gap-1.5 text-xs font-mono uppercase text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-4 h-4" /> Back to Review Hub
          </a>
        </Link>
        {playbook.review_status === "approved" && (
          <Link href={`/report/${incidentId}`}>
            <a className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-mono font-bold uppercase">
              View Final Report <ExternalLink className="w-4 h-4" />
            </a>
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Incident Scope & Metadata */}
        <div className="space-y-6">
          <Card className="bg-card/40 border-border/50">
            <CardHeader className="border-b border-border/40 pb-3">
              <CardTitle className="text-xs font-mono font-bold uppercase text-primary flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> Telemetry Scope
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <Label className="text-[10px] uppercase font-mono text-muted-foreground">Incident ID</Label>
                <div className="font-mono text-sm break-all bg-muted/40 p-2 rounded border border-border/40">{incidentId}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-[10px] uppercase font-mono text-muted-foreground">Urgency Tier</Label>
                  <div className="text-sm font-semibold uppercase">{incident.priority}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase font-mono text-muted-foreground">Status</Label>
                  <div className={`text-sm font-bold uppercase ${
                    playbook.review_status === 'approved' ? 'text-green-500' :
                    playbook.review_status === 'rejected' ? 'text-red-500' :
                    'text-yellow-400'
                  }`}>{playbook.review_status}</div>
                </div>
              </div>
              <div>
                <Label className="text-[10px] uppercase font-mono text-muted-foreground">Analyst</Label>
                <div className="text-sm">{incident.analyst_name}</div>
              </div>
              <div>
                <Label className="text-[10px] uppercase font-mono text-muted-foreground">Source</Label>
                <div className="text-sm font-mono">{incident.incident_source || "manual"}</div>
              </div>
              <div>
                <Label className="text-[10px] uppercase font-mono text-muted-foreground">Incident Description</Label>
                <div className="text-sm leading-relaxed max-h-48 overflow-y-auto bg-muted/20 p-2.5 rounded border border-border/30 font-mono text-xs">
                  {incident.incident_description}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Framework alignment card */}
          {playbook.framework_context && (
            <Card className="bg-card/40 border-border/50">
              <CardHeader className="border-b border-border/40 pb-3">
                <CardTitle className="text-xs font-mono font-bold uppercase text-primary flex items-center gap-2">
                  <BookOpen className="w-4 h-4" /> Framework Alignments
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div>
                  <h4 className="text-[10px] uppercase font-mono font-bold text-muted-foreground mb-1">NIST Phase Mapping</h4>
                  <div className="flex flex-wrap gap-1">
                    {playbook.framework_context.nist_phases?.map((p: any, i: any) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">{p}</span>
                    )) || <span className="text-xs text-muted-foreground">None</span>}
                  </div>
                </div>
                <div>
                  <h4 className="text-[10px] uppercase font-mono font-bold text-muted-foreground mb-1">MITRE ATT&CK Techniques</h4>
                  <ul className="space-y-1">
                    {playbook.framework_context.mitre_techniques?.map((t: any, i: any) => (
                      <li key={i} className="text-xs font-mono text-foreground">• {t}</li>
                    )) || <li className="text-xs text-muted-foreground">None</li>}
                  </ul>
                </div>
                <div>
                  <h4 className="text-[10px] uppercase font-mono font-bold text-muted-foreground mb-1">OWASP Category Mapping</h4>
                  <div className="flex flex-wrap gap-1">
                    {playbook.framework_context.owasp_categories?.map((c: any, i: any) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">{c}</span>
                    )) || <span className="text-xs text-muted-foreground">None</span>}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Compliance scoring */}
          {playbook.reviewer_feedback && (
            <Card className="bg-destructive/10 border-destructive/20">
              <CardHeader>
                <CardTitle className="text-xs font-mono font-bold uppercase text-destructive flex items-center gap-2">
                  <XCircle className="w-4 h-4" /> Last Revision Request
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm font-mono text-destructive-foreground">
                {playbook.reviewer_feedback}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column: Playbook details, Markdown output & triage actions */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-card/40 border-border/50 min-h-[500px] flex flex-col">
            <CardHeader className="border-b border-border/40 flex flex-row items-center justify-between">
              <CardTitle className="text-xs font-mono font-bold uppercase text-primary flex items-center gap-2">
                <ScrollText className="w-4 h-4" /> Response Playbook Draft
              </CardTitle>
              {playbook.generation_duration_ms && (
                <span className="text-[10px] font-mono bg-muted/50 px-2 py-0.5 rounded border border-border/40">
                  AGENT_SPEED: {(playbook.generation_duration_ms / 1000).toFixed(2)}s
                </span>
              )}
            </CardHeader>
            <CardContent className="flex-1 p-6 overflow-y-auto">
              {playbook.review_status === "generating" ? (
                <div className="flex flex-col items-center justify-center h-64 space-y-3">
                  <Loader2 className="w-8 h-8 text-primary animate-spin" />
                  <span className="text-primary font-mono text-sm uppercase animate-pulse">Regenerating playbook draft...</span>
                </div>
              ) : (
                <MarkdownRenderer content={playbook.generated_playbook || ""} />
              )}
            </CardContent>
            
            {/* Triage actions bar */}
            {playbook.review_status !== "generating" && playbook.review_status !== "approved" && (
              <div className="p-4 border-t border-border/40 bg-muted/10 flex flex-col space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-48">
                    <Label className="text-[10px] uppercase font-mono text-muted-foreground">Sign-off Analyst ID</Label>
                    <Input value={analystId} onChange={(e) => setAnalystId(e.target.value)} className="font-mono text-xs h-8 bg-background border-border" />
                  </div>
                  <div className="flex-1 flex gap-2 justify-end pt-4">
                    <Button 
                      variant="outline" 
                      onClick={() => setShowRejectForm(!showRejectForm)}
                      className="border-destructive/30 hover:bg-destructive/10 text-destructive text-xs uppercase font-mono"
                    >
                      <XCircle className="w-4 h-4 mr-2" /> Request Revisions
                    </Button>
                    <Button 
                      onClick={handleApprove}
                      disabled={isMutating}
                      className="bg-green-600 hover:bg-green-700 text-white text-xs uppercase font-mono"
                    >
                      {approvePlaybook.isPending ? (
                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> SIGNING...</>
                      ) : (
                        <><CheckCircle2 className="w-4 h-4 mr-2" /> Approve & Sign-off</>
                      )}
                    </Button>
                  </div>
                </div>

                {showRejectForm && (
                  <div className="p-4 rounded border border-destructive/20 bg-destructive/5 space-y-3">
                    <Label className="text-xs font-mono text-destructive uppercase">Revision Guidelines (Analyst Feedback)</Label>
                    <Textarea 
                      placeholder="Specify sections to revise, extra containment steps, or tools that should be mentioned..." 
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      className="min-h-[80px] bg-background border-border font-mono text-xs"
                    />
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => setShowRejectForm(false)} className="text-xs uppercase font-mono">Cancel</Button>
                      <Button size="sm" onClick={handleReject} disabled={isMutating} className="bg-destructive text-white hover:bg-destructive/95 text-xs uppercase font-mono">
                        {isMutating ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : <Cpu className="w-3.5 h-3.5 mr-2" />} Submit & Auto-Regenerate
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
