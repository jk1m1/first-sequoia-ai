# First Sequoia Financial — AI Research Assistant
## Setup & Deployment Guide

---

## What This Tool Does

A private, password-protected web app for Eric and employees to:
- Type any stock ticker (e.g. AAPL, NVDA, MSFT)
- Select a filing type: 10-K (annual), 10-Q (quarterly), or 8-K (current events)
- Get a structured AI summary in ~20 seconds pulled live from SEC EDGAR
- Download summaries as .txt files for client notes or internal records

**Cost to run: $0/month** (Groq free tier + Streamlit Community Cloud free tier)

---

## Step 1 — Get a Free Groq API Key (5 minutes)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Click **"API Keys"** → **"Create API Key"**
4. Copy the key — you'll need it in Step 4

> Groq's free tier: 14,400 requests/day, 30/minute. More than enough for a small firm.

---

## Step 2 — Set Your Own Passwords

1. Open `generate_passwords.py`
2. Replace `YourEricPasswordHere` and `YourInternPasswordHere` with your actual passwords
3. Run it:
   ```bash
   pip install streamlit-authenticator==0.2.3 bcrypt==4.0.1
   python generate_passwords.py
   ```
4. Copy the two hashes it prints
5. Open `config.yaml` and paste them under `eric → password` and `intern → password`
6. Also change the cookie `key` to any long random string (e.g. smash your keyboard for 30 chars)
7. Delete the plaintext passwords from `generate_passwords.py`

---

## Step 3 — Test Locally (optional but recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Groq key temporarily
export GROQ_API_KEY="your_key_here"   # Mac/Linux
# or: set GROQ_API_KEY=your_key_here  # Windows

# Run the app
streamlit run app.py
```

Open http://localhost:8501 — log in with eric / intern credentials and test a summary.

---

## Step 4 — Deploy to Streamlit Community Cloud (Free, ~10 minutes)

### 4a. Push to a PRIVATE GitHub repo

```bash
cd first-sequoia-ai
git init
git add app.py requirements.txt
# DO NOT add config.yaml or .env — they contain passwords/keys
git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/first-sequoia-ai.git
git push -u origin main
```

> Keep the repo **private** on GitHub (Settings → Change visibility → Private)

### 4b. Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"** → select your private repo → `main` branch → `app.py`
4. Click **"Advanced settings"** → paste this into the Secrets box:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
5. Click **Deploy**

### 4c. Upload config.yaml directly via Streamlit Cloud

Since `config.yaml` is gitignored, upload it separately:
- In your app's Streamlit Cloud dashboard → **Files** tab → upload `config.yaml`
- Or add its contents to Streamlit secrets as a TOML block (advanced)

> **Alternative**: Store `config.yaml` contents in Streamlit secrets under `[auth]` and load from `st.secrets` — ask your intern to implement this upgrade.

---

## Security Summary

| Layer | What it does |
|---|---|
| Password login | `streamlit-authenticator` — bcrypt-hashed, cookie-based sessions |
| HTTPS | Automatic via Streamlit Community Cloud |
| API key protection | Stored in Streamlit Cloud secrets, never in code |
| Passwords not in code | `config.yaml` is gitignored, never pushed to GitHub |
| Private GitHub repo | Source code not publicly visible |
| Session expiry | Cookies expire after 30 days (configurable in config.yaml) |

---

## How Other Firms Do This

| Firm Size | Approach | Cost |
|---|---|---|
| BlackRock, JPMorgan | Custom LLM pipelines on Azure/AWS, proprietary data feeds | $millions |
| Mid-size RIAs | AlphaSense, Kensho, Tegus | $500–$2,000/month |
| Small boutiques | Manual reading, basic Bloomberg terminals | $2,000/month+ |
| **First Sequoia (this tool)** | **Custom-built, Groq + SEC EDGAR** | **$0/month** |

---

## Workflow Integration for Eric

**Before a client meeting:**
- Open the app → type the client's held tickers → generate 10-K summaries → paste key points into meeting notes

**During investment research:**
- Run 8-K summaries on earnings day to catch guidance and surprises in seconds

**Quarterly review prep:**
- Pull 10-Q summaries for each portfolio holding → compile into a client-ready report

**Future upgrades (intern project ideas):**
- Add a portfolio tracker tab (enter all holdings at once, batch summarize)
- Email digest: auto-send weekly summaries for watchlist tickers
- Earnings calendar integration
- Export summaries directly to Word/PDF for client packets

---

## File Structure

```
first-sequoia-ai/
├── app.py                  ← Main Streamlit application
├── config.yaml             ← Auth config with hashed passwords (NEVER push to GitHub)
├── requirements.txt        ← Python dependencies
├── .gitignore              ← Prevents secrets from being pushed
├── generate_passwords.py   ← Run once to hash passwords, then delete passwords from it
└── SETUP_GUIDE.md          ← This file
```
