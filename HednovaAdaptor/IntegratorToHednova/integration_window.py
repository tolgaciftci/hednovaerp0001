# integration_window.py
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
from datetime import datetime

from sql_crud import *
from api_requests import *

# ---------------------------
# Üst Kart: Session ID Alımı
# ---------------------------
class SessionCard(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame#card {
                background: #ffffff;
                border: 1px solid #d7dde5;
                border-radius: 10px;
            }
            QPushButton.primary {
                background-color: #2563eb; color: #fff; font-weight: 600;
                padding: 10px 14px; border-radius: 8px; border: none;
            }
            QPushButton.primary:hover { background-color: #1e40af; }
            QPushButton.danger {
                background-color: #dc2626; color: #fff; font-weight: 600;
                padding: 10px 14px; border-radius: 8px; border: none;
            }
            QPushButton.danger:hover { background-color: #991b1b; }
            QTableWidget {
                background: #ffffff;
                gridline-color: #d9e0e8;
                border: 1px solid #d7dde5;
                border-radius: 8px;
            }
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        # Başlık + Buton
        head = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Entegrasyon Session ID Alımı")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        head.addWidget(title, 0, QtCore.Qt.AlignLeft)

        head.addStretch(1)
        self.btnToggle = QtWidgets.QPushButton("İşlemi Başlat")
        self.btnToggle.setObjectName("btnSession")
        self.btnToggle.setCursor(QtCore.Qt.PointingHandCursor)
        self.btnToggle.setProperty("class", "primary")
        head.addWidget(self.btnToggle, 0, QtCore.Qt.AlignRight)
        root.addLayout(head)

        # 2x3 tablo
        self.table = QtWidgets.QTableWidget(2, 3)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setFixedHeight(120)
        self.table.setRowHeight(0, 46)
        self.table.setRowHeight(1, 46)

        self._set_cell(0, 0, "Session ID", True)
        self._set_cell(0, 1, "Son Alım Tarihi", True)
        self._set_cell(0, 2, "API Yanıtı", True)

        self.cellSession = self._set_cell(1, 0, "-")
        self.cellDate    = self._set_cell(1, 1, "-")
        self.cellApi     = self._set_cell(1, 2, "-")

        root.addWidget(self.table)

    def _set_cell(self, r, c, text, bold=False):
        it = QtWidgets.QTableWidgetItem(text)
        f = it.font(); f.setBold(bold); it.setFont(f)
        it.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.table.setItem(r, c, it)
        return it


# ----------------------------------------------------
# VA Kartı: RESULT6='VA' satırı için tek bir görev kartı
# ----------------------------------------------------
class VaTaskCard(QtWidgets.QFrame):
    def __init__(self, code: str, result2: str, result3: str,
                 title_result4: str, last_update_result5: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build(code, result2, result3, title_result4, last_update_result5)

    def _build(self, code, result2, result3, title_result4, last_update_result5):
        self.setStyleSheet("""
            QFrame#card {
                background: #ffffff;
                border: 1px solid #d7dde5;
                border-radius: 10px;
            }
            QPushButton.primary {
                background-color: #2563eb; color: #fff; font-weight: 600;
                padding: 8px 12px; border-radius: 8px; border: none;
            }
            QPushButton.primary:hover { background-color: #1e40af; }
            QTableWidget {
                background: #ffffff;
                gridline-color: #d9e0e8;
                border: 1px solid #d7dde5;
                border-radius: 8px;
            }
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # Üst: Başlık (RESULT4) + Buton
        head = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(title_result4 or "Görev")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        head.addWidget(title, 0, QtCore.Qt.AlignLeft)

        head.addStretch(1)
        self.btnStart = QtWidgets.QPushButton("İşlemi Başlat")
        self.btnStart.setObjectName("btnVA")
        self.btnStart.setProperty("class", "primary")
        self.btnStart.setCursor(QtCore.Qt.PointingHandCursor)
        # Gizli alanlar (UI'de görünmez)
        self.btnStart.setProperty("code", code)
        self.btnStart.setProperty("rapor_kodu", result2)
        self.btnStart.setProperty("result3", result3)
        head.addWidget(self.btnStart, 0, QtCore.Qt.AlignRight)
        root.addLayout(head)

        # 2x2 tablo – üst satır başlıklar
        self.table = QtWidgets.QTableWidget(2, 2)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setFixedHeight(120)
        self.table.setRowHeight(0, 46)
        self.table.setRowHeight(1, 46)

        self._set_cell(0, 0, "Son Güncelleme Bilgisi", True)
        self._set_cell(0, 1, "API Yanıtı", True)

        self.cellLastUpdate = self._set_cell(1, 0, last_update_result5 or "-")
        self.cellApi        = self._set_cell(1, 1, "-")

        root.addWidget(self.table)

    def _set_cell(self, r, c, text, bold=False):
        it = QtWidgets.QTableWidgetItem(text)
        f = it.font(); f.setBold(bold); it.setFont(f)
        it.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.table.setItem(r, c, it)
        return it


# ---------------------------
# Ana Pencere
# ---------------------------
class IntegrationWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hednova ERP Entegrasyon Paneli")
        self.setFixedSize(1400, 850)  # sabit büyük pencere

        # Session döngüsü için timer (30 dakika)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(30 * 60 * 1000)
        self._timer.timeout.connect(self._run_session_cycle)
        self._running = False

        self._build_ui()
        self._wire_session_button()
        self._load_va_from_db()

    # ---------- UI kur ----------
    def _build_ui(self):
        self.setStyleSheet("QWidget { background: #f6f8fb; font-family: 'Segoe UI'; color: #0f172a; }")
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(36, 28, 36, 28)
        main.setSpacing(20)

        # 1) Session kartı
        self.sessionCard = SessionCard(self)
        main.addWidget(self.sessionCard)

        # 2) VA başlık
        lbl = QtWidgets.QLabel("Tablolar")
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 6px;")
        main.addWidget(lbl)

        # 3) VA kart listesi (scroll alanı)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._vaContainer = QtWidgets.QWidget()
        self._vaList = QtWidgets.QVBoxLayout(self._vaContainer)
        self._vaList.setContentsMargins(0, 0, 0, 0)
        self._vaList.setSpacing(14)

        self.scroll.setWidget(self._vaContainer)
        main.addWidget(self.scroll, 1)

        main.addStretch(0)

    # ---------- Session buton wiring ----------
    def _wire_session_button(self):
        self.sessionCard.btnToggle.clicked.connect(self._toggle_session_button)
        self._set_btn_state(start=True)

    def _set_btn_state(self, start: bool):
        btn = self.sessionCard.btnToggle
        if start:
            btn.setText("İşlemi Başlat")
            btn.setProperty("class", "primary")
            btn.setStyleSheet("QPushButton { background-color: #2563eb; color: #fff; font-weight: 600; padding: 10px 14px; border-radius: 8px; border: none; } QPushButton:hover { background-color: #1e40af; }")
        else:
            btn.setText("İşlemi Durdur")
            btn.setProperty("class", "danger")
            btn.setStyleSheet("QPushButton { background-color: #dc2626; color: #fff; font-weight: 600; padding: 10px 14px; border-radius: 8px; border: none; } QPushButton:hover { background-color: #991b1b; }")

    # ---------- Start/Stop ----------
    def _toggle_session_button(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self._set_btn_state(start=True)
        else:
            self._running = True
            self._set_btn_state(start=False)
            self._run_session_cycle()       # ilk tıklamada hemen
            self._timer.start()             # sonra 30 dakikada bir

    # ---------- Her turda yapılacaklar (Session) ----------
    def _run_session_cycle(self):
        self.sessionCard.cellApi.setText("⏳ İstek gönderiliyor...")
        result = login()  # {'code': '200', 'msg': '<session_id>'} veya hata
        code = str(result.get("code", "0"))
        msg  = str(result.get("msg", ""))

        now_text_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_text_ui = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        self.sessionCard.cellApi.setText(f"code: {code}, msg: {msg}")

        if code == "200":
            self.sessionCard.cellSession.setText(msg)
            self.sessionCard.cellDate.setText(now_text_ui)
            ok, db_msg = update_session_row(session_id=msg, text_datetime=now_text_db)
            suffix = f" | DB: {'OK' if ok else 'HATA'} - {db_msg}"
            self.sessionCard.cellApi.setText(f"code: {code}, msg: {msg}{suffix}")
        else:
            self.sessionCard.cellSession.setText("- Hata oluştu -")
            self.sessionCard.cellDate.setText("-")

    # ---------- VA verilerini yükle ----------
    def _load_va_from_db(self):
        ok, rows, msg = fetch_va_rows()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Veri Yükleme Hatası", msg)
            rows = []
        self.load_va_rows(rows)

    # rows: [{CODE, RESULT2, RESULT3, RESULT4, RESULT5}, ...]
    def load_va_rows(self, rows):
        # mevcut kartları temizle
        while self._vaList.count():
            it = self._vaList.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        # yeni kartları ekle ve BUTONLARI ORTAK HANDLER'A BAĞLA
        for row in rows:
            code    = str(row.get("CODE", ""))
            r2      = str(row.get("RESULT2", ""))
            r3      = str(row.get("RESULT3", ""))
            r4      = str(row.get("RESULT4", ""))
            r5      = str(row.get("RESULT5", ""))

            card = VaTaskCard(code, r2, r3, r4, r5)
            # ORTAK CLICK: tek sefer çalışacak; şimdilik MessageBox ile CODE & RESULT2 göster
            card.btnStart.clicked.connect(lambda _, c=code, rc=r2, card_ref=card: self.on_va_start_clicked(card_ref, c, rc))
            self._vaList.addWidget(card)

    # ---- VA ORTAK CLICK HANDLER ----
    def on_va_start_clicked(self, card: VaTaskCard, code: str, report_code: str):
        # 1) API’den raporu çek
        result = report_result_get(report_code)  # session_id verilmezse DB'den aktif session alınır
        rcode = str(result.get("code", "0"))
        msg   = str(result.get("msg", ""))
        rows  = result.get("rows", []) or []

        # 2) UI ve konsol çıktısı
        if rcode == "200":
            # Konsola satırları bas
            try:
                print("=== Rapor Sonucu Satırlar ===")
                for row in rows:
                    print(row)
                print(f"Toplam satır: {len(rows)}")
            except Exception:
                pass

            card.cellApi.setText(f"code 200 başarılı - toplam {len(rows)} satır döndü")
        else:
            card.cellApi.setText(f"code: {rcode}  msg: {msg}")
            return  # başarısızsa aşağıdaki case’lere geçmeyelim
        
        now_text_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_text_ui = now_text_db 

        # 3) API SONUCUNDAN SONRA KOD-BAZLI AYRIM (şimdilik yer tutucu)
        if code == "ENT-02":
            ok, db_msg, new_count = ent02_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        if code == "ENT-03":
            ok, db_msg, new_count = ent03_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return

        if code == "ENT-04":
            ok, db_msg, new_count = ent04_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-05":
            ok, db_msg, new_count = ent05_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-06":
            ok, db_msg, new_count = ent06_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-07":
            ok, db_msg, new_count = ent07_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-08":
            ok, db_msg, new_count = ent08_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return


        if code == "ENT-09":
            ok, db_msg, new_count = ent09_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-10":
            ok, db_msg, new_count = ent10_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return
        
        
        if code == "ENT-11":
            ok, db_msg, new_count = ent11_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return


        
        if code == "ENT-12":
            ok, db_msg, new_count = ent12_update(rows)
            if ok:

                ok2, msg2 = update_entegrasyone_last_update(code, now_text_db)
                if ok2:
                    card.cellLastUpdate.setText(now_text_ui)

                # API Yanıtı: senkron özeti + RESULT5 güncelleme durumu
                suffix = f" | RESULT5: {'OK' if ok2 else 'HATA'}"
                card.cellApi.setText(f"{db_msg}{suffix}")
            else:
                card.cellApi.setText(f"HATA: {db_msg} | yeni kayıt: 0")
            return

        # Diğer kodlar için (varsayılan) bir şey yapmayacaksak burada bitiririz
        return
    
    
    





