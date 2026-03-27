import json
import random
import os
import schedule
import time
import threading
from datetime import datetime, timezone, timedelta
from ligler import SPORLAR
from market_olusturucu import (
    ms_olasiliklari_hesapla,
    futbol_marketleri_olustur,
    diger_spor_marketleri,
    olasiliktan_oran
)

IST = timezone(timedelta(hours=3))

def ist_simdi():
    return datetime.now(IST)

MAC_SAATLERI = {
    "Futbol": ["13:00", "13:30", "15:00", "16:00", "17:00", "17:30", "18:00", "19:00", "19:30", "20:00", "20:30", "20:45", "21:00", "21:30", "22:00"],
    "Basketbol": ["17:00", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30"],
    "Voleybol": ["14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"],
    "Tenis": ["11:00", "12:00", "13:00", "14:00", "14:30", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"],
}

MAC_ID_SAYACI = {"deger": 1000}

def mac_id_uret():
    MAC_ID_SAYACI["deger"] += 1
    return MAC_ID_SAYACI["deger"]

def takim_gucu_uret(takim_adi, tarih_str):
    seed_val = hash(takim_adi + tarih_str) % 999999
    rng = random.Random(seed_val)
    return rng.randint(30, 95)

MILLI_TAKIM_LIGLERI = ["uefanl", "wcq_eu"]
KULUP_TURNUVALARI = ["ucl", "uel", "uecl", "copa_lib"]
AVRUPA_KULUP_LIGLERI = [
    "premier", "laliga", "seriea", "bundesliga", "ligue1", "super_lig",
    "eredivisie", "primeira_liga", "russian_pl", "belgian_pro", "scottish_prem",
    "greek_sl", "czech_liga", "polish_ekstr", "swiss_sl", "austrian_bl",
    "danish_sl", "norwegian_el", "swedish_all", "ukrainian_pl", "croatian_hnl",
    "serbian_sl", "israeli_pl"
]

def milli_takim_haftasi_mi(tarih_obj):
    ay = tarih_obj.month
    gun = tarih_obj.day
    if ay == 3 and gun >= 20:
        return True
    if ay == 6 and gun >= 1 and gun <= 15:
        return True
    if ay == 9 and gun >= 1 and gun <= 12:
        return True
    if ay == 10 and gun >= 8 and gun <= 18:
        return True
    if ay == 11 and gun >= 10 and gun <= 22:
        return True
    return False

def gun_mac_sayisi(lig, gun_index, tarih_obj, tarih_str):
    lig_id = lig["id"]
    seviye = lig.get("seviye", 2)
    haftanin_gunu = tarih_obj.weekday()

    seed_val = hash(lig_id + tarih_str) % 999999
    rng = random.Random(seed_val)

    milli_hafta = milli_takim_haftasi_mi(tarih_obj)

    if lig_id in MILLI_TAKIM_LIGLERI:
        if milli_hafta:
            if haftanin_gunu in [3, 4, 5]:
                return rng.choice([6, 8, 10])
            elif haftanin_gunu in [0, 1, 2]:
                return rng.choice([4, 6, 8])
            return rng.choice([0, 0, 2])
        else:
            return 0

    if lig_id in KULUP_TURNUVALARI:
        if milli_hafta:
            return 0
        if lig_id == "copa_lib":
            if haftanin_gunu in [2, 3]:
                return rng.choice([3, 4, 6])
            return 0
        if haftanin_gunu in [1, 2]:
            return rng.choice([4, 6, 8])
        elif haftanin_gunu in [3]:
            return rng.choice([0, 0, 2])
        return 0

    if milli_hafta and lig_id in AVRUPA_KULUP_LIGLERI:
        return 0

    LIG_GUNLERI = {
        "premier": [4, 5, 6, 0],
        "laliga": [4, 5, 6, 0],
        "seriea": [4, 5, 6, 0],
        "bundesliga": [5, 6],
        "ligue1": [4, 5, 6, 0],
        "super_lig": [4, 5, 6, 0],
        "eredivisie": [5, 6, 0],
        "primeira_liga": [4, 5, 6, 0],
        "nba": [0, 1, 2, 3, 4, 5, 6],
        "euroleague": [1, 2, 3, 4],
        "turkish_bsl": [5, 6, 0, 2],
        "acb": [5, 6, 0],
        "lba": [5, 6, 0],
        "atp": [0, 1, 2, 3, 4, 5, 6],
        "wta": [0, 1, 2, 3, 4, 5, 6],
        "mls": [5, 6, 0, 2],
        "brasileirao": [5, 6, 0, 2, 3],
        "argentina_pd": [5, 6, 0, 1],
        "liga_mx": [5, 6, 0, 2],
        "j_league": [5, 6, 0, 2],
        "k_league": [5, 6, 0],
        "saudi_pl": [3, 4, 5, 6],
    }

    lig_mac_gunleri = LIG_GUNLERI.get(lig_id, None)

    if lig_mac_gunleri is not None:
        if haftanin_gunu not in lig_mac_gunleri:
            return 0
        if seviye <= 1:
            return rng.choice([3, 4, 5, 6, 7])
        else:
            return rng.choice([2, 3, 4])
    else:
        if milli_hafta:
            return 0
        mac_olasilik = rng.random()
        if haftanin_gunu in [5, 6, 0]:
            if mac_olasilik < 0.2:
                return 0
            if seviye <= 1:
                return rng.choice([3, 4, 5, 6])
            else:
                return rng.choice([2, 3, 4])
        elif haftanin_gunu in [4]:
            if mac_olasilik < 0.4:
                return 0
            if seviye <= 1:
                return rng.choice([2, 3, 4])
            else:
                return rng.choice([1, 2, 3])
        else:
            if mac_olasilik < 0.6:
                return 0
            if seviye <= 1:
                return rng.choice([1, 2, 3])
            else:
                return rng.choice([1, 2])

def mac_olustur(spor, lig, tarih_str, mac_index):
    seed_val = hash(lig["id"] + tarih_str + str(mac_index)) % 999999
    rng = random.Random(seed_val)

    takimlar = lig["takimlar"]
    if len(takimlar) < 2:
        return None

    secilen = rng.sample(takimlar, 2)
    ev_sahibi = secilen[0]
    deplasman = secilen[1]

    ev_gucu = takim_gucu_uret(ev_sahibi, tarih_str)
    dep_gucu = takim_gucu_uret(deplasman, tarih_str)

    ev_avantaj = 8 if spor == "Futbol" else 3
    ms = ms_olasiliklari_hesapla(ev_gucu + ev_avantaj, dep_gucu, spor)

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

    saatler = MAC_SAATLERI.get(spor, ["18:00", "20:00"])
    saat = rng.choice(saatler)

    if spor == "Futbol":
        ekstra = futbol_marketleri_olustur(ev_gucu + ev_avantaj, dep_gucu, ms)
    else:
        ekstra = diger_spor_marketleri(spor, ms)

    return {
        "id": mac_id_uret(),
        "spor": spor,
        "lig": lig["isim"],
        "ligId": lig["id"],
        "ulke": lig.get("ulke", ""),
        "evSahibi": ev_sahibi,
        "deplasman": deplasman,
        "tarih": tarih_str,
        "saat": saat,
        "oranlar": oranlar,
        "aiIhtimaller": ai_ihtimaller,
        "ekstraBahisler": ekstra,
    }

def sistemi_guncelle():
    simdi = ist_simdi()
    su_an = simdi.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{su_an}] Sistem guncelleniyor (Istanbul saati)...")

    try:
        from api_canli import api_ile_guncelle
        basarili = api_ile_guncelle(gun_sayisi=2)
        if basarili:
            print(f"[{su_an}] API ile guncelleme basarili!")
            return
        else:
            print(f"[{su_an}] API basarisiz, yedek sisteme geciliyor...")
    except Exception as e:
        print(f"[{su_an}] API hatasi: {e}, yedek sisteme geciliyor...")

    MAC_ID_SAYACI["deger"] = 1000

    tum_maclar = []
    gun_bazli = {}

    for gun_index in range(8):
        tarih = simdi + timedelta(days=gun_index)
        tarih_str = tarih.strftime("%Y-%m-%d")
        gun_bazli[tarih_str] = {"Futbol": [], "Basketbol": [], "Voleybol": [], "Tenis": []}

        for spor, ligler in SPORLAR.items():
            for lig in ligler:
                sayac = gun_mac_sayisi(lig, gun_index, tarih, tarih_str)
                for mac_i in range(sayac):
                    try:
                        mac = mac_olustur(spor, lig, tarih_str, mac_i)
                        if mac:
                            tum_maclar.append(mac)
                            gun_bazli[tarih_str][spor].append(mac)
                    except Exception as e:
                        print(f"Mac olusturma hatasi ({lig['isim']}): {e}")

    tum_maclar.sort(key=lambda m: (m["tarih"], m["saat"], m["spor"], m["lig"]))

    gun_ozeti = {}
    for tarih_str, sporlar in gun_bazli.items():
        toplam = sum(len(v) for v in sporlar.values())
        gun_ozeti[tarih_str] = {
            "toplam": toplam,
            "Futbol": len(sporlar["Futbol"]),
            "Basketbol": len(sporlar["Basketbol"]),
            "Voleybol": len(sporlar["Voleybol"]),
            "Tenis": len(sporlar["Tenis"]),
        }

    veri = {
        "guncelleme": su_an,
        "macSayisi": len(tum_maclar),
        "gunOzeti": gun_ozeti,
        "maclar": tum_maclar
    }

    dosya_yolu = os.path.join(os.path.dirname(__file__), "api_veri.json")
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))

    print(f"[{su_an}] Yedek sistem ile guncelleme: {len(tum_maclar)} mac kaydedildi.")
    for t, o in sorted(gun_ozeti.items()):
        print(f"  {t}: {o['toplam']} mac (F:{o['Futbol']} B:{o['Basketbol']} V:{o['Voleybol']} T:{o['Tenis']})")


def guncelleme_zamanlayici():
    sistemi_guncelle()

    schedule.every(6).hours.do(sistemi_guncelle)
    schedule.every().day.at("00:00").do(sistemi_guncelle)
    schedule.every().day.at("00:05").do(sistemi_guncelle)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    guncelleme_zamanlayici()
