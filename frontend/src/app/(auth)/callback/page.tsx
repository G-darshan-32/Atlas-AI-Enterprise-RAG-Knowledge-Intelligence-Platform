"use client";
import { Suspense } from "react";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/auth.store";
import { authApi } from "@/lib/api";
import { Brain } from "lucide-react";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const access_token = searchParams.get("access_token");
    const refresh_token = searchParams.get("refresh_token");
    if (!access_token || !refresh_token) {
      router.push("/login?error=oauth_failed");
      return;
    }
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    authApi.me()
      .then((res) => { setAuth(res.data, access_token, refresh_token); router.push("/workspaces"); })
      .catch(() => router.push("/login?error=profile_failed"));
  }, [searchParams, router, setAuth]);

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center animate-pulse">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <p className="text-white/50 text-sm">Signing you in...</p>
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center animate-pulse">
          <Brain className="w-6 h-6 text-white" />
        </div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
