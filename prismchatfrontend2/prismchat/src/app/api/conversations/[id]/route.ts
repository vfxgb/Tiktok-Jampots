import { NextResponse } from "next/server";
import { getConversation } from "@/lib/mockdb";

export async function GET(_: Request, { params }: { params: { id: string } }) {
  const messages = getConversation(params.id);
  return NextResponse.json({ conversationId: params.id, messages });
}
