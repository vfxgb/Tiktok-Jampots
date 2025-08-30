import { NextResponse } from "next/server";
import { listConversations } from "@/lib/mockdb";

export async function GET() {
  return NextResponse.json({ conversations: listConversations() });
}
