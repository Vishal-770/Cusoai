"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Ticket, ImageIcon } from "lucide-react";

type TicketRow = {
  id: string;
  title: string;
  category: string | null;
  urgency: string | null;
  status: string;
  createdAt: string;
  images: { id: string; cloudinaryUrl: string }[];
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

export default function TicketsPage() {
  const { data: session, isPending } = useSession();
  const router = useRouter();
  const [tickets, setTickets] = useState<TicketRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isPending) return;
    if (!session) {
      router.push("/login");
      return;
    }
    fetch("/api/tickets")
      .then((r) => r.json())
      .then((data) => {
        setTickets(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load tickets");
        setLoading(false);
      });
  }, [session, isPending, router]);

  if (isPending || loading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-10 sm:px-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My Support Tickets</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {tickets.length} ticket{tickets.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/tickets/new">
            <Plus className="mr-2 h-4 w-4" />
            New Ticket
          </Link>
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {tickets.length === 0 && !error && (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16">
            <Ticket className="h-10 w-10 text-muted-foreground" />
            <p className="text-muted-foreground">No tickets yet</p>
            <Button asChild>
              <Link href="/tickets/new">Submit your first ticket</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {tickets.map((t) => (
          <Link key={t.id} href={`/tickets/${t.id}`} className="block">
            <Card className="transition-colors hover:bg-muted/50">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-4">
                  <CardTitle className="text-base leading-snug">
                    {t.title}
                  </CardTitle>
                  <Badge
                    variant={statusVariant[t.status] ?? "default"}
                    className="shrink-0 capitalize"
                  >
                    {t.status.replace("_", " ")}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-2">
                {t.category && <Badge variant="secondary">{t.category}</Badge>}
                {t.urgency && (
                  <Badge variant={urgencyVariant[t.urgency] ?? "outline"}>
                    {t.urgency}
                  </Badge>
                )}
                {t.images.length > 0 && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground ml-auto">
                    <ImageIcon className="h-3 w-3" />
                    {t.images.length}
                  </span>
                )}
                <span className="text-xs text-muted-foreground ml-auto">
                  {new Date(t.createdAt).toLocaleDateString()}
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
