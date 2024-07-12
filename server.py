from flask import Flask, request, jsonify
import os
import joblib
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__)

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir('data/')
except:
    # data/ folder already exists
    pass

MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

@app.route('/new_chat', methods=['POST'])
def new_chat():
    new_chat_id = str(time.time())
    past_chats[new_chat_id] = f'ChatSession-{new_chat_id}'
    joblib.dump(past_chats, 'data/past_chats_list')
    return jsonify({'chat_id': new_chat_id})

@app.route('/get_chats', methods=['GET'])
def get_chats():
    return jsonify(list(past_chats.keys()))

@app.route('/get_chat_history', methods=['POST'])
def get_chat_history():
    chat_id = request.json['chat_id']
    try:
        messages = joblib.load(f'data/{chat_id}-st_messages')
        gemini_history = joblib.load(f'data/{chat_id}-gemini_messages')
        return jsonify({'messages': messages, 'gemini_history': gemini_history})
    except:
        return jsonify({'messages': [], 'gemini_history': []})

@app.route('/send_message', methods=['POST'])
def send_message():
    chat_id = request.json['chat_id']
    prompt = request.json['prompt']
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=joblib.load(f'data/{chat_id}-gemini_messages'))
    response = chat.send_message(prompt, stream=True)
    full_response = ''
    for chunk in response:
        for ch in chunk.text.split(' '):
            full_response += ch + '
    message = dict(role=MODEL_ROLE, content=full_response, avatar=AI_AVATAR_ICON)
    messages = joblib.load(f'data/{chat_id}-st_messages')
    messages.append(dict(role='user', content=prompt))
    messages.append(message)
    joblib.dump(messages, f'data/{chat_id}-st_messages')
    joblib.dump(chat.history, f'data/{chat_id}-gemini_messages')
    return jsonify({'message': message})

if __name__ == '__main__':
    app.run(debug=True)