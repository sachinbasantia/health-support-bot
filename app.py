import streamlit as st
import json
import os
import sqlite3
from datetime import datetime
from groq import Groq

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Assistant",
    page_icon="💊",
    layout="centered"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 780px; }

    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
        border-radius: 18px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.4rem;
        color: white;
        box-shadow: 0 4px 20px rgba(26,115,232,0.3);
    }
    .header-title {
        font-size: 1.7rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.01em;
    }
    .header-subtitle {
        font-size: 0.9rem;
        opacity: 0.85;
        margin-top: 0.3rem;
    }
    .header-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.6rem;
    }

    /* Welcome card */
    .welcome-card {
        background: white;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        border-left: 4px solid #1a73e8;
    }
    .welcome-title {
        font-size: 1rem;
        font-weight: 700;
        color: #202124;
        margin-bottom: 0.3rem;
    }
    .welcome-text {
        font-size: 0.88rem;
        color: #5f6368;
        line-height: 1.5;
    }

    /* Suggestion chips */
    .chips-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #5f6368;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.5rem;
        margin-top: 0.2rem;
    }

    /* Chat source badges */
    .source-kb {
        display: inline-block;
        background: #e6f4ea;
        color: #137333;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    .source-ai {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 0.3rem;
    }

    /* Ticket section */
    .ticket-section {
        background: white;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-top: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e8eaed;
    }
    .ticket-heading {
        font-size: 0.95rem;
        font-weight: 700;
        color: #202124;
        margin-bottom: 0.4rem;
    }
    .ticket-subtext {
        font-size: 0.82rem;
        color: #5f6368;
        margin-bottom: 0.8rem;
    }

    /* Clear chat link style */
    .clear-row {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 0.5rem;
    }

    /* Override Streamlit chat bubble styling */
    [data-testid="stChatMessage"] {
        background: white !important;
        border-radius: 14px !important;
        padding: 0.8rem 1rem !important;
        margin-bottom: 0.5rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    }

    /* Input bar */
    [data-testid="stChatInput"] > div {
        border-radius: 14px !important;
        border: 2px solid #c2d4f8 !important;
        background: white !important;
        box-shadow: 0 2px 8px rgba(26,115,232,0.08) !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: #1a73e8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────
def load_knowledge_base():
    with open("knowledge_base.json", "r") as f:
        data = json.load(f)
    return data["faqs"]


def search_knowledge_base(user_query, faqs):
    query_lower = user_query.lower()
    for faq in faqs:
        for keyword in faq["keywords"]:
            if keyword.lower() in query_lower:
                return faq["answer"]
    return None


def ask_groq(user_query, chat_history):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    system_prompt = """You are a warm, professional healthcare insurance support assistant called "Healthcare Assistant". 
You help users with health insurance questions — claims, coverage, premiums, deductibles, hospitalisation, and policy details.

If a question is unrelated to health insurance, politely say:
"I'm here specifically for health insurance queries. For other concerns, please reach out to our general support line."

Keep answers concise, friendly, and clear. Use bullet points where helpful. 
Do not invent specific policy numbers or amounts — direct users to their policy document or member portal.
If unsure, say I do not have enough information — please raise a ticket. Never invent specific amounts or policy numbers."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=500,
        temperature=0.1
    )
    return response.choices[0].message.content


def create_ticket(chat_history):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            conversation TEXT,
            status TEXT DEFAULT 'open'
        )
    """)
    conversation_text = "\n".join(
        [f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history]
    )
    cursor.execute(
        "INSERT INTO tickets (timestamp, conversation, status) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), conversation_text, "open"),
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


# ── Session state ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ticket_raised" not in st.session_state:
    st.session_state.ticket_raised = False
if "suggested" not in st.session_state:
    st.session_state.suggested = None
if "last_ticket_id" not in st.session_state:
    st.session_state.last_ticket_id = None

faqs = load_knowledge_base()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <div class="header-title">💊 Healthcare Assistant</div>
    <div class="header-subtitle">Your personal health insurance support, available 24/7</div>
    <div class="header-badge">🟢 Online &nbsp;·&nbsp; AI-Powered</div>
</div>
""", unsafe_allow_html=True)

# ── Welcome card + suggestions (only when no messages) ────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-title">👋 Hello! How can I help you today?</div>
        <div class="welcome-text">
            I can help you with claims, coverage, premiums, deductibles, 
            hospitalisation benefits, and more. Just type your question or 
            choose one of the common topics below.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chips-label">Common questions</div>', unsafe_allow_html=True)

    suggestions = [
        "💰 What is my deductible?",
        "🏥 Is hospitalisation covered?",
        "📋 How do I file a claim?",
        "💳 How do I pay my premium?",
        "🔄 Can I update my policy?",
    ]

    cols = st.columns(len(suggestions))
    for i, (col, suggestion) in enumerate(zip(cols, suggestions)):
        with col:
            if st.button(suggestion, key=f"chip_{i}", use_container_width=True):
                st.session_state.suggested = suggestion
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# ── Process suggestion chip click ─────────────────────────────
if st.session_state.suggested:
    user_input_auto = st.session_state.suggested
    st.session_state.suggested = None

    st.session_state.messages.append({"role": "user", "content": user_input_auto})

    kb_answer = search_knowledge_base(user_input_auto, faqs)
    if kb_answer:
        st.session_state.messages.append(
            {"role": "assistant", "content": kb_answer, "label": "KB"}
        )
    else:
        ai_answer = ask_groq(user_input_auto, st.session_state.messages)
        st.session_state.messages.append(
            {"role": "assistant", "content": ai_answer, "label": "AI"}
        )
    st.rerun()

# ── Chat history display ───────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "label" in msg:
            if msg["label"] == "KB":
                st.markdown('<span class="source-kb">✅ Knowledge Base</span>', unsafe_allow_html=True)
            elif msg["label"] == "AI":
                st.markdown('<span class="source-ai">🌐 Answered from Web / AI — verify with your official policy documents</span>', unsafe_allow_html=True)

# ── Clear chat button (only when there are messages) ──────────
if st.session_state.messages:
    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button("🗑️ Clear", help="Clear the conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.ticket_raised = False
            st.rerun()

# ── Chat input ────────────────────────────────────────────────
user_input = st.chat_input("Ask me about your health insurance policy…")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    kb_answer = search_knowledge_base(user_input, faqs)

    if kb_answer:
        with st.chat_message("assistant"):
            st.markdown(kb_answer)
            st.markdown('<span class="source-kb">✅ Knowledge Base</span>', unsafe_allow_html=True)
        st.session_state.messages.append(
            {"role": "assistant", "content": kb_answer, "label": "KB"}
        )
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                ai_answer = ask_groq(user_input, st.session_state.messages)
            st.markdown(ai_answer)
            st.markdown('<span class="source-ai">🌐 Answered from Web / AI — verify with your official policy documents</span>', unsafe_allow_html=True)
        st.session_state.messages.append(
            {"role": "assistant", "content": ai_answer, "label": "AI"}
        )

# ── Ticket section ────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("""
    <div class="ticket-section">
        <div class="ticket-heading">🎫 Still need help?</div>
        <div class="ticket-subtext">
            If your issue wasn't resolved, raise a support ticket and our 
            team will get back to you within 24 hours.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.ticket_raised:
        if st.button("Raise a Support Ticket →", use_container_width=True, type="primary"):
            ticket_id = create_ticket(st.session_state.messages)
            st.session_state.ticket_raised = True
            st.session_state.last_ticket_id = ticket_id
            st.success(f"✅ Ticket #{ticket_id} raised! Our team will contact you within 24 hours.")
            st.balloons()
    else:
        st.success("🎫 Your ticket is open. Our team will reach out to you soon.")

        resolution = st.text_area("Resolve ticket — enter resolution summary", key="resolution_input")
        if st.button("Resolve and Update KB", key="resolve_btn"):
            if resolution.strip():
                with open("knowledge_base.json", "r") as f:
                    kb_data = json.load(f)
                new_id = max(entry["id"] for entry in kb_data["faqs"]) + 1
                kb_data["faqs"].append({
                    "id": new_id,
                    "question": f"Resolved ticket #{st.session_state.last_ticket_id}",
                    "keywords": resolution.lower().split()[:6],
                    "answer": resolution.strip(),
                    "source": "resolved_ticket"
                })
                with open("knowledge_base.json", "w") as f:
                    json.dump(kb_data, f, indent=2)
                if st.session_state.last_ticket_id:
                    conn = sqlite3.connect("tickets.db")
                    conn.execute(
                        "UPDATE tickets SET status = 'resolved' WHERE id = ?",
                        (st.session_state.last_ticket_id,)
                    )
                    conn.commit()
                    conn.close()
                st.success(f"✅ Ticket #{st.session_state.last_ticket_id} marked resolved and KB updated.")
            else:
                st.warning("Please enter a resolution summary before submitting.")
