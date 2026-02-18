print("🟢 Starting app.py...")

import os
import sys
import io
import signal
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
from flask import Flask, request, jsonify, render_template, session, send_file
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
app.secret_key = os.urandom(24)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ping")
def ping():
    return "pong"

# Existing chatbot endpoint
@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        user_question = request.json.get("question")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a kind and intelligent professor teaching Python programming to complete beginners. Use extremely simple words and always show working Python code examples that can be run in PyCharm."
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            temperature=0.5
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Error in /api/ask:", e)
        return jsonify({"error": str(e)}), 400

# Practice questions endpoint
@app.route("/api/generate-questions", methods=["POST"])
def generate_questions():
    try:
        topic = request.json.get("topic")
        
        prompt = f"""Generate exactly 5 beginner-level Python practice questions on {topic}.

Format your response EXACTLY like this:

Q1: [Question text here]
A1: [Answer with code example]

Q2: [Question text here]
A2: [Answer with code example]

Q3: [Question text here]
A3: [Answer with code example]

Q4: [Question text here]
A4: [Answer with code example]

Q5: [Question text here]
A5: [Answer with code example]

Make questions practical and include code examples in answers."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Python programming instructor creating practice questions for beginners. Always follow the exact format requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        questions_text = response.choices[0].message.content.strip()
        session['last_questions'] = questions_text
        session['last_topic'] = topic
        
        return jsonify({"questions": questions_text, "topic": topic})

    except Exception as e:
        print("❌ Error in /api/generate-questions:", e)
        return jsonify({"error": str(e)}), 400

# Secure code execution endpoint
@app.route("/api/execute-code", methods=["POST"])
def execute_code():
    try:
        code = request.json.get("code", "").strip()
        
        if not code:
            return jsonify({"error": "No code provided"}), 400
        
        # Security checks - block dangerous operations
        dangerous_keywords = [
            'import os', 'import sys', 'import subprocess', 'import socket',
            '__import__', 'eval', 'exec', 'compile', 'open(', 'file(',
            'input(', 'raw_input'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in code.lower():
                return jsonify({
                    "error": f"Security: '{keyword}' is not allowed for safety reasons"
                }), 400
        
        # Execute code in restricted environment
        output, error = execute_safely(code)
        
        return jsonify({
            "output": output,
            "error": error
        })
        
    except Exception as e:
        print("❌ Error in /api/execute-code:", e)
        return jsonify({"error": str(e)}), 400

def execute_safely(code):
    """
    Execute Python code in a restricted environment with timeout
    """
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Restricted built-ins (remove dangerous functions)
    safe_builtins = {
        'print': print,
        'range': range,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'abs': abs,
        'max': max,
        'min': min,
        'sum': sum,
        'sorted': sorted,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'type': type,
        'isinstance': isinstance,
        'True': True,
        'False': False,
        'None': None,
    }
    
    # Create restricted globals
    restricted_globals = {
        "__builtins__": safe_builtins,
        "__name__": "__main__",
        "__doc__": None,
    }
    
    try:
        # Set timeout using signal (Unix/Linux) or threading (Windows)
        if sys.platform != 'win32':
            # Unix/Linux timeout
            def timeout_handler(signum, frame):
                raise TimeoutError("Code execution timeout (3 seconds)")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)
        
        # Execute code with output capture
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, restricted_globals)
        
        if sys.platform != 'win32':
            signal.alarm(0)  # Cancel alarm
        
        output = stdout_capture.getvalue()
        error = stderr_capture.getvalue()
        
        return output if output else "Code executed successfully (no output)", error
        
    except TimeoutError as e:
        return "", f"⏱️ Timeout Error: {str(e)}"
    except Exception as e:
        return "", f"❌ Error: {type(e).__name__}: {str(e)}"
    finally:
        if sys.platform != 'win32':
            signal.alarm(0)

# Download notes endpoint
@app.route("/api/download-notes", methods=["POST"])
def download_notes():
    try:
        content = request.json.get("content", "")
        topic = request.json.get("topic", "python_notes")
        
        if not content:
            return jsonify({"error": "No content to download"}), 400
        
        # Format content for notes
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{topic.lower().replace(' ', '_')}_notes_{date_str}.txt"
        
        # Create formatted notes
        notes = f"""{'='*60}
AI PYTHON TUTOR - STUDY NOTES
{'='*60}

Topic: {topic}
Date: {date_str}
Source: ASM NEXTGEN Technical Campus

{'='*60}
CONTENT:
{'='*60}

{content}

{'='*60}
END OF NOTES
{'='*60}

Developed by Dr. Yogesh Shepal
ASM NEXTGEN Technical Campus
https://www.asmnext.edu.in/
"""
        
        # Create in-memory file
        notes_file = io.BytesIO()
        notes_file.write(notes.encode('utf-8'))
        notes_file.seek(0)
        
        return send_file(
            notes_file,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print("❌ Error in /api/download-notes:", e)
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    print("🚀 Running Flask app")
    app.run(debug=True)
