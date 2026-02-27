"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import { ArrowLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ChatPanel } from "@/components/chat-panel";
import { useSession } from "@/lib/auth-client";

type TicketSummary = {
  id: string;
  title: string;
  description: string;
  category: string | null;
  urgency: string | null;
  status: string;
  createdAt: string;
};

const urgencyVariant: Record<
  string,
  "destructive" | "secondary" | "outline" | "default"
> = {
  Critical: "destructive",
  High: "destructive",
  Medium: "secondary",
  Low: "outline",
};

const statusVariant: Record<string, "default" | "secondary" | "outline"> = {
  open: "default",
  in_progress: "secondary",
  resolved: "outline",
  closed: "outline",
};

export default function TicketChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: session } = useSession();
  const [ticket, setTicket] = useState<TicketSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/tickets/${id}`)
      .then((r) => {
        if (!r.ok)
          throw new Error(
            r.status === 404 ? "Ticket not found" : "Failed to load",
          );
        return r.json();
      })
      .then((data) => {
        setTicket(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load");
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
        <p className="text-sm text-destructive">
          {error ?? "Ticket not found"}
        </p>
        <Button variant="outline" asChild>
          <Link href="/tickets">Back to tickets</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
      {/* ── Top bar ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 border-b px-4 py-3 shrink-0 bg-background/80 backdrop-blur-sm">
        <Link
          href={`/tickets/${id}`}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Link>
        <Separator orientation="vertical" className="h-4 shrink-0" />
        <p className="text-sm font-medium truncate flex-1 min-w-0">
          {ticket.title}
        </p>
        <Badge
          variant={statusVariant[ticket.status] ?? "default"}
          className="shrink-0 capitalize"
        >
          {ticket.status.replace("_", " ")}
        </Badge>
      </div>

      {/* ── Body ────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Sidebar — ticket context (desktop only) */}
        <aside className="hidden lg:flex flex-col w-72 shrink-0 border-r overflow-y-auto bg-muted/20">
          <div className="p-5 space-y-5">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Category &amp; Urgency
              </p>
              <div className="flex flex-wrap gap-1.5">
                {ticket.category ? (
                  <Badge variant="secondary">{ticket.category}</Badge>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    Uncategorized
                  </span>
                )}
                {ticket.urgency && (
                  <Badge variant={urgencyVariant[ticket.urgency] ?? "outline"}>
                    {ticket.urgency} urgency
                  </Badge>
                )}
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Issue Description
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {ticket.description}
              </p>
            </div>

            <Separator />

            <p className="text-[11px] text-muted-foreground">
              Submitted {new Date(ticket.createdAt).toLocaleString()}
            </p>
          </div>
        </aside>

        {/* Chat area */}
        <div className="flex flex-1 min-h-0 flex-col p-4 lg:p-5">
          <ChatPanel
            ticketId={id}
            ticketStatus={ticket.status}
            userName={session?.user?.name ?? ""}
            fullPage
          />
        </div>
      </div>
    </div>
  );
}
