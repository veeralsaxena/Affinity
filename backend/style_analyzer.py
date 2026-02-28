"""
style_analyzer.py — User Digital Fingerprint Analyzer

Analyzes the user's historical messages to build a "StyleProfile" —
a mathematical representation of how they write. This profile is injected
into the Ghost Writer's prompt to achieve stylistic mimicry.

The key insight from the research: generic LLM outputs trigger the
"algorithmic uncanny valley" — recipients detect inauthenticity,
which actively damages trust. The Ghost Writer must mimic the user's
exact digital fingerprint.

Analyzed dimensions:
  - Capitalization patterns (all lowercase? Mixed? Proper?)
  - Average sentence length and punctuation style
  - Emoji frequency and preferred emojis
  - Slang/filler usage ("lol", "ngl", "tbh", "lowkey")
  - Contraction patterns ("don't" vs "do not")
  - Question frequency
  - Greeting/closing patterns
"""

import re
import statistics
from typing import List, Dict
from collections import Counter
from pydantic import BaseModel, Field


class StyleProfile(BaseModel):
    """Mathematical representation of a user's writing style."""
    capitalization: str = Field(description="'lowercase', 'mixed', 'proper', or 'uppercase'")
    avg_message_length: float = Field(description="Average message length in characters")
    avg_word_count: float = Field(description="Average words per message")
    punctuation_style: str = Field(description="'minimal', 'standard', or 'heavy'")
    emoji_frequency: float = Field(description="Emojis per message (avg)")
    top_emojis: List[str] = Field(default_factory=list, description="Most used emojis")
    uses_slang: bool = Field(description="Whether user uses slang")
    common_fillers: List[str] = Field(default_factory=list, description="Common filler words used")
    contraction_ratio: float = Field(description="0-1, how often contractions are used vs full forms")
    question_frequency: float = Field(description="Fraction of messages that contain questions")
    exclamation_frequency: float = Field(description="Fraction of messages with exclamation marks")
    ellipsis_usage: bool = Field(description="Whether user uses '...' frequently")
    style_summary: str = Field(description="Natural language summary for prompt injection")


_emoji_pattern = re.compile(
    r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
    r'\U0001F900-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
    r'\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]'
)

_slang_words = {
    "lol", "lmao", "ngl", "tbh", "lowkey", "highkey", "fr", "bruh",
    "smh", "imo", "wyd", "hmu", "ty", "thx", "omg", "btw", "ik",
    "rn", "istg", "nvm", "idk", "idc", "wdym", "fyi", "iirc",
    "bro", "dude", "fam", "vibe", "vibes", "slay", "lit", "goat",
    "bet", "cap", "no cap", "sus", "yolo", "fomo", "aight",
}

_contraction_patterns = re.compile(
    r"\b(don't|doesn't|didn't|wasn't|weren't|won't|wouldn't|couldn't|shouldn't|"
    r"can't|isn't|aren't|hasn't|haven't|hadn't|i'm|i've|i'll|i'd|"
    r"you're|you've|you'll|you'd|we're|we've|we'll|we'd|"
    r"they're|they've|they'll|they'd|he's|she's|it's|"
    r"that's|there's|here's|what's|where's|who's|how's|"
    r"let's|ain't|y'all|gonna|wanna|gotta|kinda|sorta)\b",
    re.IGNORECASE
)

_full_form_patterns = re.compile(
    r"\b(do not|does not|did not|was not|were not|will not|would not|could not|"
    r"should not|cannot|is not|are not|has not|have not|had not|"
    r"i am|i have|i will|i would|"
    r"you are|you have|you will|you would)\b",
    re.IGNORECASE
)


