from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI
import logging
import json
import os
import datetime
import re
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client_messages = {}
client_files = {}  # 用于存储每个客户端的文件对象

if not os.path.exists('data'):
    os.makedirs('data')

client = OpenAI(api_key="sk-a46de6af7d2040369632dccff859f93d", base_url="https://api.deepseek.com/")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app, resources={r'*': {'origins': 'http://localhost:8000'}})
socketio = SocketIO(app, cors_allowed_origins='http://localhost:8000')

def run(messages):
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=messages,
            timeout=200,
            max_tokens=2048
        )
        result = response.choices[0].message.content
        elapsed_time = time.time() - start_time
        return {"result": result, "time": elapsed_time}
    except Exception as e:
        logger.error(f"对话失败: {e}")
        return {"result": "对话失败，请稍后再试。", "time": None}

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    logger.info(f'Client connected: {sid}')
    # 为每个客户端创建一个文件，用于存储聊天记录
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    data_filename = os.path.join('data', f"{sid}_{timestamp}.jsonl")
    client_files[sid] = open(data_filename, 'a', encoding='utf-8')
    client_messages[sid] = [
        {"role": "system", "content": "你是智能聊天机器人"},
    ]

@socketio.on('message')
def handle_message(msg):
    sid = request.sid
    if sid not in client_messages:
        client_messages[sid] = [
            {"role": "system", "content": "你是智能聊天机器人"},
        ]
    client_messages[sid].append({"role": "user", "content": msg})
    response_data = run(client_messages[sid])
    response = response_data["result"]
    elapsed_time = response_data["time"]
    client_messages[sid].append({"role": "assistant", "content": response})
    response = re.sub(r'（[^）]*）', '', response).strip()
    if elapsed_time is not None:
        response_with_time = f"{response} （耗时{elapsed_time:.2f}秒）"
    else:
        response_with_time = f"{response} （请求失败）"
    emit('response', {'content': response_with_time, 'time': elapsed_time})
    # 将聊天记录写入文件
    if sid in client_files:
        json_line = json.dumps({"question": msg, "response": response, "time": elapsed_time}, ensure_ascii=False)
        client_files[sid].write(json_line + '\n')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    logger.info(f'Client disconnected: {sid}')
    if sid in client_messages:
        del client_messages[sid]
    if sid in client_files:
        client_files[sid].close()
        del client_files[sid]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)