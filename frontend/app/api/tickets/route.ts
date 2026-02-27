import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { desc, eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, ticketImage } from "@/lib/db/schema";
import { uploadImage } from "@/lib/cloudinary";

const MAX_FILES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export async function POST(request: NextRequest) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: "Invalid form data" }, { status: 400 });
  }

  const title = (formData.get("title") as string | null)?.trim() ?? "";
  const description =
    (formData.get("description") as string | null)?.trim() ?? "";
  const files = formData.getAll("images") as File[];

  if (!title) {
    return NextResponse.json({ error: "Title is required" }, { status: 400 });
  }
  if (title.length > 200) {
    return NextResponse.json(
      { error: "Title must be 200 characters or less" },
      { status: 400 },
    );
  }
  if (!description || description.length < 5) {
    return NextResponse.json(
      { error: "Description must be at least 5 characters" },
      { status: 400 },
    );
  }
  if (description.length > 2000) {
    return NextResponse.json(
      { error: "Description must be 2000 characters or less" },
      { status: 400 },
    );
  }
  if (files.length > MAX_FILES) {
    return NextResponse.json(
      { error: `Maximum ${MAX_FILES} images allowed` },
      { status: 400 },
    );
  }
  for (const file of files) {
    if (!file.type.startsWith("image/")) {
      return NextResponse.json(
        { error: "Only image files are allowed" },
        { status: 400 },
      );
    }
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: "Each image must be under 10 MB" },
        { status: 400 },
      );
    }
  }

  // Upload images to Cloudinary in parallel
  const imageUploads = await Promise.all(
    files.map(async (file) => {
      const buffer = Buffer.from(await file.arrayBuffer());
      return uploadImage(buffer);
    }),
  );

  const fastapiUrl = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

  // Analyze images via Gemini Vision in parallel
  const analyses: (string | null)[] = await Promise.all(
    imageUploads.map(async (img) => {
      try {
        const res = await fetch(`${fastapiUrl}/analyze_image`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_url: img.url }),
          signal: AbortSignal.timeout(20_000),
        });
        if (!res.ok) return null;
        const data = await res.json();
        return (data.analysis as string | null) ?? null;
      } catch {
        return null;
      }
    }),
  );

  // Run ML pipeline via FastAPI
  let category: string | null = null;
  let confidence: number | null = null;
  let urgency: string | null = null;
  let urgencyScore: number | null = null;
  let aiDraft: string | null = null;

  try {
    const mlRes = await fetch(`${fastapiUrl}/process_ticket`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description }),
    });
    if (mlRes.ok) {
      const mlData = await mlRes.json();
      category = mlData.category ?? null;
      confidence = mlData.category_confidence ?? null;
      urgency = mlData.urgency ?? null;
      urgencyScore = mlData.urgency_score ?? null;
      aiDraft = mlData.ai_draft_reply ?? null;
    }
  } catch {
    return NextResponse.json(
      {
        error: "Classification service is unavailable. Please try again later.",
      },
      { status: 503 },
    );
  }

  // Persist ticket and images
  const ticketId = crypto.randomUUID();
  const now = new Date();

  await db.insert(ticket).values({
    id: ticketId,
    userId: session.user.id,
    title,
    description,
    category,
    confidence,
    urgency,
    urgencyScore,
    aiDraft,
    status: "open",
    createdAt: now,
    updatedAt: now,
  });

  if (imageUploads.length > 0) {
    await db.insert(ticketImage).values(
      imageUploads.map((img, idx) => ({
        id: crypto.randomUUID(),
        ticketId,
        cloudinaryUrl: img.url,
        cloudinaryPublicId: img.publicId,
        analysisText: analyses[idx] ?? null,
        uploadedAt: now,
      })),
    );
  }

  return NextResponse.json(
    { id: ticketId, category, urgency, status: "open" },
    { status: 201 },
  );
}

export async function GET() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const tickets = await db.query.ticket.findMany({
    where: eq(ticket.userId, session.user.id),
    with: { images: { columns: { id: true, cloudinaryUrl: true } } },
    orderBy: [desc(ticket.createdAt)],
  });

  return NextResponse.json(tickets);
}
