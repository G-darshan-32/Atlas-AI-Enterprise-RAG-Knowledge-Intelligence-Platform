"""LangGraph multi-agent orchestrator for Atlas AI."""
from typing import AsyncGenerator
from langgraph.graph import StateGraph, END

from app.ai.agents.state import AgentState
from app.ai.agents.router_agent import router_agent
from app.ai.agents.memory_agent import memory_agent
from app.ai.agents.retriever_agent import retriever_agent
from app.ai.agents.document_agent import document_agent
from app.ai.agents.github_agent import github_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.reasoning_agent import reasoning_agent
from app.ai.agents.citation_agent import citation_agent
from app.ai.agents.analytics_agent import analytics_agent
from app.ai.agents.report_agent import report_agent
from app.core.config import settings
from langchain_core.messages import HumanMessage, SystemMessage


# ─── Routing logic ───────────────────────────────────────

def route_after_memory(state: AgentState) -> str:
    """Route to the appropriate specialised agent after memory loading."""
    intent = state.get("intent", "DOCUMENT_QA")
    routing = {
        "CODE_EXPLANATION": "github_agent",
        "RESEARCH_QUERY": "research_agent",
        "GENERAL_CHAT": "reasoning_agent",   # skip retrieval
        "REPORT_REQUEST": "retriever_agent", # fetch context, then report_agent
        "COMPARISON": "retriever_agent",
        "SUMMARIZATION": "retriever_agent",
        "DOCUMENT_QA": "document_agent",
        "ANALYTICS": "analytics_agent",
    }
    return routing.get(intent, "retriever_agent")


def route_after_retrieval(state: AgentState) -> str:
    """After retrieval, decide if we need report_agent or reasoning_agent."""
    intent = state.get("intent", "DOCUMENT_QA")
    if intent in ("REPORT_REQUEST", "SUMMARIZATION"):
        return "report_agent"
    return "reasoning_agent"


# ─── Graph construction ──────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("router_agent", router_agent)
    graph.add_node("memory_agent", memory_agent)
    graph.add_node("document_agent", document_agent)
    graph.add_node("retriever_agent", retriever_agent)
    graph.add_node("github_agent", github_agent)
    graph.add_node("research_agent", research_agent)
    graph.add_node("analytics_agent", analytics_agent)
    graph.add_node("report_agent", report_agent)
    graph.add_node("reasoning_agent", reasoning_agent)
    graph.add_node("citation_agent", citation_agent)

    # Entry: router → memory
    graph.set_entry_point("router_agent")
    graph.add_edge("router_agent", "memory_agent")

    # Memory → specialised retrieval (conditional)
    graph.add_conditional_edges(
        "memory_agent",
        route_after_memory,
        {
            "document_agent": "document_agent",
            "retriever_agent": "retriever_agent",
            "github_agent": "github_agent",
            "research_agent": "research_agent",
            "reasoning_agent": "reasoning_agent",
            "analytics_agent": "analytics_agent",
        },
    )

    # Analytics intent: skip retrieval, go direct to analytics_agent → citation_agent → END
    graph.add_edge("analytics_agent", "citation_agent")

    # Retrieval agents → reasoning or report (conditional)
    for retrieval_node in ("retriever_agent", "document_agent", "github_agent", "research_agent"):
        graph.add_conditional_edges(
            retrieval_node,
            route_after_retrieval,
            {
                "report_agent": "report_agent",
                "reasoning_agent": "reasoning_agent",
            },
        )

    # report_agent already runs citation internally, but still route through END
    graph.add_edge("report_agent", END)

    # Reasoning → citation → END
    graph.add_edge("reasoning_agent", "citation_agent")
    graph.add_edge("citation_agent", END)

    return graph.compile()


# ─── Singleton compiled graph ─────────────────────────────

_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ─── Orchestrator ─────────────────────────────────────────

