"use client";
import { Suspense } from "react";
import { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Brain, Eye, EyeOff, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authApi } from "@/lib/api";
import Link from "next/link";

const schema = z.object({
  new_password: z.string().min(8).regex(/[A-Z]/).regex(/\d/),
  confirm: z.string(),
}).refine((d) => d.new_password === d.confirm, { message: "Passwords don't match", path: ["confirm"] });

type FormData = z.infer<typeof schema>;

function ResetContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";
  const [done, setDone] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    if (!token) { toast.error("Invalid reset link"); return; }
    try {
      await authApi.resetPassword(token, data.new_password);
      setDone(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e?.response?.data?.detail || "Reset failed. Link may have expired.");
    }
  };

  return (
    <div className="w-full max-w-sm">
      <div className="flex flex-col items-center mb-8">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg shadow-atlas-500/30">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">Set new password</h1>
      </div>
      {done ? (
        <div className="text-center">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
          <p className="text-white/80 font-medium mb-1">Password updated</p>
          <p className="text-sm text-white/40 mb-6">You can now sign in with your new password.</p>
          <Link href="/login"><Button variant="atlas" className="w-full">Sign in</Button></Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="relative">
            <Input type={showPw ? "text" : "password"} placeholder="New password"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 pr-10"
              {...register("new_password")} />
            <button type="button" onClick={() => setShowPw(!showPw)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
              {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            {errors.new_password && <p className="text-xs text-red-400 mt-1">{String(errors.new_password.message)}</p>}
          </div>
          <div>
            <Input type="password" placeholder="Confirm new password"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20"
              {...register("confirm")} />
            {errors.confirm && <p className="text-xs text-red-400 mt-1">{String(errors.confirm.message)}</p>}
          </div>
          <Button variant="atlas" className="w-full h-11" isLoading={isSubmitting}>Reset password</Button>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <Suspense fallback={<div className="w-8 h-8 border-2 border-atlas-500/30 border-t-atlas-500 rounded-full animate-spin" />}>
        <ResetContent />
      </Suspense>
    </div>
  );
}