def analyze_style(messages: List[Dict], user_sender: str = None) -> StyleProfile:
    """
    Analyze a user's messages to build their digital fingerprint.

    Args:
        messages: List of message dicts with "sender" and "message" keys
        user_sender: The sender name to analyze (if None, picks the most frequent)
    """
    # Filter to user's messages only
    if user_sender is None:
        # Pick the most frequent sender
        sender_counts = Counter(m.get("sender", "unknown") for m in messages)
        user_sender = sender_counts.most_common(1)[0][0] if sender_counts else "unknown"

    user_msgs = [m.get("message", "") for m in messages if m.get("sender") == user_sender]

    if not user_msgs:
        return _default_profile()

    # ── Capitalization ──
    lowercase_count = sum(1 for m in user_msgs if m == m.lower())
    uppercase_count = sum(1 for m in user_msgs if m == m.upper() and len(m) > 1)
    proper_count = sum(1 for m in user_msgs if m and m[0].isupper() and m[1:] != m[1:].upper())

    if lowercase_count / len(user_msgs) > 0.7:
        capitalization = "lowercase"
    elif uppercase_count / len(user_msgs) > 0.3:
        capitalization = "uppercase"
    elif proper_count / len(user_msgs) > 0.5:
        capitalization = "proper"
    else:
        capitalization = "mixed"

    # ── Length stats ──
    avg_length = statistics.mean(len(m) for m in user_msgs)
    avg_words = statistics.mean(len(m.split()) for m in user_msgs)

    # ── Punctuation ──
    period_ratio = sum(m.count('.') for m in user_msgs) / max(len(user_msgs), 1)
    comma_ratio = sum(m.count(',') for m in user_msgs) / max(len(user_msgs), 1)
    if period_ratio + comma_ratio < 0.3:
        punctuation_style = "minimal"
    elif period_ratio + comma_ratio > 1.5:
        punctuation_style = "heavy"
    else:
        punctuation_style = "standard"

    # ── Emojis ──
    all_emojis = []
    for m in user_msgs:
        found = _emoji_pattern.findall(m)
        all_emojis.extend(found)
    emoji_freq = len(all_emojis) / max(len(user_msgs), 1)
    top_emojis = [e for e, _ in Counter(all_emojis).most_common(5)]

    # ── Slang ──
    slang_count = 0
    found_fillers = Counter()
    for m in user_msgs:
        words = set(re.findall(r'\b\w+\b', m.lower()))
        matched = words & _slang_words
        slang_count += len(matched)
        for s in matched:
            found_fillers[s] += 1
    uses_slang = slang_count / max(len(user_msgs), 1) > 0.1
    common_fillers = [w for w, _ in found_fillers.most_common(5)]

    # ── Contractions ──
    contraction_count = sum(len(_contraction_patterns.findall(m)) for m in user_msgs)
    full_form_count = sum(len(_full_form_patterns.findall(m)) for m in user_msgs)
    total_forms = contraction_count + full_form_count
    contraction_ratio = contraction_count / max(total_forms, 1) if total_forms > 0 else 0.5

    # ── Questions and exclamations ──
    question_freq = sum(1 for m in user_msgs if '?' in m) / max(len(user_msgs), 1)
    exclamation_freq = sum(1 for m in user_msgs if '!' in m) / max(len(user_msgs), 1)
    ellipsis_usage = sum(1 for m in user_msgs if '...' in m) / max(len(user_msgs), 1) > 0.1

    # ── Build natural language summary ──
    style_parts = []
    if capitalization == "lowercase":
        style_parts.append("writes in all lowercase")
    elif capitalization == "uppercase":
        style_parts.append("WRITES IN ALL CAPS frequently")
    elif capitalization == "proper":
        style_parts.append("uses proper capitalization")

    if punctuation_style == "minimal":
        style_parts.append("rarely uses punctuation")
    elif punctuation_style == "heavy":
        style_parts.append("uses lots of punctuation")

    if emoji_freq > 0.5:
        style_parts.append(f"uses emojis frequently (favorites: {', '.join(top_emojis[:3])})")
    elif emoji_freq < 0.1:
        style_parts.append("rarely uses emojis")

    if uses_slang:
        style_parts.append(f"uses slang like {', '.join(common_fillers[:3])}")

    if contraction_ratio > 0.7:
        style_parts.append("always uses contractions (don't, can't, won't)")
    elif contraction_ratio < 0.3:
        style_parts.append("prefers full forms over contractions")

    if question_freq > 0.3:
        style_parts.append("asks lots of questions")

    if ellipsis_usage:
        style_parts.append("uses '...' frequently")

    style_parts.append(f"average message is {int(avg_words)} words long")

    style_summary = "This person " + ", ".join(style_parts) + "."

    return StyleProfile(
        capitalization=capitalization,
        avg_message_length=round(avg_length, 1),
        avg_word_count=round(avg_words, 1),
        punctuation_style=punctuation_style,
        emoji_frequency=round(emoji_freq, 2),
        top_emojis=top_emojis,
        uses_slang=uses_slang,
        common_fillers=common_fillers,
        contraction_ratio=round(contraction_ratio, 2),
        question_frequency=round(question_freq, 2),
        exclamation_frequency=round(exclamation_freq, 2),
        ellipsis_usage=ellipsis_usage,
        style_summary=style_summary,
    )


def _default_profile() -> StyleProfile:
    return StyleProfile(
        capitalization="mixed",
        avg_message_length=40.0,
        avg_word_count=8.0,
        punctuation_style="standard",
        emoji_frequency=0.2,
        top_emojis=[],
        uses_slang=False,
        common_fillers=[],
        contraction_ratio=0.5,
        question_frequency=0.2,
        exclamation_frequency=0.1,
        ellipsis_usage=False,
        style_summary="Default style profile — no historical data available.",
    )
