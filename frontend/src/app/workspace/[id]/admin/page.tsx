"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Shield, Users, Building2, FileText, Activity,
  CheckCircle, XCircle, Clock, BarChart3
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";
import { formatRelativeTime } from "@/lib/utils";

export default function AdminPage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();

  const { data: health } = useQuery({
    queryKey: ["admin-health"],
    queryFn: () => api.get("/admin/system/health").then((r) => r.data),
    enabled: !!user?.is_superadmin,
  });

  const { data: workspaces } = useQuery({
    queryKey: ["admin-workspaces"],
    queryFn: () => api.get("/admin/workspaces?limit=10").then((r) => r.data),
    enabled: !!user?.is_superadmin,
  });

  const { data: users } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get("/admin/users?limit=10").then((r) => r.data),
    enabled: !!user?.is_superadmin,
  });

  const { data: auditLogs } = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => api.get("/admin/audit-logs?limit=20").then((r) => r.data),
    enabled: !!user?.is_superadmin,
  });

  const toggleUserMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      api.put(`/admin/users/${userId}/status`, { is_active: !isActive }),
    onSuccess: () => {
      toast.success("User status updated");
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  if (!user?.is_superadmin) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-96">
        <Shield className="w-12 h-12 text-white/10 mb-4" />
        <p className="text-white/40">Super Admin access required</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="w-6 h-6 text-atlas-400" /> Admin Panel
        </h1>
        <p className="text-white/40 text-sm mt-0.5">Platform-wide management and oversight</p>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Platform Status", value: health?.status || "—", icon: Activity, ok: health?.status === "healthy" },
          { label: "Total Users", value: health?.user_count ?? "—", icon: Users, ok: true },
          { label: "Active Workspaces", value: health?.workspace_count ?? "—", icon: Building2, ok: true },
          { label: "API Version", value: health?.version || "1.0.0", icon: BarChart3, ok: true },
        ].map((s) => (
          <Card key={s.label} className="bg-white/[0.02] border-white/5">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-2">
                <s.icon className="w-4 h-4 text-white/40" />
                {s.ok ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
              </div>
              <p className="text-xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-white/40 mt-0.5">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workspaces */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-white/60 flex items-center gap-2">
              <Building2 className="w-4 h-4" /> All Workspaces
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {workspaces?.map((ws: { id: string; name: string; tier: string; is_active: boolean; created_at: string }) => (
              <div key={ws.id} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/[0.03]">
                <div>
                  <p className="text-sm text-white/70">{ws.name}</p>
                  <p className="text-xs text-white/30">{formatRelativeTime(ws.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={ws.tier === "enterprise" ? "atlas" : ws.tier === "pro" ? "info" : "outline"} className="text-xs">
                    {ws.tier}
                  </Badge>
                  <Badge variant={ws.is_active ? "success" : "destructive"} className="text-xs">
                    {ws.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Users */}
        <Card className="bg-white/[0.02] border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-white/60 flex items-center gap-2">
              <Users className="w-4 h-4" /> All Users
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {users?.map((u: { id: string; email: string; full_name: string; is_active: boolean; is_superadmin: boolean }) => (
              <div key={u.id} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/[0.03] group">
                <div>
                  <p className="text-sm text-white/70">{u.full_name}</p>
                  <p className="text-xs text-white/30">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  {u.is_superadmin && <Badge variant="atlas" className="text-xs">Admin</Badge>}
                  <button
                    onClick={() => toggleUserMutation.mutate({ userId: u.id, isActive: u.is_active })}
                    className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                      u.is_active
                        ? "border-red-500/20 text-red-400 hover:bg-red-500/10"
                        : "border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10"
                    }`}
                  >
                    {u.is_active ? "Disable" : "Enable"}
                  </button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Audit Logs */}
      <Card className="bg-white/[0.02] border-white/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/60 flex items-center gap-2">
            <FileText className="w-4 h-4" /> Audit Log
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-white/5 overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/5 bg-white/[0.02]">
                  <th className="text-left px-3 py-2 text-white/30">Action</th>
                  <th className="text-left px-3 py-2 text-white/30">Resource</th>
                  <th className="text-left px-3 py-2 text-white/30">User</th>
                  <th className="text-left px-3 py-2 text-white/30">IP</th>
                  <th className="text-left px-3 py-2 text-white/30">Time</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs?.map((log: {
                  id: string; action: string; resource_type?: string; user_id?: string;
                  ip_address?: string; created_at: string;
                }) => (
                  <tr key={log.id} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="px-3 py-2">
                      <span className="font-mono text-atlas-400">{log.action}</span>
                    </td>
                    <td className="px-3 py-2 text-white/40">{log.resource_type || "—"}</td>
                    <td className="px-3 py-2 text-white/30 font-mono">{log.user_id?.slice(0, 8) || "—"}</td>
                    <td className="px-3 py-2 text-white/30">{log.ip_address || "—"}</td>
                    <td className="px-3 py-2 text-white/25">{formatRelativeTime(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!auditLogs?.length && (
              <p className="text-center py-6 text-xs text-white/20">No audit events yet</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
