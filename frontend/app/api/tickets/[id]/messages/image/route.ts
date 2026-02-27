import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { asc, eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, ticketMessage, ticketImage } from "@/lib/db/schema";
import { uploadImage } from "@/lib/cloudinary";

const CHAT_ACTIVE_STATUSES = ["open", "in_progress"];
const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";
const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

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

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: "Invalid form data" }, { status: 400 });
  }

  const imageFile = formData.get("image") as File | null;
  const content = ((formData.get("content") as string | null) ?? "").trim();

  if (!imageFile || !imageFile.type.startsWith("image/")) {
    return NextResponse.json(
      { error: "A valid image file is required." },
      { status: 400 },
    );
  }
  if (imageFile.size > 10 * 1024 * 1024) {
    return NextResponse.json(
      { error: "Image must be under 10 MB." },
      { status: 400 },
    );
  }

  const messageContent = content || "I've attached an image.";

  // Upload to Cloudinary
  const buffer = Buffer.from(await imageFile.arrayBuffer());
  let imageUpload: { url: string; publicId: string };
  try {
    imageUpload = await uploadImage(buffer);
  } catch {
    return NextResponse.json(
      { error: "Image upload failed. Please try again." },
      { status: 502 },
    );
  }

  // Analyze via Gemini Vision
  let newAnalysis: string | null = null;
  try {
    const analyzeRes = await fetch(`${FASTAPI_BASE_URL}/analyze_image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_url: imageUpload.url }),
      signal: AbortSignal.timeout(20_000),
    });
    if (analyzeRes.ok) {
      const analyzeData = await analyzeRes.json();
      newAnalysis = (analyzeData.analysis as string | null) ?? null;
    }
  } catch {
    // analysis failure is non-fatal — AI will respond without image context
  }

  // Store as ticketImage record
  const now = new Date();
  await db.insert(ticketImage).values({
    id: crypto.randomUUID(),
    ticketId: id,
    cloudinaryUrl: imageUpload.url,
    cloudinaryPublicId: imageUpload.publicId,
    analysisText: newAnalysis,
    uploadedAt: now,
  });

  // Fetch full conversation history
  const history = await db
    .select()
    .from(ticketMessage)
    .where(eq(ticketMessage.ticketId, id))
    .orderBy(asc(ticketMessage.createdAt));

  // Insert customer message with imageUrl
  const customerMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "customer" as const,
    content: messageContent,
    imageUrl: imageUpload.url,
    createdAt: now,
  };
  await db.insert(ticketMessage).values(customerMsg);

  // Combine existing ticket image analyses + the new one
  const existingAnalyses = (row.images ?? [])
    .map((img) => img.analysisText)
    .filter((a): a is string => Boolean(a));
  const allAnalyses = newAnalysis
    ? [...existingAnalyses, newAnalysis]
    : existingAnalyses;

  // Call FastAPI /chat with image context
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
      user_message: messageContent,
      image_analyses: allAnalyses,
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

  const aiMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "ai" as const,
    content: aiReply,
    imageUrl: null,
    createdAt: new Date(),
  };
  await db.insert(ticketMessage).values(aiMsg);

  return NextResponse.json({ customerMessage: customerMsg, aiMessage: aiMsg });
}
