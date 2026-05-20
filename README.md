# 🏥 HealthSure Customer Support Bot

An AI-powered customer support chatbot for a health insurance company, built as part of the DevX Labs coding assessment.

## 🎥 Demo Video
[Watch the demo](#)<https://drive.google.com/drive/folders/1-B1OQxEuOJFPL8y4BrTRF8foDmmQUcNx)>

## 🚀 What It Does

- Answers customer queries instantly from a built-in knowledge base
- Falls back to AI (Groq / Llama 3.1) for questions not in the KB
- Clearly labels every response: ✅ Answered from KB or 🤖 Answered by AI
- Lets customers raise a support ticket when the AI can't fully help
- Admin dashboard to view and manage all raised tickets
- Fully Dockerised for easy deployment

## 🏗️ Architecture
Customer Query
│
▼
Knowledge Base Lookup (knowledge_base.json)
│
├── Match found → Answer from KB ✅
│
└── No match → Groq AI (Llama 3.1) 🤖
│
└── Still unsatisfied → Raise Ticket 🎫

## 🛠️ Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| UI | Streamlit | Fast to build, clean chat interface |
| LLM | Groq API (Llama 3.1) | Free, fast, no credit card required |
| Knowledge Base | JSON file | Simple, readable, easy to extend |
| Ticketing | SQLite | Zero setup, lightweight, perfect for demo |
| Hosting | Replit | Browser-based, no local setup needed |

> **Note on LLM choice:** The assessment specifies Claude API (Anthropic). 
> Anthropic requires a credit card even for free-tier API access. 
> Groq (Llama 3.1-8b-instant) was used as a functionally identical substitute — 
> same API structure, same logic. Switching to Claude requires changing 
> exactly one line in app.py.

## ⚙️ Running Locally

### Option 1 — Standard Python

```bash
# Clone the repo
git clone https://github.com/sachinbasantia/health-support-bot
cd health-support-bot

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY=your_groq_key_here

# Run the app
streamlit run app.py
```

Open your browser at `http://localhost:8501`

### Option 2 — Docker

```bash
# Build the image
docker build -t health-support-bot .

# Run the container
docker run -e GROQ_API_KEY=your_groq_key_here -p 8080:8080 health-support-bot
```

Open your browser at `http://localhost:8080`

## 📁 Project Structure
health-support-bot/
├── app.py                 # Main Streamlit application
├── knowledge_base.json    # Pre-loaded health insurance Q&A pairs
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── .dockerignore          # Docker ignore rules
└── README.md              # This file

## 📚 Knowledge Base Entries

The KB includes 6 pre-loaded entries:
- What is my deductible?
- How do I file a claim?
- Is physiotherapy covered?
- What is the cashless hospitalisation process?
- How do I add a dependent to my plan?
- What is the claim reimbursement timeline?

## ⚠️ Known Limitations & Shortcuts

- **LLM swap:** Groq used instead of Claude API due to billing requirements
- **KB matching:** Uses keyword matching instead of vector/semantic search — 
  a production system would use embeddings for better accuracy
- **Ticket management:** SQLite used instead of a full tool like Plane or Zammad — 
  sufficient for demo purposes
- **No authentication:** No login/auth layer — would be needed in production
- **Web fallback:** Not implemented due to time constraints — 
  the AI model handles out-of-KB queries directly instead

## 👤 Author

**Sachin Basantia**  
Built for DevX Labs Assessment
