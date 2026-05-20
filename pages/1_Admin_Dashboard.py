import streamlit as st
import sqlite3
import json
import pandas as pd

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# ── Helpers ───────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect("tickets.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            conversation TEXT,
            status TEXT DEFAULT 'open'
        )
    """)
    conn.commit()
    return conn


def load_tickets(status_filter=None):
    conn = get_conn()
    if status_filter and status_filter != "All":
        df = pd.read_sql_query(
            "SELECT id, timestamp, status, conversation FROM tickets WHERE status = ? ORDER BY id DESC",
            conn,
            params=(status_filter.lower(),)
        )
    else:
        df = pd.read_sql_query(
            "SELECT id, timestamp, status, conversation FROM tickets ORDER BY id DESC",
            conn
        )
    conn.close()
    df["preview"] = df["conversation"].str[:100]
    return df


def resolve_ticket(ticket_id):
    conn = get_conn()
    conn.execute("UPDATE tickets SET status = 'resolved' WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()


def update_kb(ticket_id, resolution):
    with open("knowledge_base.json", "r") as f:
        kb = json.load(f)
    new_id = max(entry["id"] for entry in kb["faqs"]) + 1
    kb["faqs"].append({
        "id": new_id,
        "question": f"Resolved ticket #{ticket_id}",
        "keywords": [w for w in resolution.lower().split() if len(w) > 3][:6],
        "answer": resolution.strip(),
        "source": "resolved_ticket"
    })
    with open("knowledge_base.json", "w") as f:
        json.dump(kb, f, indent=2)


# ── Page header ───────────────────────────────────────────────
st.title("🛠️ Admin Dashboard")
st.caption("View and manage all support tickets. Resolve open tickets to update the knowledge base.")

col_filter, col_refresh = st.columns([3, 1])
with col_filter:
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Open", "Resolved"],
        index=0
    )
with col_refresh:
    st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── Load & display tickets table ─────────────────────────────
df = load_tickets(status_filter)

st.markdown(f"**{len(df)} ticket(s)** found")

if df.empty:
    st.info("No tickets match the selected filter.")
else:
    st.dataframe(
        df[["id", "timestamp", "status", "preview"]].rename(columns={
            "id": "ID",
            "timestamp": "Timestamp",
            "status": "Status",
            "preview": "Conversation (first 100 chars)"
        }),
        use_container_width=True,
        hide_index=True
    )

# ── Open ticket resolution ────────────────────────────────────
open_df = df[df["status"] == "open"]

if not open_df.empty and status_filter != "Resolved":
    st.divider()
    st.subheader("📋 Resolve Open Tickets")

    for _, row in open_df.iterrows():
        tid = int(row["id"])

        with st.expander(f"Ticket #{tid} — {row['timestamp']}"):
            st.markdown("**Conversation preview:**")
            st.text(row["conversation"][:500] + ("…" if len(row["conversation"]) > 500 else ""))

            resolution = st.text_area(
                "Resolve ticket — enter resolution summary",
                key=f"res_{tid}",
                placeholder="Describe the resolution clearly. This will be added to the knowledge base as a new FAQ answer."
            )

            if st.button("Resolve & Update KB", key=f"resolve_{tid}", type="primary"):
                if resolution.strip():
                    resolve_ticket(tid)
                    update_kb(tid, resolution)
                    st.success(
                        f"✅ Ticket #{tid} has been marked as **resolved** and the knowledge base has been updated with the new FAQ entry."
                    )
                    st.rerun()
                else:
                    st.warning("Please enter a resolution summary before submitting.")
