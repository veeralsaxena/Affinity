"""
graph.py — Enhanced LangGraph State Machine for Synchrony

Multi-agent orchestration with 10 nodes implementing the full
Autonomous Personal Relationship Intelligence pipeline:

  quantify → entropy_calc → effort_calc → route →
    [conflict_resolve | re_engage | log_memory] →
    style_analyze → ghost_write → memory_log → output

Key innovations over v1:
  - 8-layer composite scoring (not just 3)
  - Relational Entropy + KL Divergence calculations
  - Effort Score + Gottman 5:1 + Digital Mirroring
  - Stylistic mimicry (matches user's exact writing voice)
  - Tiered memory (episodic + semantic) integration
  - Gemini 2.0 Flash (replaces OpenAI GPT-4o)
"""

import os
import json
from typing import TypedDict, Literal, List, Dict, Optional

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from scoring import compute_composite_score
from style_analyzer import analyze_style, StyleProfile

load_dotenv()

# ─── Gemini Client Setup ────────────────────────────────────────────────────

_gemini_model = None

def _get_gemini():
    """Lazy-init Gemini client for ghost writing."""
    global _gemini_model
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception as e:
            print(f"Gemini init failed: {e}")
    return _gemini_model


# ─── State Schema ────────────────────────────────────────────────────────────

class RelationshipState(TypedDict):
    """The shared state that flows through every node in the graph."""
    # Input
    raw_messages: List[Dict]
    user_id: str
    target_person: str

    # Scoring (set by quantify node)
    composite_heat: float
    composite_decay: float
    dominant_emotion: str
    reasoning: str
    scoring_layers: Dict

    # Advanced metrics (set by entropy/effort nodes)
    entropy_data: Dict
    effort_data: Dict
    gottman_data: Dict
    mirroring_data: Dict
    kl_drift_data: Dict

    # Routing decision
    route: str  # "conflict" | "decay" | "stable"

    # Style analysis
    style_profile: Dict

    # Agent outputs
    analysis_report: str
    suggested_nudges: List[str]
    memory_entries: List[str]

    # Memory context
    memory_context: str

    # Final
    dashboard_payload: Dict


# ─── Node: Quantify ──────────────────────────────────────────────────────────

def quantify_node(state: RelationshipState) -> dict:
    """
    Runs the 8-Layer Hybrid Scoring Engine on the raw messages.
    This is the DETERMINISTIC heart of the system.
    """
    messages = state["raw_messages"]
    result = compute_composite_score(messages)

    return {
        "composite_heat": result["composite_heat"],
        "composite_decay": result["composite_decay"],
        "dominant_emotion": result["dominant_emotion"],
        "reasoning": result["reasoning"],
        "scoring_layers": result["layers"],
        # Extract individual layer data for downstream nodes
        "entropy_data": result["layers"].get("entropy", {}),
        "effort_data": result["layers"].get("effort", {}),
        "gottman_data": result["layers"].get("gottman", {}),
        "mirroring_data": result["layers"].get("mirroring", {}),
        "kl_drift_data": result["layers"].get("kl_drift", {}),
    }


# ─── Node: Router (Conditional — NO LLM) ────────────────────────────────────

def route_node(state: RelationshipState) -> dict:
    """
    Pure Python conditional logic. This is what makes it deterministic.
    The LLM does NOT decide where to go — the scores do.

    Enhanced with Gottman ratio and effort balance for more nuanced routing.
    """
    heat = state["composite_heat"]
    decay = state["composite_decay"]
    gottman_status = state.get("gottman_data", {}).get("status", "stable")
    effort_balance = state.get("effort_data", {}).get("effort_balance", "balanced")

    # Conflict takes priority
    if heat >= 6 or gottman_status == "critical":
        return {"route": "conflict"}
    elif decay >= 6 or effort_balance in ("severely_imbalanced", "imbalanced"):
        return {"route": "decay"}
    else:
        return {"route": "stable"}


def get_route(state: RelationshipState) -> str:
    """Edge condition function for LangGraph."""
    return state["route"]


# ─── Node: Conflict Resolver ─────────────────────────────────────────────────

