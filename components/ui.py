from __future__ import annotations

from html import escape
import re
import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """<style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

      /* ── Base & App Shell ── */
      :root {
        color-scheme: dark;
      }
      html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #080c18 !important;
        color: #edf0ff !important;
      }
      input, textarea, select, button {
        color-scheme: dark;
      }
      .stApp {
        background: radial-gradient(circle at 15% 0%, #25234c 0, #0b1020 40%, #080c18 100%) !important;
      }

      /* ── Sidebar ── */
      [data-testid="stSidebar"] {
        background: #0d1327 !important;
        border-right: 1px solid rgba(255,255,255,.08) !important;
      }
      [data-testid="stSidebar"] * { color: #edf0ff !important; }
      [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }
      [data-testid="stSidebarContent"] { background: transparent !important; }

      /* ── All text elements ── */
      h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #edf0ff !important;
      }
      .muted, [data-testid="stCaption"], small, .stCaption {
        color: #aeb8d5 !important;
      }

      /* ── Inputs, Textareas, Select ── */
      .stTextInput > div > div > input,
      .stTextArea > div > div > textarea,
      .stSelectbox > div > div > div,
      .stMultiSelect > div > div > div,
      .stNumberInput > div > div > input {
        background-color: rgba(255,255,255,.06) !important;
        color: #edf0ff !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        border-radius: 8px !important;
      }
      .stTextInput > div > div > input:focus,
      .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,.25) !important;
      }
      input::placeholder, textarea::placeholder { color: #6b7fa3 !important; }

      /* ── Labels ── */
      .stTextInput label, .stTextArea label, .stSelectbox label,
      .stRadio label, .stCheckbox label, .stNumberInput label {
        color: #aeb8d5 !important;
        font-size: .85rem !important;
        font-weight: 500 !important;
      }

      /* ── Radio buttons ── */
      [data-testid="stRadio"] > div { gap: 4px !important; }
      [data-testid="stRadio"] label {
        background: rgba(255,255,255,.04) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        color: #aeb8d5 !important;
        transition: all .15s ease !important;
      }
      [data-testid="stRadio"] label:has(input:checked) {
        background: rgba(99,102,241,.18) !important;
        border-color: #6366f1 !important;
        color: #edf0ff !important;
      }

      /* ── Buttons ── */
      div.stButton > button {
        border-radius: 9px !important;
        border: 0 !important;
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        font-weight: 650 !important;
        transition: opacity .15s ease !important;
      }
      div.stButton > button:hover { opacity: .88 !important; }
      div.stButton > button[kind="secondary"] {
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        color: #edf0ff !important;
      }

      /* ── Form submit button ── */
      div.stFormSubmitButton > button {
        border-radius: 9px !important;
        border: 0 !important;
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        font-weight: 650 !important;
      }

      /* ── Expanders ── */
      [data-testid="stExpander"] {
        background: rgba(255,255,255,.03) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 10px !important;
      }
      [data-testid="stExpander"] summary {
        color: #edf0ff !important;
        font-weight: 500 !important;
      }
      [data-testid="stExpander"] summary:hover {
        color: #a78bfa !important;
      }

      /* ── Containers / Borders ── */
      [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: rgba(255,255,255,.025) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 12px !important;
      }

      /* ── Chat ── */
      [data-testid="stChatMessage"] {
        background: rgba(255,255,255,.035) !important;
        border: 1px solid rgba(255,255,255,.06) !important;
        border-radius: 12px !important;
      }
      /* Markdown responses: give generated answers a clear visual hierarchy. */
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3,
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h4 {
        color: #c4b5fd !important;
        letter-spacing: -.015em;
        margin-top: 1rem;
        margin-bottom: .45rem;
      }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
        color: #c4b5fd !important;
        font-weight: 750 !important;
      }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li::marker {
        color: #a78bfa !important;
      }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] blockquote {
        border-left: 3px solid #8b5cf6 !important;
        color: #cbd5e1 !important;
      }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        color: #bfdbfe !important;
        background: rgba(99,102,241,.16) !important;
        border-radius: 4px;
        padding: .1rem .3rem;
      }
      [data-testid="stChatInput"] > div {
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        border-radius: 12px !important;
      }
      [data-testid="stChatInput"] textarea {
        color: #edf0ff !important;
        background: transparent !important;
      }

      /* ── Progress bar ── */
      [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
      }
      [data-testid="stProgressBar"] > div {
        background: rgba(255,255,255,.08) !important;
      }

      /* ── Alerts / Info / Warning / Error ── */
      [data-testid="stAlert"] {
        background: rgba(255,255,255,.04) !important;
        border-radius: 10px !important;
        border-left: 3px solid #6366f1 !important;
      }
      [data-testid="stAlert"][kind="error"] { border-left-color: #fda4af !important; }
      [data-testid="stAlert"][kind="success"] { border-left-color: #86efac !important; }
      [data-testid="stAlert"][kind="warning"] { border-left-color: #fcd34d !important; }

      /* ── Selectbox dropdown ── */
      [data-baseweb="select"] > div {
        background-color: rgba(255,255,255,.06) !important;
        border-color: rgba(255,255,255,.12) !important;
        color: #edf0ff !important;
      }
      [data-baseweb="menu"] {
        background-color: #131b35 !important;
        border: 1px solid rgba(255,255,255,.12) !important;
      }
      [data-baseweb="option"] { color: #edf0ff !important; background: transparent !important; }
      [data-baseweb="option"]:hover { background: rgba(99,102,241,.15) !important; }
      [data-baseweb="popover"], [data-baseweb="popover"] > div {
        background-color: #131b35 !important;
        color: #edf0ff !important;
      }

      /* ── Popover ── */
      [data-testid="stPopover"] > div {
        background: #131b35 !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        border-radius: 12px !important;
      }
      [data-testid="stTooltipHoverTarget"] + div,
      [role="listbox"] {
        background: #131b35 !important;
        color: #edf0ff !important;
      }

      /* ── Divider ── */
      hr { border-color: rgba(255,255,255,.08) !important; }

      /* ── Spinner ── */
      [data-testid="stSpinner"] > div { border-top-color: #6366f1 !important; }

      /* ── Scrollbar ── */
      ::-webkit-scrollbar { width: 5px; height: 5px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: rgba(99,102,241,.4); border-radius: 10px; }

      /* ── Custom components ── */
      .glass-card {
        background: rgba(22, 29, 56, .78) !important;
        border: 1px solid rgba(168, 139, 250, .20) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        box-shadow: 0 12px 35px rgba(0,0,0,.18) !important;
      }
      .metric-card {
        background: rgba(255,255,255,.035) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 13px !important;
        padding: .9rem 1rem !important;
        min-height: 86px !important;
      }
      .metric-value { font-size: 1.45rem !important; font-weight: 750 !important; color: #f5f3ff !important; }
      .metric-label { color: #aeb8d5 !important; font-size: .82rem !important; }
      .eyebrow { color: #a78bfa !important; font-size: .78rem !important; font-weight: 700 !important; letter-spacing: .10em !important; text-transform: uppercase !important; }
      .status-ready { color: #86efac !important; font-weight: 700 !important; }
      .status-failed { color: #fda4af !important; font-weight: 700 !important; }

      /* ── Hide Streamlit chrome ── */
      [data-testid="stToolbar"] { visibility: hidden !important; }
      #MainMenu { visibility: hidden !important; }
      footer { visibility: hidden !important; }
      [data-testid="stDecoration"] { display: none !important; }
    </style>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, hint: str | None = None) -> None:
    hint_markup = f'<div class="muted">{escape(hint)}</div>' if hint else ""
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{escape(value)}</div><div class="metric-label">{escape(label)}</div>{hint_markup}</div>',
        unsafe_allow_html=True,
    )


def source_caption(sources: list[str]) -> None:
    if sources:
        st.caption("Sources: " + " · ".join(sources))


_LABELED_RESPONSE_LINE = re.compile(
    r"^([A-Za-z][A-Za-z0-9 /&()]{1,60}?)\s*(?:—|–|→)\s+(.+)$"
)


def format_assistant_markdown(content: str) -> str:
    """Add lightweight structure to plain-text assistant answers.

    Markdown returned by the model is preserved.  For unformatted explanation
    lines such as ``Input layer — 784 neurons``, create a readable list with
    an accented bold label.  This avoids relying on a particular model prompt.
    """
    formatted: list[str] = []
    for line in content.splitlines():
        match = _LABELED_RESPONSE_LINE.match(line.strip())
        if match and not line.lstrip().startswith(("- ", "* ", "+ ")):
            label, description = match.groups()
            formatted.append(f"- **{label}** — {description}")
        else:
            formatted.append(line)
    return "\n".join(formatted)


def status_card(status: str | None, detail: str | None = None) -> None:
    state = (status or "pending").lower()
    if state in {"completed", "complete", "ready", "success", "processed"}:
        label, klass = "Ready for questions", "status-ready"
    elif state in {"failed", "error"}:
        label, klass = "Processing failed", "status-failed"
    else:
        label, klass = "Processing video…", "muted"
    description = escape(
        str(detail or "We are fetching the video and grounding its transcript.")
    )
    st.markdown(
        f'<div class="glass-card"><div class="eyebrow">Analysis status</div><div class="{klass}">{label}</div><div class="muted">{description}</div></div>',
        unsafe_allow_html=True,
    )


def sidebar() -> str:
    user = st.session_state.get("user", {})
    with st.sidebar:
        st.markdown("## ✦ RAG Video Insight")
        st.caption("Grounded video intelligence")
        st.divider()
        st.markdown(
            f"**{escape(str(user.get('name') or user.get('email') or 'Signed in'))}**",
            unsafe_allow_html=True,
        )
        user_id = user.get("id") or user.get("userId") or user.get("uid")
        if user_id:
            with st.expander("Account"):
                with st.form("profile_form"):
                    name = st.text_input("Name", value=str(user.get("name") or ""))
                    email = st.text_input("Email", value=str(user.get("email") or ""))
                    save = st.form_submit_button("Save profile", use_container_width=True)
                if save:
                    from api_client import APIError
                    from auth import client
                    try:
                        updated = client().update_user_profile(str(user_id), name=name, email=email)
                        st.session_state.user = updated.get("user") or updated.get("profile") or updated
                        st.success("Profile updated.")
                    except APIError as error:
                        st.error(str(error))
        page = st.radio(
            "Workspace",
            ["Dashboard", "Video chat"],
            key="current_page",
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Log out", use_container_width=True):
            from auth import logout

            logout()
            st.rerun()
    return page
