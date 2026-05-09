#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import webbrowser
import threading
import time
from groq import Groq

# ── APNI GROQ API KEY YAHAN PASTE KARO ─────────────
API_KEY = "Enter your Groq API"
# ───────────────────────────────────────────────────

client = Groq(api_key=API_KEY)

SYSTEM_PROMPT = """You are an AI assistant for a Hotel Reservations Dashboard built in Power BI.
You help hotel owners and managers analyze their booking data.

You know about this hotel's data:
- Booking Status (Cancelled / Not Cancelled)
- Lead Time (days before check-in booking was made)
- Market Segment Type (Online, Offline, Corporate, Aviation, Complementary)
- Stay Duration (number of nights)
- Total Guests
- Total Revenue, Revenue Lost, Revenue per Booking
- Cancellation Rate, Occupancy Rate
- Repeated Guest %
- Month-wise data

You can:
1. CANCELLATION RISK: Predict if a booking might cancel based on lead time, market segment, guests
   - High Risk: lead time > 150 days, online segment, large groups
   - Medium Risk: lead time 80-150 days
   - Low Risk: lead time < 80 days, corporate/repeated guests

2. REVENUE FORECAST: Based on month and occupancy, suggest revenue expectations
   - Peak months: October to March
   - Off season: April to July

3. GENERAL Q&A: Answer questions about hotel performance, market segments, strategies

Respond in Language you get input in. Keep answers concise and business-focused.Format as bullet points starting with - on separate lines. Max 5 points. No paragraphs. """

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hotel AI Assistant</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #faf8f5; --surface: #ffffff; --surface2: #f5f1eb;
    --border: #e8e0d5; --accent: #8b6914; --accent2: #c4972a;
    --text: #2a2118; --text-dim: #8c7a6b; --user-bg: #2a2118;
  }
  body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
  .header { padding: 16px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 14px; background: var(--user-bg); }
  .header-icon { font-size: 24px; }
  .header-text h1 { font-family: 'Playfair Display', serif; font-size: 18px; color: #fff; }
  .header-text p { font-size: 11px; color: #ffffff88; margin-top: 2px; letter-spacing: .08em; text-transform: uppercase; }
  .header-badge { margin-left: auto; background: #c4972a22; border: 1px solid var(--accent2); color: var(--accent2); font-size: 10px; padding: 4px 10px; border-radius: 20px; letter-spacing: .1em; text-transform: uppercase; }
  .chat-area { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; scrollbar-width: thin; }
  .welcome { text-align: center; padding: 32px 20px; animation: fadeIn .6s ease forwards; }
  @keyframes fadeIn { from{opacity:0} to{opacity:1} }
  .welcome-icon { font-size: 40px; margin-bottom: 16px; }

  .greeting-wrapper { position: relative; height: 52px; margin-bottom: 6px; }
  .greeting-text { font-family: 'Playfair Display', serif; font-size: 24px; color: var(--text); position: absolute; width: 100%; text-align: center; top: 0; left: 0; opacity: 0; transition: opacity 0.8s ease; }
  .greeting-text.visible { opacity: 1; }
  .lang-label { font-size: 13px; color: var(--accent); margin-bottom: 14px; height: 20px; letter-spacing: .08em; transition: opacity .4s ease; }

  .welcome p { font-size: 14px; color: var(--text-dim); line-height: 1.6; max-width: 420px; margin: 0 auto 20px; }
  .feature-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; max-width: 480px; margin: 0 auto 20px; }
  .feature-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: left; cursor: pointer; transition: all .2s; }
  .feature-card:hover { border-color: var(--accent); background: #8b691411; }
  .card-icon { font-size: 20px; margin-bottom: 6px; }
  .card-title { font-size: 12px; font-weight: 500; color: var(--text); margin-bottom: 4px; }
  .card-desc { font-size: 11px; color: var(--text-dim); line-height: 1.4; }
  .suggestions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
  .suggestion { background: var(--surface); border: 1px solid var(--border); color: var(--text-dim); font-size: 12px; padding: 8px 14px; border-radius: 20px; cursor: pointer; transition: all .2s; font-family: 'DM Sans', sans-serif; }
  .suggestion:hover { border-color: var(--accent); color: var(--accent); }

  .message { display: flex; gap: 12px; opacity: 0; animation: slideIn .3s ease forwards; max-width: 85%; }
  @keyframes slideIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  .message.user { margin-left: auto; flex-direction: row-reverse; }
  .message.bot { margin-right: auto; }
  .avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
  .avatar.bot { background: var(--user-bg); border: 1px solid var(--border); }
  .avatar.user { background: var(--surface2); border: 1px solid var(--border); }
  .bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.65; }
  .message.user .bubble { background: var(--user-bg); border-bottom-right-radius: 4px; color: #fff; }
  .message.bot .bubble { background: var(--surface); border: 1px solid var(--border); border-bottom-left-radius: 4px; color: var(--text); }
  .typing .bubble { display: flex; gap: 4px; align-items: center; padding: 14px 18px; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); animation: bounce 1.2s infinite; }
  .dot:nth-child(2){animation-delay:.2s} .dot:nth-child(3){animation-delay:.4s}
  @keyframes bounce { 0%,60%,100%{transform:translateY(0);opacity:.4} 30%{transform:translateY(-6px);opacity:1} }
  .input-area { padding: 16px 24px; border-top: 1px solid var(--border); background: var(--surface); display: flex; gap: 12px; align-items: flex-end; }
  textarea { flex: 1; background: var(--surface2); border: 1px solid var(--border); border-radius: 12px; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; padding: 12px 16px; resize: none; outline: none; min-height: 44px; max-height: 120px; transition: border-color .2s; line-height: 1.5; }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--text-dim); }
  .send-btn { width: 44px; height: 44px; background: var(--user-bg); border: none; border-radius: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; color: white; transition: all .2s; flex-shrink: 0; }
  .send-btn:hover { opacity: .85; transform: scale(1.05); }
  .send-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }
  .footer-note { text-align: center; font-size: 11px; color: var(--text-dim); padding: 8px; background: var(--surface); border-top: 1px solid var(--border); }
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">🏨</div>
  <div class="header-text">
    <h1>Hotel AI Assistant</h1>
    <p>Reservations Intelligence · Powered by Groq AI</p>
  </div>
  <div class="header-badge">● Live</div>
