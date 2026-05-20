import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="HealthSure Admin Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Overall background */
    .stApp { background-color: #f4f6f9; }

    /* Hide default Streamlit header padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* KPI cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 5px solid #1a73e8;
        margin-bottom: 1rem;
    }
    .kpi-card.green  { border-left-color: #34a853; }
    .kpi-card.amber  { border-left-color: #fbbc04; }
    .kpi-card.red    { border-left-color: #ea4335; }
    .kpi-card.blue   { border-left-color: #1a73e8; }
    .kpi-card.purple { border-left-color: #9334e6; }

    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #5f6368;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #202124;
        line-height: 1;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #80868b;
        margin-top: 0.3rem;
    }

    /* Section header */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #202124;
        margin: 1.4rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e8eaed;
    }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-open        { background: #fce8e6; color: #c5221f; }
    .badge-in_progress { background: #fef7e0; color: #b06000; }
    .badge-resolved    { background: #e6f4ea; color: #137333; }

    /* Ticket card */
    .ticket-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
        border-left: 4px solid #dadce0;
        transition: box-shadow 0.15s;
    }
    .ticket-card:hover { box-shadow: 0 3px 8px rgba(0,0,0,0.12); }
    .ticket-card.open        { border-left-color: #ea4335; }
    .ticket-card.in_progress { border-left-color: #fbbc04; }
    .ticket-card.resolved    { border-left-color: #34a853; }

    /* Conversation bubbles */
    .bubble-user {
        background: #e8f0fe;
        border-radius: 12px 12px 12px 2px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 2rem 0.3rem 0;
        font-size: 0.88rem;
        color: #1a1a2e;
    }
    .bubble-assistant {
        background: #f1f3f4;
        border-radius: 12px 12px 2px 12px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0 0.3rem 2rem;
        font-size: 0.88rem;
        color: #202124;
    }
    .bubble-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
        color: #5f6368;
    }

    /* Page title */
    .page-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #202124;
        margin-bottom: 0.2rem;
    }
    .page-subtitle {
        font-size: 0.92rem;
        color: #5f6368;
        margin-bottom: 1.5rem;
    }
    hr.divider {
        border: none;
        border-top: 1px solid #e8eaed;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── DB helpers ────────────────────────────────────────────────
def get_connection():
    return sqlite3.connect("tickets.db")


def ensure_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            conversation TEXT,
            status TEXT DEFAULT 'open'
        )
    """)
    conn.commit()
    conn.close()


def load_tickets():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, timestamp, conversation, status FROM tickets ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


def update_status(ticket_id, new_status):
    conn = get_connection()
    conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
    conn.commit()
    conn.close()


def delete_ticket(ticket_id):
    conn = get_connection()
    conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()


def parse_conversation(raw):
    lines = []
    for line in raw.strip().split("\n"):
        if line.startswith("USER:"):
            lines.append(("user", line[5:].strip()))
        elif line.startswith("ASSISTANT:"):
            lines.append(("assistant", line[10:].strip()))
    return lines


def extract_preview(conversation_text, max_chars=120):
    for line in conversation_text.strip().split("\n"):
        if line.startswith("USER:"):
            text = line[5:].strip()
            return text[:max_chars] + ("…" if len(text) > max_chars else "")
    return "No preview available"


ensure_table()

# ── Page header ───────────────────────────────────────────────
st.markdown('<div class="page-title">🏥 HealthSure Admin Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="page-subtitle">Support ticket management &nbsp;·&nbsp; '
    f'Last refreshed: {datetime.now().strftime("%d %b %Y, %H:%M")}</div>',
    unsafe_allow_html=True
)

col_refresh, _ = st.columns([1, 8])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── Load data ─────────────────────────────────────────────────
df = load_tickets()

total      = len(df)
open_c     = len(df[df["status"] == "open"])
inprog_c   = len(df[df["status"] == "in_progress"])
resolved_c = len(df[df["status"] == "resolved"])

# Resolution rate
res_rate = f"{int(resolved_c / total * 100)}%" if total > 0 else "—"

# Avg tickets last 7 days (rough)
if total > 0:
    df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    week_ago = datetime.now() - timedelta(days=7)
    week_c = len(df[df["ts"] >= week_ago])
else:
    week_c = 0

# ── KPI Row ───────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-label">Total Tickets</div>
        <div class="kpi-value">{total}</div>
        <div class="kpi-sub">All time</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card red">
        <div class="kpi-label">Open</div>
        <div class="kpi-value">{open_c}</div>
        <div class="kpi-sub">Awaiting action</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card amber">
        <div class="kpi-label">In Progress</div>
        <div class="kpi-value">{inprog_c}</div>
        <div class="kpi-sub">Being handled</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-label">Resolved</div>
        <div class="kpi-value">{resolved_c}</div>
        <div class="kpi-sub">Resolution rate: {res_rate}</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card purple">
        <div class="kpi-label">Last 7 Days</div>
        <div class="kpi-value">{week_c}</div>
        <div class="kpi-sub">New tickets</div>
    </div>""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────
st.markdown('<div class="section-header">Ticket Queue</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns([2, 2, 4])
with f1:
    status_filter = st.selectbox(
        "Status",
        ["All", "Open", "In Progress", "Resolved"],
        label_visibility="collapsed"
    )
with f2:
    sort_order = st.selectbox(
        "Sort",
        ["Newest First", "Oldest First"],
        label_visibility="collapsed"
    )
with f3:
    search_query = st.text_input(
        "Search",
        placeholder="🔍  Search ticket content…",
        label_visibility="collapsed"
    )

# Apply filters
filtered = df.copy()

status_map = {
    "All": None,
    "Open": "open",
    "In Progress": "in_progress",
    "Resolved": "resolved"
}
selected_status = status_map[status_filter]
if selected_status:
    filtered = filtered[filtered["status"] == selected_status]

if search_query:
    mask = filtered["conversation"].str.contains(search_query, case=False, na=False)
    filtered = filtered[mask]

if sort_order == "Newest First":
    filtered = filtered.sort_values("id", ascending=False)
else:
    filtered = filtered.sort_values("id", ascending=True)

# ── Ticket list ───────────────────────────────────────────────
if filtered.empty:
    st.info("No tickets match the current filters.")
else:
    st.markdown(f"<p style='color:#5f6368;font-size:0.85rem;margin-bottom:0.8rem'>"
                f"Showing <strong>{len(filtered)}</strong> ticket(s)</p>",
                unsafe_allow_html=True)

    for _, row in filtered.iterrows():
        tid     = int(row["id"])
        status  = row["status"]
        ts      = row["timestamp"]
        preview = extract_preview(row["conversation"])

        badge_cls = {
            "open": "badge-open",
            "in_progress": "badge-in_progress",
            "resolved": "badge-resolved"
        }.get(status, "badge-open")

        badge_label = status.replace("_", " ").title()

        with st.container():
            st.markdown(f"""
            <div class="ticket-card {status}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:700;color:#202124;font-size:0.95rem;">
                            Ticket #{tid}
                        </span>
                        &nbsp;&nbsp;
                        <span class="badge {badge_cls}">{badge_label}</span>
                    </div>
                    <span style="font-size:0.78rem;color:#80868b;">{ts}</span>
                </div>
                <div style="margin-top:0.4rem;font-size:0.86rem;color:#3c4043;">
                    {preview}
                </div>
            </div>""", unsafe_allow_html=True)

            with st.expander(f"  View details — Ticket #{tid}"):

                # Conversation transcript
                st.markdown("**Conversation Transcript**")
                turns = parse_conversation(row["conversation"])
                if turns:
                    for role, content in turns:
                        if role == "user":
                            st.markdown(
                                f'<div class="bubble-label">Customer</div>'
                                f'<div class="bubble-user">{content}</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f'<div class="bubble-label">Agent</div>'
                                f'<div class="bubble-assistant">{content}</div>',
                                unsafe_allow_html=True
                            )
                else:
                    st.caption("No conversation content available.")

                st.markdown("<hr class='divider'>", unsafe_allow_html=True)

                # Actions
                a1, a2, a3 = st.columns([2, 2, 2])

                with a1:
                    new_status = st.selectbox(
                        "Update Status",
                        ["open", "in_progress", "resolved"],
                        index=["open", "in_progress", "resolved"].index(status),
                        key=f"status_{tid}"
                    )
                with a2:
                    st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
                    if st.button("💾 Save Status", key=f"save_{tid}", use_container_width=True):
                        update_status(tid, new_status)
                        st.success(f"Ticket #{tid} updated to **{new_status.replace('_',' ').title()}**")
                        st.rerun()
                with a3:
                    st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete Ticket", key=f"del_{tid}", use_container_width=True, type="secondary"):
                        delete_ticket(tid)
                        st.warning(f"Ticket #{tid} deleted.")
                        st.rerun()
