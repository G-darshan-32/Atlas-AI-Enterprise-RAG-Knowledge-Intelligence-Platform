"use client";
import { useEffect } from "react";
import { useRouter, useParams, usePathname } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Brain, LayoutDashboard, MessageSquare, Search, FileText,
  GitBranch, BarChart3, FileBarChart, Bell, Settings,
  ChevronDown, LogOut, Shield, CreditCard, HelpCircle, UserCircle
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { useWorkspaceStore } from "@/store/workspace.store";
import { workspaceApi } from "@/lib/api";
import { cn, getInitials } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "chat", icon: MessageSquare, label: "Chat" },
  { href: "search", icon: Search, label: "Search" },
  { href: "documents", icon: FileText, label: "Documents" },
  { href: "repositories", icon: GitBranch, label: "Repositories" },
  { href: "analytics", icon: BarChart3, label: "Analytics" },
  { href: "reports", icon: FileBarChart, label: "Reports" },
];

const BOTTOM_NAV_ITEMS = [
  { href: "admin", icon: Shield, label: "Admin", superadminOnly: true },
  { href: "billing", icon: CreditCard, label: "Billing" },
  { href: "help", icon: HelpCircle, label: "Help" },
  { href: "profile", icon: UserCircle, label: "Profile" },
];

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const params = useParams();
  const pathname = usePathname();
  const workspaceId = params.id as string;

  const { user, isAuthenticated, logout } = useAuthStore();
  const { activeWorkspace, setActiveWorkspace } = useWorkspaceStore();

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: workspace } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => workspaceApi.get(workspaceId).then((r) => r.data),
    enabled: !!workspaceId && isAuthenticated,
  });

  useEffect(() => {
    if (workspace) setActiveWorkspace(workspace);
  }, [workspace, setActiveWorkspace]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col border-r border-white/5 bg-[#0d0d14]">
        {/* Logo + Workspace name */}
        <div className="px-4 h-14 flex items-center gap-2.5 border-b border-white/5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Brain className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{activeWorkspace?.name || workspace?.name || "Atlas AI"}</p>
          </div>
          <Link href="/workspaces">
            <ChevronDown className="w-4 h-4 text-white/30 hover:text-white/70 transition-colors" />
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const href = `/workspace/${workspaceId}/${item.href}`;
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={item.href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
                  isActive
                    ? "bg-atlas-500/15 text-atlas-300 font-medium"
                    : "text-white/40 hover:text-white/80 hover:bg-white/[0.04]"
                )}
              >
                <item.icon className={cn("w-4 h-4 flex-shrink-0", isActive && "text-atlas-400")} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="px-2 py-3 border-t border-white/5 space-y-0.5">
          {BOTTOM_NAV_ITEMS.filter(item => !item.superadminOnly || user?.is_superadmin).map((item) => {
            const href = `/workspace/${workspaceId}/${item.href}`;
            const isActive = pathname === href;
            return (
              <Link
                key={item.href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
                  isActive
                    ? "bg-atlas-500/15 text-atlas-300 font-medium"
                    : "text-white/40 hover:text-white/80 hover:bg-white/[0.04]"
                )}
              >
                <item.icon className={cn("w-4 h-4 flex-shrink-0", isActive && "text-atlas-400")} />
                {item.label}
              </Link>
            );
          })}

          {/* Notifications shortcut */}
          <Link
            href={`/workspace/${workspaceId}/notifications`}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
              pathname.includes("notifications")
                ? "bg-atlas-500/15 text-atlas-300 font-medium"
                : "text-white/40 hover:text-white/80 hover:bg-white/[0.04]"
            )}
          >
            <Bell className="w-4 h-4" />
            Notifications
          </Link>

          {/* Settings shortcut */}
          <Link
            href={`/workspace/${workspaceId}/settings`}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
              pathname.includes("/settings")
                ? "bg-atlas-500/15 text-atlas-300 font-medium"
                : "text-white/40 hover:text-white/80 hover:bg-white/[0.04]"
            )}
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>

          {/* User */}
          <div className="flex items-center gap-2.5 px-3 py-2 mt-1 rounded-lg hover:bg-white/[0.04] cursor-pointer group">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-atlas-500/60 to-purple-600/60 flex items-center justify-center text-xs font-semibold flex-shrink-0">
              {user ? getInitials(user.full_name) : "?"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate text-white/70">{user?.full_name}</p>
              <p className="text-xs text-white/30 truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5 text-white/30 hover:text-white/70" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