</div>

<div class="chat-area" id="chatArea">
  <div class="welcome" id="welcome">
    <div class="welcome-icon">🏨</div>
    <div class="greeting-wrapper" id="greetingWrapper"></div>
    <div class="lang-label" id="langLabel"></div>
    <p>Ask me anything about hotel bookings, cancellations, revenue, and market performance.</p>
    <div class="feature-cards">
      <div class="feature-card" onclick="sendSuggestion('Lead time 180 days, online booking, 3 guests — will it cancel?')">
        <div class="card-icon">⚠️</div>
        <div class="card-title">Cancellation Risk</div>
        <div class="card-desc">Predict if a booking will cancel</div>
      </div>
      <div class="feature-card" onclick="sendSuggestion('What is the revenue forecast for December?')">
        <div class="card-icon">📈</div>
        <div class="card-title">Revenue Forecast</div>
        <div class="card-desc">Month wise revenue expectations</div>
      </div>
      <div class="feature-card" onclick="sendSuggestion('How to reduce cancellation rate?')">
        <div class="card-icon">💡</div>
        <div class="card-title">Business Strategy</div>
        <div class="card-desc">Tips to improve performance</div>
      </div>
      <div class="feature-card" onclick="sendSuggestion('Which market segment gives highest revenue?')">
        <div class="card-icon">🎯</div>
        <div class="card-title">Market Analysis</div>
        <div class="card-desc">Best performing segments</div>
      </div>
    </div>
    <div class="suggestions">
      <button class="suggestion" onclick="sendSuggestion(this.textContent)">Why do online bookings cancel more?</button>
      <button class="suggestion" onclick="sendSuggestion(this.textContent)">Is 60% occupancy rate good?</button>
      <button class="suggestion" onclick="sendSuggestion(this.textContent)">How to reduce revenue lost?</button>
    </div>
  </div>
