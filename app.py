import os
import requests
import time
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def test_groq():
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Say 'Agents online' in 3 words."}],
        max_tokens=20
    )
    return response.choices[0].message.content

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthHandler)
    server.serve_forever()

def main():
    print("🚀 Agent starting...")
    threading.Thread(target=run_server, daemon=True).start()
    
    groq_reply = test_groq()
    print(f"Groq says: {groq_reply}")
    
    send_telegram(f"""🤖 AI Agents Test Successful!

✅ Groq API: Working
✅ Telegram: Working
✅ Server: Online

Groq says: {groq_reply}""")
    
    print("✅ Test message sent!")
    
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
