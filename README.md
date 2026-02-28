# Synchrony — Autonomous Personal Relationship Intelligence 🧠💗

**A multi-agent, 8-layer behavioral analysis platform powered by LangGraph and Gemini.**

Built for the **Paradigm 1.0 Hackathon** by CodeBase, MPSTME.

> Upload your WhatsApp or Instagram chats. Our AI pipeline detects relational entropy, spots unresolved tension using the Gottman 5:1 ratio, measures digital mirroring, and crafts messages that match your exact writing voice.

---

## The Problem: Hyper-Connectivity ≠ Connection

Generation Z exists in a state of absolute hyper-connectivity — yet reports the highest rates of loneliness and social isolation of any generation. The paradox is not a lack of platforms; it's the systemic absence of **intelligent infrastructure** to manage the cognitive and emotional labor of maintaining hundreds of simultaneous digital relationships.

Traditional contact apps store static metadata (names, numbers). They fail to capture:
- **Conversational dynamics** — who initiates? who goes silent?
- **Emotional trajectories** — is sentiment drifting negative over weeks?
- **Behavioral patterns** — are replies getting shorter? fewer emojis?

Synchrony solves this by transforming raw chat data into **structured relational intelligence** and **autonomous action**.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 15)                          │
│  Landing → Auth (JWT) → Dashboard → Upload Modal → 8-Layer Results     │
│  AuthContext ─ Session Management ─ Token in localStorage              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ REST API (JWT Auth)
┌──────────────────────────────▼──────────────────────────────────────────┐
│                        BACKEND (FastAPI)                                │
│                                                                         │
│  ┌──────────────┐  ┌────────────────────────────────────┐              │
│  │   Ingestor   │  │    8-LAYER SCORING ENGINE           │              │
│  │  WhatsApp    │  │  L1: VADER (NLP sentiment)         │              │
│  │  Instagram   │──│  L2: Frequency (behavioral stats)  │              │
│  │  Audio       │  │  L3: Gemini (structured output)    │              │
│  └──────────────┘  │  L4: Relational Entropy (Shannon)  │              │
│                     │  L5: Effort Score (reciprocity)    │              │
│  ┌──────────────┐  │  L6: Gottman 5:1 Ratio             │              │
│  │  Style       │  │  L7: Digital Mirroring (Dice)      │              │
│  │  Analyzer    │  │  L8: KL Divergence (drift)         │              │
│  │  (digital    │  └────────────────────────────────────┘              │
│  │  fingerprint)│                                                       │
│  └──────────────┘  ┌────────────────────────────────────┐              │
│                     │       LangGraph State Machine       │              │
│  ┌──────────────┐  │  quantify → route →                 │              │
│  │   Memory     │  │    [conflict | decay | stable] →    │              │
│  │   Manager    │  │    style_analyze → ghost_write →    │              │
│  │  (Episodic + │  │    output                           │              │
│  │   Semantic)  │  └────────────────────────────────────┘              │
│  └──────────────┘                                                       │
│                     ┌────────────────────────────────────┐              │
│                     │  PostgreSQL (Users, Contacts,       │              │
│                     │  Analyses, EpisodicMemory,          │              │
│                     │  SemanticMemory)                    │              │
│                     └────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 8-Layer Scoring Engine — How It Actually Works

This is **NOT** a simple LLM wrapper. The pipeline uses an 8-layer hybrid scoring engine where 6 of 8 layers are **100% deterministic** — same input always gives same output.

### Layer 1: VADER (Deterministic NLP Sentiment)
- Runs VADER sentiment analyzer on every message
- Produces per-person average compound scores (-1.0 to +1.0)
- Tracks sentiment trajectory (first half vs second half)
- **100% deterministic**

### Layer 2: Frequency & Behavioral Analysis
- Average message length per sender
- Message count ratio between senders
- One-word reply ratio (passive-aggression signal)
- Emoji density (non-ASCII character ratio)
- **100% deterministic**

### Layer 3: Gemini Structured Output
- Calls Gemini 2.0 Flash with `temperature=0`
- Forces JSON output: `heat (0-10)`, `decay (0-10)`, `dominant_emotion`, `reasoning`
- Falls back to heuristic scoring if no API key
- **Near-deterministic** (temperature=0 + structured schema)

### Layer 4: Relational Entropy (Shannon)
Based on **Shannon's Information Theory** (1948):
```
H = -Σ p(x) log₂ p(x)
```
- Measures how irregular/unpredictable communication patterns are
- A perfectly regular communicator (1 msg/day) has LOW entropy
- An erratic communicator (5 msgs, silence, 20 msgs) has HIGH entropy
- **100% deterministic**

### Layer 5: Effort Score
Quantifies per-person effort using three sub-metrics:
- **Initiation ratio**: Who texts first after a gap? (0.5 = balanced)
- **Question reciprocity**: Ratio of questions asked vs answered
- **Length disparity**: Normalized difference in average message length
- Composite: `effort = 0.4 * initiation + 0.3 * questions + 0.3 * length`
- **100% deterministic**

