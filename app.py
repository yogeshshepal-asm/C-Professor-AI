print("🟢 Starting app.py...")

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    from groq import Groq
except ImportError as e:
    print("❌ ImportError:", e)
    raise

# Load .env and environment variables
try:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    print("🔑 GROQ_API_KEY from os.environ:", api_key is not None)
    if not api_key:
        raise ValueError("GROQ_API_KEY not found or is empty")
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized")
except Exception as e:
    print("❌ Error initializing Groq client:", e)
    raise

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ping")
def ping():
    return "pong"

@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        user_question = request.json.get("question")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a kind and intelligent professor teaching C programming to complete beginners. Use extremely simple words and always show working C code examples that can be used in VS Code."},
                {"role": "user", "content": user_question}
            ],
            temperature=0.5
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        print("❌ Error in /api/ask:", e)
        return jsonify({"reply": "Internal server error"}), 500

if __name__ == "__main__":
    print("🚀 Running Flask app")
    app.run(debug=True)
