import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Headphones,
  Zap,
  Brain,
  ShieldCheck,
  MessageSquare,
  TicketCheck,
  ArrowRight,
  Bot,
  Tag,
  AlertTriangle,
} from "lucide-react";

const features = [
  {
    icon: <Brain className="h-5 w-5" />,
    title: "AI-Powered Classification",
    description:
      "Every ticket is automatically categorized using a fine-tuned DeBERTa model — billing, technical, account, and more — so it reaches the right team instantly.",
  },
  {
    icon: <AlertTriangle className="h-5 w-5" />,
    title: "Urgency Detection",
    description:
      "Our RoBERTa-based urgency model flags critical issues in real time, ensuring high-priority tickets are never buried in the queue.",
  },
  {
    icon: <Bot className="h-5 w-5" />,
    title: "RAG-Powered Assistant",
    description:
      "An intelligent assistant scans your knowledge base with retrieval-augmented generation to surface instant, accurate answers before a human even needs to respond.",
  },
  {
    icon: <Tag className="h-5 w-5" />,
    title: "Smart Routing",
    description:
      "Tickets flow automatically to the correct specialist the moment they're submitted, cutting average resolution time dramatically.",
  },
  {
    icon: <MessageSquare className="h-5 w-5" />,
    title: "Real-Time Updates",
    description:
      "Customers see live status changes — open, in-progress, resolved — keeping them informed and reducing follow-up noise.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "Secure by Design",
    description:
      "Role-based access control, session-based authentication, and encrypted data storage keep every customer interaction private and safe.",
  },
];

const steps = [
  {
    number: "01",
    title: "Submit a Ticket",
    description:
      "Describe your issue, attach screenshots, and hit submit. Our AI gets to work immediately.",
  },
  {
    number: "02",
    title: "Instant AI Triage",
    description:
      "The ticket is classified, urgency-scored, and routed to the right queue — all within seconds.",
  },
  {
    number: "03",
    title: "Get Resolved Fast",
    description:
      "Agents see a pre-analyzed ticket with full context, so they can focus on solving — not sorting.",
  },
];

const stats = [
  { value: "< 2s", label: "AI triage time" },
  { value: "5+", label: "Ticket categories" },
  { value: "4", label: "Urgency levels" },
  { value: "200k+", label: "Training samples" },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* ── Hero ── */}
      <section className=" py-24 px-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-2xl text-center">
            <Badge
              variant="outline"
              className="mb-6 gap-1.5 px-3 py-1 text-xs font-medium"
            >
              <Zap className="h-3 w-3 text-primary" />
              AI-Powered Support Platform
            </Badge>

            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-foreground leading-[1.15]">
              Faster support,{" "}
              <span className="text-primary">powered by AI</span>
            </h1>

            <p className="mt-5 text-base text-muted-foreground leading-relaxed">
              SupportDesk uses fine-tuned language models and
              retrieval-augmented generation to classify, prioritize, and
              resolve customer tickets faster than any traditional helpdesk.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
              <Button asChild size="lg" className="gap-2">
                <Link href="/tickets/new">
                  Open a Ticket
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="gap-2">
                <Link href="/tickets">
                  <TicketCheck className="h-4 w-4" />
                  My Tickets
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className=" bg-background py-10 px-4 sm:px-6">
        <div className="mx-auto max-w-6xl grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-6 text-center">
          {stats.map((s, i) => (
            <div key={s.label} className="flex flex-col items-center">
              <p className="text-2xl font-bold text-foreground">{s.value}</p>
              <p className="mt-1 text-xs text-muted-foreground uppercase tracking-wide">
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-4 sm:px-6 bg-background">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
              Everything in one intelligent platform
            </h2>
            <p className="mt-2 text-muted-foreground max-w-lg">
              From the moment a ticket lands to the second it&apos;s resolved,
              every step is accelerated by AI.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f) => (
              <Card key={f.title} className=" bg-card">
                <CardContent className="pt-5 pb-5">
                  <div className="flex items-center justify-center h-9 w-9 rounded-lg border bg-background text-primary mb-4">
                    {f.icon}
                  </div>
                  <h3 className="font-semibold text-sm text-foreground mb-1.5">
                    {f.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {f.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* <Separator /> */}

      {/* ── How it works ── */}
      <section className="py-20 px-4 sm:px-6 bg-background">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
              How it works
            </h2>
            <p className="mt-2 text-muted-foreground">
              Three steps from problem to resolution.
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-6">
            {steps.map((step, i) => (
              <div key={step.number} className="flex gap-4">
                <div className="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-lg  text-primary font-bold text-sm">
                  {step.number}
                </div>
                <div>
                  <h3 className="font-semibold text-foreground text-sm mb-1">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* <Separator /> */}

      {/* ── CTA ── */}
      <section className="py-20 px-4 sm:px-6 ">
        <div className="mx-auto max-w-6xl flex flex-col sm:flex-row items-center justify-between gap-8">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 flex h-11 w-11 items-center justify-center rounded-xl  bg-background text-primary">
              <Headphones className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">
                Ready to get help?
              </h2>
              <p className="mt-1 text-sm text-muted-foreground max-w-md">
                Submit a ticket in seconds and let our AI handle triage while
                your support team focuses on what matters.
              </p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 flex-shrink-0">
            <Button asChild size="lg" className="gap-2">
              <Link href="/tickets/new">
                Submit a Ticket
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/login">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className=" py-6 px-4 sm:px-6 bg-background">
        <div className="mx-auto max-w-6xl flex items-center justify-between text-xs text-muted-foreground">
          <span>© {new Date().getFullYear()} SupportDesk</span>
          <span>AI-powered ticket management</span>
        </div>
      </footer>
    </div>
  );
}
