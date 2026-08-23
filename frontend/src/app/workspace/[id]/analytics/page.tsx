"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsApi } from "@/lib/api";
import { formatBytes } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspace.store";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

const MOCK_DOC_TYPES = [
  { name: "PDF", value: 35, color: "#ef4444" },
  { name: "Markdown", value: 28, color: "#6366f1" },
  { name: "DOCX", value: 18, color: "#3b82f6" },
  { name: "PPTX", value: 10, color: "#f59e0b" },
  { name: "Other", value: 9, color: "#6b7280" },
];

const MOCK_QUERIES = [
  { day: "Mon", queries: 14 }, { day: "Tue", queries: 22 }, { day: "Wed", queries: 9 },
  { day: "Thu", queries: 31 }, { day: "Fri", queries: 28 }, { day: "Sat", queries: 8 }, { day: "Sun", queries: 16 },
];

const MOCK_TOP_DOCS = [
  { title: "Backend Architecture Guide", queries: 47 },
  { title: "Employee Handbook", queries: 38 },
  { title: "API Documentation v2.1", queries: 31 },
  { title: "Authentication Guide", queries: 24 },
  { title: "CI/CD Pipeline Documentation", queries: 19 },
];

export default function AnalyticsPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const { activeWorkspace } = useWorkspaceStore();

  const { data: overview } = useQuery({
    queryKey: ["analytics-overview", workspaceId],
    queryFn: () => analyticsApi.overview(workspaceId).then((r) => r.data),
  });

  const { data: chatAnalytics } = useQuery({
    queryKey: ["analytics-chat", workspaceId],
    queryFn: () => analyticsApi.chat(workspaceId, 30).then((r) => r.data),
  });

  const storagePercent = activeWorkspace
    ? Math.round((activeWorkspace.storage_used_bytes / activeWorkspace.storage_quota_bytes) * 100)
    : 0;

  return (
    <div className="p-6 max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-white/40 text-sm mt-0.5">Workspace usage and knowledge base insights</p>
      </div>

      {/* Top metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Documents Total", value: overview?.documents_total ?? "—" },
          { label: "Documents Indexed", value: overview?.documents_indexed ?? "—" },
          { label: "AI Queries (30d)", value: overview?.queries_30d ?? "—" },
          { label: "Chat Sessions (30d)", value: overview?.chat_sessions_30d ?? "—" },
        ].map((m) => (
          <Card key={m.label} className="bg-white/[0.02] border-white/5">
            <CardContent className="p-5">
              <p className="text-2xl font-bold text-white">{m.value}</p>
              <p className="text-xs text-white/40 mt-0.5">{m.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Queries over time */}
        <Card className="lg:col-span-2 bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/60">AI Queries — Last 7 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chatAnalytics?.messages_by_day?.length ? chatAnalytics.messages_by_day : MOCK_QUERIES}>
                <defs>
                  <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fill: "#ffffff30", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#ffffff30", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#0d0d14", border: "1px solid #ffffff10", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="queries" stroke="#6366f1" strokeWidth={2} fill="url(#queryGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Document type breakdown */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/60">Document Types</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={MOCK_DOC_TYPES} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                  {MOCK_DOC_TYPES.map((entry, i) => (
                    <Cell key={i} fill={entry.color} opacity={0.85} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0d0d14", border: "1px solid #ffffff10", borderRadius: "8px" }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-x-4 gap-y-1 justify-center mt-2">
              {MOCK_DOC_TYPES.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-xs text-white/40">
                  <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                  {d.name}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Most queried docs */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/60">Most Referenced Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={MOCK_TOP_DOCS} layout="vertical">
                <XAxis type="number" tick={{ fill: "#ffffff30", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="title" type="category" tick={{ fill: "#ffffff50", fontSize: 10 }} width={160} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#0d0d14", border: "1px solid #ffffff10", borderRadius: "8px" }} />
                <Bar dataKey="queries" fill="#6366f1" radius={[0, 4, 4, 0]} opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Storage */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/60">Storage Usage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-xs text-white/40 mb-1.5">
                <span>{formatBytes(activeWorkspace?.storage_used_bytes ?? 0)} used</span>
                <span>{formatBytes(activeWorkspace?.storage_quota_bytes ?? 0)} total</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-atlas-500 to-purple-500 transition-all"
                  style={{ width: `${storagePercent}%` }}
                />
              </div>
              <p className="text-xs text-white/30 mt-1">{storagePercent}% used</p>
            </div>

            <div className="space-y-2 pt-2">
              {MOCK_DOC_TYPES.map((d) => (
                <div key={d.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                    <span className="text-xs text-white/50">{d.name}</span>
                  </div>
                  <span className="text-xs text-white/30">{formatBytes(Math.random() * 50 * 1024 * 1024)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
