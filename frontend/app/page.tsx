"use client";

import { useSession } from "@/lib/auth-client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  PlusCircle,
  TicketCheck,
  Zap,
  ShieldCheck,
  MessageSquare,
  ArrowRight,
  Clock,
  Bot,
} from "lucide-react";

export default function Home() {
  const { data: session, isPending } = useSession();

  if (isPending) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (session) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-12 sm:px-6 space-y-10">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">
            Welcome back, {session.user.name?.split(" ")[0]}
          </h1>
          <p className="text-muted-foreground text-sm">How can we help you today?</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/tickets/new" className="group block">
            <Card className="h-full transition-all hover:border-primary/50 hover:shadow-md">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <PlusCircle className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold">Submit a Request</p>
                  <p className="text-sm text-muted-foreground">Describe your issue and attach images</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
              </CardContent>
            </Card>
          </Link>

          <Link href="/tickets" className="group block">
            <Card className="h-full transition-all hover:border-primary/50 hover:shadow-md">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <TicketCheck className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold">My Tickets</p>
                  <p className="text-sm text-muted-foreground">View status and updates on your requests</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
              </CardContent>
            </Card>
          </Link>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-4">How it works</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { step: "1", title: "Submit your request", desc: "Fill in a title, describe your issue, and attach any relevant screenshots.", icon: <MessageSquare className="h-5 w-5" /> },
              { step: "2", title: "AI analysis", desc: "Our system instantly categorises and prioritises your ticket using ML models.", icon: <Bot className="h-5 w-5" /> },
              { step: "3", title: "Get a response", desc: "You will receive an AI-drafted reply and a support agent will follow up.", icon: <Clock className="h-5 w-5" /> },
            ].map((item) => (
              <div key={item.step} className="flex gap-4 rounded-lg border p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-bold">{item.step}</div>
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  return (
    <div className="flex flex-col">
      <section className="mx-auto w-full max-w-5xl px-4 py-20 sm:px-6 text-center space-y-6">
        <Badge variant="secondary" className="text-xs">AI-powered support routing</Badge>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          Support that actually <span className="text-primary">understands you</span>
        </h1>
        <p className="mx-auto max-w-xl text-base text-muted-foreground">
          Submit your issue, upload screenshots, and let our AI instantly route your request to the right team.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button size="lg" asChild>
            <Link href="/login">Get started free <ArrowRight className="ml-2 h-4 w-4" /></Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </section>

      <section className="border-t bg-muted/30">
        <div className="mx-auto w-full max-w-5xl px-4 py-16 sm:px-6">
          <h2 className="text-center text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-10">Why SupportDesk?</h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              { icon: <Zap className="h-6 w-6 text-primary" />, title: "Instant AI routing", desc: "Every ticket is automatically classified and prioritised the moment it is submitted." },
              { icon: <TicketCheck className="h-6 w-6 text-primary" />, title: "Track every request", desc: "See real-time status updates on all your open and resolved tickets in one place." },
              { icon: <ShieldCheck className="h-6 w-6 text-primary" />, title: "Secure and private", desc: "Sign in with Google. Your data is stored in encrypted Neon PostgreSQL, always safe." },
            ].map((f) => (
              <Card key={f.title}>
                <CardHeader className="pb-3">
                  <div className="mb-1">{f.icon}</div>
                  <CardTitle className="text-base">{f.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-5xl px-4 py-16 sm:px-6 text-center space-y-4">
        <h2 className="text-2xl font-bold">Ready to get help?</h2>
        <p className="text-muted-foreground text-sm">Sign in with your Google account. It takes less than 10 seconds.</p>
        <Button size="lg" asChild>
          <Link href="/login">Sign in with Google <ArrowRight className="ml-2 h-4 w-4" /></Link>
        </Button>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex h-12 max-w-5xl items-center justify-between px-6">
          <p className="text-xs text-muted-foreground">2026 SupportDesk. Powered by Next.js, Better Auth and Neon.</p>
        </div>
      </footer>
    </div>
  );
}
