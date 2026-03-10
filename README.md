# CashFlow-Agent
A smart dashboard for local businesses to track pending payments and generate context-aware WhatsApp reminders using AI.
# 💸 Tone-Adjusting Cash Flow Chaser (B2B SaaS MVP)

An AI-assisted workflow dashboard designed for local SMEs to manage pending payments, track capital, and generate context-aware payment reminders without ruining client relationships.

## ⚠️ The Business Problem
Local business owners (SMEs) face a constant dilemma: They need to recover delayed payments to maintain cash flow, but they hesitate to send strict reminders out of fear of damaging long-term customer relationships. Manual tracking via registers or basic Excel sheets leads to missed follow-ups and lost capital.

## 💡 The Solution
This tool replaces manual tracking with a **Smart Action Queue** and uses Generative AI to act as a digital accounts manager. Instead of sending robotic, static WhatsApp templates, the AI reads the specific client's "Relationship Status" and "Previous Context" to draft highly personalized, empathetic messages.

## 🚀 Core Features
* **Smart Action Queue:** Automatically filters and prioritizes clients who need to be contacted *today* based on custom snooze dates and payment status.
* **Dynamic AI Tone Engine:** Integrates Google Gemini 2.5 Flash to adjust the communication tone (Friendly, Firm, or Strict) based on exactly how many days the payment is overdue and the client's VIP/Tense status.
* **Zero-Cost WhatsApp Integration:** Bypasses expensive official WhatsApp API costs by dynamically encoding AI-generated text into direct `wa.me` web links for 1-click sending.
* **AI Chat Analyzer (Human-in-the-loop):** Users can paste raw WhatsApp chat replies from clients. The AI extracts the unstructured data (promises to pay, relationship updates) into strict JSON and smart-matches it to update the correct Client ID in the database.

## 🛠️ Tech Stack & Architecture
* **Frontend:** Streamlit (Python)
* **Data Engineering:** Pandas (for DataFrame manipulation and local CSV state management)
* **AI Integration:** Google Generative AI SDK (Gemini-2.5-Flash)
* **Architecture Highlights:** Implemented synthetic Primary Keys (`Client_ID`) to ensure true B2B entity tracking (avoiding data corruption from employee/phone number changes), and built a self-healing schema migration script.

## ⚙️ How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your `.streamlit/secrets.toml` with your `GEMINI_API_KEY`.
4. Run the main application: `streamlit run Tool-2.py`

## 🔮 Future Scope (Sprint 6)
* Migration from local CSV storage to a persistent Cloud Database (PostgreSQL/Supabase).
* Implementation of true Multi-Tenancy architecture with isolated `Tenant_IDs`.
* Automated CRON jobs for zero-touch daily email alerts to operations managers.
