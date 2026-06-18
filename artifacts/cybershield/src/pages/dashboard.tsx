import { useGetDashboardMetrics } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, ShieldAlert, CheckCircle, Clock, AlertTriangle, XCircle, Cpu, Network, Database, Zap, Eye, RotateCcw } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function Dashboard() {
  const { data: metrics, isLoading, error } = useGetDashboardMetrics();

  if (isLoading) {
    return <div className="p-8 flex items-center justify-center h-full text-primary font-mono animate-pulse">Initializing telemetry...</div>;
  }

  if (error) {
    return <div className="p-8 text-destructive font-mono flex items-center gap-2"><AlertTriangle /> Error retrieving telemetry.</div>;
  }

  const statCards = [
    { title: "Total Incidents", value: metrics?.total_incidents ?? 0, icon: ShieldAlert, color: "text-primary" },
    { title: "Pending Review", value: metrics?.pending_review ?? 0, icon: Activity, color: "text-yellow-400" },
    { title: "Approved", value: metrics?.approved_playbooks ?? 0, icon: CheckCircle, color: "text-green-500" },
    { title: "Rejected", value: metrics?.rejected_playbooks ?? 0, icon: XCircle, color: "text-red-500" },
    { title: "Avg Generation", value: `${((metrics?.avg_generation_time_ms ?? 0) / 1000).toFixed(2)}s`, icon: Clock, color: "text-cyan-400" },
  ];

  const agentStats = [
    { label: "Classifier", value: metrics?.agent_stats?.classifier_runs ?? 0, icon: Network },
    { label: "Mapper", value: metrics?.agent_stats?.mapper_runs ?? 0, icon: Database },
    { label: "RAG Engine", value: metrics?.agent_stats?.rag_runs ?? 0, icon: Cpu },
    { label: "Generator", value: metrics?.agent_stats?.generator_runs ?? 0, icon: Zap },
    { label: "Reviewer", value: metrics?.agent_stats?.reviewer_runs ?? 0, icon: Eye },
    { label: "Regenerator", value: metrics?.agent_stats?.regenerator_runs ?? 0, icon: RotateCcw },
  ];

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-mono font-bold text-primary tracking-tight uppercase border-b-2 border-primary/30 pb-2 inline-block">Mission Control</h1>
        <div className="flex items-center gap-2 text-xs font-mono bg-card px-3 py-1 rounded border border-border">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-muted-foreground">SYSTEM_STATUS: NOMINAL</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statCards.map((stat, i) => (
          <Card key={i} className="bg-card/50 border-border/50 shadow-none backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-mono font-bold text-foreground">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="col-span-2 bg-card/50 border-border/50">
          <CardHeader>
            <CardTitle className="text-sm font-mono font-bold text-primary uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4" /> Recent Incident Telemetry
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {metrics?.recent_incidents?.length ? (
                metrics.recent_incidents.map((incident: any) => (
                  <div key={incident?.incident_id ?? Math.random().toString()} className="flex items-center justify-between p-3 rounded bg-muted/30 border border-border/40 hover:bg-muted/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        incident?.priority === 'critical' ? 'bg-red-500' :
                        incident?.priority === 'high' ? 'bg-orange-500' :
                        incident?.priority === 'medium' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`} />
                      <div>
                        <div className="font-mono text-xs text-muted-foreground mb-1">
                          {incident?.incident_id ? incident.incident_id.split('-')[0] : "unknown"}
                        </div>
                        <div className="text-sm font-medium text-foreground truncate max-w-md">
                          {incident?.description ?? "No description provided"}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <div className="text-xs font-mono text-muted-foreground">
                        {incident?.created_at ? formatDistanceToNow(new Date(incident.created_at), { addSuffix: true }) : "Unknown time"}
                      </div>
                      <div className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-sm border ${
                        incident?.status === 'approved' ? 'text-green-500 border-green-500/20 bg-green-500/10' :
                        incident?.status === 'rejected' ? 'text-red-500 border-red-500/20 bg-red-500/10' :
                        'text-yellow-400 border-yellow-400/20 bg-yellow-400/10'
                      }`}>
                        {incident?.status ?? "submitted"}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm font-mono text-muted-foreground text-center py-8">NO_RECENT_TELEMETRY</div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader>
            <CardTitle className="text-sm font-mono font-bold text-primary uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4" /> Agent Operations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {agentStats.map((agent, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <agent.icon className="w-4 h-4" />
                    {agent.label}
                  </div>
                  <div className="font-mono text-sm font-medium text-foreground bg-muted/50 px-2 py-0.5 rounded border border-border/50">
                    {agent.value}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
