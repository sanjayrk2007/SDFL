import json
import os
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUDIT_LOG = PROJECT_ROOT / "audit_log.jsonl"

st.set_page_config(page_title="SDFL Hospital Dashboard", layout="wide")


def init_local_db():
    os.makedirs(os.path.dirname(LOCAL_DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            status TEXT CHECK(status IN ('PASSED', 'REJECTED')) NOT NULL,
            reason TEXT,
            inpaint_ratio REAL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS privacy_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id INTEGER NOT NULL,
            epsilon_consumed REAL NOT NULL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


CLIENT_ID = os.getenv("CLIENT_ID", "unknown")
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "https://coordinator.sdfl-vendor.com")
EPSILON_THRESHOLD = float(os.getenv("EPSILON_KILL_THRESHOLD", "3.0"))
LOCAL_DB_PATH = os.getenv("LOCAL_DB_PATH", str(PROJECT_ROOT / "data" / "client.db"))
DRAFTS_DIR = Path(os.getenv("LOCAL_DRAFTS_DIR", "/data/incoming_drafts"))
REJECTED_DIR = Path(os.getenv("LOCAL_REJECTED_DIR", "/data/rejected"))
TRAINING_DIR = Path(os.getenv("LOCAL_TRAINING_DIR", "/data/training"))

init_local_db()

st.sidebar.markdown(
    f"### SDFL Hospital Client Node\n**Hospital:** `{CLIENT_ID}`"
)
st.sidebar.markdown("---")


def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def read_audit_log():
    if not AUDIT_LOG.exists():
        return []
    entries = []
    with open(AUDIT_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---- Page 1: PHI Monitor & Annotation Queue ----

def page_phi_monitor():
    st.header("PHI Monitor & Annotation Queue")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM processed_files")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM processed_files WHERE status='PASSED'")
    passed = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM processed_files WHERE status='REJECTED'")
    rejected = cur.fetchone()[0]

    rejection_rate = (rejected / total * 100) if total > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Processed", total)
    col2.metric("Total Passed", passed)
    col3.metric("Total Rejected", rejected)
    col4.metric("Rejection Rate", f"{rejection_rate:.1f}%")

    st.subheader("Recent Files")
    cur.execute(
        "SELECT filename, status, reason, inpaint_ratio, processed_at "
        "FROM processed_files ORDER BY processed_at DESC LIMIT 50"
    )
    rows = cur.fetchall()
    conn.close()

    if rows:
        def color_status(s):
            return f':green[{s}]' if s == 'PASSED' else f':red[{s}]'

        data = [
            {
                "filename": r["filename"],
                "status": color_status(r["status"]),
                "reason": r["reason"] or "",
                "inpaint_ratio": f"{r['inpaint_ratio']:.4f}" if r["inpaint_ratio"] else "",
                "processed_at": r["processed_at"],
            }
            for r in rows
        ]
        st.dataframe(data, width="stretch", hide_index=True)
    else:
        st.info("No processed files yet.")

    st.subheader("Annotation Queue")

    if not DRAFTS_DIR.exists():
        st.warning(f"Drafts directory not found: {DRAFTS_DIR}")
        return

    draft_files = sorted(
        [p for p in DRAFTS_DIR.iterdir() if p.suffix == ".png" and not p.stem.endswith("_mask")]
    )

    st.caption(f"**{len(draft_files)} images awaiting annotation**")

    for fp in draft_files:
        mask_fp = DRAFTS_DIR / f"{fp.stem}_mask.png"
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            try:
                img = Image.open(fp)
                st.image(img, caption=f"Image: {fp.name}", width="stretch")
            except Exception:
                st.error(f"Cannot load {fp.name}")
        with col_b:
            if mask_fp.exists():
                try:
                    mask = Image.open(mask_fp)
                    st.image(mask, caption=f"Mask: {mask_fp.name}", width="stretch")
                except Exception:
                    st.error(f"Cannot load {mask_fp.name}")
            else:
                st.info("No mask yet")
        with col_c:
            if st.button("✅ Approve", key=f"app_{fp.stem}"):
                from platform.client.agent import promote_to_training
                promote_to_training(fp.stem, str(DRAFTS_DIR), str(TRAINING_DIR))
                st.success(f"Approved {fp.stem}")
                st.rerun()
            if st.button("✏️ Reject", key=f"rej_{fp.stem}"):
                from platform.client.agent import reject_draft
                reject_draft(fp.stem, str(DRAFTS_DIR), str(REJECTED_DIR))
                st.success(f"Rejected {fp.stem}")
                st.rerun()
            st.write("")  # spacing for Skip label
            st.caption("Skip")
        st.divider()


# ---- Page 2: Privacy Budget Tracker ----

def page_privacy_budget():
    st.header("Privacy Budget Tracker")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(epsilon_consumed) FROM privacy_logs")
    row = cur.fetchone()
    current_eps = row[0] if row and row[0] is not None else 0.0
    threshold = EPSILON_THRESHOLD

    if current_eps >= threshold:
        st.error("🔴 **EPSILON KILL THRESHOLD REACHED — Training locked**")
    elif current_eps >= 0.9 * threshold:
        st.warning("🟡 **Approaching epsilon kill threshold**")

    ratio = min(current_eps / threshold, 1.0) if threshold > 0 else 0.0
    pct = ratio * 100
    if pct < 60:
        gauge_color = "green"
    elif pct < 90:
        gauge_color = "goldenrod"
    else:
        gauge_color = "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_eps,
        delta={"reference": threshold, "increasing": {"color": "red"}},
        gauge={
            "axis": {"range": [0, threshold * 1.2]},
            "bar": {"color": gauge_color},
            "steps": [
                {"range": [0, threshold * 0.6], "color": "lightgreen"},
                {"range": [threshold * 0.6, threshold * 0.9], "color": "lightyellow"},
                {"range": [threshold * 0.9, threshold], "color": "lightcoral"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": threshold,
            },
        },
        title={"text": "ε Budget Consumption"},
    ))
    fig.update_layout(height=350)
    st.plotly_chart(fig, width="stretch")

    cur.execute(
        "SELECT round_id, MAX(epsilon_consumed) AS eps "
        "FROM privacy_logs GROUP BY round_id ORDER BY round_id"
    )
    rounds = cur.fetchall()

    if rounds:
        rounds_data = [dict(r) for r in rounds]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[r["round_id"] for r in rounds_data],
            y=[r["eps"] for r in rounds_data],
            mode="lines+markers",
            name="ε per round",
        ))
        fig2.add_hline(y=threshold, line_dash="dash", line_color="red",
                       annotation_text=f"Threshold ({threshold})")
        fig2.update_layout(
            title="ε Per Round",
            xaxis_title="Round ID",
            yaxis_title="ε Consumed",
            height=350,
        )
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No privacy logs yet.")

    st.subheader("Configuration")
    st.markdown(f"- **Current threshold:** `{threshold}`")
    st.info("To change threshold, update `EPSILON_KILL_THRESHOLD` in `.env`")

    conn.close()


