"""
Chronicle AI - Conversational Memory Chat

Answers natural language questions about the user's history using RAG.
"""

import logging
from typing import List, Dict, Any, Optional, NamedTuple
from .semantic_search import get_semantic_search
from .llm_client import get_llm_client

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
    
    def __init__(self, semantic_search=None, llm_client=None):
        """
        Initialize with optional search engine and LLM client.
        """
        self.search_engine = semantic_search or get_semantic_search()
        self.llm = llm_client or get_llm_client()
        self.history: List[Dict[str, str]] = []
        self.all_sources: List[Dict[str, Any]] = []

    def clear(self):
        """Reset conversation context."""
        self.history = []
        self.all_sources = []

    def ask(self, question: str) -> MemoryResponse:
        """
        Analyse a question, retrieve relevant memories, and generate an answer.
        
        Args:
            question: Natural language question about the user's past.
            
        Returns:
            MemoryResponse containing the answer and citation sources.
        """
        # 1. Search for relevant context across episodes
        # We increase context slightly for follow-up questions
        results = self.search_engine.search(question, limit=5)
        
        # Track all unique sources in this session
        for res in results:
            if not any(s.get('episode_id') == res.get('episode_id') for s in self.all_sources):
                self.all_sources.append(res)

        # 2. Build context string from search results
        context_str = ""
        for i, res in enumerate(results):
            episode_id = res.get("episode_id", "Unknown")
            date = res.get("date", "Unknown Date")
            text = res.get("text_snippet", "")
            title = res.get("title", "Untitled Episode")
            # Ensure we cite the source clearly for the LLM
            context_str += f"--- MEMORY [{i+1}] ---\nEPISODE {episode_id}: '{title}' ({date})\nCONTENT: {text}\n\n"

        # 3. Format history for prompt (last 5 exchanges)
        history_str = ""
        for msg in self.history[-10:]: # 5 exchanges = 10 messages
            role = "USER" if msg["role"] == "user" else "CHRONICLE"
            history_str += f"{role}: {msg['content']}\n"

        # 4. Construct the prompt for RAG
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

        # 5. Generate the conversational response
        try:
            answer = self.llm.generate(prompt, system_prompt=system_prompt)
            
            if not answer or len(answer.strip()) < 5:
                # Basic fallback if LLM chain fails
                answer = "I found some relevant memories, but I'm having trouble formulating a clear answer right now. You might want to check Episodes: " + \
                         ", ".join([str(r.get('episode_id')) for r in results])
                
            # Update history
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            
            # Keep history to last 5 exchanges (10 messages)
            if len(self.history) > 10:
                self.history = self.history[-10:]
                
            return MemoryResponse(answer=answer, sources=results)
            
        except Exception as e:
            logger.error(f"Failed to generate memory response: {e}")
            return MemoryResponse(
                answer="I encountered an error while trying to process your memories. Please try again later.",
                sources=results
            )

def get_memory_chat():
    """Factory function for MemoryChat."""
    return MemoryChat()
