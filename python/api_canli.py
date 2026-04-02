import os
import json
import time
import random
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=3))
BASE_URL = "https://v3.football.api-sports.io"

API_FOOTBALL_KEYS = []
for k in ["API_FOOTBALL_KEY_1", "API_FOOTBALL_KEY_2", "API_FOOTBALL_KEY_3", "API_FOOTBALL_KEY"]:
    val = os.environ.get(k, "").strip()
    if val and val not in API_FOOTBALL_KEYS:
        API_FOOTBALL_KEYS.append(val)

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "").strip()
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

_aktif_key_index = [0]
_kalan_istek = {}

def aktif_api_key():
    for i in range(len(API_FOOTBALL_KEYS)):
        idx = (_aktif_key_index[0] + i) % len(API_FOOTBALL_KEYS)
        key = API_FOOTBALL_KEYS[idx]
        if _kalan_istek.get(key, 999) > 0:
            _aktif_key_index[0] = idx
            return key
    return API_FOOTBALL_KEYS[0] if API_FOOTBALL_KEYS else ""

def api_istek(endpoint, params=None):
    if not API_FOOTBALL_KEYS:
        return None

    for deneme in range(len(API_FOOTBALL_KEYS)):
        key = aktif_api_key()
        if not key:
            return None

        url = f"{BASE_URL}/{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{query}"
        try:
            req = urllib.request.Request(url, headers={"x-apisports-key": key})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())

            kalan = _kalan_istek.get(key, 999)
            headers_dict = dict(resp.headers)
            remaining_hdr = headers_dict.get("x-ratelimit-requests-remaining", None)
            if remaining_hdr is not None:
                try:
                    _kalan_istek[key] = int(remaining_hdr)
                except:
                    pass

            if data.get("errors"):
                err_str = str(data["errors"])
                if "limit" in err_str.lower() or "quota" in err_str.lower():
                    print(f"[API] Key #{deneme+1} limit doldu, diger key deneniyor...")
                    _kalan_istek[key] = 0
                    idx = _aktif_key_index[0]
                    _aktif_key_index[0] = (idx + 1) % len(API_FOOTBALL_KEYS)
                    continue
                print(f"[API HATA] {endpoint}: {data['errors']}")
                return None

            return data.get("response", [])
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):
                print(f"[API] Key limit/403 hatasi, sonraki key'e geciliyor...")
                _kalan_istek[key] = 0
                _aktif_key_index[0] = (_aktif_key_index[0] + 1) % len(API_FOOTBALL_KEYS)
                continue
            print(f"[API HATA] {endpoint}: HTTP {e.code}")
            return None
        except Exception as e:
            print(f"[API HATA] {endpoint}: {e}")
            return None

    return None