### Layer 6: Gottman 5:1 Ratio
Based on **Dr. John Gottman's research** on relationship stability:
- Stable relationships maintain a **5:1 ratio** of positive to negative interactions
- VADER compound > 0.05 → positive; < -0.05 → negative; else neutral
- Status thresholds: ≥5:1 → Thriving, ≥3:1 → Stable, ≥1:1 → At Risk, <1:1 → Critical
- **100% deterministic**

### Layer 7: Digital Mirroring
Based on research showing that **linguistic alignment** predicts relational satisfaction:
- **Emoji reciprocity**: Sørensen–Dice coefficient of shared emoji sets
- **Length alignment**: `1 - |avg_len_A - avg_len_B| / max(avg_len_A, avg_len_B)`
- **Pronoun integration**: Ratio of "we/us/our" vs "I/me/my" usage
- Composite: `mirroring = 0.4 * emoji + 0.3 * length + 0.3 * pronoun`
- **100% deterministic**

### Layer 8: KL Divergence Sentiment Drift
Based on **Kullback-Leibler divergence** (1951):
```
D_KL(P || Q) = Σ P(x) · log(P(x) / Q(x))
```
- Splits messages into temporal halves (baseline vs recent)
- Builds 5-bin sentiment probability distributions
- Calculates distributional shift between periods
- D_KL > 0.3 → significant drift detected
- **100% deterministic**

### Composite Score Formula
```
Heat/Decay = (
    0.15 × VADER +
    0.15 × Frequency +
    0.20 × Gemini LLM +
    0.15 × Effort +
    0.10 × Gottman +
    0.10 × Entropy +
    0.10 × Mirroring +
    0.05 × KL Drift
)
```

---

## 🎭 Stylistic Mimicry — Eliminating Robotic Acting

A critical innovation: the Ghost Writer analyzes the user's **digital fingerprint** before generating messages. This solves the "algorithmic uncanny valley" — where recipients detect inauthenticity from generic AI outputs.

