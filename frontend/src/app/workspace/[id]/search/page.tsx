"use client";
import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Search, Filter, FileText, Clock, ChevronRight, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { searchApi } from "@/lib/api";
import { cn, getFileTypeIcon } from "@/lib/utils";
import { useDebounce } from "@/hooks/use-debounce";

interface SearchResult {
  chunk_id: string;
  document_id: string;
  title: string;
  file_type: string;
  content: string;
  score: number;
  page_number?: number;
  tags?: string[];
  chunk_index: number;
}

const FILE_TYPE_FILTERS = ["All", "pdf", "docx", "markdown", "pptx", "xlsx", "txt"];

export default function SearchPage() {
  const params = useParams();
  const workspaceId = params.id as string;

  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const searchMutation = useMutation({
    mutationFn: (q: string) =>
      searchApi.search(workspaceId, q, activeFilter !== "All" ? { file_type: activeFilter } : {}, 12)
        .then((r) => r.data),
    onSuccess: (data) => {
      setResults(data.results || []);
      setHasSearched(true);
    },
  });

  const handleSearch = useCallback(
    (value: string) => {
      if (value.trim().length >= 2) searchMutation.mutate(value.trim());
    },
    [searchMutation]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSearch(query);
  };

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Semantic Search</h1>
        <p className="text-white/40 text-sm">Search your entire knowledge base with natural language</p>
      </div>

      {/* Search input */}
      <div className="relative mb-4">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Try: "employee leave policy" or "how does authentication work"'
          className="pl-11 h-12 text-base bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus-visible:ring-atlas-500 focus-visible:border-atlas-500/40"
        />
        {searchMutation.isPending && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 animate-spin" />
        )}
      </div>

      {/* File type filters */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <Filter className="w-3.5 h-3.5 text-white/30" />
        {FILE_TYPE_FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={cn(
              "px-3 py-1 rounded-full text-xs transition-all capitalize",
              activeFilter === f
                ? "bg-atlas-500/20 text-atlas-300 border border-atlas-500/30"
                : "text-white/30 hover:text-white/60 border border-white/5 hover:border-white/15"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Results */}
      {hasSearched && (
        <div>
          <p className="text-xs text-white/30 mb-4">
            {results.length} result{results.length !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
          </p>

          {results.length === 0 ? (
            <div className="text-center py-16">
              <Search className="w-10 h-10 text-white/10 mx-auto mb-4" />
              <p className="text-white/30">No results found. Try different search terms.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((r) => (
                <div
                  key={r.chunk_id}
                  className="rounded-xl border border-white/5 bg-white/[0.02] p-5 hover:border-white/10 hover:bg-white/[0.04] transition-all group cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="text-lg">{getFileTypeIcon(r.file_type)}</span>
                      <div>
                        <h3 className="font-medium text-sm text-white group-hover:text-atlas-300 transition-colors">
                          {r.title}
                        </h3>
                        <div className="flex items-center gap-2 mt-0.5">
                          {r.page_number && (
                            <span className="text-xs text-white/25">Page {r.page_number}</span>
                          )}
                          {r.tags?.map((tag) => (
                            <Badge key={tag} variant="outline" className="text-[10px] py-0 border-white/10 text-white/25">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <div className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {Math.round(r.score * 10) / 10}% match
                      </div>
                      <ChevronRight className="w-4 h-4 text-white/20 group-hover:text-white/50" />
                    </div>
                  </div>

                  <p className="text-sm text-white/50 leading-relaxed line-clamp-3">{r.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!hasSearched && (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/5 flex items-center justify-center mx-auto mb-4">
            <Search className="w-7 h-7 text-white/20" />
          </div>
          <p className="text-white/30 text-sm">Start typing to search your knowledge base</p>
          <p className="text-white/20 text-xs mt-1">Hybrid semantic + keyword search across all indexed documents</p>
        </div>
      )}
    </div>
  );
}
