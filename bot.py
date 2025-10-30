#!/usr/bin/env python3
import requests, os
from datetime import datetime

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

zonas_resultado = []

for nombre, (lat, lon) in ZONAS.items():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,windspeed_10m&timezone=Europe/Madrid"
        datos = requests.get(url, timeout=10).json()
        temp = datos["current"]["temperature_2m"]
        viento_kmh = datos["current"]["windspeed_10m"]
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
        
        zonas_resultado.append({
            "nombre": nombre,
            "temp": temp,
            "viento": viento_nudos,
            "score": score,
            "rating": rating
        })
    except:
        pass

zonas_resultado.sort(key=lambda x: x["score"], reverse=True)

msg = f"🎣 RECOMENDACIONES MALLORKAYAK\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

medallas = ["🥇", "🥈", "🥉"]

for idx, zona in enumerate(zonas_resultado[:5]):
    medalla = medallas[idx] if idx < 3 else "  "
    msg += f"{medalla} {zona['nombre']}\n⭐ {zona['score']}/10\n🌡️ {zona['temp']:.1f}°C | 💨 {zona['viento']:.1f} nudos\n{zona['rating']}\n\n"

print(msg)

if TOKEN and CHAT_ID:
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("✅ Enviado a Telegram")
    except:
        print("❌ Error Telegram")
