# sql_crud.py
# -*- coding: utf-8 -*-

import json
import pyodbc
from typing import Tuple
from typing import Tuple, List, Dict

def _pick_odbc_driver() -> str:
    """Makinede yüklü SQL Server ODBC sürücülerinden en uygun olanı seç."""
    try:
        drivers = pyodbc.drivers()
    except Exception:
        drivers = []
    preferred = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    for p in preferred:
        if p in drivers:
            return p
    # Hiçbiri bulunamazsa boş dön (kullanıcıya anlamlı hata vereceğiz)
    return ""

def _load_conn_string() -> str:
    """data.json'daki connectionstring'i al; gerekirse DRIVER ve Encrypt/Trust seçeneklerini ekle."""
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    base = data["hednova"]["connectionstring"].strip()

    # Driver yoksa otomatik ekle
    if "driver=" not in base.lower():
        driver_name = _pick_odbc_driver()
        if not driver_name:
            raise RuntimeError(
                "Uygun SQL Server ODBC sürücüsü bulunamadı. Lütfen 'ODBC Driver 18 for SQL Server' "
                "veya 'ODBC Driver 17 for SQL Server' kurun."
            )
        base = f"Driver={{{driver_name}}};" + base

    # ODBC 18'de varsayılan Encrypt=yes. TrustServerCertificate varsa sorun yok.
    # Emin olmak için eksikse ekleyelim:
    low = base.lower()
    if "encrypt=" not in low and "trustservercertificate=" not in low:
        # Sunucuda sertifika yönetmiyorsak şöyle güvenli bir ikili iyi çalışır:
        base += "Encrypt=yes;TrustServerCertificate=yes;"

    return base

def update_session_row(session_id: str, text_datetime: str) -> Tuple[bool, str]:
    """
    KR_ENTEGRASYONE tablosunda CODE='ENT-01' satırını günceller:
      RESULT1 = session_id (TEXT)
      RESULT2 = text_datetime (TEXT 'YYYY-MM-DD HH:MM:SS')
    Dönüş: (başarılı_mı, mesaj)
    """
    try:
        conn_str = _load_conn_string()
    except Exception as e:
        return (False, f"Bağlantı cümlesi hazırlanamadı: {e}")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}")

    try:
        cursor = conn.cursor()
        sql = """
        UPDATE [KR_ENTEGRASYONE]
           SET [RESULT1] = ?, [RESULT2] = ?
         WHERE [CODE] = 'ENT-01';
        """
        cursor.execute(sql, (session_id, text_datetime))
        rows = cursor.rowcount
        cursor.close()
        conn.close()
        # MSSQL bazen rowcount=-1 döndürebilir; bu gerçek bir hata değildir
        if rows is None or rows < 0:
            return (True, "Güncelleme çalıştı (rowcount bilinmiyor).")
        return (True, f"Güncellendi (etkilenen satır: {rows}).")
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return (False, f"Sorgu hatası: {e}")



def fetch_va_rows() -> Tuple[bool, List[Dict], str]:
    """
    KR_ENTEGRASYONE tablosundan RESULT6='VA' olan satırları çeker.
    Dönen yapı:
      (True/False, rows, message)
      rows: [{ "CODE":..., "RESULT2":..., "RESULT3":..., "RESULT4":..., "RESULT5":... }, ...]
    """
    try:
        conn_str = _load_conn_string()
    except Exception as e:
        return (False, [], f"Bağlantı cümlesi hazırlanamadı: {e}")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
    except Exception as e:
        return (False, [], f"Veritabanı bağlantı hatası: {e}")

    try:
        cursor = conn.cursor()
        sql = """
            SELECT [CODE], [RESULT2], [RESULT3], [RESULT4], [RESULT5]
              FROM [KR_ENTEGRASYONE]
             WHERE [RESULT6] = 'VA'
             ORDER BY [CODE];
        """
        cursor.execute(sql)
        rows = []
        for r in cursor.fetchall():
            rows.append({
                "CODE":    str(r[0]) if r[0] is not None else "",
                "RESULT2": str(r[1]) if r[1] is not None else "",
                "RESULT3": str(r[2]) if r[2] is not None else "",
                "RESULT4": str(r[3]) if r[3] is not None else "",
                "RESULT5": str(r[4]) if r[4] is not None else "",
            })
        cursor.close()
        conn.close()
        return (True, rows, f"{len(rows)} kayıt bulundu.")
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return (False, [], f"Sorgu hatası: {e}")
    
      

