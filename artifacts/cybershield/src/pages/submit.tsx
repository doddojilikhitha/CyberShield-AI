import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useLocation } from "wouter";
import { useCreateIncident, useGeneratePlaybook } from "@workspace/api-client-react";
import { useToast } from "@/hooks/use-toast";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ShieldAlert, AlertTriangle, AlertCircle, Info, Loader2, Zap } from "lucide-react";
import { CreateIncidentRequestPriority } from "@workspace/api-zod";

const formSchema = z.object({
  incident_description: z.string().min(10, "Description must be at least 10 characters"),
  analyst_name: z.string().min(2, "Analyst name required"),
  incident_source: z.string().optional(),
  priority: z.enum(["low", "medium", "high", "critical"] as const).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function Submit() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const createIncident = useCreateIncident();
  const generatePlaybook = useGeneratePlaybook();
  
  const [generationStep, setGenerationStep] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      incident_description: "",
      analyst_name: "",
      incident_source: "manual",
      priority: "medium",
    },
  });

  const onSubmit = (data: FormValues) => {
    createIncident.mutate(
      { data: {
        incident_description: data.incident_description,
        analyst_name: data.analyst_name,
        incident_source: data.incident_source,
        priority: data.priority as CreateIncidentRequestPriority
      } },
      {
        onSuccess: (res: any) => {
          toast({ title: "Incident logged", description: `ID: ${res.incident_id}`, variant: "default" });
          
          setGenerationStep("Classifying Threat Vector...");
          
          generatePlaybook.mutate(
            { data: { incident_id: res.incident_id } },
            {
              onSuccess: () => {
                setLocation(`/review/${res.incident_id}`);
              },
              onError: (err: any) => {
                toast({ title: "Generation Failed", description: err.detail || "Unknown error", variant: "destructive" });
                setGenerationStep(null);
                setLocation(`/review/${res.incident_id}`);
              }
            }
          );

          // Fake progress updates for UI feel
          setTimeout(() => setGenerationStep("Mapping Frameworks (NIST/MITRE)..."), 2000);
          setTimeout(() => setGenerationStep("Retrieving Context (RAG)..."), 4000);
          setTimeout(() => setGenerationStep("Generating Playbook..."), 6000);
          setTimeout(() => setGenerationStep("Compliance Review..."), 8000);
        },
        onError: (err: any) => {
          toast({ title: "Submission Failed", description: err.detail || "Unknown error", variant: "destructive" });
        }
      }
    );
  };

  const isGenerating = generatePlaybook.isPending;

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto h-full flex flex-col">
      <div className="mb-8">
        <h1 className="text-2xl font-mono font-bold text-primary uppercase tracking-wider mb-2 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6" /> Incident Intake
        </h1>
        <p className="text-muted-foreground text-sm border-l-2 border-primary/30 pl-3">
          Log a new security event to initiate automated playbook generation.
        </p>
      </div>

      {isGenerating ? (
        <div className="flex-1 flex flex-col items-center justify-center space-y-6">
          <div className="relative flex items-center justify-center w-32 h-32">
            <div className="absolute inset-0 border-t-2 border-primary rounded-full animate-spin"></div>
            <div className="absolute inset-2 border-r-2 border-cyan-400 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
            <div className="absolute inset-4 border-b-2 border-accent rounded-full animate-spin" style={{ animationDuration: '3s' }}></div>
            <Zap className="w-8 h-8 text-primary animate-pulse" />
          </div>
          <div className="text-center space-y-2">
            <h3 className="text-xl font-mono font-bold text-foreground">Awaiting Agent Pipeline</h3>
            <p className="text-primary font-mono text-sm tracking-widest uppercase animate-pulse">{generationStep || "Initializing..."}</p>
          </div>
          <div className="w-full max-w-md bg-muted/30 h-1.5 rounded-full overflow-hidden">
            <div className="h-full bg-primary animate-pulse w-full"></div>
          </div>
        </div>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 bg-card/40 p-6 rounded-lg border border-border/50 shadow-sm backdrop-blur">
            <FormField
              control={form.control}
              name="incident_description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-mono text-xs uppercase text-muted-foreground tracking-wider">Event Telemetry / Description <span className="text-destructive">*</span></FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Paste raw logs, SIEM alerts, or describe the anomalous behavior..." 
                      className="min-h-[160px] font-mono text-sm bg-background border-border focus-visible:ring-primary focus-visible:border-primary"
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage className="text-xs font-mono text-destructive" />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FormField
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono text-xs uppercase text-muted-foreground tracking-wider">Severity Level</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-background border-border font-mono text-sm">
                          <SelectValue placeholder="Select priority" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="low"><span className="flex items-center gap-2 text-blue-400"><Info className="w-3 h-3" /> LOW</span></SelectItem>
                        <SelectItem value="medium"><span className="flex items-center gap-2 text-yellow-400"><AlertCircle className="w-3 h-3" /> MEDIUM</span></SelectItem>
                        <SelectItem value="high"><span className="flex items-center gap-2 text-orange-500"><AlertTriangle className="w-3 h-3" /> HIGH</span></SelectItem>
                        <SelectItem value="critical"><span className="flex items-center gap-2 text-red-500"><ShieldAlert className="w-3 h-3" /> CRITICAL</span></SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage className="text-xs font-mono text-destructive" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="analyst_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono text-xs uppercase text-muted-foreground tracking-wider">Reporting Analyst <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. jdoe" className="bg-background border-border font-mono text-sm" {...field} />
                    </FormControl>
                    <FormMessage className="text-xs font-mono text-destructive" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="incident_source"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono text-xs uppercase text-muted-foreground tracking-wider">Detection Source</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. CrowdStrike, Splunk" className="bg-background border-border font-mono text-sm" {...field} />
                    </FormControl>
                    <FormMessage className="text-xs font-mono text-destructive" />
                  </FormItem>
                )}
              />
            </div>

            <div className="pt-4 border-t border-border flex justify-end">
              <Button 
                type="submit" 
                disabled={createIncident.isPending}
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-mono uppercase tracking-widest font-bold px-8"
              >
                {createIncident.isPending ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> ENGAGING...</>
                ) : (
                  <><Zap className="w-4 h-4 mr-2" /> ENGAGE SYSTEM</>
                )}
              </Button>
            </div>
          </form>
        </Form>
      )}
    </div>
  );
}
