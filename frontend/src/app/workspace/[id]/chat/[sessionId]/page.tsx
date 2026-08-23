"use client";
import { redirect, useParams } from "next/navigation";

// Redirect /workspace/[id]/chat/[sessionId] to /workspace/[id]/chat
// The session is handled by the chat page via URL params or state
export default function ChatSessionPage() {
  const params = useParams();
  redirect(`/workspace/${params.id}/chat`);
}
