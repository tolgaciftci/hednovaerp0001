# -*- coding: utf-8 -*-
import os
import json
import base64
import requests
import pyodbc
from datetime import datetime
from PySide6.QtCore import QTimer

BASE_DIR = os.path.dirname(__file__)
config = {}
integration_timer = None
gui_ref = None
last_session_id = None  # global değişken


def load_config():
    """data.json dosyasını oku"""
    global config
    path = os.path.join(BASE_DIR, "data.json")
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)


def log_message(msg: str):
    """GUI loguna zaman damgası ile mesaj yaz"""
    if gui_ref:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gui_ref.add_log(f"[{now}] {msg}")


# ---------------------- DİA LOGIN ----------------------
def LoginToDia():
    """DİA API'ye login olur ve session_id döner"""
    global last_session_id

    ent = config["integrator"]
    ws_url = "https://kirpi.ws.dia.com.tr/api/v3/sis/json"

    payload = {
        "login": {
            "username": ent["user"],
            "password": ent["password"],
            "disconnect_same_user": "true",
            "lang": "tr",
            "params": {"apikey": ent["apikey"]}
        }
    }

    log_message("DİA'ya login olunuyor...")

    try:
        response = requests.post(ws_url, json=payload, headers={"Content-Type": "application/json;charset=UTF-8"})
        result = response.json()

        code = result.get("code", "??")
        msg = result.get("msg", "")

        log_message(f"DİA Cevabı → code: {code}, msg: {msg}")

        if str(code) == "200":
            last_session_id = msg  # session_id kaydet
            UpdateResultInDb(msg)
            return msg
        else:
            log_message("API hatası: code 200 değil, login başarısız.")
            return None
    except Exception as e:
        log_message(f"Hata (DİA login): {e}")
        return None


# ---------------------- SQL UPDATE ----------------------
def UpdateResultInDb(message):
    """SQL'deki KR_ENTEGRASYONE tablosunda RESULT1 kolonunu günceller"""
    try:
        conn_str = config["hednova"]["connectionstring"]

        # Driver belirtilmediyse ekle
        if "Driver=" not in conn_str:
            conn_str = "Driver={ODBC Driver 17 for SQL Server};" + conn_str

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        sql = "UPDATE KR_ENTEGRASYONE SET RESULT1 = ? WHERE CODE = 'ENT-01'"
        cursor.execute(sql, (message,))
        conn.commit()
        conn.close()

        log_message("Veritabanında RESULT1 başarıyla güncellendi ✅")
    except Exception as e:
        log_message(f"Hata (SQL güncelleme): {e}")


# ---------------------- RAPOR GETİRME ----------------------
def FetchReport(session_id):
    """DİA'dan rapor çeker ve __detailrows kısmını çözer"""
    if not session_id:
        log_message("Session ID bulunamadı, rapor çekilemedi ❌")
        return

    firma = config["integrator"]["company"]
    donem = config["integrator"]["period"]

    ws_url = "https://kirpi.ws.dia.com.tr/api/v3/rpr/json"

    payload = {
        "rpr_raporsonuc_getir": {
            "session_id": session_id,
            "firma_kodu": int(firma),
            "donem_kodu": int(donem),
            "report_code": "ENT-01",
            "param": {"firma": firma, "donem": donem},
            "format_type": "json"
        }
    }

    log_message("DİA'dan rapor çekiliyor...")

    try:
        response = requests.post(ws_url, json=payload, headers={"Content-Type": "application/json;charset=UTF-8"})
        result = response.json()

        code = result.get("code", "??")
        if str(code) != "200":
            log_message(f"Rapor alınamadı ❌ (code: {code})")
            return

        # base64 çöz
        encoded = result.get("result", "")
        decoded = base64.b64decode(encoded).decode("utf-8")
        data = json.loads(decoded)

        # ✅ doğru seviyeden __detailrows al
        rows = data.get("__rows", [])
        if rows and "__detailrows" in rows[0]:
            detailrows = rows[0]["__detailrows"]
        else:
            detailrows = {}

        log_message(f"Rapor alındı ({len(detailrows)} detay kümesi bulundu) ✅")

        # terminale bas
        print("\n--- __detailrows ---")
        print(json.dumps(detailrows, indent=2, ensure_ascii=False))
        print("--------------------\n")

    except Exception as e:
        log_message(f"Hata (Rapor çekme): {e}")


# ---------------------- ANA İŞLEM ----------------------
def MakeIntegration():
    """Ana entegrasyon akışı"""
    session = LoginToDia()
    if session:
        FetchReport(session)
        log_message("Veritabanı güncelleme işlemi başladı...")


# ---------------------- SİSTEM BAŞLAT/DURDUR ----------------------
def StartIntegration(gui):
    """Entegrasyonu başlat"""
    global integration_timer, gui_ref
    gui_ref = gui

    load_config()
    minutes = config["hednova"].get("integratorperiod", 5)
    period = minutes * 60 * 1000  # dakika → milisaniye

    log_message(f"Entegrasyon başlatıldı. Her {minutes} dakikada bir çalışacak.")

    # ilk kez hemen çalıştır
    MakeIntegration()

    # QTimer periyodik
    integration_timer = QTimer()
    integration_timer.timeout.connect(MakeIntegration)
    integration_timer.start(period)


def StopIntegration():
    """Timerları durdur"""
    global integration_timer, gui_ref
    if integration_timer:
        integration_timer.stop()
    log_message("Entegrasyon durduruldu ⏹️")
    gui_ref = None
