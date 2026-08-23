"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import {
  FileText, MessageSquare, HardDrive, GitBranch,
  TrendingUp, ArrowUpRight, Zap, Search
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { analyticsApi, workspaceApi } from "@/lib/api";
import { formatBytes, formatRelativeTime, getFileTypeIcon } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspace.store";

const MOCK_ACTIVITY = [
  { day: "Mon", queries: 12, uploads: 3 },
  { day: "Tue", queries: 19, uploads: 1 },
  { day: "Wed", queries: 8, uploads: 5 },
  { day: "Thu", queries: 24, uploads: 2 },
  { day: "Fri", queries: 31, uploads: 4 },
  { day: "Sat", queries: 7, uploads: 0 },
  { day: "Sun", queries: 15, uploads: 1 },
];

export default function DashboardPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const { activeWorkspace } = useWorkspaceStore();

  const { data: overview } = useQuery({
    queryKey: ["analytics-overview", workspaceId],
    queryFn: () => analyticsApi.overview(workspaceId).then((r) => r.data),
  });

  const { data: documents } = useQuery({
    queryKey: ["documents", workspaceId, { limit: 5 }],
    queryFn: () =>
      import("@/lib/api").then((m) =>
        m.documentApi.list(workspaceId, { limit: 5 }).then((r) => r.data)
      ),
  });

  const { data: chatSessions } = useQuery({
    queryKey: ["chat-sessions", workspaceId],
    queryFn: () =>
      import("@/lib/api").then((m) =>
        m.chatApi.listSessions(workspaceId).then((r) => r.data)
      ),
  });

  const storagePercent = activeWorkspace
    ? Math.round((activeWorkspace.storage_used_bytes / activeWorkspace.storage_quota_bytes) * 100)
    : 0;

  const STATS = [
    {
      title: "Documents Indexed",
      value: overview?.documents_indexed ?? 0,
      total: overview?.documents_total ?? 0,
      icon: FileText,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      link: "documents",
    },
    {
      title: "AI Queries (30d)",
      value: overview?.queries_30d ?? 0,
      icon: MessageSquare,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      link: "chat",
    },
    {
      title: "Chat Sessions (30d)",
      value: overview?.chat_sessions_30d ?? 0,
      icon: Zap,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      link: "chat",
    },
    {
      title: "Storage Used",
      value: formatBytes(activeWorkspace?.storage_used_bytes ?? 0),
      icon: HardDrive,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      extra: `${storagePercent}% of ${formatBytes(activeWorkspace?.storage_quota_bytes ?? 0)}`,
      link: "settings",
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-white/40 mt-0.5">{activeWorkspace?.name} · Knowledge overview</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={`/workspace/${workspaceId}/search`}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.04] border border-white/8 text-sm text-white/60 hover:text-white hover:bg-white/[0.07] transition-all"
          >
            <Search className="w-4 h-4" />
            Search knowledge base
            <kbd className="text-xs bg-white/5 rounded px-1.5 py-0.5 border border-white/10">⌘K</kbd>
          </Link>
          <Link
            href={`/workspace/${workspaceId}/chat`}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-atlas-500 to-purple-500 text-white text-sm font-medium hover:brightness-110 transition-all shadow-lg shadow-atlas-500/20"
          >
            <MessageSquare className="w-4 h-4" />
            New chat
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map((stat) => (
          <Link key={stat.title} href={`/workspace/${workspaceId}/${stat.link}`}>
            <Card className="bg-white/[0.02] border-white/5 hover:border-white/10 transition-colors group cursor-pointer">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center`}>
                    <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-white/20 group-hover:text-white/50 transition-colors" />
                </div>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-white/40 mt-0.5">{stat.title}</p>
                {stat.extra && <p className="text-xs text-white/25 mt-1">{stat.extra}</p>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Charts + Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Activity chart */}
        <Card className="lg:col-span-2 bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-white/70">
              Activity — Last 7 days
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={MOCK_ACTIVITY}>
                <defs>
                  <linearGradient id="queriesGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fill: "#ffffff30", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#ffffff30", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#0d0d14", border: "1px solid #ffffff10", borderRadius: "8px", fontSize: 12 }}
                  labelStyle={{ color: "#ffffff80" }}
                />
                <Area type="monotone" dataKey="queries" stroke="#6366f1" strokeWidth={2} fill="url(#queriesGrad)" name="Queries" />
                <Area type="monotone" dataKey="uploads" stroke="#8b5cf6" strokeWidth={1.5} fill="none" strokeDasharray="4 2" name="Uploads" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent chats */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-white/70">Recent Chats</CardTitle>
              <Link href={`/workspace/${workspaceId}/chat`} className="text-xs text-atlas-400 hover:text-atlas-300">
                View all
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {chatSessions?.slice(0, 5).map((s: { id: string; title?: string; mode: string; updated_at: string }) => (
              <Link
                key={s.id}
                href={`/workspace/${workspaceId}/chat/${s.id}`}
                className="flex items-start gap-2.5 p-2 rounded-lg hover:bg-white/[0.04] transition-colors group"
              >
                <MessageSquare className="w-3.5 h-3.5 text-white/30 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white/60 truncate group-hover:text-white/80 transition-colors">
                    {s.title || "New conversation"}
                  </p>
                  <p className="text-xs text-white/25 mt-0.5">{formatRelativeTime(s.updated_at)}</p>
                </div>
              </Link>
            ))}
            {!chatSessions?.length && (
              <p className="text-xs text-white/25 text-center py-4">No chats yet. Start one!</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent documents */}
      <Card className="bg-white/[0.02] border-white/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-white/70">Recent Documents</CardTitle>
            <Link href={`/workspace/${workspaceId}/documents`} className="text-xs text-atlas-400 hover:text-atlas-300">
              View all
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {documents?.slice(0, 6).map((doc: {
              id: string; title: string; file_type: string;
              processing_status: string; chunk_count: number; created_at: string
            }) => (
              <div key={doc.id} className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/[0.03] transition-colors">
                <span className="text-base">{getFileTypeIcon(doc.file_type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/70 truncate">{doc.title}</p>
                </div>
                <Badge variant={doc.processing_status === "completed" ? "success" : doc.processing_status === "processing" ? "info" : "warning"} className="text-xs">
                  {doc.processing_status}
                </Badge>
                <span className="text-xs text-white/25">{formatRelativeTime(doc.created_at)}</span>
              </div>
            ))}
            {!documents?.length && (
              <p className="text-sm text-white/25 text-center py-6">No documents yet. Upload your first document.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
