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
    --code: #020617;
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
    width: 430px;
    height: 650px;
    background: var(--panel);
    border-radius: 18px;
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
    max-width: 90%;
    padding: 10px 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    animation: fadeIn 0.25s ease;
    line-height: 1.45;
    white-space: pre-wrap;
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

.code-block {
    background: var(--code);
    color: #c7d2fe;
    font-family: Consolas, monospace;
    font-size: 13px;
    border-radius: 10px;
    padding: 12px;
    margin-top: 8px;
    position: relative;
    overflow-x: auto;
}

.copy-btn {
    position: absolute;
    top: 6px;
    right: 8px;
    font-size: 11px;
    padding: 4px 8px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    background: #2563eb;
    color: white;
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
}

button.send {
    margin-left: 8px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0 16px;
    cursor: pointer;
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
            Hi! I can solve numericals and write Python programs for you 📘💻
        </div>
    </div>

    <div class="input-area">
        <input id="input" placeholder="Ask a question..." />
        <button class="send" onclick="send()">Send</button>
    </div>
</div>

<script>
const input = document.getElementById("input");
const messages = document.getElementById("messages");

input.addEventListener("keydown", e => {
    if (e.key === "Enter") send();
});

function addUserMsg(text) {
    const div = document.createElement("div");
    div.className = "msg user";
    div.innerText = text;
    messages.appendChild(div);
}

function addBotMsg(text) {
    const container = document.createElement("div");
    container.className = "msg bot";

    // Detect code blocks
    if (text.includes("```")) {
        const parts = text.split("```");
        container.innerText = parts[0];

        const code = document.createElement("div");
        code.className = "code-block";
        code.innerText = parts[1].replace("python", "").trim();

        const btn = document.createElement("button");
        btn.className = "copy-btn";
        btn.innerText = "Copy";
        btn.onclick = () => {
            navigator.clipboard.writeText(code.innerText);
            btn.innerText = "Copied!";
            setTimeout(() => btn.innerText = "Copy", 1500);
        };

        code.appendChild(btn);
        container.appendChild(code);
    } else {
        container.innerText = text;
    }

    messages.appendChild(container);
    messages.scrollTop = messages.scrollHeight;
    return container;
}

async function send() {
    if (!input.value.trim()) return;

    addUserMsg(input.value);
    const typing = addBotMsg("EduBot is thinking…");

    const question = input.value;
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question })
        });

        const data = await res.json();
        typing.remove();
        addBotMsg(data.response);
    } catch {
        typing.innerText = "Something went wrong.";
    }
}
</script>
</body>
</html>
"""


# -------------------- AI LOGIC --------------------
def groq_answer(question):
    try:
        system_prompt = """
You are EduBot, an advanced AI tutor for Class 12 CBSE students.

First, identify:
1. SUBJECT: Physics / Chemistry / Computer Science
2. QUESTION TYPE:
   - Conceptual / Theory
   - Numerical / Problem-solving
   - Programming (Python)

Then respond using the correct format:

FOR PHYSICS & CHEMISTRY NUMERICALS:
- Write: Given:
- Write: Formula used:
- Show substitution
- Step-by-step calculation
- Final Answer (with unit)
- Use CBSE exam style

FOR CONCEPTUAL QUESTIONS:
- Explain clearly
- Use examples
- Use diagrams-in-words if needed

FOR COMPUTER SCIENCE (PYTHON PROGRAMS):
- Write clean, correct Python code
- Follow Class 11–12 CBSE syllabus
- Add comments in code
- After code, explain briefly

ONLY answer questions related to:
- Physics
- Chemistry
- Computer Science

If outside syllabus, politely refuse.

Always be accurate, exam-oriented, and student-friendly.
"""

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.35,
            max_tokens=900
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
