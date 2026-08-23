"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Settings, Users, HardDrive, Shield, Bell, Trash2, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { workspaceApi } from "@/lib/api";
import { formatBytes, getInitials, getRoleColor } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspace.store";
import { useState } from "react";

export default function SettingsPage() {
  const params = useParams();
  const workspaceId = params.id as string;
  const { activeWorkspace, updateWorkspace } = useWorkspaceStore();
  const qc = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("employee");

  const { data: members } = useQuery({
    queryKey: ["members", workspaceId],
    queryFn: () => workspaceApi.listMembers(workspaceId).then((r) => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; description?: string }) =>
      workspaceApi.update(workspaceId, data),
    onSuccess: (res) => {
      toast.success("Workspace updated");
      updateWorkspace(workspaceId, res.data);
      qc.invalidateQueries({ queryKey: ["workspace", workspaceId] });
    },
  });

  const inviteMutation = useMutation({
    mutationFn: () => workspaceApi.inviteMember(workspaceId, { email: inviteEmail, role: inviteRole }),
    onSuccess: () => {
      toast.success(`Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      qc.invalidateQueries({ queryKey: ["members", workspaceId] });
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e?.response?.data?.detail || "Failed to invite member");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (userId: string) => workspaceApi.removeMember(workspaceId, userId),
    onSuccess: () => {
      toast.success("Member removed");
      qc.invalidateQueries({ queryKey: ["members", workspaceId] });
    },
  });

  const { register, handleSubmit } = useForm({
    defaultValues: {
      name: activeWorkspace?.name || "",
      description: activeWorkspace?.description || "",
    },
  });

  const storagePercent = activeWorkspace
    ? Math.round((activeWorkspace.storage_used_bytes / activeWorkspace.storage_quota_bytes) * 100)
    : 0;

  return (
    <div className="p-6 max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Workspace Settings</h1>
        <p className="text-white/40 text-sm mt-0.5">{activeWorkspace?.name}</p>
      </div>

      {/* General */}
      <section>
        <h2 className="text-sm font-medium text-white/70 flex items-center gap-2 mb-4">
          <Settings className="w-4 h-4" /> General
        </h2>
        <form onSubmit={handleSubmit((d) => updateMutation.mutate(d))} className="space-y-4">
          <div>
            <label className="text-xs text-white/40 block mb-1.5">Workspace Name</label>
            <Input
              {...register("name")}
              className="h-10 bg-white/[0.03] border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1.5">Description</label>
            <Input
              {...register("description")}
              className="h-10 bg-white/[0.03] border-white/10 text-white"
            />
          </div>
          <Button type="submit" variant="atlas" size="sm" isLoading={updateMutation.isPending}>
            Save changes
          </Button>
        </form>
      </section>

      <div className="border-t border-white/5" />

      {/* Storage */}
      <section>
        <h2 className="text-sm font-medium text-white/70 flex items-center gap-2 mb-4">
          <HardDrive className="w-4 h-4" /> Storage
        </h2>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
          <div className="flex justify-between text-sm mb-3">
            <span className="text-white/60">{formatBytes(activeWorkspace?.storage_used_bytes ?? 0)} used</span>
            <span className="text-white/30">{formatBytes(activeWorkspace?.storage_quota_bytes ?? 0)} total</span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden mb-2">
            <div
              className="h-full rounded-full bg-gradient-to-r from-atlas-500 to-purple-500 transition-all"
              style={{ width: `${storagePercent}%` }}
            />
          </div>
          <p className="text-xs text-white/30">{storagePercent}% of quota used</p>
        </div>
      </section>

      <div className="border-t border-white/5" />

      {/* Members */}
      <section>
        <h2 className="text-sm font-medium text-white/70 flex items-center gap-2 mb-4">
          <Users className="w-4 h-4" /> Members ({members?.length || 0})
        </h2>

        {/* Invite */}
        <div className="flex gap-2 mb-5">
          <Input
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@company.com"
            className="h-9 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 flex-1"
          />
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
            className="h-9 rounded-lg border border-white/10 bg-white/[0.03] text-white/60 text-sm px-3 outline-none"
          >
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="workspace_admin">Admin</option>
            <option value="guest">Guest</option>
          </select>
          <Button
            onClick={() => inviteMutation.mutate()}
            disabled={!inviteEmail.includes("@") || inviteMutation.isPending}
            variant="outline"
            size="sm"
            className="border-white/10 text-white/60 hover:text-white gap-1.5"
          >
            <UserPlus className="w-4 h-4" /> Invite
          </Button>
        </div>

        {/* Member list */}
        <div className="space-y-1">
          {members?.map((m: {
            id: string; user_id: string; full_name: string; email: string;
            role: string; avatar_url?: string;
          }) => (
            <div key={m.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/[0.03] group">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-atlas-500/40 to-purple-600/40 flex items-center justify-center text-xs font-semibold flex-shrink-0">
                {getInitials(m.full_name)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white/70 font-medium">{m.full_name}</p>
                <p className="text-xs text-white/30">{m.email}</p>
              </div>
              <Badge className={`text-xs border ${getRoleColor(m.role)}`}>{m.role.replace("_", " ")}</Badge>
              <button
                onClick={() => removeMutation.mutate(m.user_id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded hover:bg-red-500/10 text-white/25 hover:text-red-400 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
