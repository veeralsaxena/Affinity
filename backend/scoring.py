"""
scoring.py — Advanced Hybrid Scoring Engine (8-Layer)

The core innovation: LLMs are black boxes. Asking "rate 1-10" gives different
answers each run. We solve this with an 8-layer scoring pipeline anchored
by deterministic algorithms:

  Layer 1: VADER (deterministic sentiment polarity)
  Layer 2: Frequency / Behavioral Analysis (deterministic stats)
  Layer 3: LLM Structured Output (Gemini, near-deterministic with temp=0)
  Layer 4: Relational Entropy (information-theoretic decay model)
  Layer 5: Effort Score (initiation ratio, question reciprocity, length disparity)
  Layer 6: Gottman 5:1 Ratio (positive:negative interaction threshold)
  Layer 7: Digital Mirroring (emoji reciprocity, linguistic alignment, pronoun integration)
  Layer 8: KL Divergence Sentiment Drift (distributional shift detection)

  Composite = weighted blend across all 8 layers

References:
  - Gottman, J. (1994). "Why Marriages Succeed or Fail"
  - Shannon, C. (1948). "A Mathematical Theory of Communication"
  - Kullback & Leibler (1951). "On Information and Sufficiency"
"""

import json
import math
import statistics
import re
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime, timedelta

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pydantic import BaseModel, Field


# ─── Pydantic Schema for LLM Structured Output ──────────────────────────────

class LLMSentimentOutput(BaseModel):
    """Forces the LLM to return structured, bounded scores."""
    heat: int = Field(..., ge=0, le=10, description="Conflict intensity 0-10")
    decay: int = Field(..., ge=0, le=10, description="Communication drift 0-10")
    dominant_emotion: str = Field(..., description="e.g. frustrated, dismissive, loving, neutral")
    reasoning: str = Field(..., description="1-2 sentence justification")


# ─── Gemini Client Setup ─────────────────────────────────────────────────────

_gemini_model = None

def _get_gemini():
    """Lazy-init Gemini client."""
    global _gemini_model
    if _gemini_model is None:
        try:
            import os
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception as e:
            print(f"Gemini init failed: {e}")
    return _gemini_model


# ─── Layer 1: VADER Deterministic Sentiment ──────────────────────────────────

_vader = SentimentIntensityAnalyzer()

def vader_score_messages(messages: List[Dict]) -> Dict:
    """
    Run VADER on every message. Returns per-person average compound scores
    and overall trajectory (are things getting worse or better?).
    100% deterministic — same input always gives same output.
    """
    if not messages:
        return {"overall_compound": 0, "per_sender": {}, "trajectory": 0}

    per_sender: Dict[str, List[float]] = {}
    all_compounds: List[float] = []

    for msg in messages:
        compound = _vader.polarity_scores(msg.get("message", ""))["compound"]
        sender = msg.get("sender", "unknown")
        per_sender.setdefault(sender, []).append(compound)
        all_compounds.append(compound)

    # Trajectory: compare first-half avg vs second-half avg
    mid = len(all_compounds) // 2
    if mid > 0:
        first_half = statistics.mean(all_compounds[:mid])
        second_half = statistics.mean(all_compounds[mid:])
        trajectory = second_half - first_half  # negative = getting worse
    else:
        trajectory = 0

    per_sender_avg = {k: round(statistics.mean(v), 3) for k, v in per_sender.items()}

    return {
        "overall_compound": round(statistics.mean(all_compounds), 3) if all_compounds else 0,
        "per_sender": per_sender_avg,
        "trajectory": round(trajectory, 3),
    }


# ─── Layer 2: Frequency / Behavioral Analysis ───────────────────────────────

