"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import { toast } from "sonner";
import { Brain, Plus, FileText, Users, HardDrive, ChevronRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { workspaceApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";
import { useWorkspaceStore } from "@/store/workspace.store";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const TIER_COLORS: Record<string, string> = {
  free: "outline",
  pro: "info",
  enterprise: "atlas",
};

const TIER_GRADIENTS: Record<string, string> = {
  free: "from-slate-500 to-slate-600",
  pro: "from-blue-500 to-purple-500",
  enterprise: "from-atlas-500 to-purple-600",
};

export default function WorkspaceSelectorPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { setWorkspaces, setActiveWorkspace } = useWorkspaceStore();

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data, isLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => workspaceApi.list().then((r) => r.data),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (data) setWorkspaces(data);
  }, [data, setWorkspaces]);

  const handleSelectWorkspace = (workspace: (typeof data)[0]) => {
    setActiveWorkspace(workspace);
    router.push(`/workspace/${workspace.id}/dashboard`);
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Header */}
      <div className="border-b border-white/5 px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold">Atlas AI</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/40">{user?.full_name}</span>
          <button
            onClick={() => {
              useAuthStore.getState().logout();
              router.push("/login");
            }}
            className="text-sm text-white/30 hover:text-white/60 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-2">Your Workspaces</h1>
          <p className="text-white/40 mb-10">Select a workspace to enter your knowledge hub</p>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-40 rounded-xl bg-white/[0.02] border border-white/5 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data?.map((ws: {
                id: string;
                name: string;
                tier: string;
                description?: string;
                document_count?: number;
                member_count?: number;
                storage_used_bytes: number;
                created_at: string;
              }, i: number) => (
                <motion.div
                  key={ws.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <button
                    onClick={() => handleSelectWorkspace(ws)}
                    className="w-full text-left glass-card rounded-xl p-5 hover:border-atlas-500/30 transition-all group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${TIER_GRADIENTS[ws.tier] || "from-slate-500 to-slate-600"} flex items-center justify-center flex-shrink-0`}>
                        <FileText className="w-5 h-5 text-white/90" />
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={TIER_COLORS[ws.tier] as "outline" | "info" | "atlas"}>
                          {ws.tier}
                        </Badge>
                        <ChevronRight className="w-4 h-4 text-white/20 group-hover:text-white/60 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </div>

                    <h3 className="font-semibold text-white mb-1">{ws.name}</h3>
                    {ws.description && (
                      <p className="text-xs text-white/30 mb-4 line-clamp-2">{ws.description}</p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-white/30">
                      <span className="flex items-center gap-1.5">
                        <FileText className="w-3 h-3" />
                        {ws.document_count ?? 0} docs
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Users className="w-3 h-3" />
                        {ws.member_count ?? 1} members
                      </span>
                      <span className="flex items-center gap-1.5">
                        <HardDrive className="w-3 h-3" />
                        {formatBytes(ws.storage_used_bytes)}
                      </span>
                    </div>
                  </button>
                </motion.div>
              ))}

              {/* Create new workspace */}
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: (data?.length || 0) * 0.05 }}
              >
                <Link
                  href="/workspaces/new"
                  className="flex flex-col items-center justify-center h-full min-h-[140px] glass-card rounded-xl border-dashed hover:border-atlas-500/40 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-full bg-white/[0.03] flex items-center justify-center mb-3 group-hover:bg-atlas-500/10 transition-colors">
                    <Plus className="w-5 h-5 text-white/30 group-hover:text-atlas-400 transition-colors" />
                  </div>
                  <span className="text-sm text-white/30 group-hover:text-white/60 transition-colors">New workspace</span>
                </Link>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
