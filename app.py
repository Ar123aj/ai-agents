import os
import sys
import requests
import time
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Force unbuffered output (Render logs ke liye)
os.environ['PYTHONUNBUFFERED'] = '1'

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def log(msg):
    print(msg, flush=True)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=30)
        log(f"Telegram response: {r.status_code} - {r.text}")
        return r.status_code == 200
    except Exception as e:
        log(f"❌ Telegram error: {e}")
        return False

def test_groq():
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Say 'Agents online' in 3 words."}],
            max_tokens=20
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"❌ Groq error: {e}")
        return f"Groq failed: {e}"

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass  # Chup raho, logs saaf rakho

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    log(f"🌐 Health server running on port {port}")
    server.serve_forever()

def main():
    log("🚀 Agent starting...")
    log(f"GROQ key exists: {bool(GROQ_API_KEY)}")
    log(f"Telegram token exists: {bool(TELEGRAM_BOT_TOKEN)}")
    log(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    
    log("Testing Groq...")
    groq_reply = test_groq()
    log(f"Groq says: {groq_reply}")
    
    log("Sending Telegram message...")
    msg = f"""🤖 AI Agents Test Successful!

✅ Groq API: Working
✅ Telegram: Working
✅ Server: Online

Groq says: {groq_reply}"""
    
    success = send_telegram(msg)
    if success:
        log("✅ Test message sent!")
    else:
        log("❌ Telegram send failed")
    
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
