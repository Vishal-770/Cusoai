import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, user } from "@/lib/db/schema";

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
