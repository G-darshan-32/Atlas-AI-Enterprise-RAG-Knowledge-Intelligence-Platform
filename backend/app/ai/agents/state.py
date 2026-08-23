from typing import TypedDict, Annotated, List, Optional
from operator import add


class AgentState(TypedDict):
    """Shared state across all agents in the LangGraph workflow."""
    # Input
    query: str
    workspace_id: str
    session_id: str
    mode: str  # general | document | code | research

    # Router
    intent: Optional[str]              # DOCUMENT_QA | CODE_EXPLANATION | RESEARCH_QUERY | GENERAL_CHAT | etc.
    sub_intents: Optional[List[str]]

    # Memory
    conversation_history: Optional[List[dict]]

    # Retrieval
    retrieved_chunks: Annotated[List[dict], add]
    retrieval_queries: Optional[List[str]]

    # Response
    context: Optional[str]
    draft_response: Optional[str]
    final_response: Optional[str]
    citations: Annotated[List[dict], add]
    confidence_score: Optional[float]

    # Metadata
    agents_invoked: Annotated[List[str], add]
    error: Optional[str]
    tokens_used: Optional[int]
