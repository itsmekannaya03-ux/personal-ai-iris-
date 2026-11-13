"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="bg-[#0a0a0f] text-white min-h-screen flex items-center justify-center p-6">
        <div className="max-w-md w-full p-8 rounded-2xl border border-white/10 bg-[#0d0d17] text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5 text-red-400">
            <AlertTriangle className="w-7 h-7" />
          </div>
          <h1 className="text-xl font-bold mb-2">Application Error</h1>
          <p className="text-sm text-white/50 mb-6">
            A critical error occurred in the application root.
          </p>
          <button
            onClick={() => reset()}
            className="px-5 py-2.5 rounded-lg bg-cyan-400 text-black font-semibold hover:bg-cyan-300 transition-colors inline-flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Reload App
          </button>
        </div>
      </body>
    </html>
  );
}

