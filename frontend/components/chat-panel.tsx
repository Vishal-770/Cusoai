"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Send,
  Lock,
  Copy,
  Check,
  Sparkles,
  Paperclip,
  X,
  ImageIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────

type Message = {
  id: string;
  role: "customer" | "ai";
  content: string;
  imageUrl?: string | null;
  createdAt: string;
};

type Group = { date: string; messages: Message[] };

interface ChatPanelProps {
  ticketId: string;
  ticketStatus: string;
  userName?: string;
  fullPage?: boolean;
}

const ACTIVE_STATUSES = ["open", "in_progress"];

// ── Markdown renderer ──────────────────────────────────────────────────────

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*\n]+\*\*|\*[^*\n]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**"))
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    if (part.startsWith("*") && part.endsWith("*"))
      return <em key={i}>{part.slice(1, -1)}</em>;
    return <span key={i}>{part}</span>;
  });
}

function MarkdownContent({ text }: { text: string }) {
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (/^[-*•]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*•]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*•]\s/, ""));
        i++;
      }
      nodes.push(
        <ul key={`ul-${i}`} className="my-1.5 ml-4 list-disc space-y-0.5">
          {items.map((item, j) => (
            <li key={j} className="text-sm leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>,
      );
      continue;
    }
    if (/^\d+\.\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s/, ""));
        i++;
      }
      nodes.push(
        <ol key={`ol-${i}`} className="my-1.5 ml-4 list-decimal space-y-0.5">
          {items.map((item, j) => (
            <li key={j} className="text-sm leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ol>,
      );
      continue;
    }
    if (line.trim() === "") {
      nodes.push(<div key={`sp-${i}`} className="h-1" />);
      i++;
      continue;
    }
    nodes.push(
      <p key={`p-${i}`} className="text-sm leading-relaxed">
        {renderInline(line)}
      </p>,
    );
    i++;
  }
  return <>{nodes}</>;
}

