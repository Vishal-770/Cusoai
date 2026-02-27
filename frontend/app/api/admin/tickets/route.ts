import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { desc, eq, and } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, user } from "@/lib/db/schema";

const PAGE_SIZE = 20;

export async function GET(request: NextRequest) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Role check via DB
  const dbUser = await db.query.user.findFirst({
    where: eq(user.id, session.user.id),
    columns: { role: true },
  });
  if (!dbUser || !["agent", "admin"].includes(dbUser.role)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { searchParams } = request.nextUrl;
  const page = Math.max(1, Number(searchParams.get("page") ?? "1"));
  const statusFilter = searchParams.get("status");
  const urgencyFilter = searchParams.get("urgency");
  const categoryFilter = searchParams.get("category");

  const conditions = [];
  if (statusFilter) conditions.push(eq(ticket.status, statusFilter));
  if (urgencyFilter) conditions.push(eq(ticket.urgency, urgencyFilter));
  if (categoryFilter) conditions.push(eq(ticket.category, categoryFilter));

  const tickets = await db.query.ticket.findMany({
    where: conditions.length > 0 ? and(...conditions) : undefined,
    with: {
      user: { columns: { id: true, name: true, email: true } },
      images: { columns: { id: true } },
    },
    orderBy: [desc(ticket.createdAt)],
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  });

  return NextResponse.json({ tickets, page, pageSize: PAGE_SIZE });
}
