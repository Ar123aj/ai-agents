import os
import sys
import asyncio
import requests
import time
import threading
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Config
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# User state (kaunsa user kis step pe hai)
user_state = {}

# Niches
NICHES = {
    "1": "Applied AI Tools & B2B SaaS (SmartStackAI)",
    "2": "Productivity & Career Systems (WorkSmartHQ)",
    "3": "Health & Weight Management (HealthySugarWeightHub)",
    "4": "Cybersecurity & Privacy Explainers",
    "5": "History & Science Explainers",
    "6": "Space & Physics Lore"
}

# ============================================
# LLM CALL HELPER
# ============================================
def ask_groq(prompt, max_tokens=2000):
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"

# ============================================
# AGENT 1: RESEARCH
# ============================================
def research_agent(niche):
    prompt = f"""You are a YouTube Research Agent for US audience.

NICHE: {niche}

Find 5 trending video topics for this niche.
For each topic give:
- Title (US English, compelling)
- Why trending (1 line)
- Risk level (low/medium/high)

Output format (exactly 5):
1. [Title] | [Why] | [Risk]
2. [Title] | [Why] | [Risk]
3. [Title] | [Why] | [Risk]
4. [Title] | [Why] | [Risk]
5. [Title] | [Why] | [Risk]

Return only the list, no extra text."""
    return ask_groq(prompt, max_tokens=800)

# ============================================
# AGENT 2: SCRIPT
# ============================================
def script_agent(topic, niche):
    prompt = f"""You are a YouTube Script Writer for US audience.

TOPIC: {topic}
NICHE: {niche}
LENGTH: 8 minutes (~1200 words)
LANGUAGE: US English

STRUCTURE:
1. Hook (0-15 sec) — 3 options
2. Setup (15-60 sec) — context
3. Body (1-6 min) — main content
4. Twist/Insight (6-7 min)
5. CTA (7-8 min)

RULES:
- 100% original content
- No plagiarism
- Cite 2-3 credible sources inline
- Visual cues in [brackets]
- No misleading claims

Write the full script now."""
    return ask_groq(prompt, max_tokens=2500)

# ============================================
# AGENT 3: FACT-CHECKER
# ============================================
def fact_check_agent(script):
    prompt = f"""You are a Fact-Checker.

Review this script and identify:
1. All factual claims
2. Which claims need verification
3. Any risky/unverified statements
4. Overall: PASS or NEEDS_REVISION

SCRIPT:
{script[:3000]}

Output concise report (max 300 words)."""
    return ask_groq(prompt, max_tokens=600)

# ============================================
# AGENT 4: CHIEF/QA
# ============================================
def qa_agent(script, fact_check):
    prompt = f"""You are Chief/QA Guardian for YouTube.

EXTRA RULES FOR HEALTH NICHE:
- No medical advice — only general information
- "Consult a doctor" disclaimer must be present
- 3+ peer-reviewed sources (PubMed, NIH, WHO)
- No "cure"/"guaranteed"/"miracle" claims
- No specific diet/drug recommendations
- No fear-mongering
- AI disclosure set

Check 15 safety rules: copyright, plagiarism, facts, policy, AI disclosure, original angle, no misleading, human touch, niche fit, brand voice, disclaimer, sources, no hacking, no fear-mongering, affiliate disclosure.
Output: PASS or FAIL with reasons (max 150 words).
SCRIPT: {script[:500]}
FACT CHECK: {fact_check}"""
    return ask_groq(prompt, max_tokens=400)
# ============================================
# AGENT 5: SEO
# ============================================
def seo_agent(topic, niche):
    prompt = f"""You are an SEO Agent for YouTube.

TOPIC: {topic}
NICHE: {niche}
AUDIENCE: US

Generate:
1. 3 Title options (<60 chars, keyword-first)
2. Description (200 words, with timestamps placeholder)
3. 15 Tags (US English)
4. 5 Hashtags

Format clearly."""
    return ask_groq(prompt, max_tokens=800)

