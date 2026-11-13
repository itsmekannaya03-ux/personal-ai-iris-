"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error caught by boundary:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center p-6 select-none">
      <div className="max-w-md w-full p-8 rounded-2xl border border-white/10 bg-[#0d0d17]/90 backdrop-blur-xl shadow-2xl text-center">
        <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5 text-red-400">
          <AlertTriangle className="w-7 h-7" />
        </div>

        <h1 className="text-xl font-bold text-white mb-2">Something went wrong</h1>
        <p className="text-sm text-white/50 mb-6 leading-relaxed">
          An unexpected error occurred. You can retry or head back to the home page.
        </p>

        {error?.message && (
          <div className="mb-6 p-3 rounded-lg bg-red-500/5 border border-red-500/20 text-xs font-mono text-red-300 text-left overflow-auto max-h-32">
            {error.message}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            onClick={() => reset()}
            className="w-full sm:w-auto bg-cyan-400 text-black hover:bg-cyan-300 font-semibold"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
          <Link href="/" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto border-white/20">
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

