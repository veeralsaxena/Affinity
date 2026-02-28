"""
memory.py — Tiered Memory Architecture with ChromaDB Vector Search

Three-tier memory system:
  1. Working Memory: Short-term (in LangGraph state, not persisted)
  2. Episodic Memory: Chronological event log (PostgreSQL)
  3. Semantic Memory: Structured facts + Vector embeddings (PostgreSQL + ChromaDB)

ChromaDB provides SEMANTIC SEARCH over facts — instead of dumping all 500 facts
about a contact into the Ghost Writer prompt, we embed the current conversation
context and retrieve only the top-5 most relevant facts.

Redis caching is integrated for fact extraction responses.
"""

import os
import json
import hashlib
import math
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# ChromaDB import — lazy to handle Python 3.14 Pydantic v1 incompatibility
try:
    import chromadb
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False
    print("⚠️ ChromaDB unavailable (Pydantic v1 compat issue), using in-memory vector store")

import models
from cache import get_cache


# ─── ChromaDB Vector Store ───────────────────────────────────────────────────

class ChromaVectorStore:
    """
    Persistent vector database for semantic memory search.
    Uses ChromaDB when available, falls back to in-memory keyword matching.
    """

    def __init__(self, persist_dir: str = None):
        self._persist_dir = persist_dir or os.path.join(
            os.path.dirname(__file__), "chroma_data"
        )
        self._client = None
        self._fallback_store: Dict[str, List[Dict]] = {}  # In-memory fallback

        if CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(path=self._persist_dir)
                print(f"✅ ChromaDB initialized: {self._persist_dir}")
            except Exception as e:
                print(f"⚠️ ChromaDB init failed: {e}, using in-memory fallback")

    def _get_collection(self, user_id: str):
        """Get or create a collection for a user."""
        if not self._client:
            return None
        collection_name = f"user_{user_id[:8]}_facts"
        collection_name = collection_name.replace("-", "_")
        try:
            return self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"ChromaDB collection error: {e}")
            return None

    def store_fact(
        self,
        user_id: str,
        contact_name: str,
        fact_type: str,
        fact_value: str,
    ):
        """Store a fact with its embedding."""
        fact_id = hashlib.md5(
            f"{user_id}:{contact_name}:{fact_type}:{fact_value}".encode()
        ).hexdigest()

        collection = self._get_collection(user_id)
        if collection:
            try:
                collection.upsert(
                    documents=[f"{fact_type}: {fact_value}"],
                    metadatas=[{
                        "contact_name": contact_name,
                        "fact_type": fact_type,
                        "fact_value": fact_value,
                        "timestamp": datetime.utcnow().isoformat(),
                    }],
                    ids=[fact_id],
                )
                return
            except Exception as e:
                print(f"ChromaDB store failed: {e}")

        # Fallback: store in memory
        key = f"{user_id}:{contact_name}"
        if key not in self._fallback_store:
            self._fallback_store[key] = []
        # Avoid duplicates
        for existing in self._fallback_store[key]:
            if existing["fact_value"] == fact_value:
                return
        self._fallback_store[key].append({
            "fact_type": fact_type,
            "fact_value": fact_value,
            "id": fact_id,
        })

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Simple keyword overlap similarity (fallback for vector search)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / math.sqrt(len(words1) * len(words2))

    def query_relevant_facts(
        self,
        user_id: str,
        contact_name: str,
        context: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """Semantic search for relevant facts."""
        collection = self._get_collection(user_id)
        if collection:
            try:
                results = collection.query(
                    query_texts=[context],
                    n_results=top_k,
                    where={"contact_name": contact_name},
                )
                facts = []
                if results and results["metadatas"]:
                    for meta in results["metadatas"][0]:
                        facts.append({
                            "fact_type": meta.get("fact_type", "unknown"),
                            "fact_value": meta.get("fact_value", ""),
                        })
                return facts
            except Exception as e:
                print(f"ChromaDB query failed: {e}")

        # Fallback: keyword similarity search
        key = f"{user_id}:{contact_name}"
        all_facts = self._fallback_store.get(key, [])
        if not all_facts:
            return []

        scored = []
        for f in all_facts:
            sim = self._keyword_similarity(context, f"{f['fact_type']} {f['fact_value']}")
            scored.append((sim, f))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"fact_type": f["fact_type"], "fact_value": f["fact_value"]} for _, f in scored[:top_k]]

    def get_all_facts(
        self,
        user_id: str,
        contact_name: str,
    ) -> List[Dict]:
        """Get all stored facts for a contact."""
        collection = self._get_collection(user_id)
        if collection:
            try:
                results = collection.get(
                    where={"contact_name": contact_name},
                )
                facts = []
                if results and results["metadatas"]:
                    for meta in results["metadatas"]:
                        facts.append({
                            "fact_type": meta.get("fact_type", "unknown"),
                            "fact_value": meta.get("fact_value", ""),
                        })
                return facts
            except Exception:
                pass

        # Fallback
        key = f"{user_id}:{contact_name}"
        return [{"fact_type": f["fact_type"], "fact_value": f["fact_value"]}
                for f in self._fallback_store.get(key, [])]