The `StyleAnalyzer` maps:
- Capitalization patterns (all lowercase? proper? mixed?)
- Punctuation style (minimal, standard, heavy)
- Emoji frequency & preferred emojis
- Slang usage (lol, tbh, ngl, fr, bruh...)
- Contraction patterns (don't vs do not)
- Average message length and question frequency

This profile is injected into the Ghost Writer prompt, ensuring generated messages are **linguistically indistinguishable** from manually typed text.

---

## 🧠 Tiered Memory Architecture

| Tier | Type | Storage | Purpose |
|---|---|---|---|
| **Tier 1** | Working Memory | LangGraph state | Current session context |
| **Tier 2** | Episodic Memory | PostgreSQL `episodic_memories` | Chronological event log (conflicts, milestones, sentiment shifts) |
| **Tier 3** | Semantic Memory | PostgreSQL `semantic_memories` | Structured facts (career, family, preferences, locations) |

Semantic facts are **automatically extracted** from conversations using Gemini:
> "Let's grab coffee next Thursday at 3 PM near the office" →
> - `event`: "Coffee meeting planned"
> - `schedule`: "Next Thursday, 3 PM"
> - `location`: "Near office"

This gives the Ghost Writer **long-term relational context** for deeply personalized messages.

---

## 🔀 LangGraph State Machine

```
quantify → route → [conflict_resolve | re_engage | log_memory]
                       → style_analyze → ghost_write → output
```

| Node | When | What It Does |
|---|---|---|
| `quantify` | Always | Runs 8-layer scoring engine |
| `route` | Always | **Deterministic** routing (Python if/else, NOT LLM) |
| `conflict_resolve` | Heat ≥ 6 or Gottman critical | Detailed conflict analysis with all layer data |
| `re_engage` | Decay ≥ 6 or effort severely imbalanced | Drift pattern analysis with entropy/effort data |
| `log_memory` | Both < 6 | Logs healthy relationship checkpoint |
| `style_analyze` | Conflict or Decay | Builds user's digital fingerprint |
| `ghost_write` | Conflict or Decay | Generates 3 style-matched message drafts via Gemini |
| `output` | Always | Packages full payload for dashboard |

---

## 📱 Data Ingestion

### WhatsApp Chat Export (.txt)
Export: `Chat Settings → Export Chat → Without Media`
Supports both **iOS** and **Android** timestamp formats via regex.

### Instagram JSON Export (.json)
Download: `Settings → Your Activity → Download Your Information`
Parses `message_1.json`, handles Latin-1 encoding.

### Audio Transcription (Whisper)
Supports `.mp3`, `.wav`, `.m4a`, `.ogg` via OpenAI Whisper API.

### WhatsApp Live Bridge (Optional)
Real-time message capture via `whatsapp-web.js` — scan QR code with phone, messages flow directly to the analysis pipeline.

---

## 🔑 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | No | Create account |
| `POST` | `/auth/login` | No | Login (OAuth2 form) |
| `GET` | `/auth/me` | JWT | Get current user |
| `POST` | `/ingest-and-analyze` | JWT | Upload + 8-layer analysis + save to DB + memory logging |
| `GET` | `/contacts` | JWT | List user's contacts |
| `DELETE` | `/contacts/{id}` | JWT | Remove a relationship |
| `GET` | `/analyses` | JWT | List analysis history |
| `GET` | `/dashboard` | JWT | Aggregated dashboard stats |
| `POST` | `/ingest/whatsapp` | No | Parse WhatsApp .txt |
| `POST` | `/ingest/instagram` | No | Parse Instagram .json |
| `POST` | `/analyze` | No | Run LangGraph pipeline |

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `users` | User accounts (UUID, email, hashed password) |
| `contacts` | Tracked relationships (health score, status, source) |
| `analyses` | AI analysis results (8-layer scores, nudges, report) |
| `episodic_memories` | Chronological relationship events (Tier 2 memory) |
| `semantic_memories` | Structured facts — knowledge graph (Tier 3 memory) |

---

## 🚀 Getting Started

### Prerequisites
- Docker Desktop (for PostgreSQL)
- Python 3.10+
- Node.js 18+
- Gemini API key

### 1. Start PostgreSQL
```bash
docker compose up -d db
```

### 2. Start the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://synchrony:synchrony_pass@localhost:5433/synchrony"
export JWT_SECRET="your-secret-key"
export GEMINI_API_KEY="your-gemini-api-key"

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev  # → http://localhost:3000
```

---

## 📂 Project Structure

```
synchrony/
├── backend/
│   ├── main.py            # FastAPI app with all endpoints
│   ├── auth.py            # JWT authentication (bcrypt)
│   ├── models.py          # SQLAlchemy (User, Contact, Analysis, EpisodicMemory, SemanticMemory)
│   ├── database.py        # PostgreSQL connection
│   ├── graph.py           # LangGraph state machine (8 nodes)
│   ├── scoring.py         # 8-layer hybrid scoring engine
│   ├── style_analyzer.py  # Digital fingerprint / stylistic mimicry
│   ├── memory.py          # Tiered memory manager (Episodic + Semantic)
│   ├── ingestor.py        # WhatsApp / Instagram / Audio parsers
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Landing page
│       │   ├── login/page.tsx     # Login with session management
│       │   ├── signup/page.tsx    # Signup with password confirmation
│       │   └── dashboard/page.tsx # Functional dashboard with 8-layer results
│       ├── context/
│       │   └── AuthContext.tsx     # Centralized auth state
│       └── components/ui/
├── whatsapp-bridge/
│   └── index.js           # Real-time WhatsApp listener
├── docker-compose.yml
└── README.md
```

---

## 🛠️ Tech Stack

| Technology | Role |
|---|---|
| **LangGraph** | Multi-agent orchestration (cyclical state machine) |
| **Gemini 2.0 Flash** | Structured scoring (temp=0) + creative ghost writing (temp=0.7) |
| **VADER** | Deterministic NLP sentiment analysis |
| **Shannon Entropy** | Communication regularity measurement |
| **KL Divergence** | Sentiment drift detection |
| **Gottman 5:1** | Psychological relationship health threshold |
| **Sørensen–Dice** | Digital mirroring / emoji reciprocity |
| **FastAPI** | Async backend with auto-docs |
| **PostgreSQL** | Relational data + tiered memory storage |
| **Next.js 15** | React frontend with SSR |
| **whatsapp-web.js** | Real-time WhatsApp message capture |

---

## 🔮 Production Architecture (Documented)

The following features represent the **full production architecture** described in our research. They require native mobile development and are documented as the intended roadmap:

| Feature | Mechanism | Status |
|---|---|---|
| **Passive Data Extraction** | Android `AccessibilityService` + `NotificationListenerService` | Researched |
| **iOS Integration** | App Intents + Shortcuts API | Researched |
| **OS-Level UI Automation** | Simulating human typing for message sending | Researched |
| **RLHF Fine-Tuning** | User edits as reward signal for ghost writer | Designed |
| **Personal Data Store** | Encrypted on-device processing | Designed |
| **Privacy-Preserving RAG** | Differential Privacy (DistanceDP) for cloud queries | Designed |

The web application demonstrates the **core algorithmic intelligence** that would power this production system.

---

## 🏆 Why This Wins

1. **Not a Simple LLM Call** — 8-layer hybrid scoring where 6/8 layers are 100% deterministic
2. **Real Behavioral Science** — Gottman's 5:1 ratio, Shannon entropy, KL divergence, Sørensen–Dice mirroring
3. **Stylistic Mimicry** — Ghost writer matches user's exact digital fingerprint
4. **Tiered Memory** — Episodic + Semantic memory for long-term relational context
5. **System Design** — Modular LangGraph nodes, each independently testable
6. **Live Integration** — WhatsApp bridge for real-time monitoring
7. **User Impact** — Reduces digital emotional labor while preserving authenticity