class AgentOrchestrator:
    """Streams AI responses using the LangGraph multi-agent pipeline."""

    async def stream(
        self,
        query: str,
        workspace_id: str,
        session_id: str,
        mode: str = "general",
    ) -> AsyncGenerator[dict, None]:

        initial_state: AgentState = {
            "query": query,
            "workspace_id": workspace_id,
            "session_id": session_id,
            "mode": mode,
            "intent": None,
            "sub_intents": None,
            "conversation_history": None,
            "retrieved_chunks": [],
            "retrieval_queries": None,
            "context": None,
            "draft_response": None,
            "final_response": None,
            "citations": [],
            "confidence_score": None,
            "agents_invoked": [],
            "error": None,
            "tokens_used": None,
        }

        graph = get_graph()

        try:
            final_state = await graph.ainvoke(initial_state)

            response_text = final_state.get("final_response") or final_state.get("draft_response", "")
            citations = final_state.get("citations", [])
            confidence = final_state.get("confidence_score", 0.7)

            if not response_text:
                async for chunk in self._stream_fallback(query, workspace_id):
                    yield chunk
                return

            # Stream response word-by-word to simulate token streaming
            words = response_text.split(" ")
            for i, word in enumerate(words):
                sep = " " if i < len(words) - 1 else ""
                yield {"type": "token", "content": word + sep}

            if citations:
                yield {"type": "citations", "citations": citations}

            yield {
                "type": "done",
                "confidence": confidence,
                "agents_invoked": final_state.get("agents_invoked", []),
            }

        except Exception as e:
            # Fall back to direct LLM / smart knowledge search on any graph error
            async for chunk in self._stream_fallback(query, workspace_id):
                yield chunk

    async def _stream_fallback(self, query: str, workspace_id: str = "") -> AsyncGenerator[dict, None]:
        """Direct LLM streaming fallback with smart local knowledge base search."""
        try:
            from app.ai.llm import get_llm
            llm = get_llm(temperature=0.2, streaming=True)
            messages = [
                SystemMessage(content="You are Atlas AI, an enterprise knowledge assistant. Answer helpfully and concisely using markdown."),
                HumanMessage(content=query),
            ]
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
            yield {"type": "done", "confidence": 0.5, "agents_invoked": ["fallback"]}
        except Exception as e:
            fallback_res = await self._smart_knowledge_fallback(query, workspace_id, str(e))
            for word in fallback_res["text"].split(" "):
                yield {"type": "token", "content": word + " "}
            if fallback_res.get("citations"):
                yield {"type": "citations", "citations": fallback_res["citations"]}
            yield {"type": "done", "confidence": 0.6, "agents_invoked": ["smart_knowledge_fallback"]}

    async def _smart_knowledge_fallback(self, query: str, workspace_id: str, error_msg: str) -> dict:
        """Search workspace database for relevant documents when live LLM API call fails or key is missing."""
        clean_query = query.strip()
        query_lower = clean_query.lower()

        # Common conversational greetings & meta queries that shouldn't search documents
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "sup"}
        meta_queries = {"who are you", "what can you do", "help", "what is atlas", "what is atlas ai", "thanks", "thank you"}

        if query_lower in greetings or any(m in query_lower for m in meta_queries):
            text = f"Hello! I am Atlas AI, your enterprise knowledge assistant.\n\n" \
                   f"You can ask me questions about your uploaded documents, policies, research, code, or workspace analytics.\n\n" \
                   f"---\n*Note: Configure a valid `GROQ_API_KEY` in `backend/.env` for generative reasoning.*"
            return {"text": text, "citations": []}

        # Extract search keywords (filter out stop words and punctuation)
        stop_words = {
            "what", "where", "when", "which", "how", "who", "why", "the", "and", "is", "are", "was", "were",
            "tell", "about", "for", "with", "this", "that", "from", "can", "you", "please", "me", "show", "get",
            "find", "some", "any", "all", "your", "my", "our", "have", "has", "had", "does", "do", "did"
        }
        raw_words = [w.strip("?!.,:; \t\n'\"()[]{}") for w in clean_query.split()]
        words = [w.lower() for w in raw_words if len(w) >= 3 and w.lower() not in stop_words]

        matched_docs_info = []

        if workspace_id and words:
            try:
                import uuid
                from sqlalchemy import select, or_
                from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
                from app.models.document import Document, DocumentChunk
                from app.core.config import settings

                engine = create_async_engine(settings.DATABASE_URL, echo=False)
                Session = async_sessionmaker(engine, expire_on_commit=False)

                try:
                    ws_uuid = uuid.UUID(workspace_id)
                except ValueError:
                    ws_uuid = None

                if ws_uuid:
                    async with Session() as db:
                        conds = [Document.title.ilike(f"%{w}%") for w in words]
                        conds.extend([DocumentChunk.content.ilike(f"%{w}%") for w in words])

                        stmt = (
                            select(Document, DocumentChunk)
                            .join(DocumentChunk, DocumentChunk.document_id == Document.id)
                            .where(
                                Document.workspace_id == ws_uuid,
                                Document.is_active == True,
                                or_(*conds)
                            )
                        )
                        result = await db.execute(stmt)
                        rows = result.all()
                    await engine.dispose()

                    scored_candidates = []
                    for doc, chunk in rows:
                        chunk_content = chunk.content or ""
                        content_lower = chunk_content.lower()
                        title_lower = (doc.title or "").lower()

                        score = 0
                        for word in words:
                            if word in title_lower:
                                score += 5
                            score += content_lower.count(word) * 2

                        if score > 0:
                            scored_candidates.append({
                                "doc": doc,
                                "chunk": chunk,
                                "score": score,
                                "content": chunk_content
                            })

                    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

                    seen_doc_ids = set()
                    for item in scored_candidates:
                        doc = item["doc"]
                        if doc.id not in seen_doc_ids:
                            seen_doc_ids.add(doc.id)

                            text = item["content"]
                            snippet = text
                            for w in words:
                                idx = text.lower().find(w)
                                if idx != -1:
                                    start = max(0, idx - 40)
                                    end = min(len(text), idx + 200)
                                    prefix = "..." if start > 0 else ""
                                    suffix = "..." if end < len(text) else ""
                                    snippet = prefix + text[start:end] + suffix
                                    break
                            if len(snippet) > 250:
                                snippet = snippet[:250] + "..."

                            matched_docs_info.append({
                                "doc_id": str(doc.id),
                                "title": doc.title,
                                "snippet": snippet,
                                "score": min(0.95, round(0.5 + (item["score"] / 20.0), 2))
                            })
                            if len(matched_docs_info) >= 3:
                                break
            except Exception:
                pass

        if matched_docs_info:
            text_parts = [f"Here is what I found in your knowledge base for **\"{clean_query}\"**:\n"]
            citations = []
            for idx, doc_info in enumerate(matched_docs_info, 1):
                text_parts.append(f"### [Source {idx}] {doc_info['title']}\n{doc_info['snippet']}\n")
                citations.append({
                    "source_number": idx,
                    "document_id": doc_info["doc_id"],
                    "title": doc_info["title"],
                    "score": doc_info["score"],
                    "content_preview": doc_info["snippet"][:200]
                })
            text_parts.append("\n---\n*Note: Output generated from workspace knowledge base search. Configure a valid `GROQ_API_KEY` in `backend/.env` for generative reasoning.*")
            return {"text": "\n".join(text_parts), "citations": citations}

        text = f"I searched your workspace knowledge base for **\"{clean_query}\"**, but did not find matching documents.\n\n" \
               f"*(LLM service notice: `{error_msg}`)*\n\n" \
               f"**To enable live generative AI responses for any question:**\n" \
               f"1. Open `backend/.env`\n" \
               f"2. Set `GROQ_API_KEY` to your Groq key (e.g. `gsk_...`)\n" \
               f"3. Restart the backend server."
        return {"text": text, "citations": []}

