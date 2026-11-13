import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { ArrowLeft, Sparkles } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center p-6">
      <div className="max-w-md w-full p-8 rounded-2xl border border-white/10 bg-[#0d0d17]/90 text-center">
        <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto mb-5 text-cyan-400">
          <Sparkles className="w-7 h-7" />
        </div>
        <h1 className="text-4xl font-black mb-2 tracking-tight">404</h1>
        <h2 className="text-lg font-bold mb-2">Page Not Found</h2>
        <p className="text-sm text-white/50 mb-6">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link href="/">
          <Button className="bg-cyan-400 text-black hover:bg-cyan-300 font-semibold">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </Link>
      </div>
    </div>
  );
}

