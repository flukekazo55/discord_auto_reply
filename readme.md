# 🤖 Discord Auto-Reply Bot with OpenRouter AI (Thai Style)

A Discord chatbot that automatically replies when mentioned or replied to in a thread. It uses the [OpenRouter](https://openrouter.ai/) API to generate fun and smart replies in Thai. The bot also responds via DM when your friend replies to your message in a public channel.

---

## 🚀 Features

- 🤖 Auto-reply when someone mentions you or replies to your message
- 💬 AI responses via OpenRouter (uses `deepseek/deepseek-r1:free`)
- 📩 Auto DM: Sends "ฟลุ๊คไม่อยู่ แต่เดี๋ยวกลับมาตอบ" when someone replies to your public message
- 🔄 Keep-alive server to keep Replit project running
- 🟢 UptimeRobot support (optional)

---

## 🧠 AI Personality (Prompt Style)
- Funny, friendly, and smart Thai male personality
- Speaks casually with Thai teen tone
- Answers questions on science, tech, culture, lifestyle, and more
- Avoids inappropriate questions politely

---

## 🛠️ Requirements

- Python 3.8+
- A Discord Bot Token
- OpenRouter API key
- Replit account (optional for free deployment)

---

## 🔐 Environment Variables (Secrets)

You must define the following secrets (in Replit → Secrets panel or `.env` file locally):


---

## 💻 How to Run

### On Replit (Recommended):
1. Fork or import this repo to your Replit
2. Set environment variables (Secrets)
3. Run `main.py`
4. (Optional) Use [UptimeRobot](https://uptimerobot.com/) to ping your bot's keep-alive URL

### Locally:
```bash
pip install -r requirements.txt
python main.py
