import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { asc, eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { ticket, ticketMessage } from "@/lib/db/schema";
import { uploadAudio } from "@/lib/cloudinary";

const CHAT_ACTIVE_STATUSES = ["open", "in_progress"];
const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";
const GEMINI_KEY = process.env.GEMINI_API_KEY!;
const GEMINI_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";
const GEMINI_TTS_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent";

// ── Gemini helper ───────────────────────────────────────────────────────────
async function geminiGenerate(prompt: string): Promise<string> {
  const res = await fetch(`${GEMINI_URL}?key=${GEMINI_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
    }),
    signal: AbortSignal.timeout(20_000),
  });
  if (!res.ok) throw new Error(`Gemini error ${res.status}`);
  const data = (await res.json()) as {
    candidates?: { content?: { parts?: { text?: string }[] } }[];
  };
  return data.candidates?.[0]?.content?.parts?.[0]?.text?.trim() ?? "";
}

// ── Gemini STT (audio transcription) ──────────────────────────────────────
async function transcribeAudio(
  audioBuffer: Buffer,
  mimeType: string,
): Promise<{ text: string; languageCode: string }> {
  const base64Audio = audioBuffer.toString("base64");

  const res = await fetch(`${GEMINI_URL}?key=${GEMINI_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [
        {
          parts: [
            {
              inline_data: {
                mime_type: mimeType,
                data: base64Audio,
              },
            },
            {
              text: 'Transcribe this audio exactly. Return a JSON object with two fields: "text" (the full transcription) and "language_code" (the BCP-47 code of the detected language, e.g. "en", "hi", "fr", "es"). Return ONLY the raw JSON, no markdown, no code fences.',
            },
          ],
        },
      ],
    }),
    signal: AbortSignal.timeout(30_000),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "");
    throw new Error(`Gemini STT failed (${res.status}): ${err}`);
  }

  const data = (await res.json()) as {
    candidates?: { content?: { parts?: { text?: string }[] } }[];
  };
  const raw = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim() ?? "";

  try {
    // Strip any accidental markdown fences before parsing
    const cleaned = raw.replace(/^```[^\n]*\n?|```$/g, "").trim();
    const parsed = JSON.parse(cleaned) as {
      text?: string;
      language_code?: string;
    };
    return {
      text: parsed.text?.trim() ?? "",
      languageCode: (parsed.language_code ?? "en").toLowerCase(),
    };
  } catch {
    // If JSON parsing fails, treat the whole response as plain English text
    return { text: raw, languageCode: "en" };
  }
}

// ── Gemini translation helpers ──────────────────────────────────────────────
async function translateToEnglish(text: string): Promise<string> {
  return geminiGenerate(
    `Translate the following customer support message to English. Return ONLY the translated text, no explanation, no quotes.\n\n${text}`,
  );
}

async function translateFromEnglish(
  text: string,
  targetLanguageCode: string,
): Promise<string> {
  return geminiGenerate(
    `Translate the following customer support reply to the language with BCP-47 code "${targetLanguageCode}". Return ONLY the translated text, no explanation, no quotes.\n\n${text}`,
  );
}

// ── Gemini TTS ─────────────────────────────────────────────────────────────
function pcmToWav(pcm: Buffer): Buffer {
  const sampleRate = 24000;
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataSize = pcm.length;
  const header = Buffer.allocUnsafe(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + dataSize, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20); // PCM
  header.writeUInt16LE(numChannels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bitsPerSample, 34);
  header.write("data", 36);
  header.writeUInt32LE(dataSize, 40);
  return Buffer.concat([header, pcm]);
}