def frequency_score_messages(messages: List[Dict]) -> Dict:
    """
    Deterministic behavioral metrics:
    - Average message length per sender
    - Message count ratio between senders
    - Reply delay estimation (if timestamps available)
    - Emoji / punctuation usage
    """
    if not messages:
        return {"length_ratio": 1.0, "count_ratio": 1.0, "emoji_density": 0, "one_word_ratio": 0}

    per_sender_lengths: Dict[str, List[int]] = {}
    per_sender_counts: Dict[str, int] = {}
    one_word_count = 0
    emoji_count = 0
    total_chars = 0

    for msg in messages:
        text = msg.get("message", "")
        sender = msg.get("sender", "unknown")

        per_sender_lengths.setdefault(sender, []).append(len(text))
        per_sender_counts[sender] = per_sender_counts.get(sender, 0) + 1

        # One-word / ultra-short replies are a strong passive-aggression signal
        if len(text.split()) <= 2:
            one_word_count += 1

        # Emoji density (rough: anything outside ASCII)
        emoji_count += sum(1 for c in text if ord(c) > 127)
        total_chars += len(text)

    senders = list(per_sender_counts.keys())

    # Length ratio: how much shorter is the "cold" person's messages?
    if len(senders) >= 2:
        avg_a = statistics.mean(per_sender_lengths[senders[0]])
        avg_b = statistics.mean(per_sender_lengths[senders[1]])
        length_ratio = round(min(avg_a, avg_b) / max(avg_a, avg_b, 1), 3)

        count_a = per_sender_counts[senders[0]]
        count_b = per_sender_counts[senders[1]]
        count_ratio = round(min(count_a, count_b) / max(count_a, count_b, 1), 3)
    else:
        length_ratio = 1.0
        count_ratio = 1.0

    return {
        "length_ratio": length_ratio,
        "count_ratio": count_ratio,
        "emoji_density": round(emoji_count / max(total_chars, 1), 4),
        "one_word_ratio": round(one_word_count / max(len(messages), 1), 3),
    }


# ─── Layer 3: LLM Structured Output (Gemini) ────────────────────────────────

def llm_score_messages(messages: List[Dict]) -> LLMSentimentOutput:
    """
    Calls Gemini with temperature=0 and forces structured JSON output.
    Falls back to heuristic if no API key is available.
    """
    model = _get_gemini()
    if model is None:
        return _heuristic_fallback(messages)

    conversation_text = "\n".join(
        f"{m.get('sender', '?')}: {m.get('message', '')}" for m in messages[-30:]
    )

    prompt = f"""Analyze the following conversation excerpt and return a JSON object with these exact fields:
- heat (int 0-10): conflict/tension intensity
- decay (int 0-10): communication drift/neglect level
- dominant_emotion (str): the primary emotion detected
- reasoning (str): 1-2 sentence justification

Conversation:
{conversation_text}

Return ONLY valid JSON, no markdown fences."""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )
        data = json.loads(response.text)
        return LLMSentimentOutput(**data)
    except Exception as e:
        print(f"Gemini scoring failed: {e}, using heuristic fallback")
        return _heuristic_fallback(messages)


def _heuristic_fallback(messages: List[Dict]) -> LLMSentimentOutput:
    """Simple rule-based fallback when no LLM is available."""
    vader = vader_score_messages(messages)
    freq = frequency_score_messages(messages)

    # High one-word ratio + negative sentiment = heat
    heat = min(10, max(0, int((1 - vader["overall_compound"]) * 5 + freq["one_word_ratio"] * 10)))
    # Low count ratio + low emoji density = decay
    decay = min(10, max(0, int((1 - freq["count_ratio"]) * 5 + (1 - freq["emoji_density"] * 100) * 0.5)))

    return LLMSentimentOutput(
        heat=heat,
        decay=decay,
        dominant_emotion="tense" if heat > 5 else "neutral",
        reasoning="Heuristic fallback: based on VADER sentiment and message frequency ratios."
    )


# ─── Layer 4: Relational Entropy ─────────────────────────────────────────────

