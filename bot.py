#!/usr/bin/env python3
"""
🎣 MallorKayak Weather Bot - VERSIÓN FUNCIONAL
Bot meteorológico para Telegram usando Open-Meteo (100% gratis)
"""

import requests
import json
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
    """Obtiene datos de Open-Meteo"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,windspeed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max,precipitation_sum",
            "timezone": "Europe/Madrid"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def calcular_puntuacion(temp, viento):
    """Calcula puntuación basada en temp y viento"""
    score = 0
    
    # VIENTO (0-5 bueno, 5-7 regular, >7 malo)
    if viento <= 5:
        score += 5  # BUENO
    elif viento <= 7:
        score += 3  # REGULAR
    else:
        score += 1  # MALO
    
    # TEMPERATURA (ideal: 18-24°C)
    if 18 <= temp <= 24:
        score += 5  # IDEAL
    elif 15 <= temp <= 25:
        score += 3  # BUENA
    else:
        score += 1  # FRÍA
    
    return min(10, score)

def formatear_mensaje(resultados):
    """Formatea mensaje para Telegram"""
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    msg = f"🎣 RECOMENDACIONES MALLORKAYAK\n\n"
    msg += f"📅 {hoy}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    medallas = ["🥇", "🥈", "🥉"]
    
    for idx, zona in enumerate(resultados[:5]):
        medalla = medallas[idx] if idx < 3 else "  "
        msg += f"{medalla} {zona['nombre']}\n"
        msg += f"⭐ {zona['score']}/10\n"
        msg += f"🌡️ {zona['temp']:.1f}°C | 💨 {zona['viento']:.1f} nudos\n"
        msg += f"{zona['rating']}\n\n"
    
    return msg

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("No Telegram configured - printing message:")
        print(mensaje)
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje
        }
        requests.post(url, json=data, timeout=10)
        print("✅ Mensaje enviado a Telegram")
    except Exception as e:
        print(f"❌ Error Telegram: {str(e)}")

def main():
    print("🚀 Iniciando bot...")
    
    resultados = []
    
    for nombre, coords in ZONAS.items():
        datos = obtener_datos(coords["lat"], coords["lon"])
        
        if not datos or "current" not in datos:
            continue
        
        temp = datos["current"]["temperature_2m"]
        viento = datos["current"]["windspeed_10m"]
        
        # Convertir km/h a nudos
        viento_nudos = viento * 0.539957
        
        score = calcular_puntuacion(temp, viento_nudos)
        
        # Rating
        if score >= 9:
            rating = "🟢 EXCELENTE"
        elif score >= 7:
            rating = "🟢 MUY BUENO"
        elif score >= 5:
            rating = "🟡 BUENO"
        else:
            rating = "🔴 REGULAR"
        
        resultados.append({
            "nombre": nombre,
            "temp": temp,
            "viento": viento_nudos,
            "score": score,
            "rating": rating
        })
    
    # Ordenar por puntuación
    resultados.sort(key=lambda x: x["score"], reverse=True)
    
    if resultados:
        print(f"✅ {len(resultados)} zonas analizadas")
        mensaje = formatear_mensaje(resultados)
        print(mensaje)
        enviar_telegram(mensaje)
    else:
        print("❌ No se obtuvieron datos")

if __name__ == "__main__":
    main()
