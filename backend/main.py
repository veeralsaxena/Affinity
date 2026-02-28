"""
main.py — FastAPI Backend for Synchrony v2

Endpoints:
  POST /ingest/whatsapp  — Upload WhatsApp .txt export
  POST /ingest/instagram — Upload Instagram .json export
  POST /ingest/audio     — Upload audio file for Whisper transcription
  POST /analyze          — Run the LangGraph pipeline on provided messages
  POST /ingest-and-analyze — Upload + analyze in one step (saves to DB)
  GET  /contacts         — List user's contacts
  DELETE /contacts/{id}  — Remove a relationship
  GET  /analyses         — List user's analysis history
  GET  /dashboard        — Aggregated dashboard data
  POST /whatsapp/connect — Launch WhatsApp Web browser
  GET  /whatsapp/status  — Check WhatsApp connection
  POST /whatsapp/read    — Read messages from a contact
  POST /whatsapp/send    — Send a message to a contact
  POST /whatsapp/auto-ingest — Read + analyze from WhatsApp live
  GET  /health           — Health check
"""

import json
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ingestor import UnifiedIngestor
from graph import analyze_relationship
from database import init_db, get_db
from auth import router as auth_router, get_current_user
from memory import MemoryManager
from cache import get_cache
from whatsapp_automation import get_whatsapp
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    init_db()
    yield


app = FastAPI(
    title="Synchrony — The Relational OS",
    description="Multi-agent relationship intelligence pipeline powered by LangGraph",
    version="2.0.0",
    lifespan=lifespan,
)

# Auth routes
app.include_router(auth_router)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestor = UnifiedIngestor()


# ─── Models ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    messages: List[Dict]
    user_id: str = "user_1"
    target_person: str = "friend_1"


class IngestResponse(BaseModel):
    status: str
    message_count: int
    messages: List[Dict]


class AnalyzeResponse(BaseModel):
    heat: float
    decay: float
    emotion: str
    route: str
    report: str
    nudges: List[str]
    memories: List[str]
    scoring_layers: Dict


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.0.0", "engine": "langgraph"}


@app.post("/ingest/whatsapp", response_model=IngestResponse)
async def ingest_whatsapp(file: UploadFile = File(...)):
    """Upload a WhatsApp .txt export file."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    messages = ingestor.ingest(text, "whatsapp")
    if not messages:
        raise HTTPException(status_code=400, detail="Could not parse any messages from the file.")
    return IngestResponse(status="success", message_count=len(messages), messages=messages)


@app.post("/ingest/instagram", response_model=IngestResponse)
async def ingest_instagram(file: UploadFile = File(...)):
    """Upload an Instagram .json export file."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    messages = ingestor.ingest(text, "instagram")
    if not messages:
        raise HTTPException(status_code=400, detail="Could not parse any messages from the file.")
    return IngestResponse(status="success", message_count=len(messages), messages=messages)


@app.post("/ingest/audio", response_model=IngestResponse)
async def ingest_audio(
    file: UploadFile = File(...),
    sender: str = Form(default="speaker"),
):
    """Upload an audio file (.mp3, .wav) for Whisper transcription."""
    import tempfile, os
    suffix = os.path.splitext(file.filename or ".mp3")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        messages = ingestor.ingest(tmp_path, "audio", sender=sender)
    finally:
        os.unlink(tmp_path)
    return IngestResponse(status="success", message_count=len(messages), messages=messages)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Run the full LangGraph pipeline on provided messages."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")
    result = analyze_relationship(
        raw_messages=request.messages,
        user_id=request.user_id,
        target_person=request.target_person,
    )
    return AnalyzeResponse(
        heat=result.get("heat", 0),
        decay=result.get("decay", 0),
        emotion=result.get("emotion", "unknown"),
        route=result.get("route", "stable"),
        report=result.get("report", ""),
        nudges=result.get("nudges", []),
        memories=result.get("memories", []),
        scoring_layers=result.get("scoring_layers", {}),
    )


