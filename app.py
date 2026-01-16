from flask import Flask, request, jsonify
import os
from groq import Groq

# ---------------- APP SETUP ----------------
app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("Please set GROQ_API_KEY as an environment variable")

client = Groq(api_key=GROQ_API_KEY)

# ---------------- AI FUNCTION ----------------
def groq_answer(question):
    try:
        system_prompt = """
You are EduBot, an AI tutor for CBSE Class 11 and 12 students.

SUBJECTS:
- Physics
- Chemistry
- Computer Science

QUESTION TYPES:
- Theory
- Numerical
- Programming (Python)

FOR NUMERICAL QUESTIONS:
- Solve step-by-step
- Use format:
  Given:
  Formula:
  Substitution:
  Calculation:
  Final Answer (with unit)

FOR PYTHON PROGRAMMING QUESTIONS:
- Generate valid Python code
- Wrap code in triple backticks with python
- Follow CBSE syllabus
- Add brief explanation

FOR THEORY QUESTIONS:
- Clear and exam-oriented explanation

IMPORTANT:
- Always answer subject-related questions
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=1000
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error occurred: {e}"

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return HTML_PAGE

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("message", "")
    answer = groq_answer(question)
    return jsonify({"response": answer})

# ---------------- FRONTEND ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>EduBot AI</title>

<style>
body {
    margin: 0;
    font-family: "Segoe UI", sans-serif;
    background: #0f172a;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

.chat {
    width: 100%;
    max-width: 820px;
    height: 85vh;
    background: #020617;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 25px 70px rgba(0,0,0,0.6);
}

.header {
    padding: 16px;
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white;
    text-align: center;
    font-weight: 600;
    animation: glow 3s infinite alternate;
}

@keyframes glow {
    from { box-shadow: 0 0 6px #2563eb; }
    to { box-shadow: 0 0 14px #4f46e5; }
}

.messages {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    scroll-behavior: smooth;
}

.msg {
    max-width: 90%;
    padding: 10px 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    white-space: pre-wrap;
    animation: slideFade 0.3s ease-out;
}

@keyframes slideFade {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.user {
    background: #2563eb;
    color: white;
    align-self: flex-end;
}

.bot {
    background: #1e293b;
    color: #e5e7eb;
    align-self: flex-start;
}

.code-block {
    background: #020617;
    color: #c7d2fe;
    font-family: Consolas, monospace;
    font-size: 13px;
    border-radius: 10px;
    padding: 12px;
    margin-top: 8px;
    position: relative;
    overflow-x: auto;
}

.code-block pre {
    margin: 0;
    white-space: pre;
}

.copy-btn {
    position: absolute;
    top: 6px;
    right: 8px;
    font-size: 11px;
    padding: 4px 8px;
    border: none;
    border-radius: 6px;
    background: #2563eb;
    color: white;
    cursor: pointer;
}

.input-area {
    display: flex;
    padding: 14px;
    border-top: 1px solid #1e293b;
    background: #020617;
}

input {
    flex: 1;
    padding: 10px;
    border-radius: 10px;
    border: none;
    outline: none;
}

button {
    margin-left: 8px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0 16px;
    cursor: pointer;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

button:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 10px rgba(0,0,0,0.3);
}

button:active {
    transform: scale(0.97);
}

.typing span {
    animation: blink 1.4s infinite both;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
    0% { opacity: .2; }
    20% { opacity: 1; }
    100% { opacity: .2; }
}
</style>
</head>

<body>
<div class="chat">
    <div class="header">🤖 EduBot – AI Learning Assistant</div>

    <div class="messages" id="messages">
        <div class="msg bot">
            Hello! I can answer theory questions, solve numericals, and write Python programs 📘💻
        </div>
    </div>

    <div class="input-area">
        <input id="input" placeholder="Ask a question..." />
        <button onclick="send()">Send</button>
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
    const div = document.createElement("div");
    div.className = "msg bot";

    if (text.includes("```")) {
        const parts = text.split("```");
        div.innerText = parts[0];

        const codeText = parts[1].replace("python", "").trim();

        const code = document.createElement("div");
        code.className = "code-block";

        const pre = document.createElement("pre");
        pre.innerText = codeText;

        const btn = document.createElement("button");
        btn.className = "copy-btn";
        btn.innerText = "Copy";
        btn.onclick = () => {
            navigator.clipboard.writeText(codeText);
            btn.innerText = "Copied!";
            setTimeout(() => btn.innerText = "Copy", 1500);
        };

        code.appendChild(btn);
        code.appendChild(pre);
        div.appendChild(code);
    } else {
        div.innerText = text;
    }

    messages.appendChild(div);
    messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
}

async function send() {
    if (!input.value.trim()) return;

    addUserMsg(input.value);

    const typing = document.createElement("div");
    typing.className = "msg bot";
    typing.innerHTML = 'EduBot is typing <span class="typing"><span>.</span><span>.</span><span>.</span></span>';
    messages.appendChild(typing);

    const question = input.value;
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: question})
        });

        const data = await res.json();
        typing.remove();
        addBotMsg(data.response);
    } catch {
        typing.innerText = "Error connecting to server.";
    }
}
</script>
</body>
</html>
"""

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
