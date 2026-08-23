"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FileBarChart, Plus, RefreshCw, Download, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";

const REPORT_TYPES = [
  { id: "workspace_summary", label: "Workspace Summary", desc: "Overview of documents, queries, and activity" },
  { id: "knowledge_gaps", label: "Knowledge Gaps", desc: "Topics with low coverage or high query failure rate" },
  { id: "usage_trends", label: "Usage Trends", desc: "User activity and AI usage patterns" },
];

export default function ReportsPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const qc = useQueryClient();
  const [selectedReport, setSelectedReport] = useState<{ id: string; title: string; content?: string } | null>(null);

  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports", workspaceId],
    queryFn: () => api.get(`/workspaces/${workspaceId}/reports`).then((r) => r.data),
    refetchInterval: 5000,
  });

  const generateMutation = useMutation({
    mutationFn: (type: string) =>
      api.post(`/workspaces/${workspaceId}/reports/generate`, { type }),
    onSuccess: () => {
      toast.success("Report generation started. This may take a moment.");
      qc.invalidateQueries({ queryKey: ["reports", workspaceId] });
    },
    onError: () => toast.error("Failed to generate report"),
  });

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-white/40 text-sm mt-0.5">AI-generated executive summaries and insights</p>
      </div>

      {/* Generate buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
        {REPORT_TYPES.map((rt) => (
          <button
            key={rt.id}
            onClick={() => generateMutation.mutate(rt.id)}
            disabled={generateMutation.isPending}
            className="text-left p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:border-atlas-500/30 hover:bg-atlas-500/5 transition-all group"
          >
            <div className="flex items-center justify-between mb-2">
              <FileBarChart className="w-5 h-5 text-atlas-400 group-hover:text-atlas-300" />
              {generateMutation.isPending && generateMutation.variables === rt.id && (
                <RefreshCw className="w-3.5 h-3.5 text-white/30 animate-spin" />
              )}
            </div>
            <p className="text-sm font-medium text-white/80 group-hover:text-white">{rt.label}</p>
            <p className="text-xs text-white/30 mt-1">{rt.desc}</p>
          </button>
        ))}
      </div>

      {/* Reports list + viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="space-y-2">
          <h3 className="text-xs text-white/30 font-medium uppercase tracking-wider mb-3">Generated Reports</h3>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 rounded-lg bg-white/[0.02] border border-white/5 animate-pulse" />
              ))}
            </div>
          ) : reports?.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xs text-white/25">No reports yet. Generate one above.</p>
            </div>
          ) : (
            reports?.map((r: { id: string; title: string; report_type: string; content?: string; created_at: string }) => (
              <button
                key={r.id}
                onClick={() => setSelectedReport(r)}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  selectedReport?.id === r.id
                    ? "border-atlas-500/30 bg-atlas-500/10"
                    : "border-white/5 bg-white/[0.02] hover:border-white/10"
                }`}
              >
                <p className="text-xs font-medium text-white/70 truncate">{r.title}</p>
                <p className="text-xs text-white/30 mt-0.5 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatRelativeTime(r.created_at)}
                </p>
              </button>
            ))
          )}
        </div>

        {/* Viewer */}
        <div className="lg:col-span-2">
          {selectedReport ? (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-white">{selectedReport.title}</h2>
              </div>
              {selectedReport.content ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedReport.content}</ReactMarkdown>
                </div>
              ) : (
                <div className="flex items-center gap-3 text-white/40 py-8">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Generating report with AI...</span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full min-h-[300px] rounded-xl border border-white/5 bg-white/[0.01]">
              <FileBarChart className="w-10 h-10 text-white/10 mb-3" />
              <p className="text-white/25 text-sm">Select a report to view</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
