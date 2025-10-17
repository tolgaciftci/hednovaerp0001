import json
from PyQt5 import QtCore, QtGui, QtWidgets
from integration_window import IntegrationWindow

class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hednova ERP Veri Alma Entegrasyonu Uygulaması")
        self.setFixedSize(560, 460)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #f2f4f8;")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(18)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # Logo
        logo_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("logo.png")
        pixmap = pixmap.scaled(200, 100, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignCenter)

        # Başlık
        title_label = QtWidgets.QLabel("Hednova ERP Veri Alma Entegrasyonu Uygulaması")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
        """)

        # Kullanıcı adı
        user_label = QtWidgets.QLabel("Kullanıcı Adı:")
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("Kullanıcı adınızı giriniz")
        self.user_input.setStyleSheet("""
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            background-color: #ffffff;
        """)

        # Şifre
        pass_label = QtWidgets.QLabel("Şifre:")
        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setPlaceholderText("Şifrenizi giriniz")
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_input.setStyleSheet("""
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            background-color: #ffffff;
        """)

        # Giriş butonu
        login_button = QtWidgets.QPushButton("Giriş Yap")
        login_button.setCursor(QtCore.Qt.PointingHandCursor)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: 600;
                padding: 12px;
                border-radius: 6px;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1e40af;
            }
        """)
        login_button.clicked.connect(self.check_login)

        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addSpacing(15)
        layout.addWidget(user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(pass_label)
        layout.addWidget(self.pass_input)
        layout.addSpacing(12)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def check_login(self):
        """data.json dosyasını okuyarak kullanıcı kontrolü yapar"""
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, "Hata", "data.json dosyası bulunamadı!")
            return

        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if username == data["user"] and password == data["password"]:
            self.open_integration_window()
        else:
            QtWidgets.QMessageBox.warning(self, "Hatalı Giriş", "Kullanıcı adı veya şifre hatalı!")

    def open_integration_window(self):
        """Entegrasyon sayfasını açar"""
        self.integration_window = IntegrationWindow()
        self.integration_window.show()
        self.close()
