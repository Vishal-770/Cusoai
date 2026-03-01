import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, user } from "@/lib/db/schema";
import { z } from "zod";

async function requireAdmin(sessionUserId: string) {
  const dbUser = await db.query.user.findFirst({
    where: eq(user.id, sessionUserId),
    columns: { role: true },
  });
  return dbUser && ["agent", "admin"].includes(dbUser.role);
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  const row = await db.query.ticket.findFirst({
    where: eq(ticket.id, id),
    with: { images: true },
  });

  if (!row) {
    return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
  }

  // Only the owner or an agent/admin may view this ticket
  if (row.userId !== session.user.id) {
    // Check role via DB
    const dbUser = await db.query.user.findFirst({
      where: eq(user.id, session.user.id),
      columns: { role: true },
    });
    if (!dbUser || !["agent", "admin"].includes(dbUser.role)) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
  }

  return NextResponse.json(row);
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const isAdmin = await requireAdmin(session.user.id);
  if (!isAdmin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { id } = await params;

  const row = await db.query.ticket.findFirst({
    where: eq(ticket.id, id),
    columns: { id: true },
  });
  if (!row) {
    return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
  }

  // ticket_image rows are deleted automatically via onDelete: cascade
  await db.delete(ticket).where(eq(ticket.id, id));

  return NextResponse.json({ success: true });
}

// ── PATCH /api/tickets/[id] — admin closes a ticket with a reason ──────────
const closeSchema = z.object({
  reason: z.string().min(1, "Reason is required.").max(1000),
});

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const isAdmin = await requireAdmin(session.user.id);
  if (!isAdmin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const body = await request.json().catch(() => ({}));
  const parsed = closeSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.errors[0]?.message ?? "Invalid request." },
      { status: 400 },
    );
  }

  const { id } = await params;

  const row = await db.query.ticket.findFirst({
    where: eq(ticket.id, id),
    columns: { id: true, status: true },
  });
  if (!row) {
    return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
  }
  if (row.status === "closed") {
    return NextResponse.json(
      { error: "Ticket is already closed." },
      { status: 409 },
    );
  }

  await db
    .update(ticket)
    .set({
      status: "closed",
      closedReason: parsed.data.reason,
      closedAt: new Date(),
      closedBy: session.user.id,
      updatedAt: new Date(),
    })
    .where(eq(ticket.id, id));

  return NextResponse.json({ success: true });
}