@app.post("/ingest-and-analyze")
async def ingest_and_analyze(
    file: UploadFile = File(...),
    source: str = Form(default="whatsapp"),
    target_person: str = Form(default="friend"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    One-shot endpoint: upload a chat export, run the full 8-layer LangGraph pipeline,
    save Contact + Analysis to DB, log episodic memory, extract semantic facts.
    """
    content = await file.read()

    if source == "audio":
        import tempfile, os
        suffix = os.path.splitext(file.filename or ".mp3")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            messages = ingestor.ingest(tmp_path, "audio")
        finally:
            os.unlink(tmp_path)
    else:
        text = content.decode("utf-8", errors="ignore")
        messages = ingestor.ingest(text, source)

    if not messages:
        raise HTTPException(status_code=400, detail="No messages parsed from the file.")

    # Detect contact name from messages
    senders = set(m.get("sender", "") for m in messages if m.get("sender", ""))
    contact_name = target_person

    if target_person == "friend" or not target_person:
        possible_contacts = []
        user_name = (current_user.full_name or current_user.username).lower()
        for s in senders:
            s_lower = s.lower()
            # If the sender name shares words with the user's name, it's likely the user
            is_user = any(part in s_lower for part in user_name.split() if len(part) > 2)
            if not is_user and s_lower != "you":
                possible_contacts.append(s)
        
        if possible_contacts:
            contact_name = possible_contacts[0]
        elif len(senders) >= 2:
            contact_name = list(senders)[1]
        elif senders:
            contact_name = list(senders)[0]

    # Run 8-layer pipeline
    result = analyze_relationship(
        raw_messages=messages,
        user_id=str(current_user.id),
        target_person=contact_name,
    )

    # Calculate health score from heat/decay
    heat = result.get("heat", 0)
    decay = result.get("decay", 0)
    health_score = max(0, min(100, 100 - (heat * 5 + decay * 5)))

    # Determine status
    if health_score >= 75:
        status = "Thriving"
    elif health_score >= 50:
        status = "Stable"
    elif health_score >= 25:
        status = "Declining"
    else:
        status = "Dormant"

    # Create or update Contact
    contact = db.query(models.Contact).filter(
        models.Contact.user_id == current_user.id,
        models.Contact.name == contact_name
    ).first()

    if not contact:
        contact = models.Contact(
            user_id=current_user.id,
            name=contact_name,
            source=source,
            health_score=health_score,
            status=status,
            last_message_at=datetime.utcnow(),
        )
        db.add(contact)
    else:
        contact.health_score = health_score
        contact.status = status
        contact.updated_at = datetime.utcnow()
        contact.last_message_at = datetime.utcnow()

    # Save Analysis
    analysis = models.Analysis(
        user_id=current_user.id,
        contact_name=contact_name,
        source=source,
        heat_score=heat,
        decay_score=decay,
        emotion=result.get("emotion", "unknown"),
        route=result.get("route", "stable"),
        report=result.get("report", ""),
        nudges=result.get("nudges", []),
        scoring_layers=result.get("scoring_layers", {}),
        message_count=len(messages),
    )
    db.add(analysis)
    db.commit()
    db.refresh(contact)
    db.refresh(analysis)

    # ── Memory Integration ──
    try:
        mem = MemoryManager(db)
        # Log episodic memory
        event_type = "conflict" if result.get("route") == "conflict" else "decay_alert" if result.get("route") == "decay" else "analysis"
        mem.log_episode(
            user_id=str(current_user.id),
            contact_name=contact_name,
            event_type=event_type,
            content=f"Analysis: Heat={heat:.1f}, Decay={decay:.1f}, "
                    f"Emotion={result.get('emotion', 'unknown')}, Route={result.get('route', 'stable')}",
        )
        # Extract semantic facts from conversation
        mem.extract_facts_from_conversation(
            user_id=str(current_user.id),
            contact_name=contact_name,
            messages=messages,
        )
    except Exception as e:
        print(f"Memory logging failed (non-critical): {e}")

    return {
        "ingestion": {"message_count": len(messages)},
        "analysis": result,
        "contact": {
            "id": str(contact.id),
            "name": contact.name,
            "health_score": contact.health_score,
            "status": contact.status,
        },
    }


# ─── Dashboard Data Endpoints ───────────────────────────────────────────────

@app.get("/contacts")
def list_contacts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all contacts for the current user."""
    contacts = db.query(models.Contact).filter(
        models.Contact.user_id == current_user.id
    ).order_by(models.Contact.updated_at.desc()).all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "source": c.source,
            "health_score": c.health_score,
            "status": c.status,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contacts
    ]


@app.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a relationship/contact."""
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == current_user.id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Also delete related analyses
    db.query(models.Analysis).filter(
        models.Analysis.user_id == current_user.id,
        models.Analysis.contact_name == contact.name,
    ).delete()

    db.delete(contact)
    db.commit()
    return {"status": "deleted", "id": contact_id}


@app.get("/analyses")
def list_analyses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all analyses for the current user."""
    analyses = db.query(models.Analysis).filter(
        models.Analysis.user_id == current_user.id
    ).order_by(models.Analysis.created_at.desc()).limit(50).all()

    return [
        {
            "id": str(a.id),
            "contact_name": a.contact_name,
            "source": a.source,
            "heat_score": a.heat_score,
            "decay_score": a.decay_score,
            "emotion": a.emotion,
            "route": a.route,
            "report": a.report,
            "nudges": a.nudges,
            "message_count": a.message_count,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]


@app.get("/dashboard")
def get_dashboard(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregated dashboard data for the current user."""
    contacts = db.query(models.Contact).filter(
        models.Contact.user_id == current_user.id
    ).all()

    total = len(contacts)
    avg_score = sum(c.health_score or 0 for c in contacts) / total if total else 0
    at_risk = sum(1 for c in contacts if (c.health_score or 0) < 50)
    thriving = sum(1 for c in contacts if (c.health_score or 0) >= 75)
    stable = sum(1 for c in contacts if 50 <= (c.health_score or 0) < 75)
    dormant = sum(1 for c in contacts if (c.health_score or 0) < 25)

    recent_analyses = db.query(models.Analysis).filter(
        models.Analysis.user_id == current_user.id
    ).order_by(models.Analysis.created_at.desc()).limit(5).all()

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "stats": {
            "total_contacts": total,
            "average_health": round(avg_score, 1),
            "at_risk": at_risk,
            "thriving": thriving,
            "stable": stable,
            "dormant": dormant,
        },
        "contacts": [
            {
                "id": str(c.id),
                "name": c.name,
                "source": c.source,
                "health_score": c.health_score,
                "status": c.status,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            }
            for c in contacts
        ],
        "recent_analyses": [
            {
                "id": str(a.id),
                "contact_name": a.contact_name,
                "emotion": a.emotion,
                "heat_score": a.heat_score,
                "decay_score": a.decay_score,
                "route": a.route,
                "nudges": a.nudges,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_analyses
        ],
    }


# ─── WhatsApp Automation Endpoints ───────────────────────────────────────────

@app.post("/whatsapp/connect")
async def whatsapp_connect(current_user: models.User = Depends(get_current_user)):
    """
    Launch the Playwright browser and navigate to WhatsApp Web.
    Returns {status: 'qr_needed'} if QR scan is required, or {status: 'connected'}.
    """
    wa = get_whatsapp()
    result = await wa.connect()

    if result.get("qr_needed"):
        # Wait up to 2 minutes for QR scan
        login_result = await wa.wait_for_login(timeout=120)
        return login_result

    return result


@app.get("/whatsapp/status")
async def whatsapp_status(current_user: models.User = Depends(get_current_user)):
    """Check current WhatsApp Web connection status."""
    wa = get_whatsapp()
    return await wa.get_status()


class WhatsAppReadRequest(BaseModel):
    contact_name: str
    limit: int = 50

@app.post("/whatsapp/read")
async def whatsapp_read(
    req: WhatsAppReadRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Read messages from a WhatsApp contact's chat."""
    wa = get_whatsapp()
    return await wa.read_messages(req.contact_name, req.limit)


class WhatsAppSendRequest(BaseModel):
    contact_name: str
    message: str

@app.post("/whatsapp/send")
async def whatsapp_send(
    req: WhatsAppSendRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to a WhatsApp contact using Playwright automation.
    The browser types the message and presses Enter — visible in headed mode
    so judges can watch the AI interact with WhatsApp in real-time.
    """
    wa = get_whatsapp()
    result = await wa.send_message(req.contact_name, req.message)

    # Log to episodic memory
    if result.get("status") == "sent":
        try:
            mem = MemoryManager(db)
            mem.log_episode(
                user_id=str(current_user.id),
                contact_name=req.contact_name,
                event_type="message_sent",
                content=f"AI-drafted message sent: {req.message[:100]}...",
            )
        except Exception as e:
            print(f"Memory log failed: {e}")

    return result


@app.post("/whatsapp/auto-ingest")
async def whatsapp_auto_ingest(
    req: WhatsAppReadRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pull messages LIVE from WhatsApp, then run the full 8-layer analysis pipeline.
    This is the autonomous data ingestion described in the research document.
    """
    wa = get_whatsapp()
    ingest_result = await wa.auto_ingest(req.contact_name)

    if ingest_result.get("status") != "success":
        raise HTTPException(status_code=400, detail=ingest_result.get("error", "Failed to read messages"))

    messages = ingest_result["messages"]
    if not messages:
        raise HTTPException(status_code=400, detail="No messages found for this contact")

    # Run pipeline
    result = analyze_relationship(
        raw_messages=messages,
        user_id=str(current_user.id),
        target_person=req.contact_name,
    )

    # Save to DB
    heat = result.get("heat", 0)
    decay = result.get("decay", 0)
    health_score = max(0, min(100, 100 - (heat * 5 + decay * 5)))

    if health_score >= 75:
        status = "Thriving"
    elif health_score >= 50:
        status = "Stable"
    elif health_score >= 25:
        status = "Declining"
    else:
        status = "Dormant"

    # Upsert contact
    contact = db.query(models.Contact).filter(
        models.Contact.user_id == current_user.id,
        models.Contact.name == req.contact_name,
    ).first()

    if contact:
        contact.health_score = health_score
        contact.status = status
        contact.source = "whatsapp_live"
    else:
        contact = models.Contact(
            user_id=current_user.id,
            name=req.contact_name,
            source="whatsapp_live",
            health_score=health_score,
            status=status,
        )
        db.add(contact)

    # Save analysis
    analysis = models.Analysis(
        user_id=current_user.id,
        contact_name=req.contact_name,
        source="whatsapp_live",
        heat_score=heat,
        decay_score=decay,
        emotion=result.get("emotion", "unknown"),
        route=result.get("route", "stable"),
        report=result.get("report", ""),
        nudges=result.get("nudges", []),
        scoring_layers=result.get("scoring_layers", {}),
        message_count=len(messages),
    )
    db.add(analysis)
    db.commit()

    # Memory integration
    try:
        mem = MemoryManager(db)
        mem.log_episode(
            user_id=str(current_user.id),
            contact_name=req.contact_name,
            event_type="auto_ingest",
            content=f"Live WhatsApp analysis: Heat={heat:.1f}, Decay={decay:.1f}, {len(messages)} messages",
        )
        mem.extract_facts_from_conversation(str(current_user.id), req.contact_name, messages)
    except Exception:
        pass

    return {
        "ingestion": {"source": "whatsapp_live", "message_count": len(messages)},
        "analysis": result,
        "contact": {
            "name": req.contact_name,
            "health_score": health_score,
            "status": status,
        },
    }


@app.post("/whatsapp/disconnect")
async def whatsapp_disconnect(current_user: models.User = Depends(get_current_user)):
    """Disconnect WhatsApp Web browser."""
    wa = get_whatsapp()
    await wa.disconnect()
    return {"status": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
