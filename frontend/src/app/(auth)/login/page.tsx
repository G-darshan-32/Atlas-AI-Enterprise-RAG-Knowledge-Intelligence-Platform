"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Brain, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z.string().min(1, "Password required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      const res = await authApi.login({ email: data.email!, password: data.password! });
      const { access_token, refresh_token } = res.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      const meRes = await import("@/lib/api").then(m => m.authApi.me());
      setAuth(meRes.data, access_token, refresh_token);

      toast.success("Welcome back!");
      router.push("/workspaces");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast.error(error?.response?.data?.detail || "Login failed. Check your credentials.");
    }
  };

  const fillDemo = (email: string, password: string) => {
    setValue("email", email, { shouldValidate: true });
    setValue("password", password, { shouldValidate: true });
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-gradient-to-b from-atlas-950/50 to-transparent pointer-events-none" />

      <div className="w-full max-w-sm relative">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg shadow-atlas-500/30">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Sign in to Atlas AI</h1>
          <p className="text-sm text-white/40 mt-1">Enter your workspace</p>
        </div>

        {/* Demo credentials */}
        <div className="glass-card rounded-xl p-4 mb-6">
          <p className="text-xs text-white/40 mb-3 font-medium uppercase tracking-wider">Demo accounts</p>
          <div className="space-y-2">
            {[
              { label: "Super Admin", email: "admin@atlas-ai.com", password: "Admin@123456" },
              { label: "Engineer", email: "dev@technova.com", password: "Demo@123456" },
              { label: "Researcher", email: "researcher@atlas-ai.com", password: "Demo@123456" },
            ].map((d) => (
              <button
                key={d.email}
                onClick={() => fillDemo(d.email, d.password)}
                className="w-full flex items-center justify-between text-xs rounded-lg px-3 py-2 bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 hover:border-white/10 transition-colors text-left"
              >
                <span className="text-white/60 font-medium">{d.label}</span>
                <span className="text-white/30 font-mono">{d.email}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500"
              {...register("email")}
            />
            {errors.email && <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>}
          </div>

          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              className="h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500 pr-10"
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            {errors.password && <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>}
          </div>

          <div className="flex justify-end">
            <Link href="/forgot-password" className="text-xs text-atlas-400 hover:text-atlas-300">
              Forgot password?
            </Link>
          </div>

          <Button variant="atlas" className="w-full h-11" isLoading={isSubmitting}>
            Sign in
          </Button>
        </form>

        <p className="text-center text-sm text-white/30 mt-6">
          No account?{" "}
          <Link href="/register" className="text-atlas-400 hover:text-atlas-300">
            Create one free
          </Link>
        </p>
      </div>
    </div>
  );
}
