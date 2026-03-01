import { pgTable, text, timestamp, boolean, real } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

export const user = pgTable("user", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  emailVerified: boolean("email_verified").notNull(),
  image: text("image"),
  role: text("role").notNull().default("customer"),
  createdAt: timestamp("created_at").notNull(),
  updatedAt: timestamp("updated_at").notNull(),
});

export const session = pgTable("session", {
  id: text("id").primaryKey(),
  expiresAt: timestamp("expires_at").notNull(),
  token: text("token").notNull().unique(),
  createdAt: timestamp("created_at").notNull(),
  updatedAt: timestamp("updated_at").notNull(),
  ipAddress: text("ip_address"),
  userAgent: text("user_agent"),
  userId: text("user_id")
    .notNull()
    .references(() => user.id),
});

export const account = pgTable("account", {
  id: text("id").primaryKey(),
  accountId: text("account_id").notNull(),
  providerId: text("provider_id").notNull(),
  userId: text("user_id")
    .notNull()
    .references(() => user.id),
  accessToken: text("access_token"),
  refreshToken: text("refresh_token"),
  idToken: text("id_token"),
  accessTokenExpiresAt: timestamp("access_token_expires_at"),
  refreshTokenExpiresAt: timestamp("refresh_token_expires_at"),
  scope: text("scope"),
  password: text("password"),
  createdAt: timestamp("created_at").notNull(),
  updatedAt: timestamp("updated_at").notNull(),
});

export const verification = pgTable("verification", {
  id: text("id").primaryKey(),
  identifier: text("identifier").notNull(),
  value: text("value").notNull(),
  expiresAt: timestamp("expires_at").notNull(),
  createdAt: timestamp("created_at"),
  updatedAt: timestamp("updated_at"),
});

export const ticket = pgTable("ticket", {
  id: text("id").primaryKey(),
  userId: text("user_id")
    .notNull()
    .references(() => user.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  description: text("description").notNull(),
  category: text("category"),
  confidence: real("confidence"),
  urgency: text("urgency"),
  urgencyScore: real("urgency_score"),
  aiDraft: text("ai_draft"),
  status: text("status").notNull().default("open"),
  closedReason: text("closed_reason"),
  closedAt: timestamp("closed_at"),
  closedBy: text("closed_by"),
  createdAt: timestamp("created_at").notNull(),
  updatedAt: timestamp("updated_at").notNull(),
});

export const ticketImage = pgTable("ticket_image", {
  id: text("id").primaryKey(),
  ticketId: text("ticket_id")
    .notNull()
    .references(() => ticket.id, { onDelete: "cascade" }),
  cloudinaryUrl: text("cloudinary_url").notNull(),
  cloudinaryPublicId: text("cloudinary_public_id").notNull(),
  analysisText: text("analysis_text"),
  uploadedAt: timestamp("uploaded_at").notNull(),
});

export const ticketMessage = pgTable("ticket_message", {
  id: text("id").primaryKey(),
  ticketId: text("ticket_id")
    .notNull()
    .references(() => ticket.id, { onDelete: "cascade" }),
  role: text("role").notNull(), // 'customer' | 'ai'
  content: text("content").notNull(), // always English internally
  nativeContent: text("native_content"), // original language text (null if already English)
  imageUrl: text("image_url"),
  voiceUrl: text("voice_url"), // Cloudinary audio URL
  createdAt: timestamp("created_at").notNull(),
});

// Relations
export const userRelations = relations(user, ({ many }) => ({
  tickets: many(ticket),
}));

export const ticketRelations = relations(ticket, ({ one, many }) => ({
  user: one(user, { fields: [ticket.userId], references: [user.id] }),
  images: many(ticketImage),
  messages: many(ticketMessage),
}));

export const ticketImageRelations = relations(ticketImage, ({ one }) => ({
  ticket: one(ticket, {
    fields: [ticketImage.ticketId],
    references: [ticket.id],
  }),
}));

export const ticketMessageRelations = relations(ticketMessage, ({ one }) => ({
  ticket: one(ticket, {
    fields: [ticketMessage.ticketId],
    references: [ticket.id],
  }),
}));
