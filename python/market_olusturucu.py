import random
import math

def olasiliktan_oran(olasilik, marj_carpan=1.07):
    if olasilik <= 0:
        return 0.00
    ham_oran = 1 / olasilik
    oran = round(ham_oran * marj_carpan * random.uniform(0.96, 1.04), 2)
    return max(1.01, oran)

def poisson_olasilik(lam, k):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * (math.e ** -lam) / math.factorial(min(k, 20))

def gol_beklentisi_olustur(ev_gucu, dep_gucu):
    ev_gol = (ev_gucu / 50.0) * random.uniform(0.8, 1.8)
    dep_gol = (dep_gucu / 50.0) * random.uniform(0.6, 1.5)
    return max(0.3, ev_gol), max(0.2, dep_gol)

def ms_olasiliklari_hesapla(ev_gucu, dep_gucu, spor):
    if spor == "Futbol":
        fark = (ev_gucu - dep_gucu) / 100.0
        ev_kazanma = max(0.10, min(0.85, 0.48 + fark * 1.5))
        dep_kazanma = max(0.10, min(0.75, 0.28 - fark * 1.2))
        beraberlik = max(0.05, 1.0 - ev_kazanma - dep_kazanma)
        toplam = ev_kazanma + beraberlik + dep_kazanma
        return {
            "1": round(ev_kazanma / toplam, 3),
            "0": round(beraberlik / toplam, 3),
            "2": round(dep_kazanma / toplam, 3)
        }
    else:
        fark = (ev_gucu - dep_gucu) / 100.0
        ev_kazanma = max(0.15, min(0.85, 0.53 + fark * 1.8))
        return {"1": round(ev_kazanma, 3), "0": 0, "2": round(1.0 - ev_kazanma, 3)}

