// One-time script: set a user's role to 'admin'
// Usage: node scripts/set-admin.mjs
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, "../.env") });

const USER_ID = "Q8N6XwvJZvtohY8esIkXvdVZ6fymtNnk";

const sql = neon(process.env.DATABASE_URL);
const result =
  await sql`UPDATE "user" SET role = 'admin' WHERE id = ${USER_ID} RETURNING id, name, email, role`;

if (result.length === 0) {
  console.error("No user found with that ID.");
} else {
  console.log("Updated:", result[0]);
}