def conflict_resolve_node(state: RelationshipState) -> dict:
    """
    Activated when Heat >= 6 or Gottman ratio is critical.
    Provides detailed conflict analysis with all layer data.
    """
    gottman = state.get("gottman_data", {})
    mirroring = state.get("mirroring_data", {})
    kl = state.get("kl_drift_data", {})

    report = (
        f"⚠️ CONFLICT DETECTED (Heat: {state['composite_heat']}/10)\n"
        f"Emotion: {state['dominant_emotion']}\n"
        f"Analysis: {state['reasoning']}\n\n"
        f"📊 Gottman Ratio: {gottman.get('ratio', '?')} "
        f"(+{gottman.get('positive', 0)} / -{gottman.get('negative', 0)}) → {gottman.get('status', '?')}\n"
        f"🪞 Mirroring: {mirroring.get('mirroring_score', '?')} → {mirroring.get('interpretation', '?')}\n"
        f"📈 Sentiment Drift: {kl.get('direction', 'stable')} (KL={kl.get('kl_divergence', 0)})\n\n"
        f"The conversation shows significant tension. "
        f"Passive-aggressive patterns or dismissive language detected."
    )

    memories = [
        f"Conflict event — Heat {state['composite_heat']}/10, "
        f"Emotion: {state['dominant_emotion']}, "
        f"Gottman: {gottman.get('ratio', '?')}:1"
    ]

    return {"analysis_report": report, "memory_entries": memories}


# ─── Node: Re-Engager ────────────────────────────────────────────────────────

def re_engage_node(state: RelationshipState) -> dict:
    """
    Activated when Decay >= 6 or effort is severely imbalanced.
    Uses entropy and effort data for detailed drift analysis.
    """
    entropy = state.get("entropy_data", {})
    effort = state.get("effort_data", {})
    kl = state.get("kl_drift_data", {})

    report = (
        f"🕐 COMMUNICATION DECAY DETECTED (Decay: {state['composite_decay']}/10)\n\n"
        f"📊 Effort Balance: {effort.get('effort_balance', '?')} "
        f"(initiation: {effort.get('initiation_ratio', '?')}, "
        f"questions: {effort.get('question_reciprocity', '?')})\n"
        f"🔀 Entropy: {entropy.get('regularity_score', '?')} → {entropy.get('interpretation', '?')}\n"
        f"📈 Sentiment: {kl.get('direction', 'stable')} "
        f"(baseline: {kl.get('baseline_sentiment', '?')} → recent: {kl.get('recent_sentiment', '?')})\n\n"
        f"Communication frequency has dropped below baseline. "
        f"Message count ratios and response patterns suggest drifting apart."
    )

    memories = [
        f"Decay event — Decay {state['composite_decay']}/10, "
        f"Effort: {effort.get('effort_balance', '?')}, "
        f"Entropy regularity: {entropy.get('regularity_score', '?')}"
    ]

    return {"analysis_report": report, "memory_entries": memories}


# ─── Node: Memory Logger (Stable State) ──────────────────────────────────────

def log_memory_node(state: RelationshipState) -> dict:
    """
    Activated when both Heat and Decay are low. Logs healthy observations
    with full layer detail.
    """
    gottman = state.get("gottman_data", {})
    mirroring = state.get("mirroring_data", {})

    report = (
        f"✅ RELATIONSHIP STABLE (Heat: {state['composite_heat']}/10, Decay: {state['composite_decay']}/10)\n"
        f"Emotion: {state['dominant_emotion']}\n"
        f"Gottman: {gottman.get('ratio', '?')}:1 ({gottman.get('status', '?')})\n"
        f"Mirroring: {mirroring.get('mirroring_score', '?')} ({mirroring.get('interpretation', '?')})\n"
        f"No intervention required."
    )

    memories = [
        f"Stable checkpoint — Heat {state['composite_heat']}, Decay {state['composite_decay']}, "
        f"Gottman {gottman.get('ratio', '?')}:1"
    ]

    return {
        "analysis_report": report,
        "memory_entries": memories,
        "suggested_nudges": [],
    }


# ─── Node: Style Analyzer ────────────────────────────────────────────────────

def style_analyze_node(state: RelationshipState) -> dict:
    """
    Builds the user's digital fingerprint from their historical messages.
    This profile is injected into the Ghost Writer to achieve stylistic mimicry.
    """
    messages = state["raw_messages"]
    # Analyze the style (defaults to most frequent sender)
    profile = analyze_style(messages)
    return {"style_profile": profile.model_dump()}


