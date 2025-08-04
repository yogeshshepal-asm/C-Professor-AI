from flask import Flask
app = Flask(__name__)

@app.route('/')
def home(): return "Hello Render!"
@app.route('/ping')
def ping(): return "pong"
