"use client";
import { Suspense } from "react";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Brain, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function VerifyContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) { setStatus("error"); return; }
    api.post(`/auth/verify-email?token=${token}`)
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [searchParams]);

  return (
    <div className="w-full max-w-sm text-center">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
        <Brain className="w-7 h-7 text-white" />
      </div>
      {status === "loading" && (
        <div>
          <div className="w-8 h-8 border-2 border-atlas-500/30 border-t-atlas-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/50">Verifying your email...</p>
        </div>
      )}
      {status === "success" && (
        <div>
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Email Verified</h2>
          <p className="text-white/40 text-sm mb-6">Your account is now fully activated.</p>
          <Link href="/login"><Button variant="atlas" className="w-full">Continue to sign in</Button></Link>
        </div>
      )}
      {status === "error" && (
        <div>
          <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Verification Failed</h2>
          <p className="text-white/40 text-sm mb-6">This link may be expired or invalid.</p>
          <Link href="/register"><Button variant="outline" className="w-full border-white/10 text-white/60 hover:text-white">Back to sign up</Button></Link>
        </div>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <Suspense fallback={
        <div className="w-8 h-8 border-2 border-atlas-500/30 border-t-atlas-500 rounded-full animate-spin" />
      }>
        <VerifyContent />
      </Suspense>
    </div>
  );
}