# ─── Node: Ghost Writer ──────────────────────────────────────────────────────

def ghost_write_node(state: RelationshipState) -> dict:
    """
    Generates 3 personalized message drafts using Gemini.

    Key innovation: injects the user's StyleProfile so drafts are
    linguistically indistinguishable from manually typed text.
    This eliminates the "algorithmic uncanny valley".
    """
    route = state["route"]
    emotion = state["dominant_emotion"]
    style = state.get("style_profile", {})
    style_summary = style.get("style_summary", "No style data available.")
    memory_ctx = state.get("memory_context", "")

    model = _get_gemini()
    if model:
        prompt = f"""You are an expert at writing personal messages that sound 100% human.
You must EXACTLY match the writing style described below. This is critical —
the recipient must not be able to tell this was AI-generated.

WRITING STYLE TO MATCH:
{style_summary}
- Capitalization: {style.get('capitalization', 'mixed')}
- Punctuation: {style.get('punctuation_style', 'standard')}
- Emoji frequency: {style.get('emoji_frequency', 0.2)} per message
- Top emojis: {', '.join(style.get('top_emojis', []))}
- Uses slang: {style.get('uses_slang', False)}
- Common fillers: {', '.join(style.get('common_fillers', []))}
- Average message length: {style.get('avg_word_count', 8)} words

RELATIONSHIP CONTEXT:
Route: {route}
Emotion: {emotion}
Report: {state['analysis_report']}
{f'Memory Context: {memory_ctx}' if memory_ctx else ''}

Task: Draft exactly 3 text messages the user could send to {"de-escalate the conflict" if route == "conflict" else "re-engage after silence"}.
Each message must PERFECTLY match the writing style above.
Messages should feel natural, spontaneous, and authentic.

Return a JSON object with key "nudges" containing an array of exactly 3 strings."""

        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                },
            )
            data = json.loads(response.text)
            nudges = data.get("nudges", [])[:3]
            return {"suggested_nudges": nudges}
        except Exception as e:
            print(f"Ghost writer Gemini call failed: {e}")

    # Template fallback
    if route == "conflict":
        return {"suggested_nudges": [
            "hey, i think we might be miscommunicating. can we talk about it?",
            "i didn't mean to come across that way. let me know when you're free to chat ❤️",
            "i value us too much to let this fester. wanna call tonight?",
        ]}
    else:
        return {"suggested_nudges": [
            "hey stranger 👋 been thinking about you. how's everything going?",
            "miss our convos tbh. wanna grab coffee this week?",
            "saw something today that reminded me of you haha. let's catch up soon!",
        ]}


# ─── Node: Dashboard Output ──────────────────────────────────────────────────

def output_node(state: RelationshipState) -> dict:
    """
    Packages the final state into a clean payload for the frontend dashboard.
    Includes all 8 scoring layers plus style and memory data.
    """
    payload = {
        "user_id": state.get("user_id", ""),
        "target_person": state.get("target_person", ""),
        "heat": state["composite_heat"],
        "decay": state["composite_decay"],
        "emotion": state["dominant_emotion"],
        "route": state["route"],
        "report": state["analysis_report"],
        "nudges": state.get("suggested_nudges", []),
        "memories": state.get("memory_entries", []),
        "scoring_layers": state.get("scoring_layers", {}),
        "style_profile": state.get("style_profile", {}),
        # Advanced metrics for dashboard
        "entropy": state.get("entropy_data", {}),
        "effort": state.get("effort_data", {}),
        "gottman": state.get("gottman_data", {}),
        "mirroring": state.get("mirroring_data", {}),
        "kl_drift": state.get("kl_drift_data", {}),
    }

    return {"dashboard_payload": payload}


# ─── Build the Graph ──────────────────────────────────────────────────────────

