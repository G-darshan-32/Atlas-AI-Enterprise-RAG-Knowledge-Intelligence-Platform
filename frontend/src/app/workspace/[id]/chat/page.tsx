"use client";
import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import {
  MessageSquare, Send, Plus, Pin, Archive, Trash2,
  Brain, Copy, RefreshCw, ChevronRight, Sparkles, FileText
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { chatApi } from "@/lib/api";
import { cn, formatRelativeTime, SUGGESTED_PROMPTS } from "@/lib/utils";
import { useAuthStore } from "@/store/auth.store";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence_score?: number;
  isStreaming?: boolean;
}

interface Citation {
  source_number: number;
  title: string;
  document_id?: string;
  page_number?: number;
  content_preview?: string;
  score?: number;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const qc = useQueryClient();
  const workspaceId = params.id as string;
  const sessionId = params.sessionId as string | undefined;

  const [activeSessionId, setActiveSessionId] = useState<string | null>(sessionId || null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [mode, setMode] = useState("general");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { user } = useAuthStore();

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions", workspaceId],
    queryFn: () => chatApi.listSessions(workspaceId).then((r) => r.data),
  });

  const { data: sessionData } = useQuery({
    queryKey: ["chat-session", workspaceId, activeSessionId],
    queryFn: () => chatApi.getSession(workspaceId, activeSessionId!).then((r) => r.data),
    enabled: !!activeSessionId,
  });

  useEffect(() => {
    if (sessionData?.messages) {
      setMessages(sessionData.messages);
    }
  }, [sessionData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const createSessionMutation = useMutation({
    mutationFn: () => chatApi.createSession(workspaceId, mode).then((r) => r.data),
    onSuccess: (data) => {
      setActiveSessionId(data.id);
      setMessages([]);
      qc.invalidateQueries({ queryKey: ["chat-sessions", workspaceId] });
    },
  });

  const handleNewChat = async () => {
    await createSessionMutation.mutateAsync();
  };

  const sendMessage = async () => {
    const content = input.trim();
    if (!content || isStreaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content }]);
    setIsStreaming(true);

    // Add streaming placeholder
    setMessages((prev) => [...prev, { role: "assistant", content: "", isStreaming: true }]);

    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const session = await chatApi.createSession(workspaceId, mode).then((r) => r.data);
        currentSessionId = session.id;
        setActiveSessionId(session.id);
        qc.invalidateQueries({ queryKey: ["chat-sessions", workspaceId] });
      } catch (err: any) {
        toast.error("Failed to create chat session.");
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "⚠️ **Session Error**: Could not create chat session. Please verify backend connection.",
            isStreaming: false,
          };
          return updated;
        });
        setIsStreaming(false);
        return;
      }
    }

    try {
      const token = localStorage.getItem("access_token") || useAuthStore.getState().accessToken;
      const response = await fetch(
        `${BASE_URL}/api/v1/workspaces/${workspaceId}/chat/sessions/${currentSessionId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        let errText = "Request failed";
        try {
          const errData = await response.json();
          errText = errData.detail || errText;
        } catch {}
        throw new Error(errText);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let citations: Citation[] = [];
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === "token") {
              fullContent += data.content;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: fullContent,
                  isStreaming: true,
                };
                return updated;
              });
            } else if (data.type === "citations") {
              citations = data.citations;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  citations,
                };
                return updated;
              });
            } else if (data.type === "done") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: fullContent,
                  citations,
                  isStreaming: false,
                };
                return updated;
              });
            } else if (data.type === "error") {
              fullContent = `⚠️ **AI Service Note**: ${data.content}\n\n*Tip: Check your \`GROQ_API_KEY\` in \`backend/.env\`.*`;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: fullContent,
                  isStreaming: false,
                };
                return updated;
              });
              setIsStreaming(false);
            }
          } catch {
            // skip bad line
          }
        }
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to get AI response.");
      setMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
          updated[lastIndex] = {
            role: "assistant",
            content: `⚠️ **Connection Error**: ${err?.message || "Unable to reach backend service."}`,
            isStreaming: false,
          };
        }
        return updated;
      });
    } finally {
      setIsStreaming(false);
      qc.invalidateQueries({ queryKey: ["chat-sessions", workspaceId] });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success("Copied to clipboard");
  };

  return (
    <div className="flex h-screen">
      {/* Sessions sidebar */}
      <div className="w-56 flex-shrink-0 border-r border-white/5 bg-[#0d0d14] flex flex-col">
        <div className="p-3 border-b border-white/5">
          <Button
            onClick={handleNewChat}
            variant="outline"
            size="sm"
            className="w-full border-white/10 text-white/60 hover:text-white hover:bg-white/[0.06] gap-2"
          >
            <Plus className="w-4 h-4" /> New chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {sessions?.map((s: { id: string; title?: string; is_pinned: boolean; updated_at: string }) => (
            <button
              key={s.id}
              onClick={() => { setActiveSessionId(s.id); setMessages([]); }}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-xs transition-all group",
                activeSessionId === s.id
                  ? "bg-atlas-500/15 text-atlas-300"
                  : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
              )}
            >
              <div className="flex items-center gap-1.5">
                {s.is_pinned && <Pin className="w-3 h-3 text-amber-400 flex-shrink-0" />}
                <span className="truncate">{s.title || "New conversation"}</span>
              </div>
              <span className="text-white/20 text-[10px] mt-0.5 block">{formatRelativeTime(s.updated_at)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Chat mode selector */}
        <div className="flex items-center gap-2 px-6 py-3 border-b border-white/5">
          {["general", "document", "code", "research"].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={cn(
                "px-3 py-1 rounded-full text-xs capitalize transition-all",
                mode === m
                  ? "bg-atlas-500/20 text-atlas-300 border border-atlas-500/30"
                  : "text-white/30 hover:text-white/60 hover:bg-white/[0.04]"
              )}
            >
              {m}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-8 text-center">
              <div>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-atlas-500/30">
                  <Brain className="w-7 h-7 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">Atlas AI</h2>
                <p className="text-white/40 text-sm max-w-sm">
                  Ask anything about your organization&apos;s knowledge base. I&apos;ll find answers with cited sources.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
                {SUGGESTED_PROMPTS.slice(0, 4).map((p) => (
                  <button
                    key={p}
                    onClick={() => { setInput(p); inputRef.current?.focus(); }}
                    className="text-left p-3 rounded-xl bg-white/[0.03] border border-white/5 hover:border-white/15 hover:bg-white/[0.06] text-xs text-white/50 hover:text-white/80 transition-all"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md shadow-atlas-500/30">
                  <Brain className="w-4 h-4 text-white" />
                </div>
              )}

              <div className={cn("max-w-2xl", msg.role === "user" ? "order-first" : "")}>
                <div className={cn(
                  "rounded-2xl px-4 py-3 text-sm leading-relaxed",
                  msg.role === "user"
                    ? "bg-atlas-500/20 border border-atlas-500/30 text-white ml-12"
                    : "bg-white/[0.03] border border-white/5 text-white/85"
                )}>
                  {msg.role === "assistant" ? (
                    <div className={cn("prose prose-invert prose-sm max-w-none", msg.isStreaming && "streaming-cursor")}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content || ""}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p>{msg.content}</p>
                  )}
                </div>

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {msg.citations.map((cite) => (
                      <div
                        key={cite.source_number}
                        className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/[0.04] border border-white/8 text-xs text-white/40 hover:text-white/70 transition-colors cursor-pointer"
                        title={cite.content_preview}
                      >
                        <FileText className="w-3 h-3" />
                        <span>[{cite.source_number}] {cite.title}</span>
                        {cite.page_number && <span className="text-white/25">p.{cite.page_number}</span>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Actions */}
                {msg.role === "assistant" && !msg.isStreaming && msg.content && (
                  <div className="flex items-center gap-1 mt-1.5">
                    <button
                      onClick={() => copyMessage(msg.content)}
                      className="p-1.5 rounded hover:bg-white/[0.06] text-white/25 hover:text-white/60 transition-colors"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-6 pb-6 pt-3 border-t border-white/5">
          <div className="relative rounded-xl border border-white/10 bg-white/[0.03] focus-within:border-atlas-500/40 transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your knowledge base... (Enter to send, Shift+Enter for newline)"
              rows={3}
              className="w-full bg-transparent px-4 pt-3 pb-12 text-sm text-white placeholder:text-white/20 resize-none outline-none"
            />
            <div className="absolute bottom-3 right-3 flex items-center gap-2">
              <span className="text-xs text-white/20">{input.length}/4000</span>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isStreaming}
                className="p-2 rounded-lg bg-gradient-to-r from-atlas-500 to-purple-500 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:brightness-110 transition-all shadow-lg shadow-atlas-500/20"
              >
                {isStreaming ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          <p className="text-center text-xs text-white/20 mt-2">
            Atlas AI can make mistakes. Verify important information with cited sources.
          </p>
        </div>
      </div>
    </div>
  );
}