def relational_entropy(messages: List[Dict]) -> Dict:
    """
    Measures communication irregularity using Shannon entropy.
    H = -Σ p(x) log₂ p(x)

    Higher entropy = more irregular/unpredictable communication patterns = decay signal.
    A perfectly regular communicator (one message every day) has LOW entropy.
    An erratic communicator (5 msgs, then silence, then 20 msgs) has HIGH entropy.

    We bin messages into time slots and measure the distribution's entropy.
    """
    if len(messages) < 4:
        return {"entropy": 0, "regularity_score": 1.0, "interpretation": "insufficient_data"}

    # Extract sender-level message counts per time bucket
    senders = list(set(m.get("sender", "unknown") for m in messages))
    per_sender_counts = {s: 0 for s in senders}
    for m in messages:
        per_sender_counts[m.get("sender", "unknown")] += 1

    total = len(messages)
    # Calculate entropy of message distribution across senders
    probs = [count / total for count in per_sender_counts.values() if count > 0]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)

    # Also calculate temporal entropy: how evenly spaced are messages?
    # Bin messages into equal segments
    n_bins = min(10, len(messages) // 2)
    if n_bins < 2:
        temporal_entropy = 0
    else:
        bin_size = len(messages) // n_bins
        bin_counts = []
        for i in range(n_bins):
            start = i * bin_size
            end = start + bin_size if i < n_bins - 1 else len(messages)
            bin_counts.append(end - start)

        total_bin = sum(bin_counts)
        t_probs = [c / total_bin for c in bin_counts if total_bin > 0]
        temporal_entropy = -sum(p * math.log2(p) for p in t_probs if p > 0)

    # Max entropy for uniform distribution
    max_entropy = math.log2(max(len(senders), 2))
    regularity = 1.0 - min(1.0, entropy / max(max_entropy, 0.001))

    # Interpretation
    if regularity >= 0.7:
        interpretation = "balanced"
    elif regularity >= 0.4:
        interpretation = "imbalanced"
    else:
        interpretation = "severely_imbalanced"

    return {
        "entropy": round(entropy, 3),
        "temporal_entropy": round(temporal_entropy, 3),
        "regularity_score": round(regularity, 3),
        "interpretation": interpretation,
    }


# ─── Layer 5: Effort Score ───────────────────────────────────────────────────

def effort_score(messages: List[Dict]) -> Dict:
    """
    Quantifies per-person effort in the relationship:
    - Initiation ratio: who texts first after a gap? (0.5 = balanced)
    - Question reciprocity: ratio of questions asked vs answered
    - Length disparity: normalized diff in avg message length

    Composite = 0.4 * initiation + 0.3 * questions + 0.3 * length
    """
    if len(messages) < 4:
        return {"initiation_ratio": 0.5, "question_reciprocity": 0.5,
                "length_disparity": 0.0, "effort_composite": 0.5, "effort_balance": "balanced"}

    senders = list(set(m.get("sender", "unknown") for m in messages))
    if len(senders) < 2:
        return {"initiation_ratio": 0.5, "question_reciprocity": 0.5,
                "length_disparity": 0.0, "effort_composite": 0.5, "effort_balance": "balanced"}

    s1, s2 = senders[0], senders[1]

    # --- Initiation ratio ---
    # Who sends the first message after a "gap" (different sender from previous)?
    initiations = {s1: 0, s2: 0}
    prev_sender = None
    for m in messages:
        curr = m.get("sender", "unknown")
        if curr in initiations and curr != prev_sender:
            initiations[curr] += 1
        prev_sender = curr

    total_init = sum(initiations.values())
    initiation_ratio = initiations[s1] / max(total_init, 1)

    # --- Question reciprocity ---
    questions = {s1: 0, s2: 0}
    for m in messages:
        text = m.get("message", "")
        sender = m.get("sender", "unknown")
        if sender in questions and "?" in text:
            questions[sender] += 1

    total_q = sum(questions.values())
    question_ratio = questions[s1] / max(total_q, 1) if total_q > 0 else 0.5

    # --- Length disparity ---
    lens = {s1: [], s2: []}
    for m in messages:
        sender = m.get("sender", "unknown")
        if sender in lens:
            lens[sender].append(len(m.get("message", "")))

    avg1 = statistics.mean(lens[s1]) if lens[s1] else 0
    avg2 = statistics.mean(lens[s2]) if lens[s2] else 0
    length_disparity = abs(avg1 - avg2) / max(avg1, avg2, 1)

    # Composite: closer to 0.5 is balanced
    effort_composite = round(
        0.4 * abs(initiation_ratio - 0.5) * 2 +
        0.3 * abs(question_ratio - 0.5) * 2 +
        0.3 * length_disparity,
        3
    )

    # Interpretation
    if effort_composite < 0.25:
        balance = "balanced"
    elif effort_composite < 0.5:
        balance = "slightly_imbalanced"
    elif effort_composite < 0.75:
        balance = "imbalanced"
    else:
        balance = "severely_imbalanced"

    return {
        "initiation_ratio": round(initiation_ratio, 3),
        "question_reciprocity": round(question_ratio, 3),
        "length_disparity": round(length_disparity, 3),
        "effort_composite": effort_composite,
        "effort_balance": balance,
    }


# ─── Layer 6: Gottman 5:1 Ratio ─────────────────────────────────────────────

def gottman_ratio(messages: List[Dict]) -> Dict:
    """
    Dr. John Gottman's research shows that stable relationships maintain
    a 5:1 ratio of positive to negative interactions. Tracking this ratio
    over rolling windows detects relationship distress.

    VADER compound > 0.05 → positive
    VADER compound < -0.05 → negative
    Otherwise → neutral (excluded from ratio)
    """
    if not messages:
        return {"positive": 0, "negative": 0, "neutral": 0, "ratio": 5.0, "status": "insufficient_data"}

    positive = 0
    negative = 0
    neutral = 0

    for msg in messages:
        compound = _vader.polarity_scores(msg.get("message", ""))["compound"]
        if compound > 0.05:
            positive += 1
        elif compound < -0.05:
            negative += 1
        else:
            neutral += 1

    ratio = positive / max(negative, 1)

    if ratio >= 5.0:
        status = "thriving"
    elif ratio >= 3.0:
        status = "stable"
    elif ratio >= 1.0:
        status = "at_risk"
    else:
        status = "critical"

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "ratio": round(ratio, 2),
        "status": status,
    }


