"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Info, Upload, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { notificationApi } from "@/lib/api";
import { formatRelativeTime, cn } from "@/lib/utils";

const TYPE_ICONS: Record<string, React.ElementType> = {
  document_processed: Upload,
  member_invited: UserPlus,
  default: Info,
};

export default function NotificationsPage() {
  const qc = useQueryClient();

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationApi.list().then((r) => r.data),
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unreadCount = notifications?.filter((n: { is_read: boolean }) => !n.is_read).length || 0;

  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-white/40 mt-0.5">{unreadCount} unread</p>
          )}
        </div>
        {unreadCount > 0 && (
          <Button
            onClick={() => markAllMutation.mutate()}
            variant="ghost"
            size="sm"
            className="text-white/40 hover:text-white gap-2"
          >
            <CheckCheck className="w-4 h-4" /> Mark all read
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-white/[0.02] border border-white/5 animate-pulse" />
          ))}
        </div>
      ) : notifications?.length === 0 ? (
        <div className="text-center py-16">
          <Bell className="w-10 h-10 text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">No notifications</p>
        </div>
      ) : (
        <div className="space-y-1">
          {notifications?.map((n: {
            id: string; type: string; title: string; body: string; is_read: boolean; created_at: string;
          }) => {
            const Icon = TYPE_ICONS[n.type] || TYPE_ICONS.default;
            return (
              <button
                key={n.id}
                onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
                className={cn(
                  "w-full text-left flex items-start gap-3 p-4 rounded-xl transition-colors",
                  n.is_read ? "bg-transparent hover:bg-white/[0.02]" : "bg-atlas-500/5 border border-atlas-500/15 hover:bg-atlas-500/10"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                  n.is_read ? "bg-white/5" : "bg-atlas-500/20"
                )}>
                  <Icon className={cn("w-4 h-4", n.is_read ? "text-white/30" : "text-atlas-400")} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn("text-sm font-medium", n.is_read ? "text-white/50" : "text-white/80")}>
                    {n.title}
                  </p>
                  <p className="text-xs text-white/30 mt-0.5">{n.body}</p>
                  <p className="text-xs text-white/20 mt-1">{formatRelativeTime(n.created_at)}</p>
                </div>
                {!n.is_read && <div className="w-2 h-2 rounded-full bg-atlas-500 flex-shrink-0 mt-1" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