</div>

<div class="input-area">
  <textarea id="userInput" placeholder="Ask about hotel analytics..." rows="1" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
  <button class="send-btn" id="sendBtn" onclick="sendMessage()">↑</button>
</div>
<div class="footer-note">Hotel Reservations Dashboard · Power BI + Groq AI · Data Analytics Project</div>

<script>
  const greetings = [
    { text: "Hello! I am Hotel AI",             lang: "🇬🇧 English" },
    { text: "नमस्ते! मैं हूँ Hotel AI",          lang: "🇮🇳 Hindi" },
    { text: "Hallo! Ich bin Hotel AI",           lang: "🇩🇪 German" },
    { text: "Bonjour! Je suis Hotel AI",         lang: "🇫🇷 French" },
    { text: "¡Hola! Soy Hotel AI",               lang: "🇪🇸 Spanish" },
    { text: "こんにちは！Hotel AIです",            lang: "🇯🇵 Japanese" },
    { text: "مرحباً! أنا Hotel AI",              lang: "🇸🇦 Arabic" },
    { text: "Olá! Eu sou Hotel AI",              lang: "🇧🇷 Portuguese" },
    { text: "Привет! Я Hotel AI",                lang: "🇷🇺 Russian" },
    { text: "你好！我是 Hotel AI",                lang: "🇨🇳 Chinese" },
  ];

  const wrapper = document.getElementById('greetingWrapper');
  const langLabel = document.getElementById('langLabel');
  let current = null;
  let idx = 0;

  function showNext() {
    const g = greetings[idx];
    if (current) current.classList.remove('visible');
    const el = document.createElement('div');
    el.className = 'greeting-text';
    el.textContent = g.text;
    wrapper.appendChild(el);
    setTimeout(() => { el.classList.add('visible'); langLabel.textContent = g.lang; }, 100);
    const old = current;
    setTimeout(() => { if (old) old.remove(); }, 900);
    current = el;
    idx = (idx + 1) % greetings.length;
  }

  showNext();
  setInterval(showNext, 3000);

  const chatArea = document.getElementById('chatArea');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');

  function autoResize(el) { el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,120)+'px'; }
  function handleKey(e) { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();} }
  function sendSuggestion(text) { userInput.value=text; sendMessage(); }

  function addMessage(text, role) {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();
    const msg = document.createElement('div');
    msg.className = `message ${role}`;
    const avatar = document.createElement('div');
    avatar.className = `avatar ${role}`;
    avatar.textContent = role==='bot' ? '🏨' : '👤';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
if (role === 'bot') {
  bubble.innerHTML = text.split('\\n').map(l => l.trim()).filter(l => l).join('<br>');
} else {
  bubble.textContent = text;
}
    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function addTyping() {
    const msg = document.createElement('div');
    msg.className = 'message bot typing';
    msg.id = 'typing';
    msg.innerHTML = `<div class="avatar bot">🏨</div><div class="bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function removeTyping() { const t=document.getElementById('typing'); if(t) t.remove(); }

  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    userInput.value=''; userInput.style.height='auto';
    sendBtn.disabled=true; addTyping();
    try {
      const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
      const data = await res.json();
      removeTyping(); addMessage(data.reply, 'bot');
    } catch(e) { removeTyping(); addMessage('Something went wrong. Please try again.', 'bot'); }
    sendBtn.disabled=false; userInput.focus();
  }
</script>
</body>
</html>"""

conversation_history = []

class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))
        user_msg = body.get('message', '')
        conversation_history.append({"role": "user", "content": user_msg})
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            max_tokens=300
        )
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"reply": reply}).encode())

def open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:8766")

if __name__ == "__main__":
    print("="*45)
    print("  Hotel Reservations AI Assistant")
    print("="*45)
    print("  Browser mein khul raha hai...")
    print("  Band karne ke liye Ctrl+C dabaao")
    print("="*45)
    threading.Thread(target=open_browser, daemon=True).start()
    server = HTTPServer(('localhost', 8766), ChatHandler)
    server.serve_forever()
