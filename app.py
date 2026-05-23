import streamlit as st
import requests
import re
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from groq import Groq
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="First Sequoia | AI Research Assistant",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a3a2a, #2d6a4f);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.2rem 0 0; opacity: 0.85; font-size: 0.95rem; }
    .summary-box {
        background: #f8faf9;
        border-left: 4px solid #2d6a4f;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.8rem;
    }
    .stDownloadButton > button {
        background-color: #2d6a4f;
        color: white;
        border: none;
    }
    .stDownloadButton > button:hover { background-color: #1a3a2a; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# AUTHENTICATION
# ============================================================
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("⛔ Incorrect username or password.")
    st.stop()

if auth_status is None:
    st.markdown("""
    <div style='text-align:center; margin-top: 3rem;'>
        <h2>🌲 First Sequoia Financial</h2>
        <p style='color:gray;'>Internal AI Research Assistant — Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
# HEADER (shown only after login)
# ============================================================
st.markdown(f"""
<div class="main-header">
    <h1>🌲 First Sequoia Financial — AI Research Assistant</h1>
    <p>Welcome, {name} &nbsp;|&nbsp; SEC Filing Summarizer</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    authenticator.logout("🚪 Logout", "sidebar")
    st.markdown("---")
    st.header("🔍 Filing Search")
    ticker = st.text_input("Ticker Symbol", placeholder="e.g. AAPL, NVDA, MSFT").upper().strip()
    filing_type_label = st.selectbox(
        "Filing Type",
        [
            "10-K  —  Annual Report",
            "10-Q  —  Quarterly Report",
            "8-K   —  Current Events / Press Release",
        ],
    )
    form_code = filing_type_label.split("—")[0].strip().replace(" ", "")
    st.markdown("---")
    st.caption("Data source: SEC EDGAR (live)\nAI: Groq Llama 3.3 70B")

# ============================================================
# SEC EDGAR HELPERS
# ============================================================
EDGAR_HEADERS = {"User-Agent": "FirstSequoiaFinancial info@firstseq.com"}


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_ticker(ticker: str):
    """Return (cik_padded, company_name) for a ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
    r.raise_for_status()
    for entry in r.json().values():
        if entry["ticker"].upper() == ticker:
            return str(entry["cik_str"]).zfill(10), entry["title"]
    return None, None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_filings(cik: str, form: str, count: int = 6):
    """Return a list of recent filings dicts."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    recent = data.get("filings", {}).get("recent", {})
    forms   = recent.get("form", [])
    dates   = recent.get("filingDate", [])
    accs    = recent.get("accessionNumber", [])
    docs    = recent.get("primaryDocument", [])

    results = []
    for i, f in enumerate(forms):
        if f == form and len(results) < count:
            results.append({
                "date":      dates[i],
                "acc_clean": accs[i].replace("-", ""),
                "acc_raw":   accs[i],
                "document":  docs[i] if i < len(docs) else "",
            })
    return results


def fetch_filing_text(cik: str, acc_clean: str, document: str, max_chars: int = 20000) -> str | None:
    """Download and clean filing text from EDGAR."""
    cik_int = int(cik)
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/{document}"
    try:
        r = requests.get(url, headers=EDGAR_HEADERS, timeout=30)
        if r.status_code != 200:
            return None
        text = re.sub(r"<[^>]+>", " ", r.text)   # strip HTML tags
        text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
        return text[:max_chars]
    except Exception:
        return None


# ============================================================
# AI SUMMARY
# ============================================================
def summarize(text: str, company: str, form: str, date: str) -> str:
    api_key = (
        os.environ.get("GROQ_API_KEY")
        or st.secrets.get("GROQ_API_KEY", "")
    )
    if not api_key:
        st.error("GROQ_API_KEY not set. Add it to Streamlit secrets or your .env file.")
        st.stop()

    client = Groq(api_key=api_key)

    prompt = f"""You are a senior financial analyst at a fiduciary wealth management firm.
Analyze the following {form} SEC filing for {company} (filed {date}).
Produce a concise, structured summary for an investment advisor. Be specific — include numbers where available.

Use EXACTLY this format:

## 📋 Executive Overview
[2–3 sentences on what the company does and its current business position.]

## 💰 Financial Highlights
- [Key revenue figure and YoY change]
- [Earnings/net income and YoY change]
- [Gross/operating margin]
- [Free cash flow or notable balance sheet item]
- [Any significant one-time items]

## ⚠️ Key Risks
- [Risk 1]
- [Risk 2]
- [Risk 3]
- [Risk 4 if material]

## 🔮 Outlook & Forward Guidance
[What management said about the next quarter/year — guidance ranges, macro commentary, strategic initiatives.]

## 🎯 Investment Considerations
[2–3 sentences on what a wealth manager placing client capital should weigh about this company — valuation, competitive position, portfolio fit.]

---
FILING TEXT:
{text}
"""

    # Try primary model, fall back to smaller model if rate limited
    for model in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"]:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["rate", "limit", "capacity", "decommission", "deprecated", "not supported"]):
                continue  # try next model
            raise  # re-raise if it's a different error
    raise Exception("All models failed — try again in a minute.")


# ============================================================
# MAIN TABS
# ============================================================
tab_generate, tab_history = st.tabs(["📄 Generate Summary", "📚 Session History"])

# ---- Session state init ----
if "summaries" not in st.session_state:
    st.session_state.summaries = []

# ============================================================
# TAB 1 — GENERATE
# ============================================================
with tab_generate:
    if not ticker:
        st.info("👈 Enter a ticker symbol in the sidebar to get started.")
    else:
        # Resolve ticker → CIK
        with st.spinner(f"Looking up **{ticker}** on SEC EDGAR..."):
            cik, company_name = resolve_ticker(ticker)

        if not cik:
            st.error(f"No company found for ticker **{ticker}**. Double-check the symbol.")
        else:
            st.success(f"**{company_name}**  ·  CIK: {int(cik)}")

            # Fetch filing list
            with st.spinner(f"Fetching recent {form_code} filings..."):
                filings = fetch_filings(cik, form_code)

            if not filings:
                st.warning(f"No {form_code} filings found for {ticker}.")
            else:
                labels  = [f"{f['date']}  —  {form_code}" for f in filings]
                sel_idx = st.selectbox("Select Filing", range(len(labels)), format_func=lambda i: labels[i])
                filing  = filings[sel_idx]

                sec_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{filing['acc_clean']}/{filing['document']}"
                )
                st.caption(f"[🔗 View original filing on SEC.gov]({sec_url})")

                if st.button("🤖 Generate AI Summary", type="primary", use_container_width=True):
                    with st.spinner("Downloading filing from SEC EDGAR..."):
                        raw_text = fetch_filing_text(cik, filing["acc_clean"], filing["document"])

                    if not raw_text:
                        st.error("Could not retrieve filing text. Try a different filing or check SEC.gov directly.")
                    else:
                        word_count = len(raw_text.split())
                        st.caption(f"Filing retrieved — {word_count:,} words sent to AI for analysis.")

                        with st.spinner("AI is reading and summarizing the filing... (~15–30 sec)"):
                            summary = summarize(raw_text, company_name, form_code, filing["date"])

                        # Display
                        st.markdown("---")
                        st.markdown(f"### {company_name} — {form_code} &nbsp;·&nbsp; {filing['date']}")
                        st.markdown(summary)
                        st.markdown("---")

                        # Save to history
                        entry = {
                            "ticker":       ticker,
                            "company":      company_name,
                            "form":         form_code,
                            "filing_date":  filing["date"],
                            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "summary":      summary,
                        }
                        st.session_state.summaries.append(entry)

                        # Download
                        download_text = (
                            f"FIRST SEQUOIA FINANCIAL — AI RESEARCH SUMMARY\n"
                            f"{'=' * 55}\n"
                            f"Company:  {company_name} ({ticker})\n"
                            f"Filing:   {form_code}  |  Date: {filing['date']}\n"
                            f"Generated:{entry['generated_at']}\n"
                            f"{'=' * 55}\n\n"
                            f"{summary}"
                        )
                        st.download_button(
                            "⬇️ Download Summary (.txt)",
                            data=download_text,
                            file_name=f"{ticker}_{form_code}_{filing['date']}.txt",
                            mime="text/plain",
                        )

# ============================================================
# TAB 2 — HISTORY
# ============================================================
with tab_history:
    if not st.session_state.summaries:
        st.info("No summaries generated yet in this session. They appear here as you create them.")
    else:
        st.caption(f"{len(st.session_state.summaries)} summary/summaries generated this session.")
        for entry in reversed(st.session_state.summaries):
            label = f"📄 {entry['ticker']} — {entry['form']}  ({entry['filing_date']})  ·  Generated {entry['generated_at']}"
            with st.expander(label):
                st.markdown(entry["summary"])
                dl_text = (
                    f"FIRST SEQUOIA FINANCIAL — AI RESEARCH SUMMARY\n"
                    f"{'=' * 55}\n"
                    f"Company:  {entry['company']} ({entry['ticker']})\n"
                    f"Filing:   {entry['form']}  |  Date: {entry['filing_date']}\n"
                    f"Generated:{entry['generated_at']}\n"
                    f"{'=' * 55}\n\n"
                    f"{entry['summary']}"
                )
                st.download_button(
                    "⬇️ Download",
                    data=dl_text,
                    file_name=f"{entry['ticker']}_{entry['form']}_{entry['filing_date']}.txt",
                    key=f"dl_{entry['ticker']}_{entry['filing_date']}_{entry['generated_at']}",
                )