async function synthesizeSpeech(text: string): Promise<Buffer> {
  const plainText = text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/^[-*•]\s/gm, "")
    .replace(/^\d+\.\s/gm, "")
    .trim();

  const res = await fetch(`${GEMINI_TTS_URL}?key=${GEMINI_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: plainText.slice(0, 2500) }] }],
      generationConfig: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: "Aoede" },
          },
        },
      },
    }),
    signal: AbortSignal.timeout(40_000),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "");
    throw new Error(`Gemini TTS failed (${res.status}): ${err}`);
  }

  const data = (await res.json()) as {
    candidates?: {
      content?: {
        parts?: { inlineData?: { data?: string; mimeType?: string } }[];
      };
    }[];
  };

  const base64Audio =
    data.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) throw new Error("Gemini TTS returned no audio data");

  return pcmToWav(Buffer.from(base64Audio, "base64"));
}

// ── Route handler ───────────────────────────────────────────────────────────
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
    with: { images: { columns: { analysisText: true } } },
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

  const audioFile = formData.get("audio") as File | null;
  if (!audioFile) {
    return NextResponse.json(
      { error: "An audio file is required." },
      { status: 400 },
    );
  }
  if (audioFile.size > 25 * 1024 * 1024) {
    return NextResponse.json(
      { error: "Audio must be under 25 MB." },
      { status: 400 },
    );
  }

  const audioBuffer = Buffer.from(await audioFile.arrayBuffer());
  const mimeType = audioFile.type || "audio/webm";

  // 1. Upload user recording to Cloudinary
  let recordingUrl: string;
  try {
    const upload = await uploadAudio(audioBuffer, "support-tickets/voice");
    recordingUrl = upload.url;
  } catch {
    return NextResponse.json(
      { error: "Audio upload failed. Please try again." },
      { status: 502 },
    );
  }

  // 2. STT — native transcript + detected language
  let nativeTranscript: string;
  let languageCode: string;
  try {
    const stt = await transcribeAudio(audioBuffer, mimeType);
    nativeTranscript = stt.text;
    languageCode = stt.languageCode;
  } catch (err) {
    console.error("STT failed:", err);
    return NextResponse.json(
      {
        error: "Speech recognition failed. Please speak clearly and try again.",
      },
      { status: 502 },
    );
  }

  if (!nativeTranscript) {
    return NextResponse.json(
      {
        error:
          "Could not transcribe audio. Please speak clearly and try again.",
      },
      { status: 422 },
    );
  }

  // 3. Translate to English for AI processing (if not English)
  const isEnglish = languageCode.startsWith("en");
  let englishTranscript: string;
  try {
    englishTranscript = isEnglish
      ? nativeTranscript
      : await translateToEnglish(nativeTranscript);
  } catch {
    englishTranscript = nativeTranscript; // fallback: pass as-is
  }

  // 4. Fetch history and call FastAPI /chat in English
  const history = await db
    .select()
    .from(ticketMessage)
    .where(eq(ticketMessage.ticketId, id))
    .orderBy(asc(ticketMessage.createdAt));

  const imageAnalyses = (row.images ?? [])
    .map((img) => img.analysisText)
    .filter((a): a is string => Boolean(a));

  let englishReply = "";
  try {
    const chatPayload = {
      ticket_description: row.description,
      ticket_category: row.category ?? null,
      ticket_urgency: row.urgency ?? null,
      conversation_history: history.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      user_message: englishTranscript,
      image_analyses: imageAnalyses,
    };

    const aiRes = await fetch(`${FASTAPI_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(chatPayload),
      signal: AbortSignal.timeout(30_000),
    });

    if (aiRes.ok) {
      const aiData = (await aiRes.json()) as { reply?: string };
      englishReply = aiData.reply ?? "";
    } else {
      englishReply =
        "I'm sorry, I'm having trouble responding right now. Please try again or contact support@company.com.";
    }
  } catch {
    englishReply =
      "I'm sorry, I'm having trouble responding right now. Please try again or contact support@company.com.";
  }

  // 5. Translate AI reply to user's language if needed
  let nativeReply: string;
  try {
    nativeReply = isEnglish
      ? englishReply
      : await translateFromEnglish(englishReply, languageCode);
  } catch {
    nativeReply = englishReply;
  }

  // 6. TTS — synthesize in user's language (non-fatal if fails)
  let ttsUrl: string | null = null;
  try {
    const ttsBuffer = await synthesizeSpeech(nativeReply);
    const ttsUpload = await uploadAudio(ttsBuffer, "support-tickets/voice-tts");
    ttsUrl = ttsUpload.url;
  } catch (err) {
    console.error("TTS failed (non-fatal):", err);
  }

  // 7. Persist both messages
  const now = new Date();
  const customerMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "customer" as const,
    content: englishTranscript,
    nativeContent: isEnglish ? null : nativeTranscript,
    imageUrl: null,
    voiceUrl: recordingUrl,
    createdAt: now,
  };
  await db.insert(ticketMessage).values(customerMsg);

  const aiMsg = {
    id: crypto.randomUUID(),
    ticketId: id,
    role: "ai" as const,
    content: englishReply,
    nativeContent: isEnglish ? null : nativeReply,
    imageUrl: null,
    voiceUrl: ttsUrl,
    createdAt: new Date(),
  };
  await db.insert(ticketMessage).values(aiMsg);

  return NextResponse.json({
    customerMessage: customerMsg,
    aiMessage: aiMsg,
    detectedLanguage: languageCode,
    transcript: nativeTranscript,
  });
}
