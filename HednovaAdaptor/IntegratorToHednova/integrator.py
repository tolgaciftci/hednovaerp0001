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
last_session_id = None  # DİA oturum ID'si
db_conn = None           # Global SQL connection
last_fetch_datetime = None  # Son başarılı rapor çekme zamanı


# ---------------------- CONFIG YÜKLEME ----------------------
def load_config():
    """data.json dosyasını oku"""
    global config
    path = os.path.join(BASE_DIR, "data.json")
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)


# ---------------------- LOG MESAJI ----------------------
def log_message(msg: str):
    """GUI loguna zaman damgası ile mesaj yaz"""
    if gui_ref:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gui_ref.add_log(f"[{now}] {msg}")
    else:
        print(msg)


# ---------------------- SQL BAĞLANTI YÖNETİMİ ----------------------
def open_db_connection():
    """Global SQL bağlantısını açar (her entegrasyon başında yenilenir)"""
    global db_conn
    try:
        # Önce varsa eski bağlantıyı kapatalım
        if db_conn:
            db_conn.close()
            db_conn = None

        conn_str = config["hednova"]["connectionstring"]
        if "Driver=" not in conn_str:
            conn_str = "Driver={ODBC Driver 17 for SQL Server};" + conn_str

        db_conn = pyodbc.connect(conn_str)
        log_message("SQL bağlantısı kuruldu ✅")

    except Exception as e:
        log_message(f"Hata (SQL bağlantısı açma): {e}")
        db_conn = None


def close_db_connection():
    """Global SQL bağlantısını kapatır"""
    global db_conn
    try:
        if db_conn:
            db_conn.close()
            db_conn = None
            log_message("SQL bağlantısı kapatıldı 🔒")
    except Exception as e:
        log_message(f"Hata (SQL bağlantısı kapatma): {e}")


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
    global db_conn
    try:
        if not db_conn:
            open_db_connection()
        cursor = db_conn.cursor()

        sql = "UPDATE KR_ENTEGRASYONE SET RESULT1 = ? WHERE CODE = 'ENT-01'"
        cursor.execute(sql, (message,))
        db_conn.commit()

        log_message("Veritabanında RESULT1 başarıyla güncellendi ✅")

    except Exception as e:
        log_message(f"Hata (SQL güncelleme): {e}")


