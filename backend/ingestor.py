"""
ingestor.py — Multi-Source Data Ingestion Pipeline

Supports:
  1. WhatsApp exported .txt files (iOS + Android formats)
  2. Instagram exported .json files
  3. Audio/voice memo .mp3/.wav files → OpenAI Whisper transcription
"""

import re
import json
import os
from typing import List, Dict
from datetime import datetime


# ─── WhatsApp .txt Parser ────────────────────────────────────────────────────

class WhatsAppIngestor:
    """Parses exported WhatsApp chat histories (.txt)."""
    
    def __init__(self):
        # iOS: "[dd/mm/yy, hh:mm:ss] Name: Message"
        self.ios_pattern = re.compile(
            r'^\[(\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}:\d{2}(?:\s*[AP]M)?)\]\s*([^:]+):\s*(.+)$'
        )
        # Android: "dd/mm/yy, hh:mm - Name: Message"
        self.android_pattern = re.compile(
            r'^(\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}(?:\s*[aApP][mM])?)\s*-\s*([^:]+):\s*(.+)$'
        )
    
    def parse(self, text_content: str) -> List[Dict]:
        """Parse raw WhatsApp export text into structured messages."""
        messages = []
        current_msg = None
        
        for line in text_content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            ios_match = self.ios_pattern.match(line)
            android_match = self.android_pattern.match(line)
            
            if ios_match:
                if current_msg:
                    messages.append(current_msg)
                current_msg = {
                    "timestamp": ios_match.group(1),
                    "sender": ios_match.group(2).strip(),
                    "message": ios_match.group(3).strip(),
                    "source": "whatsapp",
                }
            elif android_match:
                if current_msg:
                    messages.append(current_msg)
                current_msg = {
                    "timestamp": android_match.group(1),
                    "sender": android_match.group(2).strip(),
                    "message": android_match.group(3).strip(),
                    "source": "whatsapp",
                }
            else:
                if current_msg:
                    current_msg["message"] += f"\n{line}"
        
        if current_msg:
            messages.append(current_msg)
        
        return messages


# ─── Instagram .json Parser ──────────────────────────────────────────────────

class InstagramIngestor:
    """
    Parses Instagram's "Download Your Data" JSON export.
    Instagram exports messages in: your_instagram_activity/messages/inbox/<chat>/message_1.json
    """
    
    def parse(self, json_content: str) -> List[Dict]:
        """Parse raw Instagram JSON export into structured messages."""
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            return []
        
        messages = []
        
        # Instagram format: {"participants": [...], "messages": [...]}
        raw_messages = data.get("messages", [])
        
        for msg in raw_messages:
            # Instagram encodes text in Latin-1, we decode it
            content = msg.get("content", "")
            if isinstance(content, str):
                try:
                    content = content.encode('latin-1').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
            
            sender = msg.get("sender_name", "unknown")
            try:
                sender = sender.encode('latin-1').decode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass
            
            timestamp_ms = msg.get("timestamp_ms", 0)
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000).isoformat() if timestamp_ms else ""
            
            if content:  # Skip media-only messages
                messages.append({
                    "timestamp": timestamp,
                    "sender": sender,
                    "message": content,
                    "source": "instagram",
                })
        
        # Instagram exports are reverse-chronological
        messages.reverse()
        return messages


# ─── Audio Transcription (Whisper) ────────────────────────────────────────────

class AudioIngestor:
    """Transcribes audio files using OpenAI Whisper API."""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception:
            self.client = None
    
    def transcribe(self, audio_path: str, sender: str = "speaker") -> List[Dict]:
        """Transcribe an audio file and return as messages."""
        if not self.client:
            return [{"sender": sender, "message": "[Audio transcription unavailable — no API key]", "source": "audio"}]
        
        try:
            with open(audio_path, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text"
                )
            
            return [{
                "timestamp": datetime.now().isoformat(),
                "sender": sender,
                "message": transcript,
                "source": "audio",
            }]
        except Exception as e:
            return [{"sender": sender, "message": f"[Transcription error: {e}]", "source": "audio"}]


# ─── Unified Ingestor ────────────────────────────────────────────────────────

class UnifiedIngestor:
    """Routes to the correct parser based on source type."""
    
    def __init__(self):
        self.whatsapp = WhatsAppIngestor()
        self.instagram = InstagramIngestor()
        self.audio = AudioIngestor()
    
    def ingest(self, content: str, source: str, **kwargs) -> List[Dict]:
        """
        Unified ingestion entry point.
        source: "whatsapp" | "instagram" | "audio"
        """
        if source == "whatsapp":
            return self.whatsapp.parse(content)
        elif source == "instagram":
            return self.instagram.parse(content)
        elif source == "audio":
            return self.audio.transcribe(content, kwargs.get("sender", "speaker"))
        else:
            raise ValueError(f"Unknown source: {source}")


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ingestor = UnifiedIngestor()
    
    # Test WhatsApp
    sample = """[10/12/23, 14:32:01] Alice: Hey! Are you coming to the party tonight?
[10/12/23, 14:33:45] Bob: Yeah I think so. Just wrapping up some work.
What time are you heading there?
[10/12/23, 14:35:10] Alice: Probably around 9 PM."""
    
    result = ingestor.ingest(sample, "whatsapp")
    print(f"WhatsApp: {len(result)} messages parsed")
    for m in result:
        print(f"  [{m['sender']}]: {m['message'][:50]}")
