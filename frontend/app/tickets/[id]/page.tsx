"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  ImageIcon,
  Bot,
  ArrowLeft,
  MessageSquare,
  XCircle,
} from "lucide-react";

type TicketDetail = {
  id: string;
  title: string;
  description: string;
  category: string | null;
  confidence: number | null;
  urgency: string | null;
  urgencyScore: number | null;
  aiDraft: string | null;
  status: string;
  closedReason: string | null;
  closedAt: string | null;
  createdAt: string;
  images: { id: string; cloudinaryUrl: string; cloudinaryPublicId: string }[];
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

export default function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<string | null>(null);

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
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
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
    <>
      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setLightbox(null)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={lightbox}
            alt="attachment"
            className="max-h-[90vh] max-w-[90vw] rounded-md"
          />
        </div>
      )}

      <main className="mx-auto w-full max-w-4xl px-4 py-10 sm:px-6 space-y-6">
        {/* Back breadcrumb */}
        <Link
          href="/tickets"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to My Tickets
        </Link>
        {/* Header */}
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-2xl font-semibold leading-snug">
              {ticket.title}
            </h1>
            <Badge
              variant={statusVariant[ticket.status] ?? "default"}
              className="shrink-0 capitalize"
            >
              {ticket.status.replace("_", " ")}
            </Badge>
          </div>

          <div className="flex flex-wrap gap-2">
            {ticket.category && (
              <Badge variant="secondary">{ticket.category}</Badge>
            )}
            {ticket.urgency && (
              <Badge variant={urgencyVariant[ticket.urgency] ?? "outline"}>
                {ticket.urgency} urgency
              </Badge>
            )}
            {ticket.confidence !== null && (
              <Badge variant="outline">
                {Math.round(ticket.confidence * 100)}% confidence
              </Badge>
            )}
          </div>

          <p className="text-xs text-muted-foreground">
            Submitted {new Date(ticket.createdAt).toLocaleString()}
          </p>
        </div>

        <Separator />

        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Description
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{ticket.description}</p>
          </CardContent>
        </Card>

        {/* Images */}
        {ticket.images.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                <ImageIcon className="h-4 w-4" />
                Attachments ({ticket.images.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {ticket.images.map((img) => (
                  <button
                    key={img.id}
                    type="button"
                    onClick={() => setLightbox(img.cloudinaryUrl)}
                    className="aspect-square overflow-hidden rounded-md border bg-muted hover:opacity-90 transition-opacity"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={img.cloudinaryUrl}
                      alt="attachment"
                      className="h-full w-full object-cover"
                    />
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Draft Reply */}
        {ticket.aiDraft && (
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                <Bot className="h-4 w-4" />
                AI Draft Reply
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap text-muted-foreground">
                {ticket.aiDraft}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Closed Reason */}
        {ticket.status === "closed" && ticket.closedReason && (
          <Card className="border-destructive/30 bg-destructive/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-destructive uppercase tracking-wide">
                <XCircle className="h-4 w-4" />
                Ticket Closed
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-sm whitespace-pre-wrap">
                {ticket.closedReason}
              </p>
              {ticket.closedAt && (
                <p className="text-xs text-muted-foreground">
                  Closed on {new Date(ticket.closedAt).toLocaleString()}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* AI Assistant */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between gap-4 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold">AI Support Assistant</p>
                <p className="text-xs text-muted-foreground">
                  Get instant answers backed by our support policies
                </p>
              </div>
            </div>
            <Button asChild className="shrink-0 gap-2">
              <Link href={`/tickets/${id}/chat`}>
                <MessageSquare className="h-4 w-4" />
                Open Chat
              </Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
