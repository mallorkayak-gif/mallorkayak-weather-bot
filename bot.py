#!/usr/bin/env python3
"""
🎣 MallorKayak Weather Bot - CON 3 DÍAS
"""

import requests
from datetime import datetime, timedelta
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
            "daily": "temperature_2m_max,windspeed_10m_max",
            "timezone": "Europe/Madrid",
            "forecast_days": 3
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def calcular_puntuacion(viento):
    """Calcula puntuación - SOLO BASADO EN VIENTO"""
    
    if viento > 7:
        return 2  # ROJO - Viento malo
    elif viento > 5:
        return 5  # AMARILLO - Viento regular
    else:
        return 9  # VERDE - Viento bueno

def get_rating(score):
    """Asigna rating según puntuación"""
    if score >= 9:
        return "🟢 EXCELENTE"
    elif score >= 7:
        return "🟢 MUY BUENO"
    elif score >= 5:
        return "🟡 BUENO"
    else:
        return "🔴 REGULAR"

def formatear_mensaje(resultados_por_dia):
    """Formatea mensaje para Telegram con 3 días"""
    
    msg = "🎣 RECOMENDACIONES MALLORKAYAK\n\n"
    
    dias_nombres = ["HOY", "MAÑANA", "PASADO MAÑANA"]
    
    for dia_idx, (fecha, zonas) in enumerate(resultados_por_dia.items()):
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_str = fecha_obj.strftime("%d/%m/%Y")
        
        msg += f"📅 {dias_nombres[dia_idx]} - {fecha_str}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        medallas = ["🥇", "🥈", "🥉"]
        
        for idx, zona in enumerate(zonas[:3]):
            medalla = medallas[idx]
            msg += f"{medalla} {zona['nombre']}\n"
            msg += f"⭐ {zona['score']}/10 | {zona['rating']}\n"
            msg += f"💨 {zona['viento']:.1f} nudos | 🌡️ {zona['temp']:.1f}°C\n\n"
        
        msg += "\n"
    
    return msg

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Test mode - printing message:")
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
        print(f"❌ Error: {str(e)}")

def main():
    print("🚀 Iniciando bot...")
    
    resultados_por_dia = {}
    
    for nombre, coords in ZONAS.items():
        datos = obtener_datos(coords["lat"], coords["lon"])
        
        if not datos or "daily" not in datos:
            continue
        
        daily = datos["daily"]
        
        # Procesar 3 días
        for day in range(3):
            fecha = daily["time"][day]
            
            if fecha not in resultados_por_dia:
                resultados_por_dia[fecha] = []
            
            temp = daily["temperature_2m_max"][day]
            viento_kmh = daily["windspeed_10m_max"][day]
            viento_nudos = viento_kmh * 0.539957
            
            score = calcular_puntuacion(viento_nudos)
            rating = get_rating(score)
            
            resultados_por_dia[fecha].append({
                "nombre": nombre,
                "temp": temp,
                "viento": viento_nudos,
                "score": score,
                "rating": rating
            })
    
    # Ordenar cada día por puntuación
    for fecha in resultados_por_dia:
        resultados_por_dia[fecha].sort(key=lambda x: x["score"], reverse=True)
    
    if resultados_por_dia:
        print(f"✅ Análisis completado para 3 días")
        mensaje = formatear_mensaje(resultados_por_dia)
        print(mensaje)
        enviar_telegram(mensaje)
    else:
        print("❌ No se obtuvieron datos")

if __name__ == "__main__":
    main()
