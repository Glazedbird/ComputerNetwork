import socket
import threading
import json
import time
import os
import datetime
from openai import OpenAI
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import re

#创建锁
lock = threading.Lock()
log_folder_lock = threading.Lock()

client = OpenAI(api_key="sk-a46de6af7d2040369632dccff859f93d", base_url="https://api.deepseek.com/")

def run(messages):
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=messages,
            timeout=200,  #超时时间
            max_tokens=2048
        )
        logger.debug(f"API响应: {response}")  # 调试日志
        result = response.choices[0].message.content
        elapsed_time = time.time() - start_time
        logger.info(f"对话成功, 耗时: {elapsed_time:.2f}秒")
        return {"result": result, "time": elapsed_time}
    except Exception as e:
        logger.error(f"对话失败: {e}")
        return {"result": "对话失败，请稍后再试。", "time": None}

def handle_client(client_socket, client_address, executor):
    logger.info(f"新连接: {client_address}")
    #生成唯一的文件名
    client_ip, client_port = client_address
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    filename = os.path.join('conversation_logs', f"{client_ip}_{client_port}_{timestamp}.jsonl")
    #初始化messages列表，包含系统提示
    messages = [
        {"role": "system", "content": "你是智能聊天机器人"},
    ]
    #打开文件，准备写入对话记录
    with open(filename, 'a', encoding='utf-8') as f:
        while True:
            try:
                #接收客户端发送的消息
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                #添加用户输入到messages列表
                messages.append({"role": "user", "content": data.strip()})
                #提交run函数的任务，并设置超时时间
                future = executor.submit(run, messages)
                try:
                    response_data = future.result(timeout=200)  #任务超时时间
                    response = response_data["result"]
                    elapsed_time = response_data["time"]
                    #使用正则表达式去除括号内的内容
                    response = re.sub(r'（[^）]*）', '', response).strip()
                    #添加回答到messages列表中，不包含时间信息
                    messages.append({"role": "assistant", "content": response})
                    #在发送回复时，添加时间信息
                    if elapsed_time is not None:
                        response_with_time = f"{response} （耗时{elapsed_time:.2f}秒）"
                    else:
                        response_with_time = f"{response} （请求失败）"
                    #发送回复
                    client_socket.send(response_with_time.encode('utf-8'))
                    #将question和response写入文件
                    json_line = json.dumps({"question": data.strip(), "response": response, "time": elapsed_time}, ensure_ascii=False)
                    f.write(json_line + '\n')
                except TimeoutError:
                    logger.warning(f"处理连接{client_address}时任务超时")
                    client_socket.send("请求超时，请稍后再试。".encode('utf-8'))
            except Exception as e:
                logger.error(f"处理连接{client_address}时发生错误: {e}")
                break
    client_socket.close()
    logger.info(f"连接关闭: {client_address}")

def main():
    host = '0.0.0.0'
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logger.info(f"服务器启动，监听{host}:{port}")
    #创建线程池
    executor = ThreadPoolExecutor(max_workers=10)
    #检查并创建conversation_logs文件夹
    with log_folder_lock:
        if not os.path.exists('conversation_logs'):
            os.makedirs('conversation_logs')
    while True:
        client_socket, client_address = server_socket.accept()
        #为新连接创建一个线程，并传入executor
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, executor))
        client_handler.start()

if __name__ == "__main__":
    main()