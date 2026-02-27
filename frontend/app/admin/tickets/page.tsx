"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ImageIcon, Trash2 } from "lucide-react";

type AdminTicket = {
  id: string;
  title: string;
  category: string | null;
  urgency: string | null;
  status: string;
  createdAt: string;
  images: { id: string }[];
  user: { id: string; name: string; email: string };
};

type ApiResponse = {
  tickets: AdminTicket[];
  page: number;
  pageSize: number;
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

const STATUSES = ["", "open", "in_progress", "resolved", "closed"];
const URGENCIES = ["", "Critical", "High", "Medium", "Low"];

export default function AdminTicketsPage() {
  const router = useRouter();
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [urgency, setUrgency] = useState("");
  const [category, setCategory] = useState("");
  const [forbidden, setForbidden] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function handleDelete(id: string) {
    if (!confirm("Delete this ticket? This cannot be undone.")) return;
    setDeleting(id);
    try {
      const res = await fetch(`/api/tickets/${id}`, { method: "DELETE" });
      if (res.ok) {
        setData((prev) =>
          prev
            ? { ...prev, tickets: prev.tickets.filter((t) => t.id !== id) }
            : prev,
        );
      }
    } finally {
      setDeleting(null);
    }
  }

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ page: String(page) });
    if (status) params.set("status", status);
    if (urgency) params.set("urgency", urgency);
    if (category) params.set("category", category);

    fetch(`/api/admin/tickets?${params}`)
      .then((r) => {
        if (r.status === 401) {
          router.push("/login");
          return null;
        }
        if (r.status === 403) {
          if (!cancelled) setForbidden(true);
          return null;
        }
        return r.json();
      })
      .then((d) => {
        if (!cancelled) {
          if (d) setData(d);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, status, urgency, category, router]);

  if (forbidden) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
        <p className="text-lg font-semibold">Access Denied</p>
        <p className="text-sm text-muted-foreground">
          You need agent or admin privileges to view this page.
        </p>
        <Button variant="outline" asChild>
          <Link href="/">Go home</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background">
      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">All Tickets</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Agent and admin view
            </p>
          </div>
        </div>
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s || "All statuses"}
              </option>
            ))}
          </select>
          <select
            value={urgency}
            onChange={(e) => {
              setUrgency(e.target.value);
              setPage(1);
            }}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {URGENCIES.map((u) => (
              <option key={u} value={u}>
                {u || "All urgencies"}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Filter by category…"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        {/* Table */}
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <>
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Title
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Customer
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Urgency
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Files
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Date
                    </th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {data?.tickets.length === 0 && (
                    <tr>
                      <td
                        colSpan={7}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        No tickets found
                      </td>
                    </tr>
                  )}
                  {data?.tickets.map((t) => (
                    <tr
                      key={t.id}
                      className="border-b transition-colors hover:bg-muted/50 cursor-pointer"
                      onClick={() => router.push(`/tickets/${t.id}`)}
                    >
                      <td className="px-4 py-3 max-w-xs truncate font-medium">
                        {t.title}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-xs">
                          <p className="font-medium">{t.user.name}</p>
                          <p className="text-muted-foreground">
                            {t.user.email}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {t.category ? (
                          <Badge variant="secondary">{t.category}</Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {t.urgency ? (
                          <Badge
                            variant={urgencyVariant[t.urgency] ?? "outline"}
                          >
                            {t.urgency}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={statusVariant[t.status] ?? "default"}
                          className="capitalize"
                        >
                          {t.status.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {t.images.length > 0 ? (
                          <span className="flex items-center gap-1 text-muted-foreground">
                            <ImageIcon className="h-3 w-3" />
                            {t.images.length}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                        {new Date(t.createdAt).toLocaleDateString()}
                      </td>
                      <td
                        className="px-4 py-3"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          disabled={deleting === t.id}
                          onClick={() => handleDelete(t.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {data?.page} · {data?.tickets.length ?? 0} results
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={
                    (data?.tickets.length ?? 0) < (data?.pageSize ?? 20)
                  }
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
