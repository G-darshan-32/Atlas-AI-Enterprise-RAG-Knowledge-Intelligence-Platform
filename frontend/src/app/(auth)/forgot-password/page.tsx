"use client";
import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Brain, ArrowLeft, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authApi } from "@/lib/api";

const schema = z.object({ email: z.string().email("Valid email required") });
type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, getValues, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await authApi.forgotPassword(data.email);
      setSent(true);
    } catch {
      toast.error("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg shadow-atlas-500/30">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Reset your password</h1>
          <p className="text-sm text-white/40 mt-1 text-center">
            We'll send a reset link to your email
          </p>
        </div>

        {sent ? (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center">
            <Mail className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
            <p className="text-sm font-medium text-white/80 mb-1">Check your inbox</p>
            <p className="text-xs text-white/40">
              We sent a reset link to <span className="text-white/70">{getValues("email")}</span>.
              The link expires in 1 hour.
            </p>
            <Link href="/login" className="inline-block mt-4 text-sm text-atlas-400 hover:text-atlas-300">
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Input
                  type="email"
                  placeholder="your@email.com"
                  className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500"
                  {...register("email")}
                />
                {errors.email && <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>}
              </div>
              <Button variant="atlas" className="w-full h-11" isLoading={isSubmitting}>
                Send reset link
              </Button>
            </form>
            <Link href="/login" className="flex items-center justify-center gap-1.5 mt-6 text-sm text-white/30 hover:text-white/60 transition-colors">
              <ArrowLeft className="w-4 h-4" /> Back to sign in
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
