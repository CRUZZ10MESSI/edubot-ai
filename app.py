from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import wikipedia
import html

# -------------------- APP SETUP --------------------
app = Flask(__name__)
app.secret_key = "edubot_secret"

# -------------------- GROQ API KEY --------------------
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")
client = Groq(api_key=GROQ_API_KEY)

# Wikipedia setup
wikipedia.set_lang("en")
wikipedia.set_user_agent("EduBot/1.0 (CBSE AI Project)")

# -------------------- MODERN CHAT UI --------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>EduBot AI</title>
<style>
:root {
    --bg: #0b1020;
    --panel: #111827;
    --bot: #1f2937;
    --user: #2563eb;
    --text: #e5e7eb;
}
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Segoe UI", sans-serif;
    background: var(--bg);
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

.chat {
    width: 420px;
    height: 620px;
    background: var(--panel);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 30px 80px rgba(0,0,0,0.6);
    overflow: hidden;
}

.header {
    padding: 16px;
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white;
    font-weight: 600;
    text-align: center;
}

.messages {
    flex: 1;
    padding: 14px;
    overflow-y: auto;
}

.msg {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    animation: fadeIn 0.25s ease;
    line-height: 1.4;
}

.bot {
    background: var(--bot);
    color: var(--text);
    align-self: flex-start;
}

.user {
    background: var(--user);
    color: white;
    align-self: flex-end;
}

.typing {
    font-style: italic;
    opacity: 0.8;
}

.input-area {
    display: flex;
    padding: 12px;
    border-top: 1px solid #1f2937;
}

input {
    flex: 1;
    padding: 10px;
    border-radius: 10px;
    border: none;
    outline: none;
    font-size: 14px;
}

button {
    margin-left: 8px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0 16px;
    cursor: pointer;
}

button:hover {
    background: #1d4ed8;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
</head>

<body>
<div class="chat">
    <div class="header">🤖 EduBot – AI Study Assistant</div>
    <div class="messages" id="messages">
        <div class="msg bot">
            Hi! I can help you with Physics, Chemistry, and Computer Science 📘
        </div>
    </div>

    <div class="input-area">
        <input id="input" placeholder="Ask your question..." />
        <button onclick="send()">Send</button>
    </div>
</div>

<script>
const input = document.getElementById("input");
const messages = document.getElementById("messages");

input.addEventListener("keydown", e => {
    if (e.key === "Enter") send();
});

function addMsg(text, cls) {
    const div = document.createElement("div");
    div.className = "msg " + cls;
    div.innerText = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

async function send() {
    if (!input.value.trim()) return;

    addMsg(input.value, "user");
    const typing = addMsg("EduBot is thinking…", "bot typing");

    const question = input.value;
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question })
        });

        const data = await res.json();
        typing.innerText = data.response;
    } catch {
        typing.innerText = "Sorry, something went wrong.";
    }
}
</script>
</body>
</html>
"""

# -------------------- AI LOGIC --------------------
def groq_answer(question):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EduBot, a friendly AI chatbot and study assistant.\n"
                        "You can have normal English conversations like a real chatbot.\n"
                        "If the user asks casual questions (hi, how are you, jokes, etc.), respond naturally.\n"
                        "If the user asks academic questions (Physics, Chemistry, Computer Science), "
                        "explain clearly at Class 12 CBSE level with examples.\n"
                        "Always be polite, engaging, and easy to understand."
                    )
                },
                {"role": "user", "content": question}
            ],
            temperature=0.6,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def wiki_fallback(topic):
    try:
        return wikipedia.summary(topic, sentences=2)
    except:
        return "I couldn’t find information on that topic. Try something more specific."

# -------------------- ROUTES --------------------
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"response": "Invalid input."})

    question = html.escape(data["message"])
    reply = groq_answer(question)

    if not reply:
        reply = wiki_fallback(question)

    return jsonify({"response": reply})

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=False)
