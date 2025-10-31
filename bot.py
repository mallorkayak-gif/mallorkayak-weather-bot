#!/usr/bin/env python3
import requests, os
from datetime import datetime, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ZONAS = {"Isla Dragonera": (39.60, 2.30), "Isla de Cabrera": (39.17, 2.89), "Bahía de Palma": (39.57, 2.73), "Portals Vells": (39.52, 2.54), "Llucmajor": (39.33, 3.07), "Punta Negra": (39.45, 3.00), "Cala d'Or": (39.35, 3.40), "Porto Cristo": (39.42, 3.41), "Cala Millor": (39.49, 3.38), "Bahía Pollença": (39.83, 3.09), "Alcúdia": (39.85, 3.11), "Can Picafort": (39.73, 3.14), "Formentor": (39.96, 3.25), "Cala Sant Vicenç": (39.88, 3.13), "Sóller": (39.77, 2.73)}

dias = {0: [], 1: [], 2: []}

for nombre, (lat, lon) in ZONAS.items():
    try:
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,windspeed_10m_max&timezone=Europe/Madrid&forecast_days=3", timeout=10).json()
        for d in range(3):
            t = r["daily"]["temperature_2m_max"][d]
            w = r["daily"]["windspeed_10m_max"][d] * 0.539957
            s = 2 if w > 7 else (5 if w > 5 else 9)
            rat = "🔴 REGULAR" if w > 7 else ("🟡 BUENO" if w > 5 else "🟢 EXCELENTE")
            dias[d].append({"nombre": nombre, "temp": t, "viento": w, "score": s, "rating": rat})
    except:
        pass

for d in dias:
    dias[d].sort(key=lambda x: x["score"], reverse=True)

msg = f"🎣 RECOMENDACIONES MALLORKAYAK\n📅 {datetime.now().strftime('%d/%m/%Y')}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
nombres = ["🌅 HOY", "🌤️ MAÑANA", "⛅ PASADO MAÑANA"]
medallas = ["🥇", "🥈", "🥉"]

for di in range(3):
    fecha = (datetime.now() + timedelta(days=di)).strftime("%d/%m")
    msg += f"{nombres[di]} - {fecha}\n━━━━━━━━━━━━━━━━━\n"
    for idx, z in enumerate(dias[di][:3]):
        msg += f"{medallas[idx]} {z['nombre']}\n⭐ {z['score']}/10 | {z['rating']}\n💨 {z['viento']:.1f} nudos | 🌡️ {z['temp']:.1f}°C\n\n"
    msg += "\n"

print(msg)

if TOKEN and CHAT_ID:
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("✅ Enviado")
    except:
        print("❌ Error")
