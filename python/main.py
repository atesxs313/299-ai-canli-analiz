import os
import json
import threading
import random
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, send_from_directory, Response, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or os.environ.get("SECRET_KEY", "gizli_anahtar_299ai_2024_super_secret_x7z")
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_NAME'] = 'session_299ai'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI_DOSYA = os.path.join(KLASOR, "api_veri.json")
DB_DOSYA = os.path.join(KLASOR, "veritabani.db")
UPLOAD_KLASOR = os.path.join(KLASOR, "uploads")
os.makedirs(UPLOAD_KLASOR, exist_ok=True)
IZINLI_UZANTILAR = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FOTO_BOYUT = 2 * 1024 * 1024

ROL_SIRASI = {"kurucu": 4, "admin": 3, "vip": 2, "kullanici": 1}
def rol_yetkili(gerekli_rol):
    mevcut = session.get("rol", "kullanici")
    return ROL_SIRASI.get(mevcut, 0) >= ROL_SIRASI.get(gerekli_rol, 99)

IST = timezone(timedelta(hours=3))

def ist_simdi():
    return datetime.now(IST)

def db_baglanti():
    conn = sqlite3.connect(DB_DOSYA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def db_kur():
    conn = db_baglanti()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            sifre_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'kullanici',
            kayit_tarihi TEXT NOT NULL,
            eposta_dogrulanmis INTEGER DEFAULT 0,
            profil_foto TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS chat_mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER,
            kullanici_adi TEXT NOT NULL,
            mesaj TEXT NOT NULL,
            cevap TEXT,
            cevaplayan TEXT,
            tarih TEXT NOT NULL,
            okundu INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS kuponlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            maclar TEXT NOT NULL,
            toplam_oran REAL NOT NULL,
            toplam_olasilik REAL NOT NULL,
            mac_sayisi INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            sonuc TEXT DEFAULT 'bekliyor',
            isim TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS dogrulama_kodlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            kod TEXT NOT NULL,
            tur TEXT NOT NULL,
            olusturma TEXT NOT NULL,
            kullanildi INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS market_urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            fiyat REAL NOT NULL,
            kategori TEXT DEFAULT 'Genel',
            resim TEXT DEFAULT '',
            aktif INTEGER DEFAULT 1,
            olusturma TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kullanici_bakiye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER UNIQUE NOT NULL,
            bakiye REAL DEFAULT 0,
            guncelleme TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bakiye_islemleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            miktar REAL NOT NULL,
            tur TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            tarih TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS shopier_odemeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            siparis_no TEXT NOT NULL,
            miktar REAL NOT NULL,
            durum TEXT DEFAULT 'bekliyor',
            tarih TEXT NOT NULL,
            shopier_data TEXT DEFAULT ''
        );
    """)
    # Migration: eski tablolara yeni kolonlar ekle
    for col, default in [("eposta_dogrulanmis", "0"), ("profil_foto", "''")]:
        try:
            conn.execute(f"ALTER TABLE kullanicilar ADD COLUMN {col} DEFAULT {default}")
        except:
            pass
    try:
        conn.execute("ALTER TABLE kuponlar ADD COLUMN sonuc TEXT DEFAULT 'bekliyor'")
    except:
        pass
    try:
        conn.execute("ALTER TABLE kuponlar ADD COLUMN isim TEXT DEFAULT ''")
    except:
        pass
    kurucu_sifre_hash = hashlib.sha256("admin".encode()).hexdigest()
    kurucu_var = conn.execute("SELECT id FROM kullanicilar WHERE rol='kurucu'").fetchone()
    if not kurucu_var:
        eski_admin = conn.execute("SELECT id FROM kullanicilar WHERE kullanici_adi='admin'").fetchone()
        if eski_admin:
            conn.execute("UPDATE kullanicilar SET rol='kurucu', sifre_hash=? WHERE id=?", (kurucu_sifre_hash, eski_admin["id"]))
        else:
            conn.execute(
                "INSERT OR IGNORE INTO kullanicilar (kullanici_adi, email, sifre_hash, rol, kayit_tarihi) VALUES (?, ?, ?, ?, ?)",
                ("admin", "admin@299ai.com", kurucu_sifre_hash, "kurucu", ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
            )
    conn.commit()
    conn.close()

db_kur()

def veri_taze_mi():
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        guncelleme = veri.get("guncelleme", "")
        if not guncelleme:
            return False
        son = datetime.strptime(guncelleme, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
        simdi = ist_simdi()
        fark = (simdi - son).total_seconds()
        if son.date() != simdi.date():
            return False
        return fark < 21600
    except:
        return False

def veriyi_yenile():
    from veri_bot import sistemi_guncelle
    sistemi_guncelle()

@app.before_request
def oturum_kalici():
    session.permanent = True

@app.route("/")
def index():
    return send_from_directory(KLASOR, "index.html")

@app.route("/admin")
def admin_sayfasi():
    if "kullanici_id" in session and session.get("rol") in ("admin", "kurucu"):
        return send_from_directory(KLASOR, "admin.html")
    if "kullanici_id" in session:
        return "<script>alert('Yetkiniz yok!');window.location.href='/';</script>"
    return send_from_directory(KLASOR, "admin.html")

@app.route("/uploads/<path:dosya>")
def upload_dosya(dosya):
    return send_from_directory(UPLOAD_KLASOR, dosya)

@app.route("/data/maclar")
def maclar():
    if not veri_taze_mi():
        try:
            veriyi_yenile()
        except:
            pass
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        resp = Response(
            json.dumps(veri, ensure_ascii=False),
            content_type="application/json; charset=utf-8"
        )
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp
    except FileNotFoundError:
        return jsonify({"guncelleme": "Veriler hazırlaniyor...", "maclar": []})
    except Exception as e:
        return jsonify({"guncelleme": "Hata", "maclar": [], "hata": str(e)}), 500

@app.route("/data/canli")
def canli_maclar():
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        maclar = veri.get("maclar", [])
        canli = [m for m in maclar if m.get("durum") == "canli"]
        resp = Response(
            json.dumps({
                "canliSayisi": len(canli),
                "canliGuncelleme": veri.get("canliGuncelleme", veri.get("guncelleme", "")),
                "maclar": canli
            }, ensure_ascii=False),
            content_type="application/json; charset=utf-8"
        )
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp
    except Exception as e:
        return jsonify({"canliSayisi": 0, "maclar": [], "hata": str(e)})

@app.route("/data/yenile", methods=["POST"])
def yenile():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    try:
        veriyi_yenile()
        return jsonify({"basarili": True, "mesaj": "Veriler guncellendi."})
    except Exception as e:
        return jsonify({"basarili": False, "mesaj": str(e)})

@app.route("/data/durum")
def durum():
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        return jsonify({
            "durum": "aktif",
            "guncelleme": veri.get("guncelleme"),
            "macSayisi": veri.get("macSayisi", 0)
        })
    except:
        return jsonify({"durum": "hazirlaniyor"})

@app.route("/data/kayit", methods=["POST"])
def kayit():
    data = request.get_json() or {}
    kullanici_adi = (data.get("kullanici_adi") or "").strip()
    email = (data.get("email") or "").strip().lower()
    sifre = (data.get("sifre") or "").strip()

    if not kullanici_adi or not email or not sifre:
        return jsonify({"basarili": False, "mesaj": "Tum alanlari doldurunuz."})
    if len(kullanici_adi) < 3:
        return jsonify({"basarili": False, "mesaj": "Kullanici adi en az 3 karakter olmali."})
    if len(sifre) < 8:
        return jsonify({"basarili": False, "mesaj": "Sifre en az 8 karakter olmali."})
    if "@" not in email or "." not in email:
        return jsonify({"basarili": False, "mesaj": "Gecerli bir email giriniz."})

    sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
    conn = None
    try:
        conn = db_baglanti()
        conn.execute(
            "INSERT INTO kullanicilar (kullanici_adi, email, sifre_hash, rol, kayit_tarihi) VALUES (?, ?, ?, ?, ?)",
            (kullanici_adi, email, sifre_hash, "kullanici", ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        user = conn.execute("SELECT * FROM kullanicilar WHERE kullanici_adi=?", (kullanici_adi,)).fetchone()
        conn.close()
        session["kullanici_id"] = user["id"]
        session["kullanici_adi"] = user["kullanici_adi"]
        session["rol"] = user["rol"]
        return jsonify({"basarili": True, "mesaj": "Kayit basarili!", "kullanici": {"id": user["id"], "kullanici_adi": user["kullanici_adi"], "rol": user["rol"]}})
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        return jsonify({"basarili": False, "mesaj": "Bu kullanici adi veya email zaten kayitli."})
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"basarili": False, "mesaj": f"Hata: {str(e)}"})

@app.route("/data/giris", methods=["POST"])
def giris():
    data = request.get_json() or {}
    kullanici_adi = (data.get("kullanici_adi") or "").strip()
    sifre = (data.get("sifre") or "").strip()

    if not kullanici_adi or not sifre:
        return jsonify({"basarili": False, "mesaj": "Kullanici adi ve sifre gerekli."})

    sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
    conn = db_baglanti()
    user = conn.execute("SELECT * FROM kullanicilar WHERE kullanici_adi=? AND sifre_hash=?", (kullanici_adi, sifre_hash)).fetchone()
    conn.close()

    if user:
        session["kullanici_id"] = user["id"]
        session["kullanici_adi"] = user["kullanici_adi"]
        session["rol"] = user["rol"]
        return jsonify({"basarili": True, "mesaj": "Giris basarili!", "kullanici": {"id": user["id"], "kullanici_adi": user["kullanici_adi"], "rol": user["rol"]}})
    else:
        return jsonify({"basarili": False, "mesaj": "Kullanici adi veya sifre hatali."})

@app.route("/data/cikis", methods=["POST"])
def cikis():
    session.clear()
    return jsonify({"basarili": True, "mesaj": "Cikis yapildi."})

def eposta_gonder(alici, konu, icerik):
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)
    if not smtp_host or not smtp_user or not smtp_pass:
        print(f"[EMAIL SIMULE] Alici: {alici}, Konu: {konu}, Icerik: {icerik}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = konu
        msg["From"] = smtp_from
        msg["To"] = alici
        html_part = MIMEText(icerik, "html", "utf-8")
        msg.attach(html_part)
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, alici, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL HATA] {e}")
        return False

def kod_uret():
    return str(random.randint(100000, 999999))

@app.route("/data/profil")
def profil():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False})
    conn = db_baglanti()
    user = conn.execute("SELECT id, kullanici_adi, email, rol, kayit_tarihi, eposta_dogrulanmis, profil_foto FROM kullanicilar WHERE id=?", (session["kullanici_id"],)).fetchone()
    conn.close()
    if not user:
        return jsonify({"basarili": False})
    return jsonify({
        "basarili": True,
        "kullanici": {
            "id": user["id"],
            "kullanici_adi": user["kullanici_adi"],
            "email": user["email"],
            "rol": user["rol"],
            "kayit_tarihi": user["kayit_tarihi"],
            "eposta_dogrulanmis": bool(user["eposta_dogrulanmis"]),
            "profil_foto": user["profil_foto"] or ""
        }
    })

@app.route("/data/profil_foto_yukle", methods=["POST"])
def profil_foto_yukle():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    if "foto" not in request.files:
        return jsonify({"basarili": False, "mesaj": "Dosya secilmedi."})
    foto = request.files["foto"]
    if not foto.filename:
        return jsonify({"basarili": False, "mesaj": "Dosya secilmedi."})
    uzanti = os.path.splitext(foto.filename)[1].lower()
    if uzanti not in IZINLI_UZANTILAR:
        return jsonify({"basarili": False, "mesaj": "Sadece JPG, PNG, GIF, WebP yuklenebilir."})
    foto.seek(0, 2)
    boyut = foto.tell()
    foto.seek(0)
    if boyut > MAX_FOTO_BOYUT:
        return jsonify({"basarili": False, "mesaj": "Dosya 2MB'den buyuk olamaz."})
    dosya_adi = f"profil_{session['kullanici_id']}_{secrets.token_hex(4)}{uzanti}"
    conn = db_baglanti()
    eski = conn.execute("SELECT profil_foto FROM kullanicilar WHERE id=?", (session["kullanici_id"],)).fetchone()
    if eski and eski["profil_foto"]:
        eski_dosya = os.path.join(UPLOAD_KLASOR, os.path.basename(eski["profil_foto"]))
        if os.path.exists(eski_dosya):
            os.remove(eski_dosya)
    foto.save(os.path.join(UPLOAD_KLASOR, dosya_adi))
    yol = f"/uploads/{dosya_adi}"
    conn.execute("UPDATE kullanicilar SET profil_foto=? WHERE id=?", (yol, session["kullanici_id"]))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Profil fotografi guncellendi!", "foto_url": yol})

@app.route("/data/sifre_degistir", methods=["POST"])
def sifre_degistir():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    eski = (data.get("eski_sifre") or "").strip()
    yeni = (data.get("yeni_sifre") or "").strip()
    if not eski or not yeni:
        return jsonify({"basarili": False, "mesaj": "Tum alanlari doldurunuz."})
    if len(yeni) < 8:
        return jsonify({"basarili": False, "mesaj": "Yeni sifre en az 8 karakter olmali."})
    eski_hash = hashlib.sha256(eski.encode()).hexdigest()
    conn = db_baglanti()
    user = conn.execute("SELECT id FROM kullanicilar WHERE id=? AND sifre_hash=?", (session["kullanici_id"], eski_hash)).fetchone()
    if not user:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Mevcut sifre yanlis."})
    yeni_hash = hashlib.sha256(yeni.encode()).hexdigest()
    conn.execute("UPDATE kullanicilar SET sifre_hash=? WHERE id=?", (yeni_hash, session["kullanici_id"]))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Sifre basariyla degistirildi!"})

@app.route("/data/eposta_dogrulama_gonder", methods=["POST"])
def eposta_dogrulama_gonder():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    conn = db_baglanti()
    user = conn.execute("SELECT email, eposta_dogrulanmis FROM kullanicilar WHERE id=?", (session["kullanici_id"],)).fetchone()
    if not user:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kullanici bulunamadi."})
    if user["eposta_dogrulanmis"]:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "E-posta zaten dogrulanmis."})
    son_kod = conn.execute(
        "SELECT olusturma FROM dogrulama_kodlari WHERE email=? AND tur='eposta' AND kullanildi=0 ORDER BY id DESC LIMIT 1",
        (user["email"],)
    ).fetchone()
    if son_kod:
        son_zaman = datetime.strptime(son_kod["olusturma"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
        if (ist_simdi() - son_zaman).total_seconds() < 60:
            conn.close()
            return jsonify({"basarili": False, "mesaj": "Lutfen 1 dakika bekleyin."})
    kod = kod_uret()
    conn.execute("UPDATE dogrulama_kodlari SET kullanildi=1 WHERE email=? AND tur='eposta' AND kullanildi=0", (user["email"],))
    conn.execute(
        "INSERT INTO dogrulama_kodlari (email, kod, tur, olusturma) VALUES (?, ?, ?, ?)",
        (user["email"], kod, "eposta", ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    html = f"""
    <div style="font-family:Arial;max-width:400px;margin:auto;padding:20px;border:1px solid #ddd;border-radius:12px;">
        <h2 style="color:#ffc107;text-align:center;">299+ Ai</h2>
        <p>E-posta dogrulama kodunuz:</p>
        <div style="text-align:center;font-size:32px;font-weight:bold;color:#007bff;padding:20px;background:#f8f9fa;border-radius:8px;letter-spacing:8px;">{kod}</div>
        <p style="font-size:12px;color:#888;margin-top:15px;">Bu kod 10 dakika gecerlidir.</p>
    </div>
    """
    eposta_gonder(user["email"], "299+ Ai - E-posta Dogrulama Kodu", html)
    return jsonify({"basarili": True, "mesaj": "Dogrulama kodu e-posta adresinize gonderildi."})

kod_deneme_sayaci = {}

@app.route("/data/eposta_dogrula", methods=["POST"])
def eposta_dogrula():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    girilen_kod = (data.get("kod") or "").strip()
    if not girilen_kod:
        return jsonify({"basarili": False, "mesaj": "Kod gerekli."})
    anahtar = f"eposta_{session['kullanici_id']}"
    sayac = kod_deneme_sayaci.get(anahtar, {"sayi": 0, "zaman": ist_simdi()})
    if (ist_simdi() - sayac["zaman"]).total_seconds() > 600:
        sayac = {"sayi": 0, "zaman": ist_simdi()}
    if sayac["sayi"] >= 5:
        return jsonify({"basarili": False, "mesaj": "Cok fazla deneme. 10 dakika bekleyin."})
    conn = db_baglanti()
    user = conn.execute("SELECT email FROM kullanicilar WHERE id=?", (session["kullanici_id"],)).fetchone()
    if not user:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kullanici bulunamadi."})
    kayit = conn.execute(
        "SELECT id, kod, olusturma FROM dogrulama_kodlari WHERE email=? AND tur='eposta' AND kullanildi=0 ORDER BY id DESC LIMIT 1",
        (user["email"],)
    ).fetchone()
    if not kayit:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Gecerli dogrulama kodu bulunamadi. Yeni kod gonderin."})
    olusturma = datetime.strptime(kayit["olusturma"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    if (ist_simdi() - olusturma).total_seconds() > 600:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kodun suresi dolmus. Yeni kod gonderin."})
    if kayit["kod"] != girilen_kod:
        sayac["sayi"] += 1
        kod_deneme_sayaci[anahtar] = sayac
        conn.close()
        return jsonify({"basarili": False, "mesaj": f"Yanlis kod. ({5-sayac['sayi']} hak kaldi)"})
    conn.execute("UPDATE kullanicilar SET eposta_dogrulanmis=1 WHERE id=?", (session["kullanici_id"],))
    conn.execute("UPDATE dogrulama_kodlari SET kullanildi=1 WHERE email=? AND tur='eposta'", (user["email"],))
    conn.commit()
    conn.close()
    kod_deneme_sayaci.pop(anahtar, None)
    return jsonify({"basarili": True, "mesaj": "E-posta basariyla dogrulandi!"})

@app.route("/data/sifre_sifirlama_gonder", methods=["POST"])
def sifre_sifirlama_gonder():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"basarili": False, "mesaj": "Gecerli bir e-posta adresi giriniz."})
    conn = db_baglanti()
    user = conn.execute("SELECT id, email FROM kullanicilar WHERE email=?", (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"basarili": True, "mesaj": "Eger bu e-posta kayitliysa kod gonderildi."})
    son_kod = conn.execute(
        "SELECT olusturma FROM dogrulama_kodlari WHERE email=? AND tur='sifre' AND kullanildi=0 ORDER BY id DESC LIMIT 1",
        (email,)
    ).fetchone()
    if son_kod:
        son_zaman = datetime.strptime(son_kod["olusturma"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
        if (ist_simdi() - son_zaman).total_seconds() < 60:
            conn.close()
            return jsonify({"basarili": False, "mesaj": "Lutfen 1 dakika bekleyin."})
    kod = kod_uret()
    conn.execute("UPDATE dogrulama_kodlari SET kullanildi=1 WHERE email=? AND tur='sifre' AND kullanildi=0", (email,))
    conn.execute(
        "INSERT INTO dogrulama_kodlari (email, kod, tur, olusturma) VALUES (?, ?, ?, ?)",
        (email, kod, "sifre", ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    html = f"""
    <div style="font-family:Arial;max-width:400px;margin:auto;padding:20px;border:1px solid #ddd;border-radius:12px;">
        <h2 style="color:#ffc107;text-align:center;">299+ Ai</h2>
        <p>Sifre sifirlama kodunuz:</p>
        <div style="text-align:center;font-size:32px;font-weight:bold;color:#dc3545;padding:20px;background:#f8f9fa;border-radius:8px;letter-spacing:8px;">{kod}</div>
        <p style="font-size:12px;color:#888;margin-top:15px;">Bu kod 10 dakika gecerlidir. Siz talep etmediyseniz bu emaili gormezden gelin.</p>
    </div>
    """
    eposta_gonder(email, "299+ Ai - Sifre Sifirlama Kodu", html)
    return jsonify({"basarili": True, "mesaj": "Sifirlama kodu e-posta adresinize gonderildi."})

@app.route("/data/sifre_sifirla", methods=["POST"])
def sifre_sifirla():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    girilen_kod = (data.get("kod") or "").strip()
    yeni_sifre = (data.get("yeni_sifre") or "").strip()
    if not email or not girilen_kod or not yeni_sifre:
        return jsonify({"basarili": False, "mesaj": "Tum alanlari doldurunuz."})
    if len(yeni_sifre) < 8:
        return jsonify({"basarili": False, "mesaj": "Sifre en az 8 karakter olmali."})
    anahtar = f"sifre_{email}"
    sayac = kod_deneme_sayaci.get(anahtar, {"sayi": 0, "zaman": ist_simdi()})
    if (ist_simdi() - sayac["zaman"]).total_seconds() > 600:
        sayac = {"sayi": 0, "zaman": ist_simdi()}
    if sayac["sayi"] >= 5:
        return jsonify({"basarili": False, "mesaj": "Cok fazla deneme. 10 dakika bekleyin."})
    conn = db_baglanti()
    kayit = conn.execute(
        "SELECT id, kod, olusturma FROM dogrulama_kodlari WHERE email=? AND tur='sifre' AND kullanildi=0 ORDER BY id DESC LIMIT 1",
        (email,)
    ).fetchone()
    if not kayit:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Gecerli sifirlama kodu bulunamadi."})
    olusturma = datetime.strptime(kayit["olusturma"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    if (ist_simdi() - olusturma).total_seconds() > 600:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kodun suresi dolmus. Yeni kod gonderin."})
    if kayit["kod"] != girilen_kod:
        sayac["sayi"] += 1
        kod_deneme_sayaci[anahtar] = sayac
        conn.close()
        return jsonify({"basarili": False, "mesaj": f"Yanlis kod. ({5-sayac['sayi']} hak kaldi)"})
    yeni_hash = hashlib.sha256(yeni_sifre.encode()).hexdigest()
    conn.execute("UPDATE kullanicilar SET sifre_hash=? WHERE email=?", (yeni_hash, email))
    conn.execute("UPDATE dogrulama_kodlari SET kullanildi=1 WHERE email=? AND tur='sifre'", (email,))
    conn.commit()
    conn.close()
    kod_deneme_sayaci.pop(anahtar, None)
    return jsonify({"basarili": True, "mesaj": "Sifre basariyla degistirildi! Giris yapabilirsiniz."})

@app.route("/data/kupon_kaydet", methods=["POST"])
def kupon_kaydet():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    maclar = data.get("maclar", [])
    toplam_oran = data.get("toplam_oran", 1.0)
    toplam_olasilik = data.get("toplam_olasilik", 0)
    isim = (data.get("isim") or "").strip()
    if not maclar:
        return jsonify({"basarili": False, "mesaj": "Kupon bos."})
    conn = db_baglanti()
    conn.execute("DELETE FROM kuponlar WHERE tarih < datetime('now', '-30 days')")
    conn.execute(
        "INSERT INTO kuponlar (kullanici_id, maclar, toplam_oran, toplam_olasilik, mac_sayisi, tarih, isim) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session["kullanici_id"], json.dumps(maclar, ensure_ascii=False), toplam_oran, toplam_olasilik, len(maclar), ist_simdi().strftime("%Y-%m-%d %H:%M:%S"), isim)
    )
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Kupon kaydedildi!"})

@app.route("/data/kuponlarim")
def kuponlarim():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "kuponlar": []})
    conn = db_baglanti()
    conn.execute("DELETE FROM kuponlar WHERE tarih < datetime('now', '-30 days')")
    conn.commit()
    kuponlar = conn.execute(
        "SELECT id, maclar, toplam_oran, toplam_olasilik, mac_sayisi, tarih, COALESCE(sonuc,'bekliyor') as sonuc, COALESCE(isim,'') as isim FROM kuponlar WHERE kullanici_id=? ORDER BY id DESC",
        (session["kullanici_id"],)
    ).fetchall()
    conn.close()
    sonuc = []
    for k in kuponlar:
        sonuc.append({
            "id": k["id"],
            "maclar": json.loads(k["maclar"]),
            "toplam_oran": k["toplam_oran"],
            "toplam_olasilik": k["toplam_olasilik"],
            "mac_sayisi": k["mac_sayisi"],
            "tarih": k["tarih"],
            "sonuc": k["sonuc"],
            "isim": k["isim"]
        })
    return jsonify({"basarili": True, "kuponlar": sonuc})

@app.route("/data/kupon_sil", methods=["POST"])
def kupon_sil():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    kid = data.get("id")
    if not kid:
        return jsonify({"basarili": False, "mesaj": "Kupon ID gerekli."})
    conn = db_baglanti()
    conn.execute("DELETE FROM kuponlar WHERE id=? AND kullanici_id=?", (kid, session["kullanici_id"]))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Kupon silindi."})

@app.route("/data/oturum")
def oturum():
    if "kullanici_id" in session:
        conn = db_baglanti()
        user = conn.execute("SELECT eposta_dogrulanmis, profil_foto, rol FROM kullanicilar WHERE id=?", (session["kullanici_id"],)).fetchone()
        conn.close()
        ed = bool(user["eposta_dogrulanmis"]) if user else False
        foto = (user["profil_foto"] or "") if user else ""
        gercek_rol = user["rol"] if user else session.get("rol", "kullanici")
        session["rol"] = gercek_rol
        return jsonify({"girisYapildi": True, "kullanici": {"id": session["kullanici_id"], "kullanici_adi": session["kullanici_adi"], "rol": gercek_rol, "eposta_dogrulanmis": ed, "profil_foto": foto}})
    return jsonify({"girisYapildi": False})

@app.route("/data/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    mesaj = (data.get("mesaj") or "").strip()
    kullanici_adi = session.get("kullanici_adi", "Misafir")
    kullanici_id = session.get("kullanici_id")

    conn = db_baglanti()
    conn.execute(
        "INSERT INTO chat_mesajlar (kullanici_id, kullanici_adi, mesaj, tarih) VALUES (?, ?, ?, ?)",
        (kullanici_id, kullanici_adi, mesaj, ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    cevap = bot_cevap(mesaj)
    return jsonify({"cevap": cevap})

@app.route("/data/chat/gecmis")
def chat_gecmis():
    kullanici_id = session.get("kullanici_id")
    if not kullanici_id:
        return jsonify({"mesajlar": []})
    conn = db_baglanti()
    mesajlar = conn.execute(
        "SELECT mesaj, cevap, cevaplayan, tarih FROM chat_mesajlar WHERE kullanici_id=? ORDER BY id DESC LIMIT 50",
        (kullanici_id,)
    ).fetchall()
    conn.close()
    return jsonify({"mesajlar": [dict(m) for m in reversed(mesajlar)]})

# ==================== BAKIYE ====================

@app.route("/data/bakiye")
def bakiye():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "bakiye": 0})
    conn = db_baglanti()
    row = conn.execute("SELECT bakiye FROM kullanici_bakiye WHERE kullanici_id=?", (session["kullanici_id"],)).fetchone()
    islemler = conn.execute(
        "SELECT miktar, tur, aciklama, tarih FROM bakiye_islemleri WHERE kullanici_id=? ORDER BY id DESC LIMIT 20",
        (session["kullanici_id"],)
    ).fetchall()
    conn.close()
    return jsonify({
        "basarili": True,
        "bakiye": row["bakiye"] if row else 0,
        "islemler": [dict(i) for i in islemler]
    })

# ==================== MARKET ====================

@app.route("/data/market/urunler")
def market_urunler():
    conn = db_baglanti()
    urunler = conn.execute("SELECT id, isim, aciklama, fiyat, kategori, resim FROM market_urunler WHERE aktif=1 ORDER BY kategori, fiyat").fetchall()
    conn.close()
    return jsonify({"basarili": True, "urunler": [dict(u) for u in urunler]})

@app.route("/data/market/satin_al", methods=["POST"])
def market_satin_al():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    urun_id = data.get("urun_id")
    if not urun_id:
        return jsonify({"basarili": False, "mesaj": "Urun secilmedi."})
    conn = db_baglanti()
    urun = conn.execute("SELECT * FROM market_urunler WHERE id=? AND aktif=1", (urun_id,)).fetchone()
    if not urun:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Urun bulunamadi."})
    bakiye_row = conn.execute("SELECT bakiye FROM kullanici_bakiye WHERE kullanici_id=?", (session["kullanici_id"],)).fetchone()
    bakiye = bakiye_row["bakiye"] if bakiye_row else 0
    if bakiye < urun["fiyat"]:
        conn.close()
        return jsonify({"basarili": False, "mesaj": f"Yetersiz bakiye. Bakiyeniz: {bakiye:.2f} TL, Urun fiyati: {urun['fiyat']:.2f} TL"})
    yeni_bakiye = bakiye - urun["fiyat"]
    if bakiye_row:
        conn.execute("UPDATE kullanici_bakiye SET bakiye=?, guncelleme=? WHERE kullanici_id=?",
                     (yeni_bakiye, ist_simdi().strftime("%Y-%m-%d %H:%M:%S"), session["kullanici_id"]))
    else:
        conn.execute("INSERT INTO kullanici_bakiye (kullanici_id, bakiye, guncelleme) VALUES (?, ?, ?)",
                     (session["kullanici_id"], yeni_bakiye, ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("INSERT INTO bakiye_islemleri (kullanici_id, miktar, tur, aciklama, tarih) VALUES (?, ?, ?, ?, ?)",
                 (session["kullanici_id"], -urun["fiyat"], "satin_al", f"Satin alindi: {urun['isim']}", ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": f"'{urun['isim']}' basariyla satin alindi!", "yeni_bakiye": yeni_bakiye})

# ==================== SHOPIER ====================

@app.route("/data/shopier/odeme_baslat", methods=["POST"])
def shopier_odeme_baslat():
    if "kullanici_id" not in session:
        return jsonify({"basarili": False, "mesaj": "Giris yapmaniz gerekiyor."})
    data = request.get_json() or {}
    miktar = data.get("miktar", 0)
    if not miktar or float(miktar) <= 0:
        return jsonify({"basarili": False, "mesaj": "Gecersiz miktar."})
    # Shopier API entegrasyonu - API anahtari gelince eklenecek
    siparis_no = f"299AI-{session['kullanici_id']}-{secrets.token_hex(4).upper()}"
    conn = db_baglanti()
    conn.execute(
        "INSERT INTO shopier_odemeler (kullanici_id, siparis_no, miktar, durum, tarih) VALUES (?, ?, ?, ?, ?)",
        (session["kullanici_id"], siparis_no, float(miktar), "bekliyor", ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    # TODO: Shopier API ile odeme linki olustur
    return jsonify({
        "basarili": True,
        "mesaj": "Odeme sistemi yakin zamanda aktif olacak.",
        "siparis_no": siparis_no,
        "durum": "yakin_zamanda"
    })

@app.route("/data/shopier/webhook", methods=["POST"])
def shopier_webhook():
    # TODO: Shopier webhook dogrulamasi
    data = request.get_json() or {}
    siparis_no = data.get("siparis_no", "")
    durum = data.get("durum", "")
    conn = db_baglanti()
    odeme = conn.execute("SELECT * FROM shopier_odemeler WHERE siparis_no=?", (siparis_no,)).fetchone()
    if odeme and durum == "odendi":
        conn.execute("UPDATE shopier_odemeler SET durum='odendi', shopier_data=? WHERE siparis_no=?",
                     (json.dumps(data), siparis_no))
        bakiye_row = conn.execute("SELECT bakiye FROM kullanici_bakiye WHERE kullanici_id=?", (odeme["kullanici_id"],)).fetchone()
        mevcut = bakiye_row["bakiye"] if bakiye_row else 0
        yeni = mevcut + odeme["miktar"]
        if bakiye_row:
            conn.execute("UPDATE kullanici_bakiye SET bakiye=?, guncelleme=? WHERE kullanici_id=?",
                         (yeni, ist_simdi().strftime("%Y-%m-%d %H:%M:%S"), odeme["kullanici_id"]))
        else:
            conn.execute("INSERT INTO kullanici_bakiye (kullanici_id, bakiye, guncelleme) VALUES (?, ?, ?)",
                         (odeme["kullanici_id"], yeni, ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
        conn.execute("INSERT INTO bakiye_islemleri (kullanici_id, miktar, tur, aciklama, tarih) VALUES (?, ?, ?, ?, ?)",
                     (odeme["kullanici_id"], odeme["miktar"], "yukle", f"Shopier odeme: {siparis_no}", ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()
    return jsonify({"basarili": True})

# ==================== ADMIN ====================

@app.route("/data/admin/kuponlar")
def admin_kuponlar():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    kuponlar = conn.execute(
        """SELECT k.id, k.kullanici_id, k.maclar, k.toplam_oran, k.toplam_olasilik,
                  k.mac_sayisi, k.tarih, COALESCE(k.sonuc,'bekliyor') as sonuc,
                  COALESCE(k.isim,'') as isim, u.kullanici_adi
           FROM kuponlar k
           LEFT JOIN kullanicilar u ON u.id = k.kullanici_id
           ORDER BY k.id DESC LIMIT 200"""
    ).fetchall()
    conn.close()
    sonuc_liste = []
    for k in kuponlar:
        sonuc_liste.append({
            "id": k["id"],
            "kullanici_adi": k["kullanici_adi"] or "?",
            "mac_sayisi": k["mac_sayisi"],
            "toplam_oran": k["toplam_oran"],
            "toplam_olasilik": k["toplam_olasilik"],
            "tarih": k["tarih"],
            "sonuc": k["sonuc"],
            "isim": k["isim"],
            "maclar": json.loads(k["maclar"])
        })
    return jsonify({"basarili": True, "kuponlar": sonuc_liste})

@app.route("/data/admin/kupon_sonuc", methods=["POST"])
def admin_kupon_sonuc():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    kid = data.get("id")
    yeni_sonuc = data.get("sonuc")
    if not kid or yeni_sonuc not in ("kazandi", "kaybetti", "bekliyor"):
        return jsonify({"basarili": False, "mesaj": "Gecersiz veri."})
    conn = db_baglanti()
    conn.execute("UPDATE kuponlar SET sonuc=? WHERE id=?", (yeni_sonuc, kid))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Kupon sonucu guncellendi."})

@app.route("/data/admin/mesajlar")
def admin_mesajlar():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    mesajlar = conn.execute("""
        SELECT cm.id, cm.kullanici_id, cm.kullanici_adi, cm.mesaj, cm.cevap, cm.cevaplayan, cm.tarih, cm.okundu
        FROM chat_mesajlar cm ORDER BY cm.id DESC LIMIT 200
    """).fetchall()
    conn.close()
    return jsonify({"mesajlar": [dict(m) for m in mesajlar]})

@app.route("/data/admin/cevapla", methods=["POST"])
def admin_cevapla():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    mesaj_id = data.get("mesaj_id")
    cevap = (data.get("cevap") or "").strip()
    if not mesaj_id or not cevap:
        return jsonify({"basarili": False, "mesaj": "Mesaj ID ve cevap gerekli."})
    conn = db_baglanti()
    conn.execute(
        "UPDATE chat_mesajlar SET cevap=?, cevaplayan=?, okundu=1 WHERE id=?",
        (cevap, session.get("kullanici_adi", "Admin"), mesaj_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Cevap gonderildi."})

@app.route("/data/admin/kullanicilar")
def admin_kullanicilar():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    kullanicilar = conn.execute("SELECT id, kullanici_adi, email, rol, kayit_tarihi, eposta_dogrulanmis FROM kullanicilar ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"kullanicilar": [dict(k) for k in kullanicilar], "benim_rolum": session.get("rol", "kullanici")})

@app.route("/data/admin/kullanici_sil", methods=["POST"])
def admin_kullanici_sil():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    kid = data.get("id")
    if not kid:
        return jsonify({"basarili": False, "mesaj": "Kullanici ID gerekli."})
    conn = db_baglanti()
    user = conn.execute("SELECT rol FROM kullanicilar WHERE id=?", (kid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kullanici bulunamadi."})
    benim_rol = session.get("rol", "kullanici")
    hedef_rol = user["rol"]
    if hedef_rol == "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kurucu silinemez."})
    if hedef_rol == "admin" and benim_rol != "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Sadece kurucu adminleri silebilir."})
    conn.execute("DELETE FROM kullanicilar WHERE id=?", (kid,))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Kullanici silindi."})

@app.route("/data/admin/kullanici_rol", methods=["POST"])
def admin_kullanici_rol():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    kid = data.get("id")
    yeni_rol = data.get("rol", "kullanici")
    if not kid:
        return jsonify({"basarili": False, "mesaj": "Kullanici ID gerekli."})
    benim_rol = session.get("rol", "kullanici")
    gecerli_roller = ["kullanici", "vip", "admin", "kurucu"]
    if yeni_rol not in gecerli_roller:
        return jsonify({"basarili": False, "mesaj": "Gecersiz rol."})
    conn = db_baglanti()
    hedef = conn.execute("SELECT rol FROM kullanicilar WHERE id=?", (kid,)).fetchone()
    if not hedef:
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kullanici bulunamadi."})
    if hedef["rol"] == "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kurucu rolu degistirilemez."})
    if yeni_rol == "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Kurucu rolu atanamaz."})
    if yeni_rol == "admin" and benim_rol != "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Sadece kurucu admin atayabilir."})
    if hedef["rol"] == "admin" and benim_rol != "kurucu":
        conn.close()
        return jsonify({"basarili": False, "mesaj": "Sadece kurucu admin rolunu degistirebilir."})
    conn.execute("UPDATE kullanicilar SET rol=? WHERE id=?", (yeni_rol, kid))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Rol guncellendi."})

@app.route("/data/admin/mesaj_sil", methods=["POST"])
def admin_mesaj_sil():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    mid = data.get("id")
    if not mid:
        return jsonify({"basarili": False, "mesaj": "Mesaj ID gerekli."})
    conn = db_baglanti()
    conn.execute("DELETE FROM chat_mesajlar WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Mesaj silindi."})

@app.route("/data/admin/tum_mesajlari_sil", methods=["POST"])
def admin_tum_mesajlari_sil():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    conn.execute("DELETE FROM chat_mesajlar")
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Tum mesajlar silindi."})

@app.route("/data/admin/istatistik")
def admin_istatistik():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    toplam_kullanici = conn.execute("SELECT COUNT(*) FROM kullanicilar").fetchone()[0]
    toplam_mesaj = conn.execute("SELECT COUNT(*) FROM chat_mesajlar").fetchone()[0]
    cevaplanmamis = conn.execute("SELECT COUNT(*) FROM chat_mesajlar WHERE cevap IS NULL").fetchone()[0]
    bugun = ist_simdi().strftime("%Y-%m-%d")
    bugun_kayit = conn.execute("SELECT COUNT(*) FROM kullanicilar WHERE kayit_tarihi LIKE ?", (bugun + "%",)).fetchone()[0]
    bugun_mesaj = conn.execute("SELECT COUNT(*) FROM chat_mesajlar WHERE tarih LIKE ?", (bugun + "%",)).fetchone()[0]
    son_kullanicilar = [dict(k) for k in conn.execute("SELECT kullanici_adi, kayit_tarihi FROM kullanicilar ORDER BY id DESC LIMIT 5").fetchall()]
    toplam_kupon = conn.execute("SELECT COUNT(*) FROM kuponlar").fetchone()[0]
    kazanan_kupon = conn.execute("SELECT COUNT(*) FROM kuponlar WHERE sonuc='kazandi'").fetchone()[0]
    kaybeden_kupon = conn.execute("SELECT COUNT(*) FROM kuponlar WHERE sonuc='kaybetti'").fetchone()[0]
    bekleyen_kupon = conn.execute("SELECT COUNT(*) FROM kuponlar WHERE COALESCE(sonuc,'bekliyor')='bekliyor'").fetchone()[0]
    toplam_urun = conn.execute("SELECT COUNT(*) FROM market_urunler WHERE aktif=1").fetchone()[0]
    toplam_bakiye = conn.execute("SELECT COALESCE(SUM(bakiye),0) FROM kullanici_bakiye").fetchone()[0]
    toplam_satin_al = conn.execute("SELECT COUNT(*) FROM bakiye_islemleri WHERE tur='satin_al'").fetchone()[0]
    conn.close()

    mac_sayisi = 0
    son_guncelleme = "-"
    spor_dagilimi = {}
    lig_sayisi = 0
    tarih_dagilimi = {}
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        mac_sayisi = veri.get("macSayisi", 0)
        son_guncelleme = veri.get("guncelleme", "-")
        maclar = veri.get("maclar", [])
        for m in maclar:
            spor = m.get("spor", "Diger")
            spor_dagilimi[spor] = spor_dagilimi.get(spor, 0) + 1
            tarih = m.get("tarih", "")
            if tarih:
                tarih_dagilimi[tarih] = tarih_dagilimi.get(tarih, 0) + 1
        ligler = set(m.get("lig", "") for m in maclar if m.get("lig"))
        lig_sayisi = len(ligler)
    except:
        pass

    return jsonify({
        "toplam_kullanici": toplam_kullanici,
        "toplam_mesaj": toplam_mesaj,
        "cevaplanmamis": cevaplanmamis,
        "mac_sayisi": mac_sayisi,
        "son_guncelleme": son_guncelleme,
        "bugun_kayit": bugun_kayit,
        "bugun_mesaj": bugun_mesaj,
        "spor_dagilimi": spor_dagilimi,
        "lig_sayisi": lig_sayisi,
        "tarih_dagilimi": tarih_dagilimi,
        "son_kullanicilar": son_kullanicilar,
        "toplam_kupon": toplam_kupon,
        "kazanan_kupon": kazanan_kupon,
        "kaybeden_kupon": kaybeden_kupon,
        "bekleyen_kupon": bekleyen_kupon,
        "toplam_urun": toplam_urun,
        "toplam_bakiye": round(toplam_bakiye, 2),
        "toplam_satin_al": toplam_satin_al
    })

@app.route("/data/admin/mac_detay")
def admin_mac_detay():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    try:
        with open(VERI_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        maclar = veri.get("maclar", [])
        lig_mac = {}
        for m in maclar:
            lig = m.get("lig", "Diger")
            if lig not in lig_mac:
                lig_mac[lig] = {"toplam": 0, "spor": m.get("spor", ""), "maclar": []}
            lig_mac[lig]["toplam"] += 1
            ai = m.get("aiIhtimaller", {})
            en_yuksek = max(ai.values()) if ai else 0
            lig_mac[lig]["maclar"].append({
                "ev": m.get("evSahibi", ""),
                "dep": m.get("deplasman", ""),
                "tarih": m.get("tarih", ""),
                "saat": m.get("saat", ""),
                "ai_max": en_yuksek
            })
        return jsonify({"basarili": True, "lig_mac": lig_mac, "kaynak": veri.get("kaynak", "")})
    except:
        return jsonify({"basarili": True, "lig_mac": {}, "kaynak": ""})

# ==================== ADMIN MARKET ====================

@app.route("/data/admin/market/urunler")
def admin_market_urunler():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    urunler = conn.execute("SELECT * FROM market_urunler ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"basarili": True, "urunler": [dict(u) for u in urunler]})

@app.route("/data/admin/market/urun_ekle", methods=["POST"])
def admin_market_urun_ekle():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    isim = (data.get("isim") or "").strip()
    aciklama = (data.get("aciklama") or "").strip()
    fiyat = data.get("fiyat", 0)
    kategori = (data.get("kategori") or "Genel").strip()
    resim = (data.get("resim") or "").strip()
    if not isim or not fiyat:
        return jsonify({"basarili": False, "mesaj": "Urun adi ve fiyati gerekli."})
    conn = db_baglanti()
    conn.execute(
        "INSERT INTO market_urunler (isim, aciklama, fiyat, kategori, resim, aktif, olusturma) VALUES (?, ?, ?, ?, ?, 1, ?)",
        (isim, aciklama, float(fiyat), kategori, resim, ist_simdi().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Urun eklendi."})

@app.route("/data/admin/market/urun_guncelle", methods=["POST"])
def admin_market_urun_guncelle():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    uid = data.get("id")
    isim = (data.get("isim") or "").strip()
    aciklama = (data.get("aciklama") or "").strip()
    fiyat = data.get("fiyat", 0)
    kategori = (data.get("kategori") or "Genel").strip()
    resim = (data.get("resim") or "").strip()
    aktif = 1 if data.get("aktif", True) else 0
    if not uid or not isim:
        return jsonify({"basarili": False, "mesaj": "Eksik veri."})
    conn = db_baglanti()
    conn.execute(
        "UPDATE market_urunler SET isim=?, aciklama=?, fiyat=?, kategori=?, resim=?, aktif=? WHERE id=?",
        (isim, aciklama, float(fiyat), kategori, resim, aktif, uid)
    )
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Urun guncellendi."})

@app.route("/data/admin/market/urun_sil", methods=["POST"])
def admin_market_urun_sil():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    uid = data.get("id")
    if not uid:
        return jsonify({"basarili": False, "mesaj": "Urun ID gerekli."})
    conn = db_baglanti()
    conn.execute("DELETE FROM market_urunler WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": "Urun silindi."})

@app.route("/data/admin/bakiye_ekle", methods=["POST"])
def admin_bakiye_ekle():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    data = request.get_json() or {}
    kullanici_id = data.get("kullanici_id")
    miktar = data.get("miktar", 0)
    aciklama = (data.get("aciklama") or "Admin tarafindan eklendi").strip()
    if not kullanici_id or float(miktar) == 0:
        return jsonify({"basarili": False, "mesaj": "Kullanici ve miktar gerekli."})
    conn = db_baglanti()
    row = conn.execute("SELECT bakiye FROM kullanici_bakiye WHERE kullanici_id=?", (kullanici_id,)).fetchone()
    mevcut = row["bakiye"] if row else 0
    yeni = mevcut + float(miktar)
    if row:
        conn.execute("UPDATE kullanici_bakiye SET bakiye=?, guncelleme=? WHERE kullanici_id=?",
                     (yeni, ist_simdi().strftime("%Y-%m-%d %H:%M:%S"), kullanici_id))
    else:
        conn.execute("INSERT INTO kullanici_bakiye (kullanici_id, bakiye, guncelleme) VALUES (?, ?, ?)",
                     (kullanici_id, yeni, ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("INSERT INTO bakiye_islemleri (kullanici_id, miktar, tur, aciklama, tarih) VALUES (?, ?, ?, ?, ?)",
                 (kullanici_id, float(miktar), "admin_ekle", aciklama, ist_simdi().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return jsonify({"basarili": True, "mesaj": f"Bakiye guncellendi. Yeni bakiye: {yeni:.2f} TL"})

@app.route("/data/admin/bakiye_listesi")
def admin_bakiye_listesi():
    if not rol_yetkili("admin"):
        return jsonify({"basarili": False, "mesaj": "Yetkiniz yok."}), 403
    conn = db_baglanti()
    rows = conn.execute("""
        SELECT kb.kullanici_id, u.kullanici_adi, kb.bakiye, kb.guncelleme
        FROM kullanici_bakiye kb
        LEFT JOIN kullanicilar u ON u.id = kb.kullanici_id
        ORDER BY kb.bakiye DESC
    """).fetchall()
    islemler = conn.execute("""
        SELECT bi.id, bi.kullanici_id, u.kullanici_adi, bi.miktar, bi.tur, bi.aciklama, bi.tarih
        FROM bakiye_islemleri bi
        LEFT JOIN kullanicilar u ON u.id = bi.kullanici_id
        ORDER BY bi.id DESC LIMIT 100
    """).fetchall()
    conn.close()
    return jsonify({
        "basarili": True,
        "bakiyeler": [dict(r) for r in rows],
        "islemler": [dict(i) for i in islemler]
    })

def bot_cevap(mesaj):
    m = mesaj.lower().strip()
    if any(k in m for k in ["merhaba", "selam", "hey", "iyi gunler", "iyi aksam"]):
        return "Merhaba! Ben 299+ Ai analiz asistaniyim. Maclar, oranlar, bahis stratejileri veya gunun kuponu hakkinda sorularinizi yanitlayabilirim."

    if any(k in m for k in ["mac sayisi", "kac mac", "toplam mac"]):
        try:
            with open(VERI_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
            sayi = veri.get("macSayisi", len(veri.get("maclar", [])))
            return f"Su anda sistemimizde **{sayi} mac** analiz edilmektedir. 50'den fazla lig ve 60'tan fazla bahis marketi mevcuttur."
        except:
            return "Su an veri yuklenemiyor, biraz sonra tekrar deneyin."

    if any(k in m for k in ["en iyi bahis", "oneri", "bugun ne oynayim", "ne oynasam", "tavsiye"]):
        try:
            with open(VERI_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
            maclar_list = veri.get("maclar", [])
            bugun = ist_simdi().strftime("%Y-%m-%d")
            bugun_maclar = [mac for mac in maclar_list if mac.get("tarih") == bugun and mac.get("spor") == "Futbol"]
            if bugun_maclar:
                mac = max(bugun_maclar, key=lambda x: max(x.get("aiIhtimaller", {}).get("1", 0), x.get("aiIhtimaller", {}).get("0", 0), x.get("aiIhtimaller", {}).get("2", 0)))
                ai = mac.get("aiIhtimaller", {})
                en_yuksek = max(ai.items(), key=lambda x: x[1]) if ai else ("1", 50)
                secim_map = {"1": "Ev Sahibi", "0": "Beraberlik", "2": "Deplasman"}
                return (f"Bugunun en yuksek AI guvenli tahmini:\n\n"
                        f"**{mac.get('evSahibi')} vs {mac.get('deplasman')}**\n"
                        f"Lig: {mac.get('lig')}\n"
                        f"Tahmin: {secim_map.get(en_yuksek[0], en_yuksek[0])}\n"
                        f"AI Guven: %{en_yuksek[1]}\n"
                        f"Oran: {mac.get('oranlar', {}).get(en_yuksek[0], 'N/A')}")
            else:
                return "Bugun icin futbol maci bulunamadi."
        except:
            return "Oneri hazirlanirken hata olustu."

    if any(k in m for k in ["oran nedir", "oran nasil", "bahis nasil"]):
        return ("**Bahis Oranlari Nasil Calisir?**\n\n"
                "Oran, kazanmaniz durumunda aldiginiz para miktarini gosterir.\n\n"
                "Dusuk oran (1.10-1.50) = Yuksek olasilikli sonuc\n"
                "Orta oran (1.50-3.00) = Normal riskli bahis\n"
                "Yuksek oran (3.00+) = Surpriz/riskli tahmin")

    if any(k in m for k in ["kupon nedir", "kupon nasil", "kombine nedir"]):
        return ("**Kupon & Kombine Hakkinda**\n\n"
                "**Kupon:** Birden fazla mac tahminini birlestirdiginiz bahis formu.\n"
                "**Kombine:** 5+ mactan olusan buyuk kuponlar.\n\n"
                "Kupona mac eklemek icin ana sayfada herhangi bir orana tiklayin.")

    if any(k in m for k in ["hangi ligler", "lig listesi", "ligler", "kac lig"]):
        return ("**Desteklenen Ligler (50+)**\n\n"
                "Futbol: UCL, Europa League, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Super Lig ve 30+ lig\n"
                "Basketbol: NBA, EuroLeague, BSL, NCAA\n"
                "Voleybol & Tenis: ATP, WTA ve uluslararasi turnuvalar")

    if any(k in m for k in ["ai nasil", "analiz nasil", "yapay zeka", "algoritma"]):
        return ("**AI Analiz Sistemi**\n\n"
                "299+ Ai, istatistiksel modelleme kullanarak mac sonuclarini tahmin eder.\n"
                "Her takimin ortalama gol beklentisi hesaplanir.\n"
                "60+ bahis marketi icin olasilik hesaplanir.")

    if any(k in m for k in ["market", "urun", "satin al", "bakiye"]):
        return ("**AI Market**\n\n"
                "AI Market'ten VIP uyelik, analiz paketleri ve ozel icerikler satin alabilirsiniz.\n"
                "Bakiyenizi Shopier ile yukleyebilirsiniz.\n"
                "Menu > AI Market'ten erisebilirsiniz.")

    if any(k in m for k in ["yardim", "ne yapabilirsin", "help"]):
        return ("**Size yardimci olabilecegim konular:**\n\n"
                "Mac sayisi ve lig bilgileri\n"
                "Gunun en iyi bahis onerileri\n"
                "Oran ve bahis aciklamalari\n"
                "Kupon ve kombine nasil olusturulur\n"
                "AI Market ve bakiye bilgileri\n"
                "AI analiz sistemi hakkinda bilgi")

    if any(k in m for k in ["tesekkur", "sag ol", "tamam", "harika", "super"]):
        return "Rica ederim! Baska sorulariniz varsa her zaman buradayim."

    default_cevaplar = [
        "Mesajiniz admin'e iletildi, en kisa surede cevaplanacaktir.",
        "Sorunuz kaydedildi. Admin cevapladiginda bildirim alacaksiniz.",
    ]
    return random.choice(default_cevaplar)


if __name__ == "__main__":
    from veri_bot import guncelleme_zamanlayici
    bot_thread = threading.Thread(target=guncelleme_zamanlayici, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 5000))
    print(f"Sunucu port {port} uzerinde baslatiliyor...")
    app.run(host="0.0.0.0", port=port, debug=False)