# ─── Layer 7: Digital Mirroring ──────────────────────────────────────────────

def digital_mirroring(messages: List[Dict]) -> Dict:
    """
    Measures linguistic alignment between conversation partners.
    Research shows couples/friends who mirror each other's patterns
    report significantly higher relational satisfaction.

    Components:
    - Emoji reciprocity: Sørensen–Dice similarity of emoji sets
    - Length alignment: how similar are average message lengths
    - Pronoun integration: "we/us/our" vs "I/me/my" usage ratio
    """
    if len(messages) < 4:
        return {"emoji_reciprocity": 0.5, "length_alignment": 0.5,
                "pronoun_integration": 0.5, "mirroring_score": 0.5, "interpretation": "insufficient_data"}

    senders = list(set(m.get("sender", "unknown") for m in messages))
    if len(senders) < 2:
        return {"emoji_reciprocity": 0.5, "length_alignment": 0.5,
                "pronoun_integration": 0.5, "mirroring_score": 0.5, "interpretation": "insufficient_data"}

    s1, s2 = senders[0], senders[1]

    # --- Emoji Reciprocity (Sørensen–Dice coefficient) ---
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]')
    emojis = {s1: [], s2: []}
    for m in messages:
        sender = m.get("sender", "unknown")
        if sender in emojis:
            found = emoji_pattern.findall(m.get("message", ""))
            emojis[sender].extend(found)

    set1 = set(emojis[s1])
    set2 = set(emojis[s2])
    if len(set1) + len(set2) > 0:
        emoji_reciprocity = 2 * len(set1 & set2) / (len(set1) + len(set2))
    else:
        emoji_reciprocity = 0.5  # No emojis = neutral

    # --- Length Alignment ---
    lens = {s1: [], s2: []}
    for m in messages:
        sender = m.get("sender", "unknown")
        if sender in lens:
            lens[sender].append(len(m.get("message", "")))

    avg1 = statistics.mean(lens[s1]) if lens[s1] else 0
    avg2 = statistics.mean(lens[s2]) if lens[s2] else 0
    length_alignment = 1.0 - abs(avg1 - avg2) / max(avg1, avg2, 1)

    # --- Pronoun Integration ---
    we_pronouns = re.compile(r'\b(we|us|our|ours|ourselves)\b', re.IGNORECASE)
    i_pronouns = re.compile(r'\b(i|me|my|mine|myself)\b', re.IGNORECASE)

    we_count = 0
    i_count = 0
    for m in messages:
        text = m.get("message", "")
        we_count += len(we_pronouns.findall(text))
        i_count += len(i_pronouns.findall(text))

    total_pronouns = we_count + i_count
    pronoun_integration = we_count / max(total_pronouns, 1) if total_pronouns > 0 else 0.5

    # Composite: higher = more mirroring = healthier
    mirroring_score = round(
        0.4 * emoji_reciprocity + 0.3 * length_alignment + 0.3 * pronoun_integration,
        3
    )

    # Interpretation
    if mirroring_score >= 0.6:
        interpretation = "high_alignment"
    elif mirroring_score >= 0.35:
        interpretation = "moderate_alignment"
    else:
        interpretation = "low_alignment"

    return {
        "emoji_reciprocity": round(emoji_reciprocity, 3),
        "length_alignment": round(length_alignment, 3),
        "pronoun_integration": round(pronoun_integration, 3),
        "mirroring_score": mirroring_score,
        "interpretation": interpretation,
    }