def odds_api_istek(endpoint, params=None):
    if not ODDS_API_KEY:
        return None
    url = f"{ODDS_BASE_URL}/{endpoint}"
    p = {"apiKey": ODDS_API_KEY}
    if params:
        p.update(params)
    query = "&".join(f"{k}={v}" for k, v in p.items())
    url += f"?{query}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return data
    except urllib.error.HTTPError as e:
        print(f"[ODDS API HATA] {endpoint}: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"[ODDS API HATA] {endpoint}: {e}")
        return None

LIG_HARITASI = {
    2: {"id": "ucl", "isim": "🏆 UEFA Şampiyonlar Ligi", "spor": "Futbol"},
    3: {"id": "uel", "isim": "🟠 UEFA Avrupa Ligi", "spor": "Futbol"},
    848: {"id": "uecl", "isim": "🟢 UEFA Konferans Ligi", "spor": "Futbol"},
    5: {"id": "uefanl", "isim": "🌍 UEFA Uluslar Ligi", "spor": "Futbol"},
    32: {"id": "wcq_eu", "isim": "🌐 Dünya Kupası Elemeleri (Avrupa)", "spor": "Futbol"},
    913: {"id": "finalissima", "isim": "🏆 CONMEBOL-UEFA Finalissima", "spor": "Futbol"},
    1222: {"id": "fifa_series", "isim": "🌍 FIFA Series", "spor": "Futbol"},
    10: {"id": "hazirlik", "isim": "⚽ Hazırlık Maçları", "spor": "Futbol"},
    39: {"id": "premier", "isim": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "spor": "Futbol"},
    140: {"id": "laliga", "isim": "🇪🇸 La Liga", "spor": "Futbol"},
    135: {"id": "seriea", "isim": "🇮🇹 Serie A", "spor": "Futbol"},
    78: {"id": "bundesliga", "isim": "🇩🇪 Bundesliga", "spor": "Futbol"},
    61: {"id": "ligue1", "isim": "🇫🇷 Ligue 1", "spor": "Futbol"},
    203: {"id": "super_lig", "isim": "🇹🇷 Süper Lig", "spor": "Futbol"},
    88: {"id": "eredivisie", "isim": "🇳🇱 Eredivisie", "spor": "Futbol"},
    94: {"id": "primeira_liga", "isim": "🇵🇹 Primeira Liga", "spor": "Futbol"},
    71: {"id": "brasileirao", "isim": "🇧🇷 Brasileirão", "spor": "Futbol"},
    128: {"id": "argentina_pd", "isim": "🇦🇷 Arjantin Primera División", "spor": "Futbol"},
    262: {"id": "liga_mx", "isim": "🇲🇽 Liga MX", "spor": "Futbol"},
    253: {"id": "mls", "isim": "🇺🇸 MLS", "spor": "Futbol"},
    98: {"id": "j_league", "isim": "🇯🇵 J-League", "spor": "Futbol"},
    292: {"id": "k_league", "isim": "🇰🇷 K-League 1", "spor": "Futbol"},
    169: {"id": "chinese_sl", "isim": "🇨🇳 Çin Süper Ligi", "spor": "Futbol"},
    307: {"id": "saudi_pl", "isim": "🇸🇦 Suudi Pro Ligi", "spor": "Futbol"},
    13: {"id": "copa_lib", "isim": "🏆 Copa Libertadores", "spor": "Futbol"},
    11: {"id": "copa_sud", "isim": "🏆 Copa Sudamericana", "spor": "Futbol"},
    235: {"id": "russian_pl", "isim": "🇷🇺 Rusya Premier Ligi", "spor": "Futbol"},
    144: {"id": "belgian_pro", "isim": "🇧🇪 Belçika Pro Ligi", "spor": "Futbol"},
    179: {"id": "scottish_prem", "isim": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership", "spor": "Futbol"},
    197: {"id": "greek_sl", "isim": "🇬🇷 Yunan Süper Ligi", "spor": "Futbol"},
    345: {"id": "czech_liga", "isim": "🇨🇿 Çek Ligi", "spor": "Futbol"},
    106: {"id": "polish_ekstr", "isim": "🇵🇱 Polonya Ekstraklasa", "spor": "Futbol"},
    207: {"id": "swiss_sl", "isim": "🇨🇭 İsviçre Süper Ligi", "spor": "Futbol"},
    218: {"id": "austrian_bl", "isim": "🇦🇹 Avusturya Bundesliga", "spor": "Futbol"},
    119: {"id": "danish_sl", "isim": "🇩🇰 Danimarka Süper Ligi", "spor": "Futbol"},
    103: {"id": "norwegian_el", "isim": "🇳🇴 Norveç Eliteserien", "spor": "Futbol"},
    113: {"id": "swedish_all", "isim": "🇸🇪 İsveç Allsvenskan", "spor": "Futbol"},
    333: {"id": "ukrainian_pl", "isim": "🇺🇦 Ukrayna Premier Ligi", "spor": "Futbol"},
    210: {"id": "croatian_hnl", "isim": "🇭🇷 Hırvatistan HNL", "spor": "Futbol"},
    286: {"id": "serbian_sl", "isim": "🇷🇸 Sırbistan Süper Ligi", "spor": "Futbol"},
    384: {"id": "israeli_pl", "isim": "🇮🇱 İsrail Premier Ligi", "spor": "Futbol"},
    233: {"id": "egyptian_pl", "isim": "🇪🇬 Mısır Premier Ligi", "spor": "Futbol"},
    188: {"id": "south_african", "isim": "🇿🇦 Güney Afrika PSL", "spor": "Futbol"},
    152: {"id": "australian", "isim": "🇦🇺 A-League", "spor": "Futbol"},
    36: {"id": "afcon_q", "isim": "🌍 Afrika Kupası Elemeleri", "spor": "Futbol"},
    850: {"id": "u21_euro", "isim": "🇪🇺 UEFA U21 Avrupa Şampiyonası Elemeleri", "spor": "Futbol"},
    1207: {"id": "concacaf_series", "isim": "🌎 CONCACAF Series", "spor": "Futbol"},
    37: {"id": "wcq_inter", "isim": "🌐 Dünya Kupası Kıtalararası Play-off", "spor": "Futbol"},
    141: {"id": "laliga2", "isim": "🇪🇸 La Liga 2", "spor": "Futbol"},
    40: {"id": "championship", "isim": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship", "spor": "Futbol"},
    79: {"id": "bundesliga2", "isim": "🇩🇪 2. Bundesliga", "spor": "Futbol"},
    136: {"id": "serieb", "isim": "🇮🇹 Serie B", "spor": "Futbol"},
    62: {"id": "ligue2", "isim": "🇫🇷 Ligue 2", "spor": "Futbol"},
    204: {"id": "tur_1lig", "isim": "🇹🇷 1. Lig", "spor": "Futbol"},
}

TERS_LIG_HARITASI = {v["id"]: k for k, v in LIG_HARITASI.items()}

ODDS_API_SPORT_HARITASI = {
    "soccer_epl": {"isim": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "spor": "Futbol"},
    "soccer_spain_la_liga": {"isim": "🇪🇸 La Liga", "spor": "Futbol"},
    "soccer_italy_serie_a": {"isim": "🇮🇹 Serie A", "spor": "Futbol"},
    "soccer_germany_bundesliga": {"isim": "🇩🇪 Bundesliga", "spor": "Futbol"},
    "soccer_france_ligue_one": {"isim": "🇫🇷 Ligue 1", "spor": "Futbol"},
    "soccer_turkey_super_league": {"isim": "🇹🇷 Süper Lig", "spor": "Futbol"},
    "soccer_uefa_champs_league": {"isim": "🏆 UEFA Şampiyonlar Ligi", "spor": "Futbol"},
    "soccer_uefa_europa_league": {"isim": "🟠 UEFA Avrupa Ligi", "spor": "Futbol"},
    "basketball_nba": {"isim": "🏀 NBA", "spor": "Basketbol"},
    "basketball_euroleague": {"isim": "🏀 EuroLeague", "spor": "Basketbol"},
    "basketball_nbl": {"isim": "🏀 NBL (Avustralya)", "spor": "Basketbol"},
    "tennis_atp_french_open": {"isim": "🎾 Roland Garros (ATP)", "spor": "Tenis"},
    "tennis_wta_french_open": {"isim": "🎾 Roland Garros (WTA)", "spor": "Tenis"},
    "tennis_atp_wimbledon": {"isim": "🎾 Wimbledon (ATP)", "spor": "Tenis"},
    "tennis_wta_wimbledon": {"isim": "🎾 Wimbledon (WTA)", "spor": "Tenis"},
    "tennis_atp_us_open": {"isim": "🎾 US Open (ATP)", "spor": "Tenis"},
    "tennis_wta_us_open": {"isim": "🎾 US Open (WTA)", "spor": "Tenis"},
    "tennis_atp_aus_open": {"isim": "🎾 Avustralya Açık (ATP)", "spor": "Tenis"},
    "tennis_wta_aus_open": {"isim": "🎾 Avustralya Açık (WTA)", "spor": "Tenis"},
    "tennis_atp_miami_open": {"isim": "🎾 Miami Open (ATP)", "spor": "Tenis"},
    "tennis_wta_miami_open": {"isim": "🎾 Miami Open (WTA)", "spor": "Tenis"},
    "tennis_atp_monte_carlo": {"isim": "🎾 Monte Carlo (ATP)", "spor": "Tenis"},
    "volleyball_wch_women_u20": {"isim": "🏐 Voleybol Dünya Şampiyonası (Kadın U20)", "spor": "Voleybol"},
    "volleyball_wcl": {"isim": "🏐 Uluslar Ligi", "spor": "Voleybol"},
}

MAC_ID_SAYACI = {"deger": 5000}


def takim_gucu_tahmin(takim_adi):
    seed_val = hash(takim_adi) % 999999
    rng = random.Random(seed_val)
    return rng.randint(40, 90)


def fixture_to_mac(fixture, mac_id):
    from market_olusturucu import (
        ms_olasiliklari_hesapla, futbol_marketleri_olustur, olasiliktan_oran
    )

    league = fixture["league"]
    teams = fixture["teams"]
    fix = fixture["fixture"]

    api_league_id = league["id"]
    lig_bilgi = LIG_HARITASI.get(api_league_id)

    if not lig_bilgi:
        lig_bilgi = {
            "id": f"api_{api_league_id}",
            "isim": f"⚽ {league['name']}",
            "spor": "Futbol"
        }

    ev_sahibi = teams["home"]["name"]
    deplasman = teams["away"]["name"]

    fix_date = fix.get("date", "")
    try:
        dt = datetime.fromisoformat(fix_date.replace("Z", "+00:00"))
        dt_ist = dt.astimezone(IST)
        tarih_str = dt_ist.strftime("%Y-%m-%d")
        saat = dt_ist.strftime("%H:%M")
    except:
        tarih_str = datetime.now(IST).strftime("%Y-%m-%d")
        saat = "20:00"

    ev_gucu = takim_gucu_tahmin(ev_sahibi)
    dep_gucu = takim_gucu_tahmin(deplasman)

    ev_avantaj = 8
    ms = ms_olasiliklari_hesapla(ev_gucu + ev_avantaj, dep_gucu, "Futbol")

    oranlar = {
        "1": olasiliktan_oran(ms["1"]),
        "0": olasiliktan_oran(ms["0"]) if ms["0"] > 0 else 0.00,
        "2": olasiliktan_oran(ms["2"]),
    }
    ai_ihtimaller = {
        "1": max(5, min(95, round(ms["1"] * 100))),
        "0": max(5, min(95, round(ms["0"] * 100))) if ms["0"] > 0 else 0,
        "2": max(5, min(95, round(ms["2"] * 100))),
    }

    ekstra = futbol_marketleri_olustur(ev_gucu + ev_avantaj, dep_gucu, ms)

    status = fix.get("status", {}).get("short", "NS")
    goals = fixture.get("goals", {})
    score_home = goals.get("home")
    score_away = goals.get("away")

    durum = "planlanmis"
    if status in ["1H", "HT", "2H", "ET", "P", "BT", "LIVE"]:
        durum = "canli"
    elif status in ["FT", "AET", "PEN"]:
        durum = "bitmis"
    elif status in ["PST", "CANC", "ABD", "AWD", "WO"]:
        durum = "iptal"

    mac = {
        "id": mac_id,
        "apiId": fix.get("id"),
        "spor": "Futbol",
        "lig": lig_bilgi["isim"],
        "ligId": lig_bilgi["id"],
        "ulke": league.get("country", ""),
        "evSahibi": ev_sahibi,
        "deplasman": deplasman,
        "tarih": tarih_str,
        "saat": saat,
        "oranlar": oranlar,
        "aiIhtimaller": ai_ihtimaller,
        "ekstraBahisler": ekstra,
        "durum": durum,
    }

    if score_home is not None and score_away is not None:
        mac["skorEv"] = score_home
        mac["skorDep"] = score_away

    return mac


def gune_ait_maclar_cek(tarih_str):
    fixtures = api_istek("fixtures", {"date": tarih_str})
    if fixtures is None:
        return None

    maclar = []
    mac_id = MAC_ID_SAYACI["deger"]

    for fix in fixtures:
        mac_id += 1
        try:
            mac = fixture_to_mac(fix, mac_id)
            if mac:
                maclar.append(mac)
        except Exception as e:
            print(f"[FIXTURE HATA] {e}")

    MAC_ID_SAYACI["deger"] = mac_id
    return maclar


def odds_api_maclar_cek():
    """The Odds API'den maç verisini çek, API-Football verisine ekle."""
    if not ODDS_API_KEY:
        return []

    from market_olusturucu import (
        ms_olasiliklari_hesapla, futbol_marketleri_olustur,
        diger_spor_marketleri, olasiliktan_oran
    )

    tum_maclar = []
    mac_id = 70000
    eklenecek_sporlar = list(ODDS_API_SPORT_HARITASI.keys())

    for idx_sport, sport_key in enumerate(eklenecek_sporlar):
        if idx_sport > 0:
            time.sleep(0.8)
        lig_bilgi = ODDS_API_SPORT_HARITASI[sport_key]
        spor = lig_bilgi["spor"]
        veri = odds_api_istek(
            f"sports/{sport_key}/events",
            {"dateFormat": "iso", "daysFrom": 0, "daysTo": 7}
        )
        if not veri or not isinstance(veri, list):
            continue

        for event in veri[:30]:
            try:
                mac_id += 1
                ev = event.get("home_team", "?")
                dep = event.get("away_team", "?")
                commence = event.get("commence_time", "")
                try:
                    dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                    dt_ist = dt.astimezone(IST)
                    tarih_str = dt_ist.strftime("%Y-%m-%d")
                    saat = dt_ist.strftime("%H:%M")
                except:
                    tarih_str = datetime.now(IST).strftime("%Y-%m-%d")
                    saat = "20:00"

                ev_gucu = takim_gucu_tahmin(ev)
                dep_gucu = takim_gucu_tahmin(dep)
                ev_avantaj = 5 if spor == "Futbol" else 3
                ms = ms_olasiliklari_hesapla(ev_gucu + ev_avantaj, dep_gucu, spor)

                if spor == "Futbol":
                    ekstra = futbol_marketleri_olustur(ev_gucu + ev_avantaj, dep_gucu, ms)
                else:
                    ekstra = diger_spor_marketleri(spor, ms)

                mac = {
                    "id": mac_id,
                    "kaynak": "odds-api",
                    "spor": spor,
                    "lig": lig_bilgi["isim"],
                    "ligId": sport_key,
                    "ulke": "",
                    "evSahibi": ev,
                    "deplasman": dep,
                    "tarih": tarih_str,
                    "saat": saat,
                    "oranlar": {
                        "1": olasiliktan_oran(ms["1"]),
                        "0": olasiliktan_oran(ms["0"]) if ms["0"] > 0 else 0.00,
                        "2": olasiliktan_oran(ms["2"]),
                    },
                    "aiIhtimaller": {
                        "1": max(5, min(95, round(ms["1"] * 100))),
                        "0": max(5, min(95, round(ms["0"] * 100))) if ms["0"] > 0 else 0,
                        "2": max(5, min(95, round(ms["2"] * 100))),
                    },
                    "ekstraBahisler": ekstra,
                    "durum": "planlanmis",
                }
                tum_maclar.append(mac)
            except Exception as e:
                print(f"[ODDS API MAC HATA] {e}")

        print(f"  [ODDS API] {lig_bilgi['isim']}: {len([m for m in tum_maclar if m.get('ligId')==sport_key])} mac")

    return tum_maclar


def tum_gunleri_cek(gun_sayisi=2):
    simdi = datetime.now(IST)
    tum_maclar = []
    gun_ozeti = {}

    key_bilgisi = f"{len(API_FOOTBALL_KEYS)} API-Football key" if API_FOOTBALL_KEYS else "API-Football key yok"
    print(f"[API] {key_bilgisi} ile veri cekiliyor...")

    for gun_index in range(gun_sayisi):
        tarih = simdi + timedelta(days=gun_index)
        tarih_str = tarih.strftime("%Y-%m-%d")

        maclar = gune_ait_maclar_cek(tarih_str)
        if maclar is None:
            print(f"[API] {tarih_str} icin veri cekilemedi, atlanıyor")
            continue

        filtreli = [m for m in maclar if not m.get("ligId", "").startswith("api_")]
        tum_maclar.extend(filtreli)
        futbol_sayisi = len(filtreli)
        gun_ozeti[tarih_str] = {
            "toplam": futbol_sayisi,
            "Futbol": futbol_sayisi,
            "Basketbol": 0,
            "Voleybol": 0,
            "Tenis": 0,
        }
        print(f"  [API-Football] {tarih_str}: {futbol_sayisi} futbol maci cekildi (key idx: {_aktif_key_index[0]+1})")

    return tum_maclar, gun_ozeti


def api_ile_guncelle(gun_sayisi=2):
    if not API_FOOTBALL_KEYS and not ODDS_API_KEY:
        print("[API] Hic API anahtari bulunamadi, simulasyon verisi kullanilacak")
        return False

    TOPLAM_GUN = 7
    print("[API] Gercek mac verileri cekiliyor...")

    futbol_maclari = []
    gun_ozeti = {}

    if API_FOOTBALL_KEYS:
        futbol_maclari, gun_ozeti = tum_gunleri_cek(gun_sayisi)
    else:
        print("[API] API-Football key yok, bu kisim atlaniyor")

    from veri_bot import ist_simdi
    simdi = ist_simdi()

    odds_maclar = []
    if ODDS_API_KEY:
        print("[ODDS API] The Odds API'den veri cekiliyor...")
        odds_maclar = odds_api_maclar_cek()
        print(f"[ODDS API] Toplam {len(odds_maclar)} mac cekildi")
        for m in odds_maclar:
            tarih_str = m.get("tarih", "")
            spor = m.get("spor", "Diger")
            if tarih_str not in gun_ozeti:
                gun_ozeti[tarih_str] = {"toplam": 0, "Futbol": 0, "Basketbol": 0, "Voleybol": 0, "Tenis": 0}
            gun_ozeti[tarih_str][spor] = gun_ozeti[tarih_str].get(spor, 0) + 1
            gun_ozeti[tarih_str]["toplam"] = gun_ozeti[tarih_str].get("toplam", 0) + 1

    tum_maclar = futbol_maclari + odds_maclar

    mac_id_set = set()
    tekrarsiz = []
    for m in tum_maclar:
        anahtar = (m.get("evSahibi",""), m.get("deplasman",""), m.get("tarih",""), m.get("saat",""))
        if anahtar not in mac_id_set:
            mac_id_set.add(anahtar)
            tekrarsiz.append(m)

    tekrarsiz.sort(key=lambda m: (m["tarih"], m["saat"], m["spor"], m["lig"]))

    if not tekrarsiz:
        print("[API] Hicbir mac cekilemedi")
        return False

    su_an = simdi.strftime("%Y-%m-%d %H:%M:%S")
    kaynak_bilgi = []
    if futbol_maclari:
        kaynak_bilgi.append(f"api-football({len(API_FOOTBALL_KEYS)} key)")
    if odds_maclar:
        kaynak_bilgi.append("the-odds-api")

    veri = {
        "guncelleme": su_an,
        "macSayisi": len(tekrarsiz),
        "gunOzeti": gun_ozeti,
        "maclar": tekrarsiz,
        "kaynak": " + ".join(kaynak_bilgi) if kaynak_bilgi else "simulasyon"
    }

    dosya_yolu = os.path.join(os.path.dirname(__file__), "api_veri.json")
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))

    print(f"[API] Guncelleme tamamlandi: {len(tekrarsiz)} mac toplam")
    print(f"  API-Football: {len(futbol_maclari)} mac ({len(API_FOOTBALL_KEYS)} key)")
    print(f"  The Odds API: {len(odds_maclar)} mac")
    for t, o in sorted(gun_ozeti.items()):
        print(f"  {t}: {o['toplam']} mac (F:{o.get('Futbol',0)} B:{o.get('Basketbol',0)} V:{o.get('Voleybol',0)} T:{o.get('Tenis',0)})")

    return True


def canli_maclar_guncelle():
    """Canlı maçları API-Football'dan çek, JSON dosyasını güncelle."""
    if not API_FOOTBALL_KEYS:
        return False

    fixtures = api_istek("fixtures", {"live": "all"})
    if fixtures is None:
        return False

    if not fixtures:
        return True

    dosya_yolu = os.path.join(os.path.dirname(__file__), "api_veri.json")
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veri = json.load(f)
    except Exception:
        return False

    maclar = veri.get("maclar", [])
    api_id_to_index = {}
    for i, m in enumerate(maclar):
        if m.get("apiId"):
            api_id_to_index[m["apiId"]] = i

    guncellenen = 0
    yeni_canli = []

    for fix in fixtures:
        fixture_data = fix.get("fixture", {})
        api_id = fixture_data.get("id")
        status = fixture_data.get("status", {}).get("short", "NS")
        elapsed = fixture_data.get("status", {}).get("elapsed")
        goals = fix.get("goals", {})
        score_home = goals.get("home")
        score_away = goals.get("away")
        league = fix.get("league", {})
        teams = fix.get("teams", {})

        durum = "canli"
        if status in ["FT", "AET", "PEN"]:
            durum = "bitmis"
        elif status in ["PST", "CANC", "ABD"]:
            durum = "iptal"

        if api_id and api_id in api_id_to_index:
            idx = api_id_to_index[api_id]
            maclar[idx]["durum"] = durum
            if score_home is not None:
                maclar[idx]["skorEv"] = score_home
            if score_away is not None:
                maclar[idx]["skorDep"] = score_away
            if elapsed is not None:
                maclar[idx]["dakika"] = elapsed
            guncellenen += 1
        else:
            api_league_id = league.get("id")
            lig_bilgi = LIG_HARITASI.get(api_league_id, {
                "id": f"api_{api_league_id}",
                "isim": f"⚽ {league.get('name', 'Bilinmiyor')}",
                "spor": "Futbol"
            })
            try:
                fix_date = fixture_data.get("date", "")
                dt = datetime.fromisoformat(fix_date.replace("Z", "+00:00"))
                dt_ist = dt.astimezone(IST)
                tarih_str = dt_ist.strftime("%Y-%m-%d")
                saat = dt_ist.strftime("%H:%M")
            except Exception:
                tarih_str = datetime.now(IST).strftime("%Y-%m-%d")
                saat = "20:00"

            from market_olusturucu import ms_olasiliklari_hesapla, futbol_marketleri_olustur, olasiliktan_oran
            ev = teams.get("home", {}).get("name", "?")
            dep = teams.get("away", {}).get("name", "?")
            ev_gucu = takim_gucu_tahmin(ev)
            dep_gucu = takim_gucu_tahmin(dep)
            ms = ms_olasiliklari_hesapla(ev_gucu + 8, dep_gucu, "Futbol")
            ekstra = futbol_marketleri_olustur(ev_gucu + 8, dep_gucu, ms)

            yeni = {
                "id": 90000 + (api_id or 0) % 9000,
                "apiId": api_id,
                "spor": "Futbol",
                "lig": lig_bilgi["isim"],
                "ligId": lig_bilgi["id"],
                "ulke": league.get("country", ""),
                "evSahibi": ev,
                "deplasman": dep,
                "tarih": tarih_str,
                "saat": saat,
                "oranlar": {
                    "1": olasiliktan_oran(ms["1"]),
                    "0": olasiliktan_oran(ms["0"]) if ms["0"] > 0 else 0.00,
                    "2": olasiliktan_oran(ms["2"]),
                },
                "aiIhtimaller": {
                    "1": max(5, min(95, round(ms["1"] * 100))),
                    "0": max(5, min(95, round(ms["0"] * 100))) if ms["0"] > 0 else 0,
                    "2": max(5, min(95, round(ms["2"] * 100))),
                },
                "ekstraBahisler": ekstra,
                "durum": durum,
            }
            if score_home is not None:
                yeni["skorEv"] = score_home
            if score_away is not None:
                yeni["skorDep"] = score_away
            if elapsed is not None:
                yeni["dakika"] = elapsed
            yeni_canli.append(yeni)

    if yeni_canli:
        maclar.extend(yeni_canli)

    veri["maclar"] = maclar
    veri["macSayisi"] = len(maclar)
    veri["canliGuncelleme"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))

    canli_sayi = sum(1 for m in maclar if m.get("durum") == "canli")
    print(f"[CANLI] {guncellenen} maç güncellendi, {len(yeni_canli)} yeni canlı maç eklendi. Toplam canlı: {canli_sayi}")
    return True