# ─── Singleton Vector Store ──────────────────────────────────────────────────

_vector_store = None

def get_vector_store() -> ChromaVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


# ─── Memory Manager ─────────────────────────────────────────────────────────

class MemoryManager:
    """Manages the tiered memory architecture for relationship intelligence."""

    def __init__(self, db: Session):
        self.db = db
        self._gemini = None
        self._vector_store = get_vector_store()
        self._cache = get_cache()

    def _get_gemini(self):
        """Lazy-init Gemini for fact extraction."""
        if self._gemini is None:
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    self._gemini = genai.GenerativeModel("gemini-2.0-flash")
            except Exception as e:
                print(f"Gemini init for memory failed: {e}")
        return self._gemini

    # ─── Episodic Memory (Tier 2) ────────────────────────────────────────

    def log_episode(
        self,
        user_id: str,
        contact_name: str,
        event_type: str,
        content: str,
    ):
        """Save a chronological event to episodic memory."""
        episode = models.EpisodicMemory(
            user_id=user_id,
            contact_name=contact_name,
            event_type=event_type,
            content=content,
            timestamp=datetime.utcnow(),
        )
        self.db.add(episode)
        self.db.commit()

    def get_episodes(
        self,
        user_id: str,
        contact_name: str,
        limit: int = 20,
    ) -> List[Dict]:
        """Retrieve recent episodic memories for a contact."""
        episodes = self.db.query(models.EpisodicMemory).filter(
            models.EpisodicMemory.user_id == user_id,
            models.EpisodicMemory.contact_name == contact_name,
        ).order_by(models.EpisodicMemory.timestamp.desc()).limit(limit).all()

        return [
            {
                "event_type": e.event_type,
                "content": e.content,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in episodes
        ]

    def get_relationship_timeline(
        self,
        user_id: str,
        contact_name: str,
    ) -> List[Dict]:
        """Get full chronological timeline."""
        return self.get_episodes(user_id, contact_name, limit=100)

    # ─── Semantic Memory (Tier 3) — PostgreSQL + ChromaDB ────────────────

    def store_fact(
        self,
        user_id: str,
        contact_name: str,
        fact_type: str,
        fact_value: str,
        confidence: float = 0.8,
    ):
        """Store a structured fact in both PostgreSQL AND ChromaDB."""
        # PostgreSQL (structured storage)
        existing = self.db.query(models.SemanticMemory).filter(
            models.SemanticMemory.user_id == user_id,
            models.SemanticMemory.contact_name == contact_name,
            models.SemanticMemory.fact_type == fact_type,
            models.SemanticMemory.fact_value == fact_value,
        ).first()

        if existing:
            existing.confidence = max(existing.confidence or 0, confidence)
            existing.extracted_at = datetime.utcnow()
        else:
            fact = models.SemanticMemory(
                user_id=user_id,
                contact_name=contact_name,
                fact_type=fact_type,
                fact_value=fact_value,
                confidence=confidence,
                extracted_at=datetime.utcnow(),
            )
            self.db.add(fact)

        self.db.commit()

        # ChromaDB (vector search)
        self._vector_store.store_fact(user_id, contact_name, fact_type, fact_value)

    def get_facts(
        self,
        user_id: str,
        contact_name: str,
    ) -> List[Dict]:
        """Retrieve all semantic facts (from PostgreSQL)."""
        facts = self.db.query(models.SemanticMemory).filter(
            models.SemanticMemory.user_id == user_id,
            models.SemanticMemory.contact_name == contact_name,
        ).order_by(models.SemanticMemory.confidence.desc()).all()

        return [
            {
                "fact_type": f.fact_type,
                "fact_value": f.fact_value,
                "confidence": f.confidence,
                "extracted_at": f.extracted_at.isoformat() if f.extracted_at else None,
            }
            for f in facts
        ]

    def extract_facts_from_conversation(
        self,
        user_id: str,
        contact_name: str,
        messages: List[Dict],
    ) -> List[Dict]:
        """Use Gemini to extract structured facts from a conversation."""

        # Check Redis cache first
        cache_key = f"facts:{hashlib.md5(json.dumps(messages[-30:], default=str).encode()).hexdigest()[:12]}"
        cached = self._cache.get(cache_key)
        if cached:
            print("📦 Fact extraction served from Redis cache")
            return cached

        model = self._get_gemini()
        if model is None:
            return []

        conversation_text = "\n".join(
            f"{m.get('sender', '?')}: {m.get('message', '')}" for m in messages[-50:]
        )

        prompt = f"""Extract structured facts from this conversation between the user and {contact_name}.
Return a JSON object with key "facts" containing an array of objects with:
- fact_type: one of "career", "family_member", "location", "preference", "milestone", "hobby", "emotion_pattern", "schedule", "event"
- fact_value: the specific fact (concise, 1 sentence max)
- confidence: 0.0-1.0 how certain you are

Only extract CLEAR, EXPLICIT facts mentioned in the text. Do not infer or assume.

Conversation:
{conversation_text}

Return ONLY valid JSON."""

        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                },
            )
            data = json.loads(response.text)
            facts = data.get("facts", [])

            # Store each fact in PostgreSQL + ChromaDB
            for f in facts:
                self.store_fact(
                    user_id=user_id,
                    contact_name=contact_name,
                    fact_type=f.get("fact_type", "unknown"),
                    fact_value=f.get("fact_value", ""),
                    confidence=f.get("confidence", 0.5),
                )

            # Cache the result in Redis
            self._cache.set(cache_key, facts, ttl=7200)

            return facts
        except Exception as e:
            print(f"Fact extraction failed: {e}")
            return []

    def get_context_for_ghost_writer(
        self,
        user_id: str,
        contact_name: str,
        conversation_context: str = "",
    ) -> str:
        """
        Build context for the Ghost Writer using VECTOR SEARCH.

        Instead of dumping all facts, we embed the current conversation
        context and retrieve only the top-5 most relevant facts.
        This keeps the prompt token-efficient while maximizing relevance.
        """
        # Recent episodes (always include — small and chronological)
        episodes = self.get_episodes(user_id, contact_name, limit=5)
        episode_text = ""
        if episodes:
            episode_text = "Recent history:\n" + "\n".join(
                f"- [{e['event_type']}] {e['content']}" for e in episodes
            )

        # Semantic facts via VECTOR SEARCH (not brute-force SQL)
        facts_text = ""
        if conversation_context:
            # Use ChromaDB semantic search for contextually relevant facts
            relevant_facts = self._vector_store.query_relevant_facts(
                user_id, contact_name, conversation_context, top_k=5
            )
            if relevant_facts:
                facts_text = "Relevant facts about this person:\n" + "\n".join(
                    f"- {f['fact_type']}: {f['fact_value']}" for f in relevant_facts
                )
        else:
            # Fallback: get top facts from PostgreSQL
            all_facts = self.get_facts(user_id, contact_name)[:5]
            if all_facts:
                facts_text = "Known facts about this person:\n" + "\n".join(
                    f"- {f['fact_type']}: {f['fact_value']}" for f in all_facts
                )

        parts = [p for p in [episode_text, facts_text] if p]
        return "\n\n".join(parts) if parts else "No prior context available."
