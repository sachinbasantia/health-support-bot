# 🏥 HealthSure — AI-Powered Customer Support Bot

> **Built as part of the DevX Labs Coding Assessment**  
> ⚠️ This is a demo-grade prototype built within a 3–4 hour constraint. It is not production-ready. All architectural decisions reflect intentional trade-offs made for speed of delivery. Limitations vs. a production system are documented explicitly at the bottom.

---

## 🎥 Watch the Demo
[▶ Watch the walkthrough video](https://drive.google.com/drive/folders/1-B1OQxEuOJFPL8y4BrTRF8foDmmQUcNx)

## 🚀 Try the Live App
[🌐 Open the live app](https://sachinbasantia-health-support-bot.streamlit.app) 

---

## 📌 What This Does

HealthSure is an end-to-end AI-powered customer support platform for a health insurance company. It reduces human agent load by deflecting common queries through an intelligent chat interface and only escalating to ticketed support when necessary.

### Customer Flow
```
Customer types a question
        │
        ▼
Knowledge Base lookup (20 pre-loaded Q&A pairs)
        │
        ├── Match found → Answered from KB ✅
        │
        └── No match → Groq AI (Llama 3.1) 🌐
                            │
                            └── Still unsatisfied → Raise Support Ticket 🎫
                                                            │
                                                            ▼
                                              Admin Dashboard resolves ticket
                                                            │
                                                            ▼
                                              Resolution feeds back into KB 🔁
                                              (Next customer gets KB answer)
```

---

## 🏗️ Architecture & Tech Stack

| Layer | Tool Chosen | Why |
|---|---|---|
| **UI** | Streamlit | Fastest way to build a clean chat interface in Python — no frontend code needed |
| **LLM** | Groq API (Llama 3.1-8b-instant) | Completely free, no credit card required, fast inference |
| **Knowledge Base** | JSON file (20 entries) | Simple, readable, easy to extend — sufficient for demo scale |
| **Ticket Storage** | SQLite | Zero setup, built into Python, creates itself automatically |
| **Hosting** | Streamlit Community Cloud | Free, connects directly to GitHub, one-click deploy |
| **Language** | Python | First-class support for all AI/ML SDKs, Streamlit, and SQLite |
| **Containerisation** | Docker | Ensures the app runs identically on any machine |

### Note on LLM Choice
The assessment specifies **Claude API (Anthropic)**. Anthropic requires a credit card on file even for free-tier API access — which was a blocker. **Groq (Llama 3.1-8b-instant)** was used as a functionally identical substitute with the same API structure and logic. Switching back to Claude requires changing exactly **one line** in `app.py`:

```python
# Current (Groq)
from groq import Groq
client = Groq(api_key=os.environ["GROQ_API_KEY"])
model = "llama-3.1-8b-instant"

# To switch to Claude
import anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
model = "claude-sonnet-4-20250514"
```

---

## 📁 Project Structure

```
health-support-bot/
├── app.py                        # Main customer-facing chat application
├── pages/
│   └── 1_Admin_Dashboard.py      # Agent-facing ticket management dashboard
├── knowledge_base.json           # 20 pre-loaded health insurance Q&A pairs
├── tickets.db                    # SQLite database (auto-created on first run)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── .streamlit/
│   └── config.toml               # Streamlit server configuration
└── README.md                     # This file
```

---

## ⚙️ Setup & Running Locally

### Prerequisites
- Python 3.11+
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Option 1 — Standard Python

```bash
# 1. Clone the repository
git clone https://github.com/sachinbasantia/health-support-bot
cd health-support-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Groq API key
export GROQ_API_KEY="your_groq_key_here"
# On Windows:
set GROQ_API_KEY=your_groq_key_here

# 4. Run the app
streamlit run app.py
```

Open your browser at `http://localhost:8501`

### Option 2 — Docker

```bash
# 1. Build the image
docker build -t health-support-bot .

# 2. Run the container
docker run -e GROQ_API_KEY="your_groq_key_here" -p 8080:8080 health-support-bot
```

Open your browser at `http://localhost:8080`

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key from console.groq.com |

---

## 💡 Feature Breakdown

### 1. Chat Interface
A clean ChatGPT-style interface built with Streamlit's `st.chat_message` component. Customers type questions and receive natural language responses with a clear source label on every reply.

### 2. Knowledge Base Q&A
20 pre-loaded health insurance Q&A pairs stored in `knowledge_base.json`. The system performs keyword matching against each entry. When a match is found, the answer is returned directly with a **✅ Answered from Knowledge Base** label — no LLM call is made, keeping responses fast and accurate.

### 3. AI Fallback (Guardrailed)
When no KB match is found, the query is passed to Groq's Llama 3.1 model with a strict system prompt. Every AI response is labelled **🌐 Answered from Web / AI — verify with your official policy documents** to make the source transparent.

### 4. Ticket Creation
A **"Raise a Support Ticket"** button appears after every conversation. Clicking it saves the full conversation to `tickets.db` with a timestamp and `status = open`.

### 5. Admin Dashboard (`/1_Admin_Dashboard`)
A separate internal-facing page where support agents can:
- View all open and resolved tickets
- Read the full conversation for each ticket
- Enter a resolution summary
- Click **"Resolve & Update KB"** to close the ticket and feed the answer back

### 6. Ticket Resolution → KB Feedback Loop
When an agent resolves a ticket, two things happen simultaneously:
1. The ticket status in `tickets.db` is updated to `resolved`
2. A new FAQ entry is appended to `knowledge_base.json` using the resolution as the answer

This means the next customer who asks a similar question gets a **✅ KB answer** instead of hitting the AI — the system gets smarter with every resolved ticket.

---

## 🛡️ Anti-Hallucination Strategy

Three layers are in place to minimise hallucinated responses:

**Layer 1 — Strict system prompt**
The LLM is explicitly told: never invent policy numbers, amounts, or dates. If unsure, direct the user to raise a ticket.

**Layer 2 — Low temperature (0.1)**
Temperature controls how "creative" the model is. At 0.1 it stays close to factual responses rather than improvising.

**Layer 3 — Source transparency**
Every AI response carries a visible label telling the user it came from AI, not official company data — prompting them to verify before acting.

---

## 🏛️ Architectural Decisions Explained

### Why JSON over a Vector Database?
A vector DB (like ChromaDB or Pinecone) stores questions as mathematical embeddings that capture semantic meaning — so "claim submission process" would match "how do I file a claim" even without shared keywords. For 20 entries and a 3–4 hour build, keyword matching is sufficient. A production system would use embeddings for far better accuracy.

### Why SQLite over Plane/Zammad/Linear?
The case mentioned several ticketing tools. Here is why each was skipped:

| Tool | Reason Skipped |
|---|---|
| **Plane** | Open source but requires Docker + server setup (30+ min overhead) |
| **Zammad** | Full helpdesk suite — heavy infrastructure for a demo |
| **Linear** | SaaS with a trial — adds API integration complexity and eventual cost |
| **SQLite** | Built into Python, zero setup, case explicitly permits "a simple DB — your call" |

SQLite is a deliberate trade-off for speed, not a limitation of understanding.

### Why Python?
Every major LLM SDK publishes Python support first. Streamlit, SQLite, and Groq all have first-class Python libraries. For an AI-powered app in a 3–4 hour window, Python is the only sensible choice.

### Why Docker?
Docker ensures the app runs identically on every machine regardless of OS or Python version. An evaluator can clone the repo and have the app running in two commands without touching their local Python environment.

### Why Not RAG?
RAG (Retrieval Augmented Generation) is the production-grade version of what we built. In a true RAG system, every KB entry would be converted to an embedding, stored in a vector DB, and retrieved by semantic similarity before being passed to the LLM as grounded context. Our system follows the same logical pattern — retrieve context, then generate — but uses keyword matching instead of vector similarity. Conceptually identical, simpler to implement at demo scale.

---

## ⚠️ Known Limitations vs. Production Grade

This is a demo prototype. The following limitations are intentional trade-offs, not oversights.

| Area | Demo Approach | Production Approach |
|---|---|---|
| **LLM** | Groq / Llama 3.1 (free) | Claude API or GPT-4 with guardrails |
| **KB Search** | Keyword matching can produce false positives  | Vector embeddings (ChromaDB + embedding model) more accurate |
| **KB Scale** | 20 entries in JSON | Thousands of entries in a vector DB |
| **Ticket Storage** | SQLite (single file) | PostgreSQL with proper indexing |
| **Ticketing Tool** | Custom SQLite tables | Plane, Zammad, or Zendesk with full workflow |
| **Web Fallback** | AI labelled as "from web" | True web search via DuckDuckGo/SerpAPI with citations |
| **Hallucination Control** | System prompt + low temp | RAG with source grounding + citation links |
| **Admin Access** | Open page, no login | Role-based authentication, audit logs |
| **Concurrency** | Single user (SQLite limitation) | Multi-user with connection pooling |
| **Error Handling** | Minimal | Full try/catch, retry logic, fallback responses |
| **Testing** | Manual only | Unit tests, integration tests, CI/CD pipeline |
| **Feedback Loop** | Manual admin input | Auto-clustering of resolved tickets, batch KB updates |

---

## 📚 Knowledge Base Coverage

20 pre-loaded entries covering the most common health insurance queries:

Deductibles · Claims filing · Physiotherapy coverage · Cashless hospitalisation · Adding dependents · Reimbursement timelines · Required documents · Maternity coverage · Pre-existing disease waiting periods · Network hospital lookup · Sum insured · Policy renewal · No-claim bonus · Dental coverage · Customer support contact · Mental health coverage · Co-payment explanation · Ambulance charges · Policy porting · Daycare treatments

---

## 🔁 How the KB Feedback Loop Works (Step by Step)

1. Customer asks a question not in the KB
2. AI answers — customer still unsatisfied → raises ticket
3. Ticket saved to `tickets.db` with `status = open`
4. Agent opens Admin Dashboard → reads the conversation
5. Agent types a resolution summary → clicks "Resolve & Update KB"
6. Code updates `tickets.db`: `status = resolved`, saves resolution text
7. Code opens `knowledge_base.json` → appends new FAQ entry with resolution as the answer
8. Next customer asks the same question → **✅ Answered from Knowledge Base**

---

## 🤝 Development Approach & Honesty Note

This project was built using AI-assisted development — specifically using Claude for architecture decisions, code generation, and debugging, and Replit's agent for execution. All product decisions, tool choices, trade-offs, and the architectural reasoning documented above reflect independent judgment.

This reflects how modern product and DevX work actually gets done — defining the problem clearly, making pragmatic tool decisions, resolving blockers (API billing constraints, deprecated model versions, port configuration issues), and shipping a working end-to-end system within the time constraint.

The choice to use Groq over Claude, JSON over a vector DB, and SQLite over Plane were all conscious decisions made with full awareness of the trade-offs — not defaults taken out of ignorance.

---

## 👤 Author

**Sachin Basantia**  
Built for DevX Labs Coding Assessment  
[github.com/sachinbasantia](https://github.com/sachinbasantia)
