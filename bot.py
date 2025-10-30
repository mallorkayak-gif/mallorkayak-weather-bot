#!/usr/bin/env python3
import requests
from datetime import datetime
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ZONAS = {
    "Isla Dragonera": {"lat": 39.60, "lon": 2.30},
    "Isla de Cabrera": {"lat": 39.17, "lon": 2.89},
    "Bahía de Palma": {"lat": 39.57, "lon": 2.73},
    "Portals Vells": {"lat": 39.52, "lon": 2.54},
    "Llucmajor": {"lat": 39.33, "lon": 3.07},
    "Punta Negra": {"lat": 39.45, "lon": 3.00},
    "Cala d'Or": {"lat": 39.35, "lon": 3.40},
    "Porto Cristo": {"lat": 39.42, "lon": 3.41},
    "Cala Millor": {"lat": 39.49, "lon": 3.38},
    "Bahía Pollença": {"lat": 39.83, "lon": 3.09},
    "Alcúdia": {"lat": 39.85, "lon": 3.11},
    "Can Picafort": {"lat": 39.73, "lon": 3.14},
    "Formentor": {"lat": 39.96, "lon": 3.25},
    "Cala Sant Vicenç": {"lat": 39.88, "lon": 3.13},
    "Sóller": {"lat": 39.77, "lon": 2.73},
}

def obtener_datos(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,windspeed_10m",
            "timezone": "Europe/Madrid"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def calcular_puntuacion(viento):
    if viento > 7:
        return 2
    elif viento > 5:
        return 5
    else:
        return 9

def get_rating(score):
    if score >= 9:
        return "🟢 EXCELENTE"
    elif score >= 7:
        return "🟢 MUY BUENO"
    elif score >= 5:
        return "🟡 BUENO"
    else:
        return "🔴 REGULAR"

def main():
    print("🚀 Iniciando bot...")
    
    resultados = []
    
    for nombre, coords in ZONAS.items():
        datos = obtener_datos(coords["lat"], coords["lon"])
        
        if not datos or "current" not in datos:
            continue
        
        temp = datos["current"]["temperature_2m"]
        viento_kmh = datos["current"]["windspeed_10m"]
        viento_nudos = viento_kmh * 0.539957
        
        score = calcular_puntuacion(viento_nudos)
        rating = get_rating(score)
        
        resultados.append({
            "nombre": nombre,
            "temp": temp,
            "viento": viento_nudos,
            "score": score,
            "rating": rating
        })
    
    resultados.sort(key=lambda x: x["score"], reverse=True)
    
    if resultados:
        msg = f"🎣 RECOMENDACIONES MALLORKAYAK\n\n"
        msg += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        medallas = ["🥇", "🥈", "🥉"]
        
        for idx, zona in enumerate(resultados[:5]):
            medalla = medallas[idx] if idx < 3 else "  "
            msg += f"{medalla} {zona['nombre']}\n"
            msg += f"⭐ {zona['score']}/10\n"
            msg += f"🌡️ {zona['temp']:.1f}°C | 💨 {zona['viento']:.1f} nudos\n"
            msg += f"{zona['rating']}\n\n"
        
        print(msg)
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
                requests.post(url, json=data, timeout=10)
                print("✅ Mensaje enviado")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
