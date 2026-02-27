import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { asc, eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, ticketMessage } from "@/lib/db/schema";

const CHAT_ACTIVE_STATUSES = ["open", "in_progress"];
const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// GET /api/tickets/[id]/messages — list all messages for a ticket
// ---------------------------------------------------------------------------
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
    columns: { id: true, userId: true },
  });

  if (!row) {
    return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
  }
  if (row.userId !== session.user.id) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const messages = await db
    .select()
    .from(ticketMessage)
    .where(eq(ticketMessage.ticketId, id))
    .orderBy(asc(ticketMessage.createdAt));

  return NextResponse.json(messages);
}

// ---------------------------------------------------------------------------
// POST /api/tickets/[id]/messages — send a customer message and get AI reply
// ---------------------------------------------------------------------------
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  // Fetch the ticket with ownership check
  const row = await db.query.ticket.findFirst({
    where: eq(ticket.id, id),
    columns: {
      id: true,
      userId: true,
      description: true,
      category: true,
      urgency: true,
      status: true,
    },
    with: {
      images: { columns: { analysisText: true } },
    },
  });

  if (!row) {
    return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
  }
  if (row.userId !== session.user.id) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
  if (!CHAT_ACTIVE_STATUSES.includes(row.status)) {
    return NextResponse.json(
      { error: "Chat is only available for open or in-progress tickets." },
      { status: 409 },
    );
  }

  // Parse body
  let body: { content?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  const content = (body.content ?? "").trim();
  if (!content || content.length > 1000) {
    return NextResponse.json(
      { error: "Message must be between 1 and 1000 characters." },
      { status: 400 },
    );
  }

  // Fetch full conversation history from DB
  const history = await db
    .select()
    .from(ticketMessage)
    .where(eq(ticketMessage.ticketId, id))
    .orderBy(asc(ticketMessage.createdAt));

  // Insert customer message
  const now = new Date();
  const customerMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "customer" as const,
    content,
    createdAt: now,
  };
  await db.insert(ticketMessage).values(customerMsg);

  // Call FastAPI /chat
  let aiReply = "";
  try {
    const chatPayload = {
      ticket_description: row.description,
      ticket_category: row.category ?? null,
      ticket_urgency: row.urgency ?? null,
      conversation_history: history.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      user_message: content,
      image_analyses: (row.images ?? [])
        .map((img) => img.analysisText)
        .filter((a): a is string => Boolean(a)),
    };

    const aiRes = await fetch(`${FASTAPI_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(chatPayload),
      signal: AbortSignal.timeout(30_000),
    });

    if (aiRes.ok) {
      const aiData = await aiRes.json();
      aiReply = aiData.reply ?? "";
    } else {
      const errText = await aiRes.text().catch(() => "");
      console.error(`FastAPI /chat error ${aiRes.status}: ${errText}`);
      aiReply =
        "I'm sorry, I'm having trouble responding right now. Please try again or contact support@company.com.";
    }
  } catch (err) {
    console.error("FastAPI /chat fetch failed:", err);
    aiReply =
      "I'm sorry, I'm having trouble responding right now. Please try again or contact support@company.com.";
  }

  // Insert AI message
  const aiMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "ai" as const,
    content: aiReply,
    createdAt: new Date(),
  };
  await db.insert(ticketMessage).values(aiMsg);

  return NextResponse.json({ customerMessage: customerMsg, aiMessage: aiMsg });
}
