import streamlit as st
import json
import os
import sqlite3
from datetime import datetime
from groq import Groq

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="HealthSure Support",
    page_icon="🏥",
    layout="centered"
)

# ── Load knowledge base ───────────────────────────────────────
def load_knowledge_base():
    with open("knowledge_base.json", "r") as f:
        data = json.load(f)
    return data["faqs"]

# ── Search KB for matching FAQ ────────────────────────────────
def search_knowledge_base(user_query, faqs):
    query_lower = user_query.lower()
    for faq in faqs:
        # Check if any keyword from this FAQ appears in the user's question
        for keyword in faq["keywords"]:
            if keyword.lower() in query_lower:
                return faq["answer"]
    return None

# ── Call Groq AI ──────────────────────────────────────────────
def ask_groq(user_query, chat_history):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    system_prompt = """You are a helpful customer support agent for HealthSure, 
a health insurance company. You only answer questions related to health insurance — 
such as claims, coverage, premiums, deductibles, hospitalisation, and policy details.

If a question is completely unrelated to health insurance, politely say:
"I can only assist with health insurance related queries. Please contact us for other concerns."

Keep your answers concise, friendly, and professional. Do not make up specific 
policy numbers or amounts — direct users to their policy document or member portal 
for specific details."""

    messages = [{"role": "system", "content": system_prompt}]

    # Add previous chat history for context
    for msg in chat_history[-6:]:  # last 6 messages for context
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add current question
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages,
        max_tokens=500,
        temperature=0.3
    )

    return response.choices[0].message.content

# ── Save ticket to SQLite ─────────────────────────────────────
def create_ticket(chat_history):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            conversation TEXT,
            status TEXT DEFAULT 'open'
        )
    """)

    # Format conversation for storage
    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in chat_history
    ])

    cursor.execute("""
        INSERT INTO tickets (timestamp, conversation, status)
        VALUES (?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), conversation_text, "open"))

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

# ── UI Starts Here ────────────────────────────────────────────
st.title("🏥 HealthSure Customer Support")
st.caption("Ask us anything about your health insurance policy.")

# Load KB
faqs = load_knowledge_base()

# Initialise session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ticket_raised" not in st.session_state:
    st.session_state.ticket_raised = False

# Display existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "label" in msg:
            if msg["label"] == "KB":
                st.caption("✅ Answered from Knowledge Base")
            elif msg["label"] == "AI":
                st.caption("🤖 Answered by AI (Groq / Llama 3)")

# Chat input
user_input = st.chat_input("Type your question here...")

if user_input:
    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Try KB first
    kb_answer = search_knowledge_base(user_input, faqs)

    if kb_answer:
        # Answered from KB
        with st.chat_message("assistant"):
            st.markdown(kb_answer)
            st.caption("✅ Answered from Knowledge Base")

        st.session_state.messages.append({
            "role": "assistant",
            "content": kb_answer,
            "label": "KB"
        })

    else:
        # Fall back to Groq AI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_answer = ask_groq(user_input, st.session_state.messages)
            st.markdown(ai_answer)
            st.caption("🤖 Answered by AI (Groq / Llama 3)")

        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_answer,
            "label": "AI"
        })

# ── Ticket Section ────────────────────────────────────────────
if len(st.session_state.messages) > 0:
    st.divider()

    if not st.session_state.ticket_raised:
        st.markdown("**Still need help?**")
        if st.button("🎫 Raise a Support Ticket", use_container_width=True):
            ticket_id = create_ticket(st.session_state.messages)
            st.session_state.ticket_raised = True
            st.success(f"✅ Ticket #{ticket_id} raised successfully! Our team will get back to you within 24 hours.")
            st.balloons()
    else:
        st.success("🎫 Your support ticket has been raised. Our team will reach out soon.")
