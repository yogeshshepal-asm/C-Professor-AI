from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq
print("✅ GROQ_API_KEY loaded:", os.getenv("GROQ_API_KEY"))

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    user_question = request.json.get('question')

    response = client.chat.completions.create(
       model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a kind and intelligent professor teaching C programming to complete beginners. Use extremely simple words and always show working C code examples that can be used in VS Code."},
            {"role": "user", "content": user_question}
        ],
        temperature=0.5
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
