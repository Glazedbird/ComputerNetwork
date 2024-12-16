import socket

def main():
    host = '127.0.0.1'
    port = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    while True:
        message = input("你: ")
        if message.lower() == 'exit':
            break
        client_socket.send(message.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        print(f"机器人: {response}")
    client_socket.close()

if __name__ == "__main__":
    main()