# ============================================
# TELEGRAM HANDLERS
# ============================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_state[chat_id] = {"step": "choose_niche"}
    
    msg = """🤖 *AI Agents Ready!*

Niche choose karo:

1️⃣ AI Tools (SmartStackAI)
2️⃣ Productivity (WorkSmartHQ)
3️⃣ Health & Weight (HealthySugarWeightHub)
4️⃣ Cybersecurity
5️⃣ History & Science
6️⃣ Space & Physics

Reply *1-6*"""
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    
    state = user_state.get(chat_id, {})
    step = state.get("step", "idle")
    
    # STEP 1: Niche choose
    if step == "choose_niche":
        if text not in NICHES:
            await update.message.reply_text("❌ 1, 2, ya 3 reply karo.")
            return
        
        niche = NICHES[text]
        state["niche"] = niche
        state["step"] = "choose_topic"
        user_state[chat_id] = state
        
        await update.message.reply_text(f"✅ Niche: *{niche}*\n\n🔍 Research Agent kaam kar raha hai... 30 sec wait karo.", parse_mode="Markdown")
        
        # Research Agent
        topics = research_agent(niche)
        state["topics"] = topics
        user_state[chat_id] = state
        
        msg = f"""📊 *5 Topics Ready:*

{topics}

Reply with *1*, *2*, *3*, *4*, or *5* to choose."""
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    # STEP 2: Topic choose
    elif step == "choose_topic":
        if text not in ["1", "2", "3", "4", "5", "6"]:
            await update.message.reply_text("❌ 1-5 mein se choose karo.")
            return
        
        topics_text = state.get("topics", "")
        lines = [l for l in topics_text.split("\n") if l.strip() and l.strip()[0].isdigit()]
        
        try:
            chosen = lines[int(text) - 1]
            topic = chosen.split("|")[0].strip()
            topic = topic[2:].strip()  # Remove "1. "
        except:
            topic = f"Topic {text}"
        
        niche = state["niche"]
        state["topic"] = topic
        state["step"] = "generating"
        user_state[chat_id] = state
        
        await update.message.reply_text(f"✅ Topic: *{topic}*\n\n📝 Script Agent likh raha hai... 60 sec wait karo.", parse_mode="Markdown")
        
        # Script Agent
        script = script_agent(topic, niche)
        state["script"] = script
        user_state[chat_id] = state
        
        await update.message.reply_text("🔍 Fact-Checker verify kar raha hai...")
        
        # Fact-Checker
        fact_check = fact_check_agent(script)
        state["fact_check"] = fact_check
        user_state[chat_id] = state
        
        await update.message.reply_text("🛡️ Chief/QA safety check kar raha hai...")
        
        # Chief/QA
        qa_result = qa_agent(script, fact_check)
        state["qa"] = qa_result
        user_state[chat_id] = state
        
        await update.message.reply_text("🔎 SEO Agent metadata bana raha hai...")
        
        # SEO
        seo = seo_agent(topic, niche)
        state["seo"] = seo
        state["step"] = "review"
        user_state[chat_id] = state
        
        # Final message
        final_msg = f"""🎬 *Video Package Ready!*

📌 *Topic:* {topic}
📁 *Niche:* {niche}

🛡️ *QA Result:*
{qa_result[:300]}

🔎 *SEO Metadata:*
{seo[:500]}

━━━━━━━━━━━━━━━
*Reply:*
✅ `approve` — Script finalize
✏️ `edit` — Changes chahiye
❌ `reject` — Cancel"""
        
        # Telegram limit 4096 chars
        if len(final_msg) > 4000:
            final_msg = final_msg[:3900] + "..."
        
        await update.message.reply_text(final_msg, parse_mode="Markdown")
    
    # STEP 3: Review
    elif step == "review":
        if text.lower() == "approve":
            state["step"] = "idle"
            user_state[chat_id] = state
            await update.message.reply_text("✅ Script approved! Phase 2 (Voice + Video) agle update mein aayega. 🎉")
        elif text.lower() == "edit":
            await update.message.reply_text("✏️ Kya change karna hai? Feedback bhejo.")
        elif text.lower() == "reject":
            state["step"] = "idle"
            user_state[chat_id] = state
            await update.message.reply_text("❌ Cancelled. /start se dobara shuru karo.")
        else:
            await update.message.reply_text("Reply: `approve`, `edit`, ya `reject`", parse_mode="Markdown")
    
    else:
        await update.message.reply_text("👋 /start bhejo shuru karne ke liye.")

# ============================================
# HEALTH SERVER (UptimeRobot ke liye)
# ============================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Health server on port {port}", flush=True)
    server.serve_forever()

# ============================================
# MAIN
# ============================================
def main():
    print("🚀 AI Agents starting...", flush=True)
    print(f"Groq key: {bool(GROQ_API_KEY)}", flush=True)
    print(f"Bot token: {bool(TELEGRAM_BOT_TOKEN)}", flush=True)
    
    # Health server background mein
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Telegram bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot polling started", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
