"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { User, Mail, Shield, Key, LogOut, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";
import { useRouter } from "next/navigation";
import { getInitials, formatDate } from "@/lib/utils";

const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, "Required"),
  new_password: z.string().min(8, "Minimum 8 characters").regex(/[A-Z]/, "Needs uppercase").regex(/\d/, "Needs number"),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

export default function ProfilePage() {
  const { user, setUser, logout } = useAuthStore();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");

  const profileForm = useForm({ resolver: zodResolver(profileSchema), defaultValues: { full_name: user?.full_name || "" } });
  const passwordForm = useForm({ resolver: zodResolver(passwordSchema) });

  const updateMutation = useMutation({
    mutationFn: (data: { full_name: string }) => authApi.updateProfile(data).then((r) => r.data),
    onSuccess: (data) => { setUser(data); toast.success("Profile updated"); },
    onError: () => toast.error("Failed to update profile"),
  });

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const tabs = [
    { id: "profile" as const, label: "Profile", icon: User },
    { id: "security" as const, label: "Security", icon: Shield },
  ];

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-white/40 text-sm mt-0.5">Manage your account settings</p>
      </div>

      {/* Avatar + Name header */}
      <div className="flex items-center gap-5 p-5 rounded-xl border border-white/5 bg-white/[0.02] mb-6">
        <div className="relative">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-atlas-500/70 to-purple-600/70 flex items-center justify-center text-xl font-bold flex-shrink-0">
            {user ? getInitials(user.full_name) : "?"}
          </div>
          <button className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-white/10 border border-white/20 flex items-center justify-center hover:bg-white/20 transition-colors">
            <Camera className="w-3 h-3 text-white/60" />
          </button>
        </div>
        <div>
          <p className="font-semibold text-white">{user?.full_name}</p>
          <p className="text-sm text-white/40">{user?.email}</p>
          <div className="flex items-center gap-2 mt-1">
            {user?.is_superadmin && <Badge variant="atlas" className="text-xs">Super Admin</Badge>}
            {user?.is_verified ? (
              <Badge variant="success" className="text-xs">Verified</Badge>
            ) : (
              <Badge variant="warning" className="text-xs">Unverified</Badge>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 p-1 rounded-lg bg-white/[0.03] border border-white/5 w-fit">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-all ${
              activeTab === t.id
                ? "bg-atlas-500/20 text-atlas-300 font-medium"
                : "text-white/40 hover:text-white/70"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "profile" && (
        <form onSubmit={profileForm.handleSubmit((d) => updateMutation.mutate(d))} className="space-y-5">
          <div>
            <label className="text-xs text-white/40 block mb-1.5">Full Name</label>
            <Input
              {...profileForm.register("full_name")}
              className="h-10 bg-white/[0.03] border-white/10 text-white"
            />
            {profileForm.formState.errors.full_name && (
              <p className="text-xs text-red-400 mt-1">{profileForm.formState.errors.full_name.message}</p>
            )}
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1.5">Email Address</label>
            <Input
              value={user?.email || ""}
              disabled
              className="h-10 bg-white/[0.02] border-white/5 text-white/30 cursor-not-allowed"
            />
            <p className="text-xs text-white/25 mt-1">Email cannot be changed</p>
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1.5">Member Since</label>
            <p className="text-sm text-white/50">{user?.created_at ? formatDate(user.created_at) : "—"}</p>
          </div>

          <Button type="submit" variant="atlas" size="sm" isLoading={updateMutation.isPending}>
            Save changes
          </Button>
        </form>
      )}

      {activeTab === "security" && (
        <div className="space-y-6">
          {/* MFA */}
          <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">Two-Factor Authentication</p>
                <p className="text-xs text-white/30 mt-0.5">Add an extra layer of security to your account</p>
              </div>
              <Badge variant={user?.mfa_enabled ? "success" : "outline"}>
                {user?.mfa_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <Button variant="outline" size="sm" className="mt-3 border-white/10 text-white/60 hover:text-white">
              {user?.mfa_enabled ? "Disable 2FA" : "Enable 2FA"}
            </Button>
          </div>

          {/* Password change */}
          <div>
            <h3 className="text-sm font-medium text-white/70 flex items-center gap-2 mb-4">
              <Key className="w-4 h-4" /> Change Password
            </h3>
            <form onSubmit={passwordForm.handleSubmit(() => toast.info("Password change not yet connected to backend"))} className="space-y-3">
              <Input
                type="password"
                placeholder="Current password"
                {...passwordForm.register("current_password")}
                className="h-10 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              />
              <Input
                type="password"
                placeholder="New password"
                {...passwordForm.register("new_password")}
                className="h-10 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              />
              <Input
                type="password"
                placeholder="Confirm new password"
                {...passwordForm.register("confirm_password")}
                className="h-10 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              />
              {passwordForm.formState.errors.confirm_password && (
                <p className="text-xs text-red-400">{String(passwordForm.formState.errors.confirm_password.message)}</p>
              )}
              <Button type="submit" variant="outline" size="sm" className="border-white/10 text-white/60 hover:text-white">
                Update password
              </Button>
            </form>
          </div>

          {/* Sign out */}
          <div className="border-t border-white/5 pt-4">
            <Button
              onClick={handleLogout}
              variant="destructive"
              size="sm"
              className="gap-2"
            >
              <LogOut className="w-4 h-4" /> Sign out of all devices
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
