from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print("✅ GROQ_API_KEY loaded:", bool(api_key))

client = Groq(api_key=api_key)

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
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a C professor helping beginners learn with simple C examples."},
                {"role": "user", "content": user_question}
            ],
            temperature=0.5
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