def build_graph():
    """
    Constructs and compiles the enhanced LangGraph state machine.

    Flow:
      quantify → route → [conflict_resolve | re_engage | log_memory]
        → style_analyze → ghost_write → output
    """
    graph = StateGraph(RelationshipState)

    # Add nodes
    graph.add_node("quantify", quantify_node)
    graph.add_node("route", route_node)
    graph.add_node("conflict_resolve", conflict_resolve_node)
    graph.add_node("re_engage", re_engage_node)
    graph.add_node("log_memory", log_memory_node)
    graph.add_node("style_analyze", style_analyze_node)
    graph.add_node("ghost_write", ghost_write_node)
    graph.add_node("output", output_node)

    # Set entry point
    graph.set_entry_point("quantify")

    # Edges
    graph.add_edge("quantify", "route")

    # Conditional routing — scores decide, NOT the LLM
    graph.add_conditional_edges(
        "route",
        get_route,
        {
            "conflict": "conflict_resolve",
            "decay": "re_engage",
            "stable": "log_memory",
        }
    )

    # After analysis → style analyze → ghost write (for conflict and decay)
    graph.add_edge("conflict_resolve", "style_analyze")
    graph.add_edge("re_engage", "style_analyze")
    graph.add_edge("log_memory", "output")  # Stable → skip ghost writer

    graph.add_edge("style_analyze", "ghost_write")
    graph.add_edge("ghost_write", "output")

    # Output → END
    graph.add_edge("output", END)

    return graph.compile()


# ─── Convenience Runner ──────────────────────────────────────────────────────

def analyze_relationship(
    raw_messages: List[Dict],
    user_id: str = "user_1",
    target_person: str = "friend_1",
) -> Dict:
    """
    Main entry point. Takes raw messages and runs the full 8-layer pipeline.
    Returns the dashboard payload.
    """
    app = build_graph()

    initial_state: RelationshipState = {
        "raw_messages": raw_messages,
        "user_id": user_id,
        "target_person": target_person,
        "composite_heat": 0,
        "composite_decay": 0,
        "dominant_emotion": "",
        "reasoning": "",
        "scoring_layers": {},
        "entropy_data": {},
        "effort_data": {},
        "gottman_data": {},
        "mirroring_data": {},
        "kl_drift_data": {},
        "route": "",
        "style_profile": {},
        "analysis_report": "",
        "suggested_nudges": [],
        "memory_entries": [],
        "memory_context": "",
        "dashboard_payload": {},
    }

    final_state = app.invoke(initial_state)
    return final_state["dashboard_payload"]


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_messages = [
        {"sender": "Alice", "message": "Hey! I got the promotion today!! 🎉🎉"},
        {"sender": "Bob", "message": "k"},
        {"sender": "Alice", "message": "That's all you have to say?"},
        {"sender": "Bob", "message": "busy"},
        {"sender": "Alice", "message": "You always do this. Whenever something good happens to me you just dismiss it."},
        {"sender": "Bob", "message": "ok"},
        {"sender": "Alice", "message": "I feel like we're drifting apart. Can we talk?"},
        {"sender": "Bob", "message": "later"},
        {"sender": "Alice", "message": "You've been saying 'later' for weeks 😔"},
        {"sender": "Bob", "message": "idk what you want me to say"},
    ]

    print("=" * 70)
    print("SYNCHRONY ENHANCED LANGGRAPH PIPELINE — 8-LAYER TEST")
    print("=" * 70)

    result = analyze_relationship(test_messages, "alice_123", "bob_456")

    print(f"\n🔥 Heat:  {result['heat']}/10")
    print(f"❄️  Decay: {result['decay']}/10")
    print(f"🎭 Emotion: {result['emotion']}")
    print(f"🛤️  Route: {result['route']}")
    print(f"\n📝 Report:\n{result['report']}")
    print(f"\n💬 Suggested Nudges:")
    for i, nudge in enumerate(result.get('nudges', []), 1):
        print(f"  {i}. {nudge}")

    print(f"\n📊 Advanced Metrics:")
    print(f"  Gottman Ratio: {result.get('gottman', {}).get('ratio', '?')}:1")
    print(f"  Mirroring: {result.get('mirroring', {}).get('mirroring_score', '?')}")
    print(f"  Effort Balance: {result.get('effort', {}).get('effort_balance', '?')}")
    print(f"  Entropy: {result.get('entropy', {}).get('regularity_score', '?')}")
    print(f"  KL Drift: {result.get('kl_drift', {}).get('direction', '?')}")

    if result.get("style_profile"):
        print(f"\n✍️ Style Profile:")
        print(f"  {result['style_profile'].get('style_summary', 'N/A')}")
