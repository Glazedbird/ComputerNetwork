import sys
import socket
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout
from PyQt5.QtGui import QFont
from datetime import datetime
import os  # 导入os模块

class SocketClient(QThread):
    received_signal = pyqtSignal(str)
    connection_status_signal = pyqtSignal(bool)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def run(self):
        print(f"尝试连接到 {self.host}:{self.port}")
        try:
            self.socket.connect((self.host, self.port))
            print("连接成功")
            self.connected = True
            self.connection_status_signal.emit(True)
            while self.connected:
                data = self.socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                print(f"收到服务器消息: {message}")
                self.received_signal.emit(message)
        except Exception as e:
            print(f"连接错误: {e}")
            self.connection_status_signal.emit(False)
        finally:
            self.socket.close()
            self.connected = False

    def send_message(self, message):
        if self.connected:
            print(f"发送消息: {message}")
            self.socket.send(message.encode('utf-8'))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("聊天客户端")
        self.setGeometry(0, 0, 1920, 1080)

        # 创建控件
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.input_message = QLineEdit(self)
        self.send_button = QPushButton("发送", self)
        self.connect_button = QPushButton("连接", self)
        self.status_label = QLabel("未连接", self)
        self.title_label = QLabel("智能机器人", self)

        # 设置字体为楷体
        font = QFont('KaiTi', 12)
        self.chat_display.setFont(font)
        self.input_message.setFont(font)
        self.title_label.setFont(QFont('KaiTi', 16, QFont.Bold))

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.chat_display)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_message)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.status_label)

        # 创建布局容器并设置背景图片
        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet(
            "background-image: url('background.jpg'); "
            "background-repeat: no-repeat; "
            "background-position: center; "
            "background-size: cover;"
        )

        # 将容器设置为中央部件
        self.setCentralWidget(container)

        # 初始化socket线程
        self.socket_thread = SocketClient('127.0.0.1', 12345)
        self.socket_thread.received_signal.connect(lambda msg: self.append_message('机器人', msg))
        self.socket_thread.connection_status_signal.connect(self.update_connection_status)

        # 连接信号和槽
        self.connect_button.clicked.connect(self.connect_to_server)
        self.send_button.clicked.connect(self.send_message)
        self.input_message.returnPressed.connect(self.send_message)

    def connect_to_server(self):
        if not self.socket_thread.isRunning():
            print("启动线程")
            self.socket_thread.start()
        else:
            print("停止线程")
            self.socket_thread.quit()
            self.socket_thread.wait()

    def send_message(self):
        if self.socket_thread.connected:
            message = self.input_message.text()
            if message:
                self.socket_thread.send_message(message)
                self.append_message('用户', message)
                self.input_message.clear()
            else:
                QMessageBox.warning(self, "警告", "消息不能为空！")
        else:
            QMessageBox.warning(self, "警告", "未连接到服务器！")

    def append_message(self, sender, message):
        print(f"显示消息: {sender}: {message}")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if sender == '用户':
            msg_html = f"""
                <div style='float:right; background-color: transparent; padding:10px; margin:5px; border-radius:10px;'>
                    <p style='font-family: KaiTi; font-size:16px;'>{message}</p>
                    <p style='font-size:10px; color:gray;'>{now}</p>
                </div>
            """
        elif sender == '机器人':
            msg_html = f"""
                <div style='float:left; background-color: #90ee90; padding:10px; margin:5px; border-radius:10px;'>
                    <p style='font-family: KaiTi; font-size:16px;'>{message}</p>
                    <p style='font-size:10px; color:gray;'>{now}</p>
                </div>
            """
        else:
            msg_html = f"<p>{message}</p>"
        self.chat_display.append(msg_html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def update_connection_status(self, status):
        print(f"连接状态: {status}")
        if status:
            self.status_label.setText("已连接")
            self.connect_button.setText("断开")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.disconnect_from_server)
        else:
            self.status_label.setText("未连接")
            self.connect_button.setText("连接")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.connect_to_server)

    def disconnect_from_server(self):
        if self.socket_thread.connected:
            print("断开连接")
            self.socket_thread.connected = False
            self.socket_thread.quit()
            self.socket_thread.wait()
            self.status_label.setText("未连接")
            self.connect_button.setText("连接")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.connect_to_server)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())