// ── Timestamp helpers ──────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400)
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (diff < 172800)
    return `Yesterday · ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  return (
    date.toLocaleDateString([], { month: "short", day: "numeric" }) +
    " · " +
    date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );
}

function getDateLabel(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const today = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const msgDay = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  if (msgDay === today) return "Today";
  if (msgDay === today - 86_400_000) return "Yesterday";
  return d.toLocaleDateString([], {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

// ── Copy button ────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="opacity-0 group-hover/msg:opacity-100 transition-opacity p-1 rounded hover:bg-black/10 dark:hover:bg-white/10"
      title="Copy message"
    >
      {copied ? (
        <Check className="h-3 w-3 text-emerald-500" />
      ) : (
        <Copy className="h-3 w-3 text-muted-foreground" />
      )}
    </button>
  );
}

// ── Typing dots ────────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="flex items-end gap-2.5">
      <Avatar className="h-7 w-7 mb-[1.35rem] shrink-0">
        <AvatarFallback className="bg-primary/10 text-primary">
          <Bot className="h-3.5 w-3.5" />
        </AvatarFallback>
      </Avatar>
      <div className="flex gap-1 rounded-2xl rounded-bl-sm bg-muted/70 border border-border/50 px-4 py-3.5 mb-5">
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:160ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:320ms]" />
      </div>
    </div>
  );
}

// ── Loading skeleton ───────────────────────────────────────────────────────

function MessageSkeleton() {
  return (
    <div className="space-y-4 px-4 py-5">
      {[
        { side: "left", w: "65%" },
        { side: "right", w: "45%" },
        { side: "left", w: "72%" },
        { side: "right", w: "38%" },
      ].map(({ side, w }, n) => (
        <div
          key={n}
          className={cn(
            "flex items-end gap-2.5",
            side === "right" ? "flex-row-reverse" : "flex-row",
          )}
        >
          <div className="h-7 w-7 rounded-full bg-muted animate-pulse shrink-0" />
          <div
            className="h-10 rounded-2xl bg-muted animate-pulse"
            style={{ width: w, maxWidth: 300 }}
          />
        </div>
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export function ChatPanel({
  ticketId,
  ticketStatus,
  userName = "",
  fullPage = false,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [pendingImage, setPendingImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isAtBottomRef = useRef(true);

  const isActive = ACTIVE_STATUSES.includes(ticketStatus);
  const userInitial = userName ? userName[0].toUpperCase() : "U";

  // Refresh timestamps every 60 s (triggers re-render → formatTimestamp updates)
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 60_000);
    return () => clearInterval(id);
  }, []);

  // Load history on mount
  useEffect(() => {
    setLoading(true);
    setLoadError(null);
    fetch(`/api/tickets/${ticketId}/messages`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load chat history");
        return r.json();
      })
      .then((data: Message[]) => {
        setMessages(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setLoadError(e instanceof Error ? e.message : "Load failed");
        setLoading(false);
      });
  }, [ticketId]);

  // Scroll to bottom after history loads (instant, no animation)
  useEffect(() => {
    if (!loading) {
      const el = containerRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, [loading]);

  // Smart auto-scroll: follow bottom only when user is already at bottom
  useEffect(() => {
    if (isAtBottomRef.current) {
      containerRef.current?.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, sending]);

  function handleScroll() {
    const el = containerRef.current;
    if (!el) return;
    isAtBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }

  function growTextarea() {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 144)}px`;
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset input so same file can be re-selected
    e.target.value = "";
    if (!file.type.startsWith("image/")) {
      setSendError("Only image files are allowed.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setSendError("Image must be under 10 MB.");
      return;
    }
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setPendingImage(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function clearPendingImage() {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setPendingImage(null);
    setImagePreview(null);
  }

  async function handleSend() {
    const content = input.trim();
    const imageToSend = pendingImage;
    const previewUrl = imagePreview;
    if ((!content && !imageToSend) || sending) return;
    setSendError(null);
    const tempId = `temp-${Date.now()}`;
    const optimistic: Message = {
      id: tempId,
      role: "customer",
      content: content || "I've attached an image.",
      imageUrl: previewUrl,
      createdAt: new Date().toISOString(),
    };

    isAtBottomRef.current = true;
    setMessages((prev) => [...prev, optimistic]);
    setInput("");
    setPendingImage(null);
    setImagePreview(null);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setSending(true);

    try {
      let res: Response;
      if (imageToSend) {
        const fd = new FormData();
        fd.append("image", imageToSend);
        if (content) fd.append("content", content);
        res = await fetch(`/api/tickets/${ticketId}/messages/image`, {
          method: "POST",
          body: fd,
        });
      } else {
        res = await fetch(`/api/tickets/${ticketId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        });
      }
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(err.error ?? "Failed to send message");
      }
      const { customerMessage, aiMessage } = (await res.json()) as {
        customerMessage: Message;
        aiMessage: Message;
      };
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempId),
        customerMessage,
        aiMessage,
      ]);
    } catch (e: unknown) {
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setInput(content);
      if (imageToSend) {
        setPendingImage(imageToSend);
        setImagePreview(previewUrl);
      }
      setSendError(
        e instanceof Error ? e.message : "Something went wrong. Try again.",
      );
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // Group messages by calendar day
  const groups = messages.reduce<Group[]>((acc, msg) => {
    const label = getDateLabel(msg.createdAt);
    const last = acc[acc.length - 1];
    if (last && last.date === label) last.messages.push(msg);
    else acc.push({ date: label, messages: [msg] });
    return acc;
  }, []);

  return (
    <Card
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border shadow-sm",
        fullPage && "h-full",
      )}
      data-tick={tick}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <CardHeader className="flex-row items-center gap-3 space-y-0 px-4 py-3 bg-muted/20 border-b">
        <div className="relative shrink-0">
          <Avatar className="h-9 w-9">
            <AvatarFallback className="bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <span
            className={cn(
              "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-card",
              isActive ? "bg-emerald-500" : "bg-muted-foreground/40",
            )}
          />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold leading-tight">
            Support Assistant
          </p>
          <p className="text-[11px] text-muted-foreground">
            {isActive
              ? "AI-powered · Backed by our policies"
              : "Conversation closed"}
          </p>
        </div>
        {!isActive && (
          <Badge variant="secondary" className="gap-1.5 text-[11px] capitalize">
            <Lock className="h-2.5 w-2.5" />
            {ticketStatus.replace("_", " ")}
          </Badge>
        )}
      </CardHeader>

      {/* ── Messages ────────────────────────────────────────────── */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className={cn(
          "overflow-y-auto px-4 py-5 scroll-smooth",
          fullPage ? "flex-1" : "min-h-96 max-h-128",
        )}
      >
        {/* Skeleton */}
        {loading && <MessageSkeleton />}

        {/* Load error */}
        {!loading && loadError && (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
            <p className="text-sm text-destructive">{loadError}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Reload
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !loadError && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-semibold">
                {isActive ? "How can I help?" : "No messages yet"}
              </p>
              <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
                {isActive
                  ? "Ask anything about your issue and I'll answer using our support policies."
                  : "This ticket is closed. No further messages can be sent."}
              </p>
            </div>
          </div>
        )}

        {/* Grouped message list */}
        {!loading && !loadError && (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group.date} className="space-y-4">
                {/* Date separator */}
                <div className="flex items-center gap-3 py-1">
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-[10px] uppercase tracking-widest font-medium text-muted-foreground/70 px-2 shrink-0">
                    {group.date}
                  </span>
                  <div className="flex-1 h-px bg-border" />
                </div>

                {group.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      "flex items-end gap-2.5 group/msg",
                      msg.role === "customer" ? "flex-row-reverse" : "flex-row",
                    )}
                  >
                    {/* Avatar */}
                    {msg.role === "ai" ? (
                      <Avatar className="h-7 w-7 mb-[1.35rem] shrink-0">
                        <AvatarFallback className="bg-primary/10 text-primary">
                          <Bot className="h-3.5 w-3.5" />
                        </AvatarFallback>
                      </Avatar>
                    ) : (
                      <Avatar className="h-7 w-7 mb-[1.35rem] shrink-0">
                        <AvatarFallback className="bg-primary text-primary-foreground text-xs font-semibold">
                          {userInitial}
                        </AvatarFallback>
                      </Avatar>
                    )}

                    {/* Bubble + meta */}
                    <div
                      className={cn(
                        "flex flex-col gap-1 max-w-[76%]",
                        msg.role === "customer" ? "items-end" : "items-start",
                      )}
                    >
                      <div
                        className={cn(
                          "rounded-2xl overflow-hidden",
                          msg.role === "customer"
                            ? "bg-primary text-primary-foreground rounded-br-sm"
                            : "bg-muted/70 border border-border/50 text-foreground rounded-bl-sm",
                          msg.id.startsWith("temp-") && "opacity-60",
                        )}
                      >
                        {msg.imageUrl && (
                          <a
                            href={msg.imageUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block"
                          >
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={msg.imageUrl}
                              alt="Attached image"
                              className="max-w-xs max-h-56 w-full object-cover"
                            />
                          </a>
                        )}
                        <div className="px-4 py-2.5">
                          {msg.role === "ai" ? (
                            <MarkdownContent text={msg.content} />
                          ) : (
                            <p className="text-sm leading-relaxed">
                              {msg.content}
                            </p>
                          )}
                        </div>
                      </div>
                      <div
                        className={cn(
                          "flex items-center gap-1",
                          msg.role === "customer"
                            ? "flex-row-reverse"
                            : "flex-row",
                        )}
                      >
                        <span className="text-[10px] text-muted-foreground/70">
                          {msg.id.startsWith("temp-")
                            ? "Sending…"
                            : formatTimestamp(msg.createdAt)}
                        </span>
                        {!msg.id.startsWith("temp-") && (
                          <CopyButton text={msg.content} />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}

            {/* Typing indicator */}
            {sending && <TypingDots />}
          </div>
        )}
      </div>

      {/* ── Send error ──────────────────────────────────────────── */}
      {sendError && (
        <div className="flex items-center justify-between gap-2 px-4 py-2 text-xs text-destructive bg-destructive/10 border-t border-destructive/20">
          <span>{sendError}</span>
          <button
            onClick={() => setSendError(null)}
            className="shrink-0 font-medium hover:underline underline-offset-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── Input area ──────────────────────────────────────────── */}
      <div className="border-t bg-background/80 backdrop-blur-sm">
        {isActive ? (
          <div className="p-3 flex flex-col gap-1.5">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleImageSelect}
            />

            {/* Image preview strip */}
            {imagePreview && (
              <div className="relative w-fit">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imagePreview}
                  alt="Image to send"
                  className="h-20 w-20 rounded-lg object-cover border border-border"
                />
                <button
                  onClick={clearPendingImage}
                  className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center shadow-sm hover:opacity-90"
                  aria-label="Remove image"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            <div className="flex items-end gap-2 rounded-xl border border-input bg-muted/20 px-3 py-2 focus-within:border-ring focus-within:ring-1 focus-within:ring-ring transition-all">
              {/* Image attach button */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={sending}
                className="shrink-0 p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors disabled:cursor-not-allowed"
                aria-label="Attach image"
                title="Attach image"
              >
                {pendingImage ? (
                  <ImageIcon className="h-4 w-4 text-primary" />
                ) : (
                  <Paperclip className="h-4 w-4" />
                )}
              </button>

              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  growTextarea();
                }}
                onKeyDown={handleKeyDown}
                disabled={sending}
                placeholder={
                  pendingImage
                    ? "Add a caption… (optional)"
                    : "Ask about your issue…"
                }
                rows={1}
                maxLength={1000}
                className="flex-1 resize-none bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed leading-6 min-h-6 max-h-36"
              />
              <Button
                size="icon"
                className="h-8 w-8 shrink-0 rounded-lg"
                disabled={(!input.trim() && !pendingImage) || sending}
                onClick={handleSend}
                aria-label="Send"
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </div>
            <div className="flex items-center justify-between px-0.5">
              <p className="text-[10px] text-muted-foreground/70">
                Enter ↵ to send · Shift+Enter for new line · 📎 attach image
              </p>
              <p
                className={cn(
                  "text-[10px]",
                  input.length > 900
                    ? "text-destructive"
                    : "text-muted-foreground/70",
                )}
              >
                {input.length}/1000
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2.5 px-4 py-4 text-sm text-muted-foreground">
            <Lock className="h-3.5 w-3.5 shrink-0" />
            Chat is closed for{" "}
            <span className="font-medium capitalize">
              {ticketStatus.replace("_", " ")}
            </span>{" "}
            tickets.
          </div>
        )}
      </div>
    </Card>
  );
}
