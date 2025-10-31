#!/usr/bin/env python3
import requests, os
from datetime import datetime, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ZONAS = {
    "Isla Dragonera": (39.60, 2.30),
    "Isla de Cabrera": (39.17, 2.89),
    "Bahía de Palma": (39.57, 2.73),
    "Portals Vells": (39.52, 2.54),
    "Llucmajor": (39.33, 3.07),
    "Punta Negra": (39.45, 3.00),
    "Cala d'Or": (39.35, 3.40),
    "Porto Cristo": (39.42, 3.41),
    "Cala Millor": (39.49, 3.38),
    "Bahía Pollença": (39.83, 3.09),
    "Alcúdia": (39.85, 3.11),
    "Can Picafort": (39.73, 3.14),
    "Formentor": (39.96, 3.25),
    "Cala Sant Vicenç": (39.88, 3.13),
    "Sóller": (39.77, 2.73),
}

dias_resultado = {0: [], 1: [], 2: []}

for nombre, (lat, lon) in ZONAS.items():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,windspeed_10m_max&timezone=Europe/Madrid&forecast_days=3"
        datos = requests.get(url, timeout=10).json()
        for dia_idx in range(3):
            temp = datos["daily"]["temperature_2m_max"][dia_idx]
            viento_kmh = datos["daily"]["windspeed_10m_max"][dia_idx]
            viento_nudos = viento_kmh * 0.539957
            if viento_nudos > 7:
                score = 2
                rating = "🔴 REGULAR"
            elif viento_nudos > 5:
                score = 5
                rating = "🟡 BUENO"
            else:
                score = 9
                rating = "🟢 EXCELENTE"
            dias_resultado[dia_idx].append({"nombre": nombre, "temp": temp, "viento": viento_nudos, "score": score, "rating": rating})
    except:
        pass

for dia in dias_resultado:
    dias_resultado[dia].sort(key=lambda x: x["score"], reverse=True)

msg = "🎣 RECOMENDACIONES MALLORKAYAK\n"
msg += f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

dias_nombres = ["🌅 HOY", "🌤️ MAÑANA", "⛅ PASADO MAÑANA"]
medallas = ["🥇", "🥈", "🥉"]

for dia_idx in range(3):
    fecha = (datetime.now() + timedelta(days=dia_idx)).strftime("%d/%m")
    msg += f"{dias_nombres[dia_idx]} - {fecha}\n"
    msg += "━━━━━━━━━━━━━━━━━\n"
    for idx, zona in enumerate(dias_resultado[dia_idx][:3]):
        medalla = medallas[idx]
        msg += f"{medalla} {zona['nombre']}\n"
        msg += f"⭐ {zona['score']}/10 | {zona['rating']}\n"
        msg += f"💨 {zona['viento']:.1f} nudos | 🌡️ {zona['temp']:.1f}°C\n\n"
    msg += "\n"

print(msg)

if TOKEN and CHAT_ID:
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("✅ Enviado a Telegram")
    except:
        print("❌ Error Telegram")
