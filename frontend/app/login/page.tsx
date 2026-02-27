"use client";

import { signIn } from "@/lib/auth-client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Headphones, ShieldCheck, TicketCheck, Zap } from "lucide-react";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      await signIn.social({ provider: "google", callbackURL: "/" });
    } catch (error) {
      console.error("Sign in failed", error);
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      {/* Left brand panel — hidden on small screens */}
      <div className="hidden lg:flex lg:w-1/2 bg-muted/40 border-r flex-col justify-between px-12 py-16">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Headphones className="h-6 w-6 text-primary" />
            <span className="font-semibold text-lg">SupportDesk</span>
          </div>
        </div>

        <div className="space-y-8">
          <div className="space-y-3">
            <h2 className="text-3xl font-bold tracking-tight leading-tight">
              AI-powered support,
              <br />
              built for speed.
            </h2>
            <p className="text-muted-foreground text-sm leading-relaxed max-w-sm">
              Submit a ticket in seconds. Our models instantly categorise and
              prioritise your request so the right team gets it immediately.
            </p>
          </div>

          <div className="space-y-4">
            {[
              {
                icon: <Zap className="h-4 w-4 text-primary" />,
                label: "Instant AI routing",
                desc: "Every ticket classified and scored in milliseconds.",
              },
              {
                icon: <TicketCheck className="h-4 w-4 text-primary" />,
                label: "Real-time tracking",
                desc: "Follow every update on your requests in one place.",
              },
              {
                icon: <ShieldCheck className="h-4 w-4 text-primary" />,
                label: "Secure by default",
                desc: "Google OAuth + encrypted database. No passwords.",
              },
            ].map((f) => (
              <div key={f.label} className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{f.icon}</div>
                <div>
                  <p className="text-sm font-medium">{f.label}</p>
                  <p className="text-xs text-muted-foreground">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-muted-foreground">© 2026 SupportDesk</p>
      </div>

      {/* Right sign-in panel */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile brand mark */}
          <div className="lg:hidden flex items-center gap-2 justify-center">
            <Headphones className="h-5 w-5 text-primary" />
            <span className="font-semibold">SupportDesk</span>
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              Welcome back
            </h1>
            <p className="text-sm text-muted-foreground">
              Sign in to submit and track your support requests.
            </p>
          </div>

          <div className="space-y-4">
            <Button
              variant="outline"
              className="w-full h-11"
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <GoogleIcon className="mr-2 h-4 w-4" />
              {loading ? "Signing in…" : "Continue with Google"}
            </Button>

            <Separator />

            <p className="text-center text-xs text-muted-foreground">
              By continuing, you agree to our{" "}
              <a
                href="#"
                className="underline underline-offset-4 hover:text-foreground"
              >
                Terms
              </a>{" "}
              and{" "}
              <a
                href="#"
                className="underline underline-offset-4 hover:text-foreground"
              >
                Privacy Policy
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function GoogleIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path
        d="M12.0003 4.75C13.7703 4.75 15.3553 5.36 16.6053 6.54L20.0303 3.13C17.9503 1.19 15.2353 0 12.0003 0C7.31033 0 3.25533 2.69 1.28033 6.60L5.27033 9.71C6.21033 6.89 8.87033 4.75 12.0003 4.75Z"
        fill="#EA4335"
      />
      <path
        d="M23.49 12.27C23.49 11.48 23.42 10.73 23.3 10H12V14.51H18.47C18.18 15.99 17.33 17.24 16.07 18.09L19.93 21.09C22.19 19 23.49 15.93 23.49 12.27Z"
        fill="#4285F4"
      />
      <path
        d="M5.26999 14.29C5.02999 13.57 4.89999 12.8 4.89999 12C4.89999 11.2 5.02999 10.43 5.26999 9.71L1.27999 6.60C0.46999 8.23 0 10.06 0 12C0 13.94 0.46999 15.77 1.27999 17.4L5.26999 14.29Z"
        fill="#FBBC05"
      />
      <path
        d="M12.0003 24C15.2403 24 17.9603 22.93 19.9303 21.09L16.0703 18.09C15.0003 18.81 13.6203 19.25 12.0003 19.25C8.87033 19.25 6.21033 17.11 5.27033 14.29L1.28033 17.4C3.25533 21.31 7.31033 24 12.0003 24Z"
        fill="#34A853"
      />
    </svg>
  );
}
