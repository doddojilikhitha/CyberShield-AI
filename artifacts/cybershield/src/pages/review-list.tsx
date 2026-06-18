import { useListIncidents } from "@workspace/api-client-react";
import { Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, AlertTriangle, Info, ShieldAlert, ArrowRight, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function ReviewList() {
  const { data: incidents, isLoading, error } = useListIncidents();

  // Log the actual value of incidents before rendering
  console.log("ReviewList telemetry: value of 'incidents' is", incidents);

  const incidentList = Array.isArray(incidents)
    ? incidents
    : Array.isArray((incidents as any)?.value)
      ? (incidents as any).value
      : Array.isArray((incidents as any)?.items)
        ? (incidents as any).items
        : [];

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="text-primary font-mono text-sm uppercase animate-pulse">Loading Incident Records...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-destructive font-mono flex items-center gap-2">
        <AlertTriangle /> Error retrieving incident database.
      </div>
    );
  }

  const getPriorityIcon = (priority?: string) => {
    switch (priority) {
      case "critical":
        return <ShieldAlert className="w-4 h-4 text-red-500" />;
      case "high":
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case "medium":
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-primary tracking-tight uppercase border-b-2 border-primary/30 pb-2 inline-block">
            Playbook Review Hub
          </h1>
          <p className="text-muted-foreground text-xs font-mono mt-2 uppercase">
            Incidents Pending Triage, Containment, & Analyst Approvals
          </p>
        </div>
        <div className="text-xs font-mono bg-card px-3 py-1.5 rounded border border-border">
          TOTAL_RECORDS: {incidentList.length}
        </div>
      </div>

      <Card className="bg-card/40 border-border/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-sm font-mono font-bold uppercase tracking-wider text-muted-foreground">
            ACTIVE ALERTS & INCIDENT STREAM
          </CardTitle>
        </CardHeader>
        <CardContent>
          {incidentList.length === 0 ? (
            <div className="text-center py-12 font-mono text-muted-foreground text-sm border-2 border-dashed border-border/40 rounded">
              NO_INCIDENTS_FOUND - RUN SYSTEM INTAKE TO LOG INCIDENTS
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border/50 text-[11px] font-mono uppercase text-muted-foreground tracking-widest pb-3">
                    <th className="pb-3 pl-2">Priority</th>
                    <th className="pb-3">Incident ID</th>
                    <th className="pb-3">Event Telemetry</th>
                    <th className="pb-3">Analyst</th>
                    <th className="pb-3">Logged</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {incidentList.map((incident: any) => (
                    <tr key={incident?.incident_id ?? Math.random().toString()} className="hover:bg-muted/20 transition-colors">
                      <td className="py-4 pl-2 font-mono text-xs uppercase font-bold">
                        <span className="flex items-center gap-1.5">
                          {getPriorityIcon(incident?.priority)}
                          {incident?.priority ?? "medium"}
                        </span>
                      </td>
                      <td className="py-4 font-mono text-xs text-muted-foreground">
                        {incident?.incident_id ? incident.incident_id.split("-")[0] : "unknown"}...
                      </td>
                      <td className="py-4 max-w-md">
                        <div className="text-sm font-medium text-foreground truncate">
                          {incident?.incident_description ?? "No description provided"}
                        </div>
                      </td>
                      <td className="py-4 font-mono text-xs text-foreground">
                        {incident?.analyst_name ?? "unknown"}
                      </td>
                      <td className="py-4 font-mono text-xs text-muted-foreground">
                        {incident?.created_at ? formatDistanceToNow(new Date(incident.created_at), { addSuffix: true }) : "Unknown time"}
                      </td>
                      <td className="py-4 text-right">
                        <Link href={`/review/${incident?.incident_id ?? ""}`}>
                          <a className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 text-xs font-mono font-bold uppercase transition-all">
                            Triage <ArrowRight className="w-3.5 h-3.5" />
                          </a>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
