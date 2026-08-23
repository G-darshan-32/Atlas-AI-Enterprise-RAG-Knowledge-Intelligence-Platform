"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { HelpCircle, ChevronDown, ChevronRight, Search, BookOpen, MessageSquare, GitBranch, Upload, Zap } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const TOPICS = [
  {
    icon: Upload,
    title: "Uploading Documents",
    items: [
      {
        q: "What file formats does Atlas AI support?",
        a: "Atlas AI supports PDF, DOCX, PPTX, XLSX, Markdown (.md), TXT, CSV, HTML, and Jupyter Notebooks (.ipynb). Files up to 50MB per upload.",
      },
      {
        q: "How long does document processing take?",
        a: "Most documents are processed within 30–60 seconds. Large PDFs with many pages may take up to 2 minutes. You'll see the status update in real-time on the Documents page.",
      },
      {
        q: "Why is my document stuck on 'Processing'?",
        a: "Check the document status on the Documents page. If it shows 'Failed', click the reprocess button. Common causes: password-protected PDFs, corrupted files, or scanned images without OCR-readable text.",
      },
    ],
  },
  {
    icon: MessageSquare,
    title: "AI Chat",
    items: [
      {
        q: "How do I chat with my documents?",
        a: "Go to the Chat page and ask any question in natural language. Atlas AI automatically searches your knowledge base and returns answers with source citations. You can also select specific documents to scope your chat.",
      },
      {
        q: "What do the [Source N] citations mean?",
        a: "When Atlas AI answers using content from your documents, it cites the specific document and page number it retrieved from. You can click on any citation card to see the exact chunk of text used.",
      },
      {
        q: "What are the different chat modes?",
        a: "General: All-purpose queries. Document: Focused on uploaded files. Code: Optimised for GitHub repos and technical docs. Research: Best for academic papers and AI research.",
      },
      {
        q: "Can I export my chat conversations?",
        a: "Yes. Open any chat session and click the export button (top right). You can export as Markdown or JSON.",
      },
    ],
  },
  {
    icon: Search,
    title: "Semantic Search",
    items: [
      {
        q: "How is search different from chat?",
        a: "Search returns ranked document chunks directly with no AI generation — ideal for quickly finding where something is documented. Chat uses those same chunks as context to generate a synthesised answer.",
      },
      {
        q: "What is hybrid search?",
        a: "Atlas AI combines dense vector search (semantic similarity) with BM25 keyword search, then fuses results using Reciprocal Rank Fusion. This means you get both semantically relevant AND keyword-matched results.",
      },
      {
        q: "How do I use search filters?",
        a: "In the Search page, click the filter icons to narrow by file type. Date, author, and tag filters are available in the advanced filter panel (click the filter icon next to the search bar).",
      },
    ],
  },
  {
    icon: GitBranch,
    title: "GitHub Integration",
    items: [
      {
        q: "How do I connect a GitHub repository?",
        a: "Go to Repositories → Connect repo. Enter the full repo name (owner/repo format, e.g. 'microsoft/vscode'). For private repos, provide a GitHub Personal Access Token with 'repo' scope.",
      },
      {
        q: "What gets indexed from a repository?",
        a: "By default: README.md and all files in /docs directories. Optionally you can enable source code indexing which will index .py, .ts, .js and other source files with their docstrings.",
      },
      {
        q: "How often is the repository synced?",
        a: "You can trigger a manual sync at any time from the Repositories page. Automatic webhook-based syncing on push events requires a GitHub App installation (enterprise feature).",
      },
    ],
  },
  {
    icon: Zap,
    title: "Workspaces & Permissions",
    items: [
      {
        q: "What can each role do?",
        a: "Guest: View documents and chat. Employee: Upload documents, chat, search. Manager: All Employee permissions + view analytics, manage folders. Workspace Admin: Full workspace control including member management. Super Admin: Platform-wide access.",
      },
      {
        q: "Can I be in multiple workspaces?",
        a: "Yes. Click the workspace name in the sidebar to switch between workspaces. Each workspace is completely isolated — documents, chat history, and settings don't cross over.",
      },
      {
        q: "How do I invite team members?",
        a: "Go to Settings → Members → enter their email and select a role. They must have an existing Atlas AI account. If they don't have one yet, they need to register first at the sign-up page.",
      },
    ],
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (key: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const filtered = TOPICS.map((topic) => ({
    ...topic,
    items: topic.items.filter(
      (item) =>
        !searchQuery ||
        item.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.a.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((t) => t.items.length > 0);

  return (
    <div className="p-6 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <HelpCircle className="w-6 h-6 text-atlas-400" /> Help Center
        </h1>
        <p className="text-white/40 text-sm mt-0.5">Find answers to common questions</p>
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search help articles..."
          className="pl-11 h-11 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500"
        />
      </div>

      {/* Topics */}
      <div className="space-y-6">
        {filtered.map((topic) => (
          <div key={topic.title}>
            <h2 className="flex items-center gap-2 text-sm font-semibold text-white/70 mb-3">
              <topic.icon className="w-4 h-4 text-atlas-400" />
              {topic.title}
            </h2>
            <div className="space-y-1">
              {topic.items.map((item, i) => {
                const key = `${topic.title}-${i}`;
                const isOpen = openItems.has(key);
                return (
                  <div key={key} className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
                    <button
                      onClick={() => toggle(key)}
                      className="w-full flex items-center justify-between px-4 py-3.5 text-left hover:bg-white/[0.03] transition-colors"
                    >
                      <span className="text-sm text-white/75 font-medium pr-4">{item.q}</span>
                      {isOpen
                        ? <ChevronDown className="w-4 h-4 text-white/30 flex-shrink-0" />
                        : <ChevronRight className="w-4 h-4 text-white/30 flex-shrink-0" />
                      }
                    </button>
                    {isOpen && (
                      <div className="px-4 pb-4 text-sm text-white/50 leading-relaxed border-t border-white/5 pt-3">
                        {item.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Contact */}
      <div className="mt-10 rounded-xl border border-white/5 bg-white/[0.02] p-5 text-center">
        <BookOpen className="w-8 h-8 text-white/20 mx-auto mb-3" />
        <p className="text-sm text-white/50 mb-1">Can't find your answer?</p>
        <p className="text-xs text-white/30">Use the AI chat to ask questions about Atlas AI itself, or email support@atlas-ai.com</p>
      </div>
    </div>
  );
}
