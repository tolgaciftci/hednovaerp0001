import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QFrame, QSizePolicy, QTextEdit
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt

import integrator  # kendi entegrasyon fonksiyonlarımız

BASE_DIR = os.path.dirname(__file__)


class LoginScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Logo
        logo = QLabel()
        pixmap = QPixmap(os.path.join(BASE_DIR, "logo.png")).scaled(
            140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ) 
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Başlık
        title = QLabel("Integrator To Hednova")
        title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Açıklama
        desc = QLabel("Bu uygulama ile diğer yazılımlardan Hednova içerisine veri transferi yapılabilir.")
        desc.setFont(QFont("Segoe UI", 11))
        desc.setStyleSheet("color: #555;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Kart görünümü
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(15)

        form_title = QLabel("Kullanıcı Girişi")
        form_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        form_title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(form_title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanıcı Adı")
        form_layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Şifre")
        self.password.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password)

        self.error = QLabel("")
        self.error.setStyleSheet("color: red; font-size: 12px;")
        self.error.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self.error)

        login_btn = QPushButton("Giriş Yap")
        login_btn.setObjectName("loginBtn")
        login_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        login_btn.clicked.connect(self.do_login)
        form_layout.addWidget(login_btn)

        layout.addWidget(form_card)
        self.setLayout(layout)

    def do_login(self):
        data_path = os.path.join(BASE_DIR, "data.json")
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.error.setText("⚠️ data.json bulunamadı!")
            return

        if self.username.text() == data["user"] and self.password.text() == data["password"]:
            self.parent.setCurrentIndex(1)
        else:
            self.error.setText("Kullanıcı adı veya şifre hatalı!")


class IntegrationScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Üst başlık
        title = QLabel("Integrator To Hednova")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Entegrasyon butonu
        self.start_btn = QPushButton("Entegrasyon Başlat")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.toggle_integration)
        layout.addWidget(self.start_btn, alignment=Qt.AlignHCenter)

        # Log alanı
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setObjectName("logArea")
        layout.addWidget(self.log_area)

        self.setLayout(layout)
        self.running = False

    def add_log(self, message):
        self.log_area.append(message)

    def toggle_integration(self):
        if not self.running:
            self.start_btn.setText("Entegrasyon Durdur")
            integrator.StartIntegration(self)
            self.running = True
        else:
            self.start_btn.setText("Entegrasyon Başlat")
            integrator.StopIntegration()
            self.running = False


class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1000, 700)  # sabit boyut

        self.login_screen = LoginScreen(self)
        self.integration_screen = IntegrationScreen()

        self.addWidget(self.login_screen)
        self.addWidget(self.integration_screen)


def main():
    app = QApplication(sys.argv)

    # Modern QSS Stil
    style = """
    QWidget {
        background-color: #ffffff;
        font-family: 'Segoe UI';
    }
    #card {
        background-color: #fefefe;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #ddd;
    }
    QLineEdit {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 2px solid #2d6cdf;
    }
    QPushButton#loginBtn {
        background-color: #2d6cdf;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton#loginBtn:hover {
        background-color: #1a4fb3;
    }
    QPushButton#startBtn {
        background-color: #28a745;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
        min-width: 200px;
    }
    QPushButton#startBtn:hover {
        background-color: #1e7e34;
    }
    #logArea {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 10px;
        font-family: Consolas, monospace;
        font-size: 13px;
        background-color: #f9f9f9;
    }
    """
    app.setStyleSheet(style)

    window = MainApp()
    window.setWindowTitle("Integrator To Hednova")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
