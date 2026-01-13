from flask import Flask, request, jsonify
import os
from groq import Groq

# ---------------- CONFIG ----------------
app = Flask(__name__)

# Load API Key from environment
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

TASK:
First identify the subject and question type.

QUESTION TYPES:
1. Theory
2. Numerical
3. Programming (Python)

RULES:

FOR NUMERICAL QUESTIONS:
- Solve step-by-step
- Use this format:
  Given:
  Formula:
  Substitution:
  Calculation:
  Final Answer (with unit)

FOR PYTHON PROGRAMMING QUESTIONS:
- Generate correct Python code
- Use triple backticks with python
- Follow CBSE syllabus (Class 11–12)
- Add brief explanation after code

FOR THEORY QUESTIONS:
- Explain clearly
- Exam-oriented language
- Simple English

IMPORTANT:
- NEVER refuse numericals or Python programs
- NEVER redirect to Wikipedia
- Answer ONLY subject-related questions
"""

        response = client.chat.completions.create(
            model="llama3-8b-8192",
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
    font-family: Segoe UI, sans-serif;
    background: #0f172a;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

.chat {
    width: 420px;
    height: 640px;
    background: #020617;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.header {
    padding: 16px;
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white;
    text-align: center;
    font-weight: 600;
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
    white-space: pre-wrap;
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
    padding: 12px;
    border-top: 1px solid #1e293b;
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
}
</style>
</head>

<body>
<div class="chat">
    <div class="header">🤖 EduBot – AI Learning Assistant</div>
    <div class="messages" id="messages">
        <div class="msg bot">
            Hello! I can solve numericals and write Python programs 📘💻
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
        div.appendChild(code);
    } else {
        div.innerText = text;
    }

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function send() {
    if (!input.value.trim()) return;

    addUserMsg(input.value);
    const temp = document.createElement("div");
    temp.className = "msg bot";
    temp.innerText = "EduBot is thinking...";
    messages.appendChild(temp);

    const question = input.value;
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: question})
        });

        const data = await res.json();
        temp.remove();
        addBotMsg(data.response);
    } catch {
        temp.innerText = "Error connecting to server.";
    }
}
</script>
</body>
</html>
"""

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
