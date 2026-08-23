"use client";
import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import {
  Upload, FileText, Trash2, Eye, RefreshCw, FolderOpen,
  Plus, Search, Filter, MoreVertical, CheckCircle, Clock, XCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { documentApi } from "@/lib/api";
import { cn, formatBytes, formatRelativeTime, getFileTypeIcon } from "@/lib/utils";

const STATUS_CONFIG = {
  completed: { icon: CheckCircle, color: "text-emerald-400", badge: "success" as const, label: "Indexed" },
  processing: { icon: RefreshCw, color: "text-blue-400", badge: "info" as const, label: "Processing" },
  pending: { icon: Clock, color: "text-amber-400", badge: "warning" as const, label: "Pending" },
  failed: { icon: XCircle, color: "text-red-400", badge: "destructive" as const, label: "Failed" },
};

export default function DocumentsPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [isUploading, setIsUploading] = useState(false);

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => documentApi.list(workspaceId, { limit: 100 }).then((r) => r.data),
    refetchInterval: (data) => {
      const hasProcessing = Array.isArray(data) && data.some(
        (d: { processing_status: string }) => d.processing_status === "processing" || d.processing_status === "pending"
      );
      return hasProcessing ? 3000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentApi.delete(workspaceId, docId),
    onSuccess: () => {
      toast.success("Document deleted");
      qc.invalidateQueries({ queryKey: ["documents", workspaceId] });
    },
    onError: () => toast.error("Failed to delete document"),
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setIsUploading(true);
      let successCount = 0;
      for (const file of acceptedFiles) {
        try {
          await documentApi.upload(workspaceId, file);
          successCount++;
        } catch (err: unknown) {
          const e = err as { response?: { data?: { detail?: string } } };
          toast.error(`Failed to upload ${file.name}: ${e?.response?.data?.detail || "Unknown error"}`);
        }
      }
      if (successCount > 0) {
        toast.success(`${successCount} file${successCount > 1 ? "s" : ""} uploaded and queued for indexing`);
        qc.invalidateQueries({ queryKey: ["documents", workspaceId] });
      }
      setIsUploading(false);
    },
    [workspaceId, qc]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/markdown": [".md"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: true,
  });

  const filtered = documents?.filter((d: { title: string; file_type: string }) => {
    const matchSearch = d.title.toLowerCase().includes(search.toLowerCase());
    const matchType = typeFilter === "all" || d.file_type === typeFilter;
    return matchSearch && matchType;
  });

  const FILE_TYPES: string[] = ["all", ...Array.from(new Set((documents as any[] || []).map((d: { file_type: string }) => d.file_type as string)))];

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-white/40 text-sm mt-0.5">{documents?.length || 0} documents in knowledge base</p>
        </div>
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-all cursor-pointer",
          isDragActive
            ? "border-atlas-500/60 bg-atlas-500/5"
            : "border-white/10 hover:border-white/20 hover:bg-white/[0.02]"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          {isUploading ? (
            <RefreshCw className="w-8 h-8 text-atlas-400 animate-spin" />
          ) : (
            <Upload className={cn("w-8 h-8", isDragActive ? "text-atlas-400" : "text-white/20")} />
          )}
          <div>
            <p className="text-sm font-medium text-white/60">
              {isDragActive ? "Drop files to upload" : isUploading ? "Uploading..." : "Drag & drop files here"}
            </p>
            <p className="text-xs text-white/25 mt-1">PDF, DOCX, PPTX, XLSX, MD, TXT, CSV — up to 50MB each</p>
          </div>
          {!isDragActive && !isUploading && (
            <Button variant="outline" size="sm" className="border-white/10 text-white/60 hover:text-white mt-1">
              Browse files
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="pl-9 h-8 text-sm bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {FILE_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cn(
                "px-3 py-1 rounded-full text-xs capitalize transition-all",
                typeFilter === t
                  ? "bg-atlas-500/20 text-atlas-300 border border-atlas-500/30"
                  : "text-white/30 hover:text-white/60 border border-white/5"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Document table */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-14 rounded-lg bg-white/[0.02] border border-white/5 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02]">
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Document</th>
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Type</th>
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Chunks</th>
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Size</th>
                <th className="text-left px-4 py-3 text-xs text-white/30 font-medium">Uploaded</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered?.map((doc: {
                id: string; title: string; file_type: string; file_size_bytes: number;
                processing_status: string; chunk_count: number; created_at: string;
              }) => {
                const status = STATUS_CONFIG[doc.processing_status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
                return (
                  <tr key={doc.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">{getFileTypeIcon(doc.file_type)}</span>
                        <span className="text-sm text-white/80 truncate max-w-xs">{doc.title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-white/40 uppercase">{doc.file_type}</span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={status.badge} className="text-xs gap-1">
                        <status.icon className={cn("w-3 h-3", status.color, doc.processing_status === "processing" && "animate-spin")} />
                        {status.label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-white/40">{doc.chunk_count}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-white/40">{formatBytes(doc.file_size_bytes)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-white/30">{formatRelativeTime(doc.created_at)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => deleteMutation.mutate(doc.id)}
                          className="p-1.5 rounded hover:bg-red-500/10 text-white/25 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filtered?.length === 0 && (
            <div className="py-16 text-center">
              <FileText className="w-10 h-10 text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm">No documents found</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
