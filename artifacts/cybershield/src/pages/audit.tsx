import { useState } from "react";
import { useGetAuditLogs } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  ScrollText, AlertTriangle, Loader2, Search, ArrowRight, ShieldCheck 
} from "lucide-react";
import { format } from "date-fns";
import { Link } from "wouter";

export default function Audit() {
  const { data: logs, isLoading, error } = useGetAuditLogs();
  const [searchTerm, setSearchTerm] = useState("");

  // Log the runtime value of logs before filtering
  console.log("Audit ledger: value of 'logs' is", logs);

  const logList = Array.isArray(logs)
    ? logs
    : Array.isArray((logs as any)?.value)
      ? (logs as any).value
      : Array.isArray((logs as any)?.logs)
        ? (logs as any).logs
        : Array.isArray((logs as any)?.items)
          ? (logs as any).items
          : [];

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="text-primary font-mono text-sm uppercase animate-pulse">Loading compliance ledger...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-destructive font-mono flex items-center gap-2">
        <AlertTriangle /> Error retrieving compliance logs.
      </div>
    );
  }

  const filteredLogs = logList.filter(
    (log: any) =>
      (log?.incident_id ?? "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log?.agent_name ?? "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log?.output_summary && log.output_summary.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-primary tracking-tight uppercase border-b-2 border-primary/30 pb-2 inline-block">
            System Compliance Ledger
          </h1>
          <p className="text-muted-foreground text-xs font-mono mt-2 uppercase">
            Immutable Audit Trail of Agent Chains and Human Operations
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 max-w-md bg-card border border-border/50 rounded px-3 py-1.5 focus-within:border-primary/50 transition-colors">
        <Search className="w-4 h-4 text-muted-foreground" />
        <Input 
          placeholder="Filter by Incident ID, Agent Name, or Output..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="border-none bg-transparent h-7 focus-visible:ring-0 p-0 text-xs font-mono"
        />
      </div>

      <Card className="bg-card/40 border-border/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-sm font-mono font-bold uppercase tracking-wider text-muted-foreground">
            AUDIT RECORDSSTREAM ({filteredLogs.length} LOGS)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredLogs.length === 0 ? (
            <div className="text-center py-12 font-mono text-muted-foreground text-sm border-2 border-dashed border-border/40 rounded">
              NO_AUDIT_LOGS_MATCH_SEARCH_CRITERIA
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border/50 text-[11px] font-mono uppercase text-muted-foreground tracking-widest pb-3">
                    <th className="pb-3 pl-2">Timestamp</th>
                    <th className="pb-3">Incident ID</th>
                    <th className="pb-3">Agent Source</th>
                    <th className="pb-3">Output/Action Summary</th>
                    <th className="pb-3 text-center">Processing</th>
                    <th className="pb-3 text-right">Scope Link</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {filteredLogs.map((log: any) => (
                    <tr key={log?.id ?? Math.random().toString()} className="hover:bg-muted/20 transition-colors text-xs">
                      <td className="py-4 pl-2 font-mono text-muted-foreground">
                        {log?.timestamp ? format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss") : "Unknown time"}
                      </td>
                      <td className="py-4 font-mono text-muted-foreground">
                        {log?.incident_id ? log.incident_id.split("-")[0] : "unknown"}...
                      </td>
                      <td className="py-4">
                        <span className={`font-mono px-2 py-0.5 rounded-sm border ${
                          log?.agent_name === 'human_review' ? 'bg-green-500/10 text-green-500 border-green-500/20 font-bold' :
                          'bg-primary/10 text-primary border-primary/20'
                        }`}>
                          {log?.agent_name ?? "unknown"}
                        </span>
                      </td>
                      <td className="py-4 max-w-sm">
                        <div className="text-foreground truncate font-mono text-xs">
                          {log?.output_summary || "N/A"}
                        </div>
                      </td>
                      <td className="py-4 text-center font-mono text-muted-foreground">
                        {log?.processing_time_ms ? `${log.processing_time_ms}ms` : "0ms"}
                      </td>
                      <td className="py-4 text-right">
                        <Link href={`/review/${log?.incident_id ?? ""}`}>
                          <a className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                            Inspect <ArrowRight className="w-3 h-3" />
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