def futbol_marketleri_olustur(ev_gucu, dep_gucu, ms_olasiliklari):
    ev_gol, dep_gol = gol_beklentisi_olustur(ev_gucu, dep_gucu)

    p1 = ms_olasiliklari["1"]
    p0 = ms_olasiliklari["0"]
    p2 = ms_olasiliklari["2"]

    def gol_alt_ust(esik):
        p_alt = sum(
            poisson_olasilik(ev_gol, i) * poisson_olasilik(dep_gol, j)
            for i in range(8) for j in range(8)
            if i + j <= esik
        )
        p_alt = max(0.05, min(0.95, p_alt))
        return p_alt, 1 - p_alt

    def korner_alt_ust(esik):
        beklenen = random.uniform(8.5, 11.5)
        p_alt = sum(poisson_olasilik(beklenen, k) for k in range(int(esik) + 1))
        p_alt = max(0.1, min(0.9, p_alt))
        return p_alt, 1 - p_alt

    def kart_alt_ust(esik):
        beklenen = random.uniform(3.0, 5.5)
        p_alt = sum(poisson_olasilik(beklenen, k) for k in range(int(esik) + 1))
        p_alt = max(0.1, min(0.9, p_alt))
        return p_alt, 1 - p_alt

    g05_alt, g05_ust = gol_alt_ust(0)
    g15_alt, g15_ust = gol_alt_ust(1)
    g25_alt, g25_ust = gol_alt_ust(2)
    g35_alt, g35_ust = gol_alt_ust(3)
    g45_alt, g45_ust = gol_alt_ust(4)
    g55_alt, g55_ust = gol_alt_ust(5)

    kg_var = max(0.20, min(0.85, 1 - (poisson_olasilik(ev_gol, 0) + poisson_olasilik(dep_gol, 0))))
    kg_yok = 1 - kg_var

    iy_p1 = max(0.10, p1 * 0.65 + 0.05)
    iy_p0 = max(0.15, 0.55 - iy_p1 * 0.3)
    iy_p2 = max(0.05, 1 - iy_p1 - iy_p0)
    t = iy_p1 + iy_p0 + iy_p2
    iy_p1 /= t; iy_p0 /= t; iy_p2 /= t

    iy_g05_alt = max(0.30, min(0.80, g05_alt * 0.5 + 0.15))
    iy_g15_alt = max(0.55, min(0.92, g15_alt * 0.75 + 0.10))

    k85_alt, k85_ust = korner_alt_ust(8)
    k95_alt, k95_ust = korner_alt_ust(9)
    k105_alt, k105_ust = korner_alt_ust(10)
    iy_k45_alt, iy_k45_ust = korner_alt_ust(4)

    ka35_alt, ka35_ust = kart_alt_ust(3)
    ka45_alt, ka45_ust = kart_alt_ust(4)
    ka55_alt, ka55_ust = kart_alt_ust(5)

    p_1x = p1 + p0; p_12 = p1 + p2; p_x2 = p0 + p2
    p_ilk_ev = max(0.15, p1 * 0.70)
    p_ilk_dep = max(0.10, p2 * 0.70)

    ts_00 = poisson_olasilik(ev_gol, 0) * poisson_olasilik(dep_gol, 0)
    ts_10 = poisson_olasilik(ev_gol, 1) * poisson_olasilik(dep_gol, 0)
    ts_20 = poisson_olasilik(ev_gol, 2) * poisson_olasilik(dep_gol, 0)
    ts_11 = poisson_olasilik(ev_gol, 1) * poisson_olasilik(dep_gol, 1)
    ts_21 = poisson_olasilik(ev_gol, 2) * poisson_olasilik(dep_gol, 1)
    ts_01 = poisson_olasilik(ev_gol, 0) * poisson_olasilik(dep_gol, 1)
    ts_02 = poisson_olasilik(ev_gol, 0) * poisson_olasilik(dep_gol, 2)

    def ai(p): return max(5, min(95, round(p * 100)))
    def opt(p): return olasiliktan_oran(max(0.01, min(0.99, p)))

    return [
        {
            "kategori": "Çifte Şans",
            "secenekler": [
                {"isim": "1X (Ev ya da Beraberlik)", "oran": opt(p_1x), "ai": ai(p_1x)},
                {"isim": "12 (Ev ya da Deplasman)", "oran": opt(p_12), "ai": ai(p_12)},
                {"isim": "X2 (Beraberlik ya da Dep.)", "oran": opt(p_x2), "ai": ai(p_x2)},
            ]
        },
        {
            "kategori": "Alt/Üst Gol",
            "secenekler": [
                {"isim": "Alt 0.5", "oran": opt(g05_alt), "ai": ai(g05_alt)},
                {"isim": "Üst 0.5", "oran": opt(g05_ust), "ai": ai(g05_ust)},
                {"isim": "Alt 1.5", "oran": opt(g15_alt), "ai": ai(g15_alt)},
                {"isim": "Üst 1.5", "oran": opt(g15_ust), "ai": ai(g15_ust)},
                {"isim": "Alt 2.5", "oran": opt(g25_alt), "ai": ai(g25_alt)},
                {"isim": "Üst 2.5", "oran": opt(g25_ust), "ai": ai(g25_ust)},
                {"isim": "Alt 3.5", "oran": opt(g35_alt), "ai": ai(g35_alt)},
                {"isim": "Üst 3.5", "oran": opt(g35_ust), "ai": ai(g35_ust)},
                {"isim": "Alt 4.5", "oran": opt(g45_alt), "ai": ai(g45_alt)},
                {"isim": "Üst 4.5", "oran": opt(g45_ust), "ai": ai(g45_ust)},
                {"isim": "Alt 5.5", "oran": opt(g55_alt), "ai": ai(g55_alt)},
                {"isim": "Üst 5.5", "oran": opt(g55_ust), "ai": ai(g55_ust)},
            ]
        },
        {
            "kategori": "Karşılıklı Gol",
            "secenekler": [
                {"isim": "KG Var", "oran": opt(kg_var), "ai": ai(kg_var)},
                {"isim": "KG Yok", "oran": opt(kg_yok), "ai": ai(kg_yok)},
                {"isim": "KG Var & Üst 2.5", "oran": opt(kg_var * g25_ust), "ai": ai(kg_var * g25_ust)},
                {"isim": "KG Var & Alt 2.5", "oran": opt(kg_var * g25_alt), "ai": ai(kg_var * g25_alt)},
            ]
        },
        {
            "kategori": "İlk Yarı Sonucu",
            "secenekler": [
                {"isim": "İY 1", "oran": opt(iy_p1), "ai": ai(iy_p1)},
                {"isim": "İY 0", "oran": opt(iy_p0), "ai": ai(iy_p0)},
                {"isim": "İY 2", "oran": opt(iy_p2), "ai": ai(iy_p2)},
                {"isim": "İY Alt 0.5", "oran": opt(iy_g05_alt), "ai": ai(iy_g05_alt)},
                {"isim": "İY Üst 0.5", "oran": opt(1 - iy_g05_alt), "ai": ai(1 - iy_g05_alt)},
                {"isim": "İY Alt 1.5", "oran": opt(iy_g15_alt), "ai": ai(iy_g15_alt)},
                {"isim": "İY Üst 1.5", "oran": opt(1 - iy_g15_alt), "ai": ai(1 - iy_g15_alt)},
            ]
        },
        {
            "kategori": "MS + Gol Kombine",
            "secenekler": [
                {"isim": "1 & Üst 1.5", "oran": opt(p1 * g15_ust * 1.1), "ai": ai(p1 * g15_ust)},
                {"isim": "1 & Alt 2.5", "oran": opt(p1 * g25_alt * 1.1), "ai": ai(p1 * g25_alt)},
                {"isim": "1 & Üst 2.5", "oran": opt(p1 * g25_ust * 1.1), "ai": ai(p1 * g25_ust)},
                {"isim": "X & Üst 1.5", "oran": opt(p0 * g15_ust * 1.2), "ai": ai(p0 * g15_ust)},
                {"isim": "X & Alt 2.5", "oran": opt(p0 * g25_alt * 1.2), "ai": ai(p0 * g25_alt)},
                {"isim": "2 & Üst 1.5", "oran": opt(p2 * g15_ust * 1.1), "ai": ai(p2 * g15_ust)},
                {"isim": "2 & Üst 2.5", "oran": opt(p2 * g25_ust * 1.1), "ai": ai(p2 * g25_ust)},
                {"isim": "1 & KG Var", "oran": opt(p1 * kg_var * 1.1), "ai": ai(p1 * kg_var)},
                {"isim": "2 & KG Var", "oran": opt(p2 * kg_var * 1.1), "ai": ai(p2 * kg_var)},
            ]
        },
        {
            "kategori": "Handikap",
            "secenekler": [
                {"isim": "Ev -1 Handikap", "oran": opt(max(0.05, p1 - 0.08)), "ai": ai(max(0.05, p1 - 0.08))},
                {"isim": "Dep +1 Handikap", "oran": opt(min(0.95, 1 - p1 + 0.08)), "ai": ai(min(0.95, 1 - p1 + 0.08))},
                {"isim": "Ev -2 Handikap", "oran": opt(max(0.05, p1 - 0.18)), "ai": ai(max(0.05, p1 - 0.18))},
                {"isim": "Dep +2 Handikap", "oran": opt(min(0.95, 1 - p1 + 0.18)), "ai": ai(min(0.95, 1 - p1 + 0.18))},
                {"isim": "Asya Handikap -0.5", "oran": opt(max(0.30, p1 + 0.05)), "ai": ai(max(0.30, p1 + 0.05))},
                {"isim": "Asya Handikap +0.5", "oran": opt(min(0.70, p2 + 0.05)), "ai": ai(min(0.70, p2 + 0.05))},
            ]
        },
        {
            "kategori": "Korner",
            "secenekler": [
                {"isim": "Korner Alt 8.5", "oran": opt(k85_alt), "ai": ai(k85_alt)},
                {"isim": "Korner Üst 8.5", "oran": opt(k85_ust), "ai": ai(k85_ust)},
                {"isim": "Korner Alt 9.5", "oran": opt(k95_alt), "ai": ai(k95_alt)},
                {"isim": "Korner Üst 9.5", "oran": opt(k95_ust), "ai": ai(k95_ust)},
                {"isim": "Korner Alt 10.5", "oran": opt(k105_alt), "ai": ai(k105_alt)},
                {"isim": "Korner Üst 10.5", "oran": opt(k105_ust), "ai": ai(k105_ust)},
                {"isim": "İY Korner Alt 4.5", "oran": opt(iy_k45_alt), "ai": ai(iy_k45_alt)},
                {"isim": "İY Korner Üst 4.5", "oran": opt(iy_k45_ust), "ai": ai(iy_k45_ust)},
            ]
        },
        {
            "kategori": "Toplam Kart",
            "secenekler": [
                {"isim": "Kart Alt 3.5", "oran": opt(ka35_alt), "ai": ai(ka35_alt)},
                {"isim": "Kart Üst 3.5", "oran": opt(ka35_ust), "ai": ai(ka35_ust)},
                {"isim": "Kart Alt 4.5", "oran": opt(ka45_alt), "ai": ai(ka45_alt)},
                {"isim": "Kart Üst 4.5", "oran": opt(ka45_ust), "ai": ai(ka45_ust)},
                {"isim": "Kart Alt 5.5", "oran": opt(ka55_alt), "ai": ai(ka55_alt)},
                {"isim": "Kart Üst 5.5", "oran": opt(ka55_ust), "ai": ai(ka55_ust)},
            ]
        },
        {
            "kategori": "İlk & Son Gol",
            "secenekler": [
                {"isim": "İlk Golü Ev Atar", "oran": opt(p_ilk_ev), "ai": ai(p_ilk_ev)},
                {"isim": "İlk Golü Dep. Atar", "oran": opt(p_ilk_dep), "ai": ai(p_ilk_dep)},
                {"isim": "İlk Yarıda Gol Yok", "oran": opt(iy_g05_alt), "ai": ai(iy_g05_alt)},
                {"isim": "Son Golü Ev Atar", "oran": opt(p1 * 0.75), "ai": ai(p1 * 0.75)},
                {"isim": "Son Golü Dep. Atar", "oran": opt(p2 * 0.75), "ai": ai(p2 * 0.75)},
            ]
        },
        {
            "kategori": "Tam Skor",
            "secenekler": [
                {"isim": "0-0", "oran": opt(max(0.02, ts_00)), "ai": ai(max(0.02, ts_00))},
                {"isim": "1-0", "oran": opt(max(0.03, ts_10)), "ai": ai(max(0.03, ts_10))},
                {"isim": "2-0", "oran": opt(max(0.02, ts_20)), "ai": ai(max(0.02, ts_20))},
                {"isim": "1-1", "oran": opt(max(0.03, ts_11)), "ai": ai(max(0.03, ts_11))},
                {"isim": "2-1", "oran": opt(max(0.03, ts_21)), "ai": ai(max(0.03, ts_21))},
                {"isim": "0-1", "oran": opt(max(0.02, ts_01)), "ai": ai(max(0.02, ts_01))},
                {"isim": "0-2", "oran": opt(max(0.01, ts_02)), "ai": ai(max(0.01, ts_02))},
                {"isim": "Diğer Skor", "oran": round(random.uniform(1.80, 3.20), 2), "ai": random.randint(10, 30)},
            ]
        },
    ]


