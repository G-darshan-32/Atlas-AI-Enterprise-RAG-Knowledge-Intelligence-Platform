"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Brain, Search, GitBranch, Shield, Zap, Users,
  ArrowRight, ChevronRight, FileText, MessageSquare, BarChart3,
} from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "Multi-Agent AI", desc: "LangGraph-powered agents for routing, retrieval, reasoning, and citation generation" },
  { icon: Search, title: "Hybrid Search", desc: "Dense vector + BM25 sparse search with cross-encoder re-ranking for maximum precision" },
  { icon: GitBranch, title: "GitHub Integration", desc: "Index repositories, README files, docs, and source code into your knowledge base" },
  { icon: Shield, title: "Enterprise Security", desc: "RBAC, workspace isolation, JWT auth, audit logs, and prompt injection protection" },
  { icon: Zap, title: "RAG Pipeline", desc: "Smart chunking, BGE embeddings, Qdrant vector storage with streaming AI responses" },
  { icon: BarChart3, title: "Analytics & Reports", desc: "AI-generated executive reports, usage dashboards, and search heatmaps" },
];

const WORKSPACES = [
  { name: "TechNova Software", docs: 20, type: "Engineering", color: "from-blue-500 to-cyan-500" },
  { name: "Developer Documentation", docs: 16, type: "Technical Docs", color: "from-purple-500 to-pink-500" },
  { name: "AI Research", docs: 14, type: "Research Papers", color: "from-orange-500 to-red-500" },
  { name: "University", docs: 12, type: "Academic", color: "from-green-500 to-teal-500" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-lg tracking-tight">Atlas AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button variant="atlas" size="sm">Get started <ArrowRight className="w-4 h-4" /></Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6">
        {/* Background glow */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-atlas-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="max-w-5xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-atlas-500/30 bg-atlas-500/10 px-4 py-1.5 text-sm text-atlas-300 mb-8">
              <Zap className="w-3.5 h-3.5" />
              Powered by GPT-4o · LangGraph · Qdrant
            </div>

            <h1 className="text-5xl sm:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
              Enterprise AI Workspace
              <br />
              <span className="text-gradient">for Organizational Intelligence</span>
            </h1>

            <p className="text-xl text-white/50 max-w-2xl mx-auto mb-10">
              Your company&apos;s private ChatGPT + Google Search + NotebookLM.
              Chat with your documents, search your codebase, and generate insights across your entire knowledge base.
            </p>

            <div className="flex items-center justify-center gap-4">
              <Link href="/register">
                <Button variant="atlas" size="lg" className="text-base px-8">
                  Start for free <ChevronRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="text-base border-white/10 text-white/70 hover:text-white hover:bg-white/5">
                  View demo
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Hero visual — workspace preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-20 rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden shadow-2xl shadow-black/50"
          >
            <div className="flex items-center gap-2 px-4 h-10 bg-white/[0.03] border-b border-white/5">
              <div className="w-3 h-3 rounded-full bg-red-500/70" />
              <div className="w-3 h-3 rounded-full bg-amber-500/70" />
              <div className="w-3 h-3 rounded-full bg-green-500/70" />
              <span className="ml-2 text-xs text-white/20 font-mono">atlas-ai.com/workspace/technova</span>
            </div>
            <div className="p-6 bg-gradient-to-b from-white/[0.02] to-transparent min-h-[300px] flex items-center justify-center">
              <div className="w-full max-w-2xl space-y-4">
                {/* Simulated chat */}
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-atlas-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Users className="w-3.5 h-3.5 text-atlas-400" />
                  </div>
                  <div className="rounded-2xl rounded-tl-sm bg-white/5 border border-white/5 px-4 py-3 text-sm text-white/80">
                    What is our backend architecture and which databases do we use?
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-atlas-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div className="rounded-2xl rounded-tl-sm bg-atlas-500/10 border border-atlas-500/20 px-4 py-3 text-sm text-white/80 flex-1">
                    <p>Based on the <span className="text-atlas-400 font-medium">Backend Architecture Guide</span> [Source 1], TechNova uses a microservices architecture with:</p>
                    <ul className="mt-2 space-y-1 text-white/60 list-disc list-inside">
                      <li>PostgreSQL for primary relational data</li>
                      <li>Redis for caching and session management</li>
                      <li>Qdrant for vector embeddings and semantic search</li>
                    </ul>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-xs bg-white/5 border border-white/10 rounded px-2 py-0.5 text-white/40">📄 Backend Architecture Guide</span>
                      <span className="text-xs bg-white/5 border border-white/10 rounded px-2 py-0.5 text-white/40">📄 Database Design Document</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Everything your team needs</h2>
            <p className="text-white/40 max-w-xl mx-auto">Built for engineering teams, HR departments, researchers, and every knowledge-intensive team in between.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                viewport={{ once: true }}
                className="glass-card rounded-xl p-6 group hover:border-atlas-500/20 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-atlas-500/10 flex items-center justify-center mb-4 group-hover:bg-atlas-500/20 transition-colors">
                  <f.icon className="w-5 h-5 text-atlas-400" />
                </div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Workspaces */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">4 demo workspaces ready to explore</h2>
            <p className="text-white/40">Sign in to try real AI-powered search and chat across curated knowledge bases.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {WORKSPACES.map((ws) => (
              <div key={ws.name} className="glass-card rounded-xl p-5 hover:border-white/20 transition-colors cursor-pointer group">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${ws.color} mb-4 flex items-center justify-center opacity-80 group-hover:opacity-100 transition-opacity`}>
                  <FileText className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-medium text-sm mb-1">{ws.name}</h3>
                <p className="text-xs text-white/30 mb-3">{ws.type}</p>
                <div className="flex items-center gap-1.5 text-xs text-white/20">
                  <FileText className="w-3 h-3" />
                  {ws.docs} documents
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to build your knowledge layer?</h2>
          <p className="text-white/40 mb-8">Start free, scale to enterprise. No credit card required.</p>
          <Link href="/register">
            <Button variant="atlas" size="lg" className="text-base px-10">
              Create your workspace <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/5 py-8 px-6 text-center text-white/20 text-sm">
        © 2024 Atlas AI · Enterprise AI Workspace for Organizational Intelligence
      </footer>
    </div>
  );
}
