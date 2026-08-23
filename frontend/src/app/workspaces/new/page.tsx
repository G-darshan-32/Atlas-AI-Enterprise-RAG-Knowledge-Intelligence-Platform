"use client";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Brain, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { workspaceApi } from "@/lib/api";
import { useWorkspaceStore } from "@/store/workspace.store";

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(100),
  description: z.string().max(500).optional(),
});

type FormData = z.infer<typeof schema>;

const TEMPLATES = [
  { id: "engineering", name: "Engineering Team", desc: "Architecture docs, API guides, coding standards, CI/CD" },
  { id: "hr", name: "HR & People", desc: "Handbooks, policies, onboarding docs, leave policies" },
  { id: "research", name: "Research", desc: "Papers, experiments, literature reviews, findings" },
  { id: "blank", name: "Blank Workspace", desc: "Start from scratch with no pre-configured structure" },
];

export default function NewWorkspacePage() {
  const router = useRouter();
  const { setActiveWorkspace } = useWorkspaceStore();

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const createMutation = useMutation({
    mutationFn: (data: FormData) => workspaceApi.create(data as { name: string; description?: string }).then((r) => r.data),
    onSuccess: (workspace) => {
      setActiveWorkspace(workspace);
      toast.success(`"${workspace.name}" created`);
      router.push(`/workspace/${workspace.id}/dashboard`);
    },
    onError: () => toast.error("Failed to create workspace"),
  });

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center px-4">
      <div className="w-full max-w-lg">
        <Link href="/workspaces" className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to workspaces
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center shadow-lg shadow-atlas-500/30">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">New Workspace</h1>
            <p className="text-xs text-white/40">Set up your knowledge base</p>
          </div>
        </div>

        {/* Template picker */}
        <div className="mb-6">
          <p className="text-xs text-white/40 font-medium uppercase tracking-wider mb-3">Start with a template</p>
          <div className="grid grid-cols-2 gap-2">
            {TEMPLATES.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  if (t.id !== "blank") setValue("name", t.name);
                  setValue("description", t.desc);
                }}
                className="text-left p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:border-atlas-500/30 hover:bg-atlas-500/5 transition-all"
              >
                <p className="text-sm font-medium text-white/80">{t.name}</p>
                <p className="text-xs text-white/30 mt-0.5 line-clamp-2">{t.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div>
            <label className="text-xs text-white/50 block mb-1.5">Workspace Name *</label>
            <Input
              {...register("name")}
              placeholder="e.g. TechNova Engineering"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500"
            />
            {errors.name && <p className="text-xs text-red-400 mt-1">{errors.name.message}</p>}
          </div>

          <div>
            <label className="text-xs text-white/50 block mb-1.5">Description</label>
            <Input
              {...register("description")}
              placeholder="What does this workspace contain?"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500"
            />
          </div>

          <Button
            type="submit"
            variant="atlas"
            className="w-full h-11"
            isLoading={createMutation.isPending}
          >
            Create workspace
          </Button>
        </form>
      </div>
    </div>
  );
}