# ---------------------- RAPOR GETİRME ----------------------
def FetchReport(session_id):
    """DİA'dan rapor çeker ve __detailrows kısmını çözer"""
    global last_fetch_datetime, db_conn

    if not session_id:
        log_message("Session ID bulunamadı, rapor çekilemedi ❌")
        return

    firma = config["integrator"]["company"]
    donem = config["integrator"]["period"]

    # ✅ Her işlemde bağlantıyı yenile
    open_db_connection()

    # RESULT2 değerini oku
    result2_value = None
    try:
        cursor = db_conn.cursor()
        sql = "SELECT RESULT2 FROM KR_ENTEGRASYONE WHERE CODE = 'ENT-01'"
        cursor.execute(sql)
        row = cursor.fetchone()
        if row:
            result2_value = row[0]
        log_message(f"RESULT2 değeri alındı: {result2_value}")
    except Exception as e:
        log_message(f"Hata (RESULT2 okuma): {e}")

    ws_url = "https://kirpi.ws.dia.com.tr/api/v3/rpr/json"

    payload = {
        "rpr_raporsonuc_getir": {
            "session_id": session_id,
            "firma_kodu": int(firma),
            "donem_kodu": int(donem),
            "report_code": "ENT-01",
            "param": {"firma": firma, "donem": donem, "tarihsaat": result2_value},
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

        # ✅ Başarılıysa tarih-saat kaydet
        last_fetch_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message(f"Rapor başarıyla alındı. Tarih: {last_fetch_datetime}")

        # base64 çöz
        encoded = result.get("result", "")
        decoded = base64.b64decode(encoded).decode("utf-8")
        data = json.loads(decoded)

        # detailrows al
        rows = data.get("__rows", [])
        if rows and "__detailrows" in rows[0]:
            detailrows = rows[0]["__detailrows"]
        else:
            detailrows = {}

        log_message(f"Rapor alındı ({len(detailrows)} detay kümesi bulundu) ✅")

        # 🟢 Sadece D-0001'i işle
        if "D-0001" in detailrows:
            UpdateSistemStokBirimleri(db_conn, "D-0001", detailrows["D-0001"])
        else:
            log_message("D-0001 detayı bulunamadı ❌")
            
        
        # 🔵 Tüm update fonksiyonları bittikten sonra RESULT2 güncelle
        try:
            cursor = db_conn.cursor()
            sql = "UPDATE KR_ENTEGRASYONE SET RESULT2 = ? WHERE CODE = 'ENT-01'"
            cursor.execute(sql, (last_fetch_datetime,))
            db_conn.commit()
            log_message(f"KR_ENTEGRASYONE.RESULT2 güncellendi → {last_fetch_datetime} ✅")
        except Exception as e:
            log_message(f"Hata (RESULT2 güncelleme): {e}")

    except Exception as e:
        log_message(f"Hata (Rapor çekme): {e}")


# ---------------------- ANA İŞLEM ----------------------
def MakeIntegration():
    """Ana entegrasyon akışı"""
    log_message("Yeni entegrasyon işlemi başlatılıyor 🔄")
    open_db_connection()

    session = LoginToDia()
    if session:
        FetchReport(session)
        log_message("Veritabanı güncelleme işlemi tamamlandı ✅")

    close_db_connection()  # işlem bitince kapat


# ---------------------- SİSTEM BAŞLAT/DURDUR ----------------------
def StartIntegration(gui):
    """Entegrasyonu başlat"""
    global integration_timer, gui_ref
    gui_ref = gui

    load_config()
    minutes = config["hednova"].get("integratorperiod", 5)
    period = minutes * 60 * 1000  # dakika → milisaniye

    log_message(f"Entegrasyon başlatıldı. Her {minutes} dakikada bir çalışacak.")

    # İlk kez hemen çalıştır
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
    close_db_connection()
    log_message("Entegrasyon durduruldu ⏹️")
    gui_ref = None


# ===================================================================
#                DİĞER GÜNCELLEME FONKSİYONLARI 
# ===================================================================

def UpdateSistemStokBirimleri(conn, kod, rows):
    """
    KR_GECOUST tablosunu günceller:
      - islemturu == 2 → INSERT
      - islemturu == 3 → UPDATE (yoksa INSERT)
      - islemturu == 4 → DELETE
    Diğer durumlar atlanır.
    """
    global last_fetch_datetime

    toplam_islem = 0
    log_message(f"Sistem Stok Birimleri ({kod}) için {len(rows)} kayıt alındı, işleniyor...")

    try:
        cursor = conn.cursor()

        # Tarih ve saat parçala
        tarih = saat = None
        if last_fetch_datetime:
            try:
                dt = datetime.strptime(last_fetch_datetime, "%Y-%m-%d %H:%M:%S")
                tarih = dt.strftime("%Y-%m-%d")
                saat = dt.strftime("%H:%M:%S")
            except:
                pass

        for item in rows:
            keykayit = str(item.get("keykayit"))
            islemturu = item.get("islemturu")
            birimkod = item.get("birimkod")
            birimadi = item.get("birimadi")

            # 🟢 INSERT (islemturu == 2)
            if islemturu == 2:
                sql_insert = """
                    INSERT INTO KR_GECOUST (EVRAKNO, KOD, AD, AP10, TLOG_LOGTARIH, TLOG_LOGTIME, ENT01)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (
                    "STUNIT",  # EVRAKNO sabit
                    birimkod,
                    birimadi,
                    1,
                    tarih,
                    saat,
                    keykayit
                ))
                toplam_islem += 1

            # 🟠 UPDATE (islemturu == 3)
            elif islemturu == 3:
                # önce kayıt var mı kontrol et
                sql_check = "SELECT COUNT(*) FROM KR_GECOUST WHERE ENT01=?"
                cursor.execute(sql_check, (keykayit,))
                exists = cursor.fetchone()[0]

                if exists:
                    # varsa UPDATE
                    sql_update = """
                        UPDATE KR_GECOUST
                        SET EVRAKNO=?, KOD=?, AD=?, AP10=?, TLOG_LOGTARIH=?, TLOG_LOGTIME=?
                        WHERE ENT01=?
                    """
                    cursor.execute(sql_update, (
                        "STUNIT",
                        birimkod,
                        birimadi,
                        1,
                        tarih,
                        saat,
                        keykayit
                    ))
                else:
                    # yoksa INSERT
                    sql_insert = """
                        INSERT INTO KR_GECOUST (EVRAKNO, KOD, AD, AP10, TLOG_LOGTARIH, TLOG_LOGTIME, ENT01)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(sql_insert, (
                        "STUNIT",
                        birimkod,
                        birimadi,
                        1,
                        tarih,
                        saat,
                        keykayit
                    ))

                toplam_islem += 1

            # 🔴 DELETE (islemturu == 4)
            elif islemturu == 4:
                sql_delete = "DELETE FROM KR_GECOUST WHERE ENT01=?"
                cursor.execute(sql_delete, (keykayit,))
                toplam_islem += 1

            # ⚪ Diğer durumlar
            else:
                continue

        conn.commit()
        log_message(f"Sistem Stok Birimleri ({kod}) → {toplam_islem} kayıt işlendi ✅")

    except Exception as e:
        log_message(f"Hata (UpdateSistemStokBirimleri - {kod}): {e}")
        try:
            conn.rollback()
        except:
            pass