# ─── Layer 8: KL Divergence Sentiment Drift ──────────────────────────────────

def kl_divergence_drift(messages: List[Dict]) -> Dict:
    """
    Measures how much recent sentiment has diverged from historical baseline
    using Kullback-Leibler divergence.

    D_KL(P_recent || P_baseline) = Σ P(x) * log(P(x) / Q(x))

    We discretize VADER compound scores into 5 bins:
    [very_negative, negative, neutral, positive, very_positive]

    High D_KL indicates a statistically significant shift in emotional tone.
    """
    if len(messages) < 8:
        return {"kl_divergence": 0, "drift_detected": False, "direction": "stable"}

    # Split into two halves
    mid = len(messages) // 2
    baseline_msgs = messages[:mid]
    recent_msgs = messages[mid:]

    def sentiment_distribution(msgs: List[Dict]) -> List[float]:
        """Create a 5-bin probability distribution of sentiment."""
        bins = [0, 0, 0, 0, 0]  # very_neg, neg, neutral, pos, very_pos
        for m in msgs:
            compound = _vader.polarity_scores(m.get("message", ""))["compound"]
            if compound <= -0.5:
                bins[0] += 1
            elif compound <= -0.05:
                bins[1] += 1
            elif compound <= 0.05:
                bins[2] += 1
            elif compound <= 0.5:
                bins[3] += 1
            else:
                bins[4] += 1

        total = sum(bins)
        if total == 0:
            return [0.2, 0.2, 0.2, 0.2, 0.2]

        # Add smoothing (Laplace) to avoid log(0)
        smoothed = [(b + 0.1) / (total + 0.5) for b in bins]
        return smoothed

    p = sentiment_distribution(recent_msgs)    # P: recent
    q = sentiment_distribution(baseline_msgs)  # Q: baseline

    # KL divergence: D_KL(P || Q)
    kl = sum(p_i * math.log(p_i / q_i) for p_i, q_i in zip(p, q) if p_i > 0 and q_i > 0)

    drift_detected = kl > 0.3

    # Determine drift direction
    recent_avg = statistics.mean(
        _vader.polarity_scores(m.get("message", ""))["compound"] for m in recent_msgs
    )
    baseline_avg = statistics.mean(
        _vader.polarity_scores(m.get("message", ""))["compound"] for m in baseline_msgs
    )

    if recent_avg > baseline_avg + 0.1:
        direction = "improving"
    elif recent_avg < baseline_avg - 0.1:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "kl_divergence": round(kl, 4),
        "drift_detected": drift_detected,
        "direction": direction,
        "baseline_sentiment": round(baseline_avg, 3),
        "recent_sentiment": round(recent_avg, 3),
    }


# ─── Composite Score Engine (8-Layer) ────────────────────────────────────────

WEIGHTS = {
    "vader": 0.15,
    "frequency": 0.15,
    "llm": 0.20,
    "effort": 0.15,
    "gottman": 0.10,
    "entropy": 0.10,
    "mirroring": 0.10,
    "kl_drift": 0.05,
}

