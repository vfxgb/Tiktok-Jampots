import { NextResponse } from "next/server";
import { z } from "zod";
import { v4 as uuid } from "uuid";
import { addMessage, ensureConversation, getConversation } from "@/lib/mockdb";
import type { SendPayload } from "@/types/chat";

const schema = z.object({
  conversationId: z.string().optional(),
  route: z.enum(["direct", "prismguard"]),
  text: z.string().optional(),
  images: z.array(z.string()).optional(),
});

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as SendPayload;
    const parsed = schema.parse(body);

    // Ensure conversation exists (create on first send)
    const conversationId = ensureConversation(
      parsed.conversationId,
      parsed.text
    );

    // Add user message
    const userMsg = {
      id: uuid(),
      role: "user" as const,
      content: parsed.text ?? "",
      images: parsed.images ?? [],
      createdAt: new Date().toISOString(),
    };
    addMessage(conversationId, userMsg);

    // Simulate assistant reply (you can replace with real PrismGuard soon)
    const assistantMsg = {
      id: uuid(),
      role: "assistant" as const,
      content:
        parsed.route === "prismguard"
          ? "🔒 (PrismGuard) Your data is protected. How can I help?"
          : "👋 (Direct) How can I help you today?",
      images: [],
      createdAt: new Date().toISOString(),
    };
    addMessage(conversationId, assistantMsg);

    // Return full message list
    const messages = getConversation(conversationId);
    return NextResponse.json({ conversationId, messages });
  } catch (e: any) {
    console.error(e);
    return NextResponse.json(
      { error: e.message ?? "Bad Request" },
      { status: 400 }
    );
  }
}
