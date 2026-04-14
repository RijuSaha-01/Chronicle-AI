"""
Chronicle AI - Conversational Memory Chat

Answers natural language questions about the user's history using RAG.
"""

import logging
import re
from typing import List, Dict, Any, Optional, NamedTuple, Tuple
from datetime import datetime, timedelta
import dateparser
from dateparser.search import search_dates
from .semantic_search import get_semantic_search
from .repository import get_repository
from .models import ChatMessage

logger = logging.getLogger(__name__)

class MemoryResponse(NamedTuple):
    """
    Structured response from the memory chat engine.
    """
    answer: str
    sources: List[Dict[str, Any]]

class MemoryChat:
    """
    Conversational interface for querying episodic memory with history.
    """
    
    def __init__(self, semantic_search=None, llm_client=None, repo=None, session_id=None):
        """
        Initialize with optional search engine, LLM client, and session ID.
        """
        self.search_engine = semantic_search or get_semantic_search()
        self.llm = llm_client or get_llm_client()
        self.repo = repo or get_repository()
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []
        self.all_sources: List[Dict[str, Any]] = []
        
        if self.session_id:
            self._load_session(self.session_id)
        else:
            # Create a new session on first interaction or when explicitly initialized
            pass

    def _ensure_session(self, initial_question: str = "New Chat"):
        """Ensure a session exists in the database."""
        if self.session_id is None:
            # Use a snippet of the first question as the title
            title = initial_question[:30] + "..." if len(initial_question) > 30 else initial_question
            session = self.repo.create_chat_session(title=title)
            self.session_id = session.id

    def _load_session(self, session_id: int):
        """Load an existing session from the database."""
        session = self.repo.get_chat_session(session_id)
        if session:
            self.history = [{"role": m.role, "content": m.content} for m in session.messages]
            self.session_id = session.id
            logger.info(f"Loaded chat session {session_id} with {len(self.history)} messages.")

    def clear(self):
        """Reset conversation context and start a new session."""
        self.history = []
        self.all_sources = []
        self.session_id = None # Will be recreation on next ask

    def _extract_time_ranges(self, question: str) -> List[Tuple[str, str]]:
        # ... (same as before)
        now = datetime.now()
        found_dates = search_dates(question, settings={'PREFER_DATES_FROM': 'past', 'RELATIVE_BASE': now})
        
        if not found_dates:
            return []
        
        ranges = []
        q_lower = question.lower()
        
        # Handle "week before [date]" or "month before [date]"
        before_match = re.search(r'(week|month|year)\s+before', q_lower)
        
        for parsed_str, dt in found_dates:
            start_date = dt
            end_date = dt
            
            p_lower = parsed_str.lower()
            
            # Determine base range granularity
            if "week" in p_lower or "week" in q_lower:
                start_date = dt - timedelta(days=dt.weekday())
                end_date = start_date + timedelta(days=6)
            elif any(m in p_lower or m in q_lower for m in ["month", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
                start_date = dt.replace(day=1)
                next_month = dt.month % 12 + 1
                curr_year = dt.year + (dt.month // 12 if next_month == 1 else 0)
                end_date = dt.replace(month=next_month, year=curr_year, day=1) - timedelta(days=1)
            elif "year" in p_lower or "year" in q_lower:
                start_date = dt.replace(month=1, day=1)
                end_date = dt.replace(month=12, day=31)
            
            # Adjust if "before" is specified
            if before_match:
                unit = before_match.group(1)
                if unit == "week":
                    end_date = start_date - timedelta(days=1)
                    start_date = end_date - timedelta(days=6)
                elif unit == "month":
                    end_date = start_date - timedelta(days=1)
                    start_date = end_date.replace(day=1)
                elif unit == "year":
                    end_date = start_date - timedelta(days=1)
                    start_date = end_date.replace(month=1, day=1, year=end_date.year) # simplified
            
            ranges.append((start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        # Deduplicate ranges
        unique_ranges = []
        for r in ranges:
            if r not in unique_ranges:
                unique_ranges.append(r)
        
        return unique_ranges

    def ask(self, question: str) -> MemoryResponse:
        """
        Analyse a question, retrieve relevant memories, and generate an answer.
        """
        self._ensure_session(question)
        
        # 1. Search for relevant context across episodes
        time_ranges = self._extract_time_ranges(question)
        
        results = []
        if time_ranges:
            for start, end in time_ranges:
                logger.info(f"Timeline search detected: {start} to {end}")
                range_results = self.search_engine.search(question, limit=3, filters={"date_range": [start, end]})
                results.extend(range_results)
        else:
            results = self.search_engine.search(question, limit=5)
        
        seen = set()
        unique_results = []
        for res in results:
            key = (res.get("episode_id"), res.get("section"))
            if key not in seen:
                unique_results.append(res)
                seen.add(key)
        results = unique_results[:7]
        
        for res in results:
            if not any(s.get('episode_id') == res.get('episode_id') for s in self.all_sources):
                self.all_sources.append(res)

        # 2. Build context string
        context_str = ""
        for i, res in enumerate(results):
            episode_id = res.get("episode_id", "Unknown")
            date = res.get("date", "Unknown Date")
            text = res.get("text_snippet", "")
            title = res.get("title", "Untitled Episode")
            context_str += f"--- MEMORY [{i+1}] ---\nEPISODE {episode_id}: '{title}' ({date})\nCONTENT: {text}\n\n"

        # 3. Format history for prompt
        history_str = ""
        for msg in self.history[-10:]:
            role = "USER" if msg["role"] == "user" else "CHRONICLE"
            history_str += f"{role}: {msg['content']}\n"

        # 4. Construct the prompt
        system_prompt = (
            "You are 'Chronicle AI', a helpful and evocative conversational assistant. "
            "You have access to the user's personal history via recorded memory chunks. "
            "Your goal is to answer questions about their life based on the provided context and history."
        )
        
        prompt = f"""Use the following memory snippets and conversation history to answer the user's question. 

### INSTRUCTIONS:
1. Always base your answer strictly on the provided memories.
2. If the memories do not contain enough information to answer, say: "I don't know based on your recorded memories."
3. Cite your sources inline using the format [Episode ID: 'Title'] (e.g., "As mentioned in [Episode 23: 'The Turning Point'], you were...").
4. If the user asks a follow-up, use the history to maintain context.
5. Maintain a supportive, cinematic tone, as if reflecting on a story.

### MEMORY CONTEXT:
{context_str}

### CONVERSATION HISTORY:
{history_str}

### CURRENT USER QUESTION:
{question}

### CONVERSATIONAL ANSWER:"""

        # 5. Generate and persist
        try:
            answer = self.llm.generate(prompt, system_prompt=system_prompt)
            
            if not answer or len(answer.strip()) < 5:
                answer = "I found some relevant memories, but I'm having trouble formulating a clear answer right now."
                
            # Persist to database
            user_msg = ChatMessage(role="user", content=question)
            asst_msg = ChatMessage(role="assistant", content=answer)
            
            self.repo.add_chat_message(self.session_id, user_msg)
            self.repo.add_chat_message(self.session_id, asst_msg)
            
            # Update local history
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            
            if len(self.history) > 10:
                self.history = self.history[-10:]
                
            return MemoryResponse(answer=answer, sources=results)
            
        except Exception as e:
            logger.error(f"Failed to generate memory response: {e}")
            return MemoryResponse(
                answer="I encountered an error while trying to process your memories.",
                sources=results
            )

    def get_history(self, limit: int = 10) -> List[Any]:
        """List past chat sessions."""
        return self.repo.list_chat_sessions(limit=limit)

    def search_history(self, query: str) -> List[Dict]:
        """Search across all chat sessions."""
        return self.repo.search_chat_history(query)

    def export_chat(self, session_id: int) -> str:
        """Export a chat session as Markdown."""
        session = self.repo.get_chat_session(session_id)
        if not session:
            return "Session not found."
            
        md = f"# 🎬 Chronicle AI Chat: {session.title}\n"
        md += f"**Session ID:** {session.id} | **Date:** {session.created_at}\n\n"
        md += "---\n\n"
        
        for msg in session.messages:
            role_display = "🦸 **You**" if msg.role == "user" else "🤖 **Chronicle AI**"
            md += f"{role_display} *({msg.timestamp})*\n\n{msg.content}\n\n"
            
        return md

    def cleanup(self, days: int = 30) -> int:
        """Clean up old chats."""
        return self.repo.cleanup_old_chats(days)

def get_memory_chat(session_id: Optional[int] = None):
    """Factory function for MemoryChat."""
    return MemoryChat(session_id=session_id)