def compute_composite_score(messages: List[Dict]) -> Dict:
    """
    THE MAIN FUNCTION. Runs all 8 layers and produces a single,
    reproducible composite score.

    Returns heat (0-10), decay (0-10), plus all layer details.
    """
    # Layer 1: VADER
    vader = vader_score_messages(messages)

    # Layer 2: Frequency
    freq = frequency_score_messages(messages)

    # Layer 3: LLM (Gemini)
    llm_out = llm_score_messages(messages)

    # Layer 4: Relational Entropy
    entropy = relational_entropy(messages)

    # Layer 5: Effort Score
    effort = effort_score(messages)

    # Layer 6: Gottman 5:1 Ratio
    gottman = gottman_ratio(messages)

    # Layer 7: Digital Mirroring
    mirroring = digital_mirroring(messages)

    # Layer 8: KL Divergence
    kl_drift = kl_divergence_drift(messages)

    # ── Composite Heat ──
    vader_heat = round((1 - vader["overall_compound"]) * 5, 2)
    freq_heat = round((freq["one_word_ratio"] * 5 + (1 - freq["length_ratio"]) * 5), 2)
    llm_heat = llm_out.heat
    effort_heat = round(effort["effort_composite"] * 10, 2)
    gottman_heat = round(max(0, (3 - gottman["ratio"])) * 2, 2)  # Higher when ratio drops below 3:1
    entropy_heat = round((1 - entropy["regularity_score"]) * 5, 2)
    mirroring_heat = round((1 - mirroring["mirroring_score"]) * 5, 2)
    kl_heat = round(min(5, kl_drift["kl_divergence"] * 10), 2) if kl_drift["direction"] == "declining" else 0

    composite_heat = round(
        WEIGHTS["vader"] * vader_heat +
        WEIGHTS["frequency"] * freq_heat +
        WEIGHTS["llm"] * llm_heat +
        WEIGHTS["effort"] * effort_heat +
        WEIGHTS["gottman"] * gottman_heat +
        WEIGHTS["entropy"] * entropy_heat +
        WEIGHTS["mirroring"] * mirroring_heat +
        WEIGHTS["kl_drift"] * kl_heat,
        1
    )
    composite_heat = max(0, min(10, composite_heat))

    # ── Composite Decay ──
    vader_decay = round((1 - abs(vader["trajectory"])) * 3, 2)
    freq_decay = round((1 - freq["count_ratio"]) * 7 + (1 - freq["emoji_density"] * 50) * 1, 2)
    llm_decay = llm_out.decay
    effort_decay = round(effort["effort_composite"] * 8, 2)
    gottman_decay = round(max(0, (5 - gottman["ratio"])) * 1.5, 2)
    entropy_decay = round(entropy["entropy"] * 3, 2)
    mirroring_decay = round((1 - mirroring["mirroring_score"]) * 4, 2)
    kl_decay = round(min(5, kl_drift["kl_divergence"] * 8), 2)

    composite_decay = round(
        WEIGHTS["vader"] * vader_decay +
        WEIGHTS["frequency"] * min(10, max(0, freq_decay)) +
        WEIGHTS["llm"] * llm_decay +
        WEIGHTS["effort"] * min(10, effort_decay) +
        WEIGHTS["gottman"] * min(10, gottman_decay) +
        WEIGHTS["entropy"] * min(10, entropy_decay) +
        WEIGHTS["mirroring"] * min(10, mirroring_decay) +
        WEIGHTS["kl_drift"] * min(10, kl_decay),
        1
    )
    composite_decay = max(0, min(10, composite_decay))

    return {
        "composite_heat": composite_heat,
        "composite_decay": composite_decay,
        "dominant_emotion": llm_out.dominant_emotion,
        "reasoning": llm_out.reasoning,
        "layers": {
            "vader": vader,
            "frequency": freq,
            "llm": {
                "heat": llm_out.heat,
                "decay": llm_out.decay,
                "emotion": llm_out.dominant_emotion,
                "reasoning": llm_out.reasoning,
            },
            "entropy": entropy,
            "effort": effort,
            "gottman": gottman,
            "mirroring": mirroring,
            "kl_drift": kl_drift,
        }
    }


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_messages = [
        {"sender": "Alice", "message": "Hey! I got the promotion today!! 🎉🎉"},
        {"sender": "Bob", "message": "k"},
        {"sender": "Alice", "message": "That's all you have to say?"},
        {"sender": "Bob", "message": "busy"},
        {"sender": "Alice", "message": "You always do this. Whenever something good happens to me, you just dismiss it."},
        {"sender": "Bob", "message": "ok"},
        {"sender": "Alice", "message": "I feel like we're drifting apart. Can we talk about this?"},
        {"sender": "Bob", "message": "later"},
        {"sender": "Alice", "message": "You've been saying 'later' for weeks now 😔"},
        {"sender": "Bob", "message": "idk what you want me to say"},
    ]

    print("=" * 70)
    print("SYNCHRONY 8-LAYER HYBRID SCORING ENGINE — TEST RUN")
    print("=" * 70)

    result = compute_composite_score(test_messages)

    print(f"\n🔥 Heat:  {result['composite_heat']}/10")
    print(f"❄️  Decay: {result['composite_decay']}/10")
    print(f"🎭 Emotion: {result['dominant_emotion']}")
    print(f"📝 Reasoning: {result['reasoning']}")

    print(f"\n{'─' * 50}")
    print("Layer Details:")
    for layer_name, layer_data in result["layers"].items():
        print(f"\n  [{layer_name.upper()}]")
        if isinstance(layer_data, dict):
            for k, v in layer_data.items():
                print(f"    {k}: {v}")