# ---- Page 3: Temporal Key Status ----

def page_temporal_key():
    st.header("Temporal Key Status")

    entries = read_audit_log()

    if not entries:
        st.info("No audit log entries found.")
        return

    last = entries[-1]
    event = last.get("event", "")

    if event == "round_open":
        tr = last.get("Tr", 0)
        remaining = max(0, tr - time.time())
        st.success("🟢 **ROUND OPEN**")
        timer_placeholder = st.empty()
        with timer_placeholder.container():
            st.metric("Time until key destruction", f"{int(remaining)}s")
        if remaining > 0:
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Key destruction deadline passed — awaiting server response.")

    elif event == "round_close":
        st.error("🔴 **ROUND CLOSED**")
        st.info("Awaiting server aggregation")

    elif event == "key_destroyed":
        st.markdown("⚫ **KEY DESTROYED**")
        st.info("Ephemeral key wiped from memory")

    else:
        st.write(f"Unknown event: {event}")

    st.subheader("Last 5 Audit Log Entries")
    recent = entries[-5:]
    data = []
    for e in reversed(recent):
        ts = e.get("timestamp") or e.get("Tr", 0)
        if isinstance(ts, (int, float)):
            ts_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(ts)
        data.append({
            "event": e.get("event", ""),
            "round_id": e.get("round_id", ""),
            "timestamp": ts_str,
        })
    st.dataframe(data, width="stretch", hide_index=True)


# ---- Page 4: Connection Status ----

def page_connection_status():
    st.header("Connection Status")

    st.subheader("Coordinator")
    st.markdown(f"**URL:** `{COORDINATOR_URL}`")

    health_url = f"{COORDINATOR_URL.rstrip('/')}/health"
    start = time.time()
    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            elapsed = (time.time() - start) * 1000
            st.success(f"🟢 Connected | Latency: `{elapsed:.0f}ms`")
            st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S')}")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        st.error(f"🔴 Disconnected | Error: `{e}`")

    st.subheader("Current Round")
    rounds_url = f"{COORDINATOR_URL.rstrip('/')}/rounds"
    try:
        req = urllib.request.Request(rounds_url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            payload = json.loads(resp.read().decode())
            st.json(payload)
    except Exception:
        st.info("Round info not available from coordinator.")

    st.subheader("Local Agent Status")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(epsilon_consumed) FROM privacy_logs")
    row = cur.fetchone()
    current_eps = row[0] if row and row[0] is not None else 0.0
    conn.close()

    st.metric("Current ε", f"{current_eps:.4f}")
    st.metric("ε Threshold", f"{EPSILON_THRESHOLD}")

    st.subheader("Auto-Refresh")
    if st.button("🔄 Refresh Now"):
        st.rerun()


# ---- Navigation ----

pages = {
    "PHI Monitor & Annotation Queue": page_phi_monitor,
    "Privacy Budget Tracker": page_privacy_budget,
    "Temporal Key Status": page_temporal_key,
    "Connection Status": page_connection_status,
}

st.sidebar.markdown("### Navigation")
selection = st.sidebar.radio("Go to", list(pages.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("Powered by SDFL v1.0 | TRL-4 Prototype")

pages[selection]()