def diger_spor_marketleri(spor, ms_olasiliklari):
    p1 = ms_olasiliklari["1"]
    p2 = ms_olasiliklari["2"]

    def ai(p): return max(5, min(95, round(p * 100)))
    def opt(p): return olasiliktan_oran(max(0.01, min(0.99, p)))

    if spor == "Basketbol":
        return [
            {
                "kategori": "Handikap",
                "secenekler": [
                    {"isim": "Ev -5.5", "oran": opt(max(0.1, p1 - 0.08)), "ai": ai(max(0.1, p1 - 0.08))},
                    {"isim": "Dep +5.5", "oran": opt(min(0.9, p2 + 0.08)), "ai": ai(min(0.9, p2 + 0.08))},
                    {"isim": "Ev -10.5", "oran": opt(max(0.05, p1 - 0.15)), "ai": ai(max(0.05, p1 - 0.15))},
                    {"isim": "Dep +10.5", "oran": opt(min(0.95, p2 + 0.15)), "ai": ai(min(0.95, p2 + 0.15))},
                ]
            },
            {
                "kategori": "Toplam Puan Alt/Üst",
                "secenekler": [
                    {"isim": "Alt 200.5", "oran": round(random.uniform(1.70, 2.10), 2), "ai": random.randint(35, 55)},
                    {"isim": "Üst 200.5", "oran": round(random.uniform(1.70, 2.10), 2), "ai": random.randint(45, 65)},
                    {"isim": "Alt 210.5", "oran": round(random.uniform(1.55, 2.00), 2), "ai": random.randint(40, 60)},
                    {"isim": "Üst 210.5", "oran": round(random.uniform(1.55, 2.00), 2), "ai": random.randint(40, 60)},
                    {"isim": "Alt 220.5", "oran": round(random.uniform(1.40, 1.80), 2), "ai": random.randint(45, 65)},
                    {"isim": "Üst 220.5", "oran": round(random.uniform(1.40, 1.80), 2), "ai": random.randint(35, 55)},
                ]
            },
            {
                "kategori": "Çeyrekler",
                "secenekler": [
                    {"isim": "1. Çeyrek Ev", "oran": round(random.uniform(1.80, 2.10), 2), "ai": random.randint(40, 60)},
                    {"isim": "1. Çeyrek Dep", "oran": round(random.uniform(1.80, 2.10), 2), "ai": random.randint(40, 60)},
                    {"isim": "İlk Yarı Ev", "oran": opt(max(0.30, p1 * 0.90)), "ai": ai(max(0.30, p1 * 0.90))},
                    {"isim": "İlk Yarı Dep", "oran": opt(min(0.70, p2 * 0.90)), "ai": ai(min(0.70, p2 * 0.90))},
                    {"isim": "İkinci Yarı Ev", "oran": opt(p1), "ai": ai(p1)},
                    {"isim": "İkinci Yarı Dep", "oran": opt(p2), "ai": ai(p2)},
                ]
            },
            {
                "kategori": "Özel Bahisler",
                "secenekler": [
                    {"isim": "Uzatma Olur", "oran": round(random.uniform(3.50, 7.00), 2), "ai": random.randint(5, 20)},
                    {"isim": "Uzatma Olmaz", "oran": round(random.uniform(1.05, 1.25), 2), "ai": random.randint(80, 95)},
                    {"isim": "Fark 1-5 Puan", "oran": round(random.uniform(2.80, 3.50), 2), "ai": random.randint(15, 30)},
                    {"isim": "Fark 6-10 Puan", "oran": round(random.uniform(2.50, 3.20), 2), "ai": random.randint(18, 32)},
                    {"isim": "Fark 11+ Puan", "oran": round(random.uniform(1.60, 2.20), 2), "ai": random.randint(30, 55)},
                ]
            },
        ]
    elif spor == "Tenis":
        return [
            {
                "kategori": "Set Bahisleri",
                "secenekler": [
                    {"isim": "2-0 P1 Kazanır", "oran": opt(max(0.10, p1 * 0.60)), "ai": ai(max(0.10, p1 * 0.60))},
                    {"isim": "2-1 P1 Kazanır", "oran": opt(max(0.10, p1 * 0.40)), "ai": ai(max(0.10, p1 * 0.40))},
                    {"isim": "0-2 P2 Kazanır", "oran": opt(max(0.10, p2 * 0.60)), "ai": ai(max(0.10, p2 * 0.60))},
                    {"isim": "1-2 P2 Kazanır", "oran": opt(max(0.10, p2 * 0.40)), "ai": ai(max(0.10, p2 * 0.40))},
                ]
            },
            {
                "kategori": "Toplam Oyun Alt/Üst",
                "secenekler": [
                    {"isim": "Alt 18.5 Oyun", "oran": round(random.uniform(1.80, 2.30), 2), "ai": random.randint(30, 50)},
                    {"isim": "Üst 18.5 Oyun", "oran": round(random.uniform(1.60, 2.10), 2), "ai": random.randint(50, 70)},
                    {"isim": "Alt 21.5 Oyun", "oran": round(random.uniform(1.55, 2.00), 2), "ai": random.randint(40, 60)},
                    {"isim": "Üst 21.5 Oyun", "oran": round(random.uniform(1.55, 2.00), 2), "ai": random.randint(40, 60)},
                ]
            },
            {
                "kategori": "1. Set & Servis",
                "secenekler": [
                    {"isim": "1. Seti P1 Kazanır", "oran": opt(max(0.30, p1 * 1.10)), "ai": ai(max(0.30, p1 * 1.10))},
                    {"isim": "1. Seti P2 Kazanır", "oran": opt(min(0.70, p2 * 1.10)), "ai": ai(min(0.70, p2 * 1.10))},
                    {"isim": "1. Set Tiebreak Olur", "oran": round(random.uniform(2.50, 4.00), 2), "ai": random.randint(15, 30)},
                    {"isim": "P1 Ace Üst 5.5", "oran": round(random.uniform(1.70, 2.20), 2), "ai": random.randint(35, 55)},
                    {"isim": "P2 Ace Üst 5.5", "oran": round(random.uniform(1.70, 2.20), 2), "ai": random.randint(35, 55)},
                    {"isim": "Toplam Ace Üst 10.5", "oran": round(random.uniform(1.60, 2.10), 2), "ai": random.randint(40, 60)},
                ]
            },
        ]
    elif spor == "Voleybol":
        return [
            {
                "kategori": "Set Sayısı",
                "secenekler": [
                    {"isim": "3-0 Ev Kazanır", "oran": opt(max(0.10, p1 * 0.45)), "ai": ai(max(0.10, p1 * 0.45))},
                    {"isim": "3-1 Ev Kazanır", "oran": opt(max(0.10, p1 * 0.35)), "ai": ai(max(0.10, p1 * 0.35))},
                    {"isim": "3-2 Ev Kazanır", "oran": opt(max(0.05, p1 * 0.20)), "ai": ai(max(0.05, p1 * 0.20))},
                    {"isim": "0-3 Dep. Kazanır", "oran": opt(max(0.05, p2 * 0.45)), "ai": ai(max(0.05, p2 * 0.45))},
                    {"isim": "1-3 Dep. Kazanır", "oran": opt(max(0.05, p2 * 0.35)), "ai": ai(max(0.05, p2 * 0.35))},
                    {"isim": "2-3 Dep. Kazanır", "oran": opt(max(0.05, p2 * 0.20)), "ai": ai(max(0.05, p2 * 0.20))},
                ]
            },
            {
                "kategori": "Toplam Set & 1. Set",
                "secenekler": [
                    {"isim": "Alt 3.5 Set", "oran": round(random.uniform(1.70, 2.20), 2), "ai": random.randint(40, 60)},
                    {"isim": "Üst 3.5 Set", "oran": round(random.uniform(1.70, 2.20), 2), "ai": random.randint(40, 60)},
                    {"isim": "1. Seti Ev Kazanır", "oran": opt(max(0.30, p1 * 1.10)), "ai": ai(max(0.30, p1 * 1.10))},
                    {"isim": "1. Seti Dep. Kazanır", "oran": opt(min(0.70, p2 * 1.10)), "ai": ai(min(0.70, p2 * 1.10))},
                ]
            },
        ]
    return []
