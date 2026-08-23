"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { GitBranch, Plus, RefreshCw, Trash2, ExternalLink, CheckCircle, Clock, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { githubApi } from "@/lib/api";
import { cn, formatRelativeTime } from "@/lib/utils";

const SYNC_STATUS_CONFIG = {
  synced: { color: "text-emerald-400", badge: "success" as const, label: "Synced" },
  syncing: { color: "text-blue-400", badge: "info" as const, label: "Syncing" },
  pending: { color: "text-amber-400", badge: "warning" as const, label: "Pending" },
  failed: { color: "text-red-400", badge: "destructive" as const, label: "Failed" },
};

export default function RepositoriesPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [repoInput, setRepoInput] = useState("");
  const [tokenInput, setTokenInput] = useState("");

  const { data: repos, isLoading } = useQuery({
    queryKey: ["repos", workspaceId],
    queryFn: () => githubApi.listRepos(workspaceId).then((r) => r.data),
    refetchInterval: (data) => {
      const hasSyncing = Array.isArray(data) && data.some(
        (r: { sync_status: string }) => r.sync_status === "syncing" || r.sync_status === "pending"
      );
      return hasSyncing ? 4000 : false;
    },
  });

  const connectMutation = useMutation({
    mutationFn: () => githubApi.connectRepo(workspaceId, { full_name: repoInput, access_token: tokenInput }),
    onSuccess: () => {
      toast.success("Repository connected and indexing started");
      setShowAdd(false);
      setRepoInput("");
      setTokenInput("");
      qc.invalidateQueries({ queryKey: ["repos", workspaceId] });
    },
    onError: () => toast.error("Failed to connect repository"),
  });

  const syncMutation = useMutation({
    mutationFn: (repoId: string) => githubApi.syncRepo(workspaceId, repoId),
    onSuccess: () => {
      toast.success("Re-sync started");
      qc.invalidateQueries({ queryKey: ["repos", workspaceId] });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (repoId: string) => githubApi.disconnectRepo(workspaceId, repoId),
    onSuccess: () => {
      toast.success("Repository disconnected");
      qc.invalidateQueries({ queryKey: ["repos", workspaceId] });
    },
  });

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Repositories</h1>
          <p className="text-white/40 text-sm mt-0.5">Index GitHub repositories into your knowledge base</p>
        </div>
        <Button
          onClick={() => setShowAdd(!showAdd)}
          variant="atlas"
          size="sm"
          className="gap-2"
        >
          <Plus className="w-4 h-4" /> Connect repo
        </Button>
      </div>

      {/* Add repo form */}
      {showAdd && (
        <div className="rounded-xl border border-atlas-500/20 bg-atlas-500/5 p-5 mb-6 space-y-3">
          <h3 className="text-sm font-medium text-white/80">Connect GitHub Repository</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1.5">Repository (owner/repo)</label>
              <Input
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="e.g. microsoft/vscode"
                className="h-9 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1.5">GitHub Token (for private repos)</label>
              <Input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="ghp_xxxx (optional for public)"
                className="h-9 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <Button
              onClick={() => connectMutation.mutate()}
              disabled={!repoInput.includes("/") || connectMutation.isPending}
              variant="atlas"
              size="sm"
              isLoading={connectMutation.isPending}
            >
              Connect & Index
            </Button>
            <Button onClick={() => setShowAdd(false)} variant="ghost" size="sm" className="text-white/40">
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Repos list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-white/[0.02] border border-white/5 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {repos?.map((repo: {
            id: string; full_name: string; description?: string; language?: string;
            sync_status: string; last_synced_at?: string; html_url?: string;
            index_readme: boolean; index_docs: boolean; index_code: boolean;
          }) => {
            const status = SYNC_STATUS_CONFIG[repo.sync_status as keyof typeof SYNC_STATUS_CONFIG] || SYNC_STATUS_CONFIG.pending;
            return (
              <div key={repo.id} className="rounded-xl border border-white/5 bg-white/[0.02] p-5 hover:border-white/10 transition-colors group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                      <GitBranch className="w-4 h-4 text-white/60" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-sm">{repo.full_name}</h3>
                        {repo.html_url && (
                          <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="w-3.5 h-3.5 text-white/25 hover:text-white/60" />
                          </a>
                        )}
                      </div>
                      {repo.description && (
                        <p className="text-xs text-white/40 mt-0.5 max-w-sm truncate">{repo.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={status.badge}>{status.label}</Badge>
                    <button
                      onClick={() => syncMutation.mutate(repo.id)}
                      disabled={syncMutation.isPending}
                      className="p-1.5 rounded hover:bg-white/[0.06] text-white/25 hover:text-white/60 transition-colors"
                      title="Re-sync"
                    >
                      <RefreshCw className={cn("w-3.5 h-3.5", repo.sync_status === "syncing" && "animate-spin")} />
                    </button>
                    <button
                      onClick={() => disconnectMutation.mutate(repo.id)}
                      className="p-1.5 rounded hover:bg-red-500/10 text-white/25 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                      title="Disconnect"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-white/25">
                  {repo.language && <span>{repo.language}</span>}
                  {repo.last_synced_at && <span>Synced {formatRelativeTime(repo.last_synced_at)}</span>}
                  <span className="flex items-center gap-2">
                    {repo.index_readme && <span className="bg-white/5 rounded px-1.5 py-0.5">README</span>}
                    {repo.index_docs && <span className="bg-white/5 rounded px-1.5 py-0.5">Docs</span>}
                    {repo.index_code && <span className="bg-white/5 rounded px-1.5 py-0.5">Code</span>}
                  </span>
                </div>
              </div>
            );
          })}

          {repos?.length === 0 && (
            <div className="py-16 text-center">
              <GitBranch className="w-10 h-10 text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm">No repositories connected</p>
              <p className="text-white/20 text-xs mt-1">Connect a GitHub repo to index its README, docs, and source code</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