def get_active_session() -> Tuple[bool, str]:
    """
    KR_ENTEGRASYONE tablosunda CODE='ENT-01' satırının RESULT1 alanını (aktif session id) döndürür.
    Dönüş: (ok, session_id_or_error_message)
    """
    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=True, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TOP 1 [RESULT1]
              FROM [KR_ENTEGRASYONE]
             WHERE [CODE] = 'ENT-01';
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0]:
            return (True, str(row[0]))
        return (False, "Aktif session bulunamadı (RESULT1 boş).")
    except Exception as e:
        try: conn.close()
        except Exception: pass
        return (False, f"Sorgu hatası: {e}")
    
    
def update_entegrasyone_last_update(code: str, text_datetime: str) -> Tuple[bool, str]:
    """
    KR_ENTEGRASYONE tablosunda ilgili CODE satırının RESULT5 alanını günceller.
    text_datetime -> 'YYYY-MM-DD HH:MM:SS' formatlı TEXT.
    Dönüş: (ok, mesaj)
    """
    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=True, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}")

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE [KR_ENTEGRASYONE]
               SET [RESULT5] = ?
             WHERE [CODE] = ?
        """, (text_datetime, code))
        rows = cur.rowcount
        cur.close()
        conn.close()
        return (True, f"RESULT5 güncellendi (etkilenen satır: {rows}).")
    except Exception as e:
        try: conn.close()
        except Exception: pass
        return (False, f"RESULT5 güncellenemedi: {e}")
    



def ent02_update(rows: List[Dict]) -> Tuple[bool, str, int]:
    """
    rows: [{"key": 13482, "kod":"HZ", "aciklama":"HİZMET"}, ...]
    Dönüş: (ok, mesaj, yeni_eklenen_kayit_sayisi)
    """
    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    evrak_const = "STUNIT"
    try:
        cur = conn.cursor()

        # 1) Mevcut ENT01 kümesini çek (EVRAKNO 'STUNIT')
        cur.execute("""
            SELECT [ENT01]
              FROM [KR_GECOUST]
             WHERE LTRIM(RTRIM([EVRAKNO])) = ?
        """, (evrak_const,))
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]))

        # 2) API keys + normalize
        api_rows = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci})
            api_keys.add(key)

        # 3) Eklenen / Güncellenen / Silinen kümeleri hesapla
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_GECOUST] ([EVRAKNO], [KOD], [AD], [AP10], [ENT01])
                    VALUES (?, ?, ?, ?, ?)
                """, (evrak_const, row["kod"], row["aciklama"], 1, row["key"]))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_GECOUST]
                       SET [KOD] = ?, [AD] = ?, [AP10] = ?, [EVRAKNO] = ?
                     WHERE [ENT01] = ? AND LTRIM(RTRIM([EVRAKNO])) = ?
                """, (row["kod"], row["aciklama"], 1, evrak_const, row["key"], evrak_const))

        # 6) DELETE (DB’de olup API’de olmayanlar)
        for key in to_delete:
            cur.execute("""
                DELETE FROM [KR_GECOUST]
                 WHERE [ENT01] = ? AND LTRIM(RTRIM([EVRAKNO])) = ?
            """, (key, evrak_const))

        conn.commit()
        msg = f"ENT-02 senkron tamamlandı: eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}."
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-02 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def ent03_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()


        cur.execute("SELECT [ENT01] FROM [KR_PERS00]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())


        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            tez = str(it.get("tezgah_kodu", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci, "tezgah_kodu": tez})
            api_keys.add(key)

  
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys


        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_PERS00] ([KOD], [AD], [REFTEXT01], [ENT01])
                    VALUES (?, ?, ?, ?)
                """, (row["kod"], row["aciklama"], row["tezgah_kodu"], row["key"]))
                inserted += 1


        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_PERS00]
                       SET [KOD] = ?, [AD] = ?, [REFTEXT01] = ?
                     WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["tezgah_kodu"], row["key"]))


        for key in to_delete:
            cur.execute("DELETE FROM [KR_PERS00] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-03 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-03 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass



def ent04_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki ENT01 kümesini çek (tüm kayıtlar)
        cur.execute("SELECT [ENT01] FROM [KR_IMLT00]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci})
            api_keys.add(key)

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_IMLT00] ([KOD], [AD], [ENT01])
                    VALUES (?, ?, ?)
                """, (row["kod"], row["aciklama"], row["key"]))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_IMLT00]
                       SET [KOD] = ?, [AD] = ?
                     WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["key"]))

        # 6) DELETE (API'de olmayanları sil)
        for key in to_delete:
            cur.execute("DELETE FROM [KR_IMLT00] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-04 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-04 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
        

def ent05_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki ENT01 kümesini çek (tüm kayıtlar)
        cur.execute("SELECT [ENT01] FROM [KR_IMLT01]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci})
            api_keys.add(key)

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_IMLT01] ([KOD], [AD], [ENT01])
                    VALUES (?, ?, ?)
                """, (row["kod"], row["aciklama"], row["key"]))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_IMLT01]
                       SET [KOD] = ?, [AD] = ?
                     WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["key"]))

        # 6) DELETE (API'de olmayanları sil)
        for key in to_delete:
            cur.execute("DELETE FROM [KR_IMLT01] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-05 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-05 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
        


def ent06_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki ENT01 kümesini çek (tüm kayıtlar)
        cur.execute("SELECT [ENT01] FROM [KR_GDEF00]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci})
            api_keys.add(key)

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_GDEF00] ([KOD], [AD], [ENT01])
                    VALUES (?, ?, ?)
                """, (row["kod"], row["aciklama"], row["key"]))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_GDEF00]
                       SET [KOD] = ?, [AD] = ?
                     WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["key"]))

        # 6) DELETE (API'de olmayanları sil)
        for key in to_delete:
            cur.execute("DELETE FROM [KR_GDEF00] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-06 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-06 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
        


def ent07_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki ENT01 kümesini çek (tüm kayıtlar)
        cur.execute("SELECT [ENT01] FROM [KR_CARI00]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci})
            api_keys.add(key)

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_CARI00] ([KOD], [AD], [ENT01])
                    VALUES (?, ?, ?)
                """, (row["kod"], row["aciklama"], row["key"]))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_CARI00]
                       SET [KOD] = ?, [AD] = ?
                     WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["key"]))

        # 6) DELETE (API'de olmayanları sil)
        for key in to_delete:
            cur.execute("DELETE FROM [KR_CARI00] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-07 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-07 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass



def ent08_update(rows: List[Dict]) -> Tuple[bool, str, int]:

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki ENT01 kümesini çek (tüm kayıtlar)
        cur.execute("SELECT [ENT01] FROM [KR_BOMU01E]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()
        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()
            aci = str(it.get("aciklama", "")).strip()
            durum = str(it.get("durum", "")).strip()
            mamulkey = str(it.get("mamulkey", "")).strip()
            mamulmiktar = float(it.get("mamulmiktar") or 0)
            mamulkod = str(it.get("mamulkod", "")).strip()
            if not key:
                continue
            api_rows.append({"key": key, "kod": kod, "aciklama": aci, "durum": durum, "mamulkey": mamulkey, "mamulmiktar": mamulmiktar, "mamulkod": mamulkod})
            api_keys.add(key)

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        # 4) INSERT
        inserted = 0
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_BOMU01E] ([ENT01], [EVRAKNO], [ACIKLAMA], [AKTIF_PASIF], [ENT02], [MAMULMIKTAR], [MAMULCODE])
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (row["key"], row["kod"], row["aciklama"], row["durum"], row["mamulkey"], row["mamulmiktar"], row["mamulkod"]))
                inserted += 1

        # 5) UPDATE
        # 5) UPDATE
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_BOMU01E]
                    SET [EVRAKNO] = ?, 
                        [ACIKLAMA] = ?, 
                        [AKTIF_PASIF] = ?, 
                        [ENT02] = ?, 
                        [MAMULMIKTAR] = ?, 
                        [MAMULCODE] = ?
                    WHERE [ENT01] = ?
                """, (row["kod"], row["aciklama"], row["durum"], row["mamulkey"], row["mamulmiktar"], row["mamulkod"], row["key"]))
                


        # 6) DELETE (API'de olmayanları sil)
        for key in to_delete:
            cur.execute("DELETE FROM [KR_BOMU01E] WHERE [ENT01] = ?", (key,))

        conn.commit()
        msg = (f"ENT-08 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-08 hata: {e}", 0)
    finally:
        try:
            conn.close()
        except Exception:
            pass





def ent09_update(rows: List[Dict]) -> Tuple[bool, str, int]:
    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) Mevcut veriyi çek (ENT01+ENT02+ENT03+ENT04+ENT05 birleşimi)
        cur.execute("SELECT [ENT01], [ENT02], [ENT03], [ENT04], [ENT05] FROM [KR_BOMU01T]")
        db_keys = set()
        for r in cur.fetchall():
            key_combo = f"{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}"
            db_keys.add(key_combo)

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()

        for it in rows or []:
            ent01 = str(it.get("evraknokey", "")).strip()
            ent02 = str(it.get("bomreccodekey", "")).strip()
            ent03 = str(it.get("bomreckaynakcodekey", "")).strip()
            ent04 = str(it.get("bomrecoperasyonkey", "")).strip()
            ent05 = str(it.get("tuketimtezgahkey", "")).strip()

            composite_key = f"{ent01}|{ent02}|{ent03}|{ent04}|{ent05}"
            api_keys.add(composite_key)

            api_rows.append({
                "ent01": ent01,
                "evrakno": str(it.get("evrakno", "")).strip(),
                "durum": str(it.get("durum", "")).strip(),
                "ent02": ent02,
                "bomreccode": str(it.get("bomreccode", "")).strip(),
                "bomrecinputtype": str(it.get("bomrecinputtype", "")).strip(),
                "ent03": ent03,
                "bomreckaynakcode": str(it.get("bomreckaynakcode", "")).strip(),
                "bomrecmamulmiktar": float(it.get("bomrecmamulmiktar") or 0),
                "bomreckaynak0": str(it.get("bomreckaynak0", "")).strip(),
                "ent04": ent04,
                "bomrecoperasyon": str(it.get("bomrecoperasyon", "")).strip(),
                "ent05": ent05,
                "tuketimtezgah": str(it.get("tuketimtezgah", "")).strip(),
                "composite_key": composite_key
            })

        # 3) fark kümeleri
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        inserted = 0

        # 4) INSERT
        for row in api_rows:
            if row["composite_key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_BOMU01T]
                    ([ENT01], [EVRAKNO], [AKTIF_PASIF], [ENT02], [BOMREC_CODE], [BOMREC_INPUTTYPE],
                     [ENT03], [BOMREC_KAYNAKCODE], [BOMREC_MAMULMIKTAR], [BOMREC_KAYNAK0],
                     [ENT04], [BOMREC_OPERASYON], [ENT05], [REFTEXT01])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["ent01"], row["evrakno"], row["durum"], row["ent02"], row["bomreccode"],
                    row["bomrecinputtype"], row["ent03"], row["bomreckaynakcode"],
                    row["bomrecmamulmiktar"], row["bomreckaynak0"], row["ent04"],
                    row["bomrecoperasyon"], row["ent05"], row["tuketimtezgah"]
                ))
                inserted += 1

        # 5) UPDATE
        for row in api_rows:
            if row["composite_key"] in to_update:
                cur.execute("""
                    UPDATE [KR_BOMU01T]
                    SET [EVRAKNO] = ?, 
                        [AKTIF_PASIF] = ?, 
                        [BOMREC_CODE] = ?, 
                        [BOMREC_INPUTTYPE] = ?, 
                        [BOMREC_KAYNAKCODE] = ?, 
                        [BOMREC_MAMULMIKTAR] = ?, 
                        [BOMREC_KAYNAK0] = ?, 
                        [BOMREC_OPERASYON] = ?, 
                        [REFTEXT01] = ?
                    WHERE [ENT01] = ? AND [ENT02] = ? AND [ENT03] = ? AND [ENT04] = ? AND [ENT05] = ?
                """, (
                    row["evrakno"], row["durum"], row["bomreccode"], row["bomrecinputtype"],
                    row["bomreckaynakcode"], row["bomrecmamulmiktar"], row["bomreckaynak0"],
                    row["bomrecoperasyon"], row["tuketimtezgah"],
                    row["ent01"], row["ent02"], row["ent03"], row["ent04"], row["ent05"]
                ))

        # 6) DELETE
        for composite_key in to_delete:
            ent01, ent02, ent03, ent04, ent05 = composite_key.split("|")
            cur.execute("""
                DELETE FROM [KR_BOMU01T]
                WHERE [ENT01] = ? AND [ENT02] = ? AND [ENT03] = ? AND [ENT04] = ? AND [ENT05] = ?
            """, (ent01, ent02, ent03, ent04, ent05))

        conn.commit()
        msg = (f"ENT-09 senkron tamamlandı: eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-09 hata: {e}", 0)

    finally:
        try:
            conn.close()
        except Exception:
            pass




def ent10_update(rows: List[Dict]) -> Tuple[bool, str, int]:
    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1) DB'deki mevcut ENT01 kayıtlarını çek
        cur.execute("SELECT [ENT01] FROM [KR_STOK40E]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2) API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()

        for it in rows or []:
            key = str(it.get("key", "")).strip()
            kod = str(it.get("kod", "")).strip()                  # fisno -> EVRAKNO
            tarih = str(it.get("tarih", "")).strip()              # tarih -> TARIH
            saat = str(it.get("saat", "")).strip()                # saat -> ISLEM_SAATI
            a1 = str(it.get("a1", "")).strip()                    # aciklama1 -> SIPLEILGILINOTLAR_1
            a2 = str(it.get("a2", "")).strip()                    # aciklama2 -> SIPLEILGILINOTLAR_2
            a3 = str(it.get("a3", "")).strip()                    # aciklama3 -> SIPLEILGILINOTLAR_3
            keycari = str(it.get("keycari", "")).strip()          # _key_scf_carikart -> ENT02
            carikod = str(it.get("carikod", "")).strip()          # carikartkodu -> MUSTERIKODU

            if not key:
                continue

            api_rows.append({
                "key": key,
                "kod": kod,
                "tarih": tarih,
                "saat": saat,
                "a1": a1,
                "a2": a2,
                "a3": a3,
                "keycari": keycari,
                "carikod": carikod
            })
            api_keys.add(key)

        # 3) Farkları bul
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        inserted = 0

        # 4) Yeni kayıt ekleme
        for row in api_rows:
            if row["key"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_STOK40E]
                        ([ENT01], [EVRAKNO], [TARIH], [ISLEM_SAATI],
                         [SIPLEILGILINOTLAR_1], [SIPLEILGILINOTLAR_2], [SIPLEILGILINOTLAR_3],
                         [ENT02], [MUSTERIKODU])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["key"], row["kod"], row["tarih"], row["saat"],
                    row["a1"], row["a2"], row["a3"], row["keycari"], row["carikod"]
                ))
                inserted += 1

        # 5) Güncelleme
        for row in api_rows:
            if row["key"] in to_update:
                cur.execute("""
                    UPDATE [KR_STOK40E]
                       SET [EVRAKNO] = ?, [TARIH] = ?, [ISLEM_SAATI] = ?,
                           [SIPLEILGILINOTLAR_1] = ?, [SIPLEILGILINOTLAR_2] = ?, [SIPLEILGILINOTLAR_3] = ?,
                           [ENT02] = ?, [MUSTERIKODU] = ?
                     WHERE [ENT01] = ?
                """, (
                    row["kod"], row["tarih"], row["saat"],
                    row["a1"], row["a2"], row["a3"],
                    row["keycari"], row["carikod"], row["key"]
                ))

        # 6) Silme
        for key in to_delete:
            cur.execute("DELETE FROM [KR_STOK40E] WHERE [ENT01] = ?", (key,))

        # 7) Commit
        conn.commit()
        msg = (f"ENT-10 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-10 hata: {e}", 0)

    finally:
        try:
            conn.close()
        except Exception:
            pass




def ent11_update(rows: List[Dict]) -> Tuple[bool, str, int]:
    """
    KR_STOK40T tablosunu API'den gelen satırlarla senkronize eder.
    Alanlar: ENT01, ENT02, EVRAKNO, TARIH, ENT03, KOD, NOTES, OR_FIYAT, PRICEUNIT, 
             OR_TUTAR, SF_MIKTAR, ENT04, ENT05, SF_SF_UNIT, SF_STOK_MIKTAR, RTESTARIH
    """

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1️⃣ Mevcut kayıtları al (ENT01 anahtar)
        cur.execute("SELECT [ENT01] FROM [KR_STOK40T]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2️⃣ API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()

        for it in rows or []:
            satirkey = str(it.get("satirkey", "")).strip()
            evraknokey = str(it.get("evraknokey", "")).strip()
            evrakno = str(it.get("evrakno", "")).strip()
            tarih = str(it.get("tarih", "")).strip()
            kodkey = str(it.get("kodkey", "")).strip()
            kod = str(it.get("kod", "")).strip()
            notes = str(it.get("notes", "")).strip()
            orfiyat = str(it.get("orfiyat", "")).strip()
            priceunit = str(it.get("priceunit", "")).strip()
            ortutar = str(it.get("ortutar", "")).strip()
            sfmiktar = str(it.get("sfmiktar", "")).strip()
            sfsfunitkey = str(it.get("sfsfunitkey", "")).strip()
            sistembirimkey = str(it.get("sistembirimkey", "")).strip()
            sfsfunit = str(it.get("sfsfunit", "")).strip()
            sfstokmiktar = str(it.get("sfstokmiktar", "")).strip()
            rtestarih = str(it.get("rtestarih", "")).strip()

            if not satirkey:
                continue

            api_rows.append({
                "satirkey": satirkey,
                "evraknokey": evraknokey,
                "evrakno": evrakno,
                "tarih": tarih,
                "kodkey": kodkey,
                "kod": kod,
                "notes": notes,
                "orfiyat": orfiyat,
                "priceunit": priceunit,
                "ortutar": ortutar,
                "sfmiktar": sfmiktar,
                "sfsfunitkey": sfsfunitkey,
                "sistembirimkey": sistembirimkey,
                "sfsfunit": sfsfunit,
                "sfstokmiktar": sfstokmiktar,
                "rtestarih": rtestarih
            })
            api_keys.add(satirkey)

        # 3️⃣ Değişiklik kümelerini oluştur
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        inserted = 0

        # 4️⃣ Yeni kayıt ekleme
        for row in api_rows:
            if row["satirkey"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_STOK40T] 
                        ([ENT01], [ENT02], [EVRAKNO], [TARIH], [ENT03], [KOD],
                         [NOTES], [OR_FIYAT], [PRICEUNIT], [OR_TUTAR], [SF_MIKTAR],
                         [ENT04], [ENT05], [SF_SF_UNIT], [SF_STOK_MIKTAR], [RTESTARIH])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["satirkey"], row["evraknokey"], row["evrakno"], row["tarih"],
                    row["kodkey"], row["kod"], row["notes"], row["orfiyat"], row["priceunit"],
                    row["ortutar"], row["sfmiktar"], row["sfsfunitkey"], row["sistembirimkey"],
                    row["sfsfunit"], row["sfstokmiktar"], row["rtestarih"]
                ))
                inserted += 1

        # 5️⃣ Güncelleme
        for row in api_rows:
            if row["satirkey"] in to_update:
                cur.execute("""
                    UPDATE [KR_STOK40T]
                       SET [ENT02] = ?, [EVRAKNO] = ?, [TARIH] = ?, [ENT03] = ?, [KOD] = ?,
                           [NOTES] = ?, [OR_FIYAT] = ?, [PRICEUNIT] = ?, [OR_TUTAR] = ?, [SF_MIKTAR] = ?,
                           [ENT04] = ?, [ENT05] = ?, [SF_SF_UNIT] = ?, [SF_STOK_MIKTAR] = ?, [RTESTARIH] = ?
                     WHERE [ENT01] = ?
                """, (
                    row["evraknokey"], row["evrakno"], row["tarih"], row["kodkey"], row["kod"],
                    row["notes"], row["orfiyat"], row["priceunit"], row["ortutar"], row["sfmiktar"],
                    row["sfsfunitkey"], row["sistembirimkey"], row["sfsfunit"], row["sfstokmiktar"],
                    row["rtestarih"], row["satirkey"]
                ))

        # 6️⃣ Silme
        for key in to_delete:
            cur.execute("DELETE FROM [KR_STOK40T] WHERE [ENT01] = ?", (key,))

        # 7️⃣ Commit
        conn.commit()
        msg = (f"ENT-11 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-11 hata: {e}", 0)

    finally:
        try:
            conn.close()
        except Exception:
            pass


def ent12_update(rows: List[Dict]) -> Tuple[bool, str, int]:
    """
    KR_STOK00 tablosunu API'den gelen stok kart verileriyle senkronize eder.
    Alanlar: ENT01, KOD, AD, ENT02, ENT03, IUNIT
    """

    try:
        conn = pyodbc.connect(_load_conn_string(), autocommit=False, timeout=10)
    except Exception as e:
        return (False, f"Veritabanı bağlantı hatası: {e}", 0)

    try:
        cur = conn.cursor()

        # 1️⃣ Mevcut ENT01 kayıtlarını al
        cur.execute("SELECT [ENT01] FROM [KR_STOK00]")
        db_keys = set()
        for r in cur.fetchall():
            if r[0] is not None:
                db_keys.add(str(r[0]).strip())

        # 2️⃣ API verisini normalize et
        api_rows: List[Dict] = []
        api_keys = set()

        for it in rows or []:
            kodkey = str(it.get("kodkey", "")).strip()
            kod = str(it.get("kod", "")).strip()
            ad = str(it.get("ad", "")).strip()
            iunitstokkey = str(it.get("iunitstokkey", "")).strip()
            iunitsistemkey = str(it.get("iunitsistemkey", "")).strip()
            iunit = str(it.get("iunit", "")).strip()

            if not kodkey:
                continue

            api_rows.append({
                "kodkey": kodkey,
                "kod": kod,
                "ad": ad,
                "iunitstokkey": iunitstokkey,
                "iunitsistemkey": iunitsistemkey,
                "iunit": iunit
            })
            api_keys.add(kodkey)

        # 3️⃣ Fark kümelerini oluştur
        to_insert = api_keys - db_keys
        to_update = api_keys & db_keys
        to_delete = db_keys - api_keys

        inserted = 0

        # 4️⃣ Yeni kayıt ekleme
        for row in api_rows:
            if row["kodkey"] in to_insert:
                cur.execute("""
                    INSERT INTO [KR_STOK00]
                        ([ENT01], [KOD], [AD], [ENT02], [ENT03], [IUNIT])
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row["kodkey"], row["kod"], row["ad"],
                    row["iunitstokkey"], row["iunitsistemkey"], row["iunit"]
                ))
                inserted += 1

        # 5️⃣ Güncelleme
        for row in api_rows:
            if row["kodkey"] in to_update:
                cur.execute("""
                    UPDATE [KR_STOK00]
                       SET [KOD] = ?, [AD] = ?, [ENT02] = ?, [ENT03] = ?, [IUNIT] = ?
                     WHERE [ENT01] = ?
                """, (
                    row["kod"], row["ad"], row["iunitstokkey"],
                    row["iunitsistemkey"], row["iunit"], row["kodkey"]
                ))

        # 6️⃣ Silme
        for key in to_delete:
            cur.execute("DELETE FROM [KR_STOK00] WHERE [ENT01] = ?", (key,))

        # 7️⃣ Commit
        conn.commit()
        msg = (f"ENT-12 senkron tamamlandı: "
               f"eklenen {inserted}, güncellenen {len(to_update)}, silinen {len(to_delete)}.")
        return (True, msg, inserted)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return (False, f"ENT-12 hata: {e}", 0)

    finally:
        try:
            conn.close()
        except Exception:
            pass
