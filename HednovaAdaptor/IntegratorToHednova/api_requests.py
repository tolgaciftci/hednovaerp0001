import json
import base64
import requests
from typing import Dict, Any
from sql_crud import get_active_session

def login():
    """
    DİA WS API login isteğini gönderir.
    data.json dosyasındaki bilgileri kullanır.
    Her durumda {'code': <kod>, 'msg': <mesaj>} şeklinde döner.
    """
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"code": "999", "msg": "data.json dosyası bulunamadı."}

    # data.json içinden bilgileri çekiyoruz
    username = data["integrator"]["user"]
    password = data["integrator"]["password"]
    apikey = data["integrator"]["apikey"]

    ws_url = "https://kirpi.ws.dia.com.tr/api/v3/sis/json"

    payload = {
        "login": {
            "username": username,
            "password": password,
            "disconnect_same_user": "true",
            "lang": "tr",
            "params": {
                "apikey": apikey
            }
        }
    }

    headers = {
        "Content-Type": "application/json;charset=UTF-8"
    }

    try:
        response = requests.post(ws_url, json=payload, headers=headers)

        # Yanıt beklenen biçimde mi?
        try:
            result = response.json()
        except Exception:
            return {"code": "998", "msg": "API'den geçerli JSON dönmedi."}

        # code ve msg değerlerini döndür
        code = str(result.get("code", "0"))
        msg = str(result.get("msg", ""))

        # Log için ekrana basabiliriz
        print(f"🔹 API Yanıtı -> code: {code}, msg: {msg}")

        return {"code": code, "msg": msg}

    except Exception as e:
        return {"code": "997", "msg": f"İstek hatası: {e}"}


def _load_integrator_fp() -> Dict[str, Any]:
    """data.json içinden firma/dönem ve apikey vb. okur (gerekirse genişletilir)."""
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    company = str(data["integrator"]["company"]).strip()
    period  = str(data["integrator"]["period"]).strip()
    return {"company": company, "period": period}

def report_result_get(report_code: str, session_id: str = None) -> Dict[str, Any]:
    """
    DİA 'rpr_raporsonuc_getir' çağrısını yapar.
    Parametreler:
      - report_code: ör. "OZL-01"
      - session_id  : verilmezse DB'den get_active_session() ile alınır.
    Dönüş:
      { "code": <str>, "msg": <str>, "rows": <list> }
      code=="200" ise rows = çözümlenmiş JSON içindeki "__rows" listesi,
      aksi halde rows = [].
    """
    # 1) session id hazırlığı
    sid = (session_id or "").strip()
    if not sid:
        ok, sid_or_err = get_active_session()
        if not ok:
            return {"code": "995", "msg": sid_or_err, "rows": []}
        sid = sid_or_err

    # 2) firma/dönem
    fp = _load_integrator_fp()
    firma_kodu = fp["company"]
    donem_kodu = fp["period"]

    # 3) istek payload
    ws_url = "https://kirpi.ws.dia.com.tr/api/v3/rpr/json"
    payload = {
        "rpr_raporsonuc_getir": {
            "session_id": sid,
            "firma_kodu": int(firma_kodu) if firma_kodu.isdigit() else firma_kodu,
            "donem_kodu": int(donem_kodu) if donem_kodu.isdigit() else donem_kodu,
            "report_code": report_code,
            "param": {
                "firma": firma_kodu,
                "donem": donem_kodu
            },
            "format_type": "json"
        }
    }
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    # 4) çağrı
    try:
        resp = requests.post(ws_url, json=payload, headers=headers, timeout=30)
    except Exception as e:
        return {"code": "997", "msg": f"HTTP isteği hatası: {e}", "rows": []}

    # 5) JSON çöz
    try:
        data = resp.json()
    except Exception:
        return {"code": "996", "msg": "Geçersiz JSON yanıtı.", "rows": []}

    code = str(data.get("code", "0"))
    msg  = str(data.get("result") or data.get("msg") or "")

    # 6) code==200 ise base64 decode + json parse + __rows
    if code == "200":
        try:
            decoded = base64.b64decode(msg)
            text = decoded.decode("utf-8", errors="ignore")
            j = json.loads(text)
            rows = j.get("__rows", [])
            return {"code": code, "msg": "OK", "rows": rows}
        except Exception as e:
            return {"code": "996", "msg": f"Base64/JSON çözümleme hatası: {e}", "rows": []}
    else:
        # Başarısız: msg alanında hata mesajı olabilir
        return {"code": code, "msg": msg, "rows": []}