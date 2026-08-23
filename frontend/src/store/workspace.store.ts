import { create } from "zustand";
import { persist } from "zustand/middleware";

interface Workspace {
  id: string;
  name: string;
  slug: string;
  description?: string;
  tier: string;
  storage_quota_bytes: number;
  storage_used_bytes: number;
  logo_url?: string;
  member_count?: number;
  document_count?: number;
  created_at: string;
}

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setActiveWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (id: string, updates: Partial<Workspace>) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspaces: [],
      activeWorkspace: null,

      setWorkspaces: (workspaces) => set({ workspaces }),

      setActiveWorkspace: (workspace) => set({ activeWorkspace: workspace }),

      updateWorkspace: (id, updates) =>
        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.id === id ? { ...w, ...updates } : w
          ),
          activeWorkspace:
            state.activeWorkspace?.id === id
              ? { ...state.activeWorkspace, ...updates }
              : state.activeWorkspace,
        })),
    }),
    {
      name: "atlas-workspace",
      partialize: (state) => ({
        activeWorkspace: state.activeWorkspace,
      }),
    }
  )
);
