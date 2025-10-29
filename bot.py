#!/usr/bin/env python3
"""
🎣 MallorKayak Weather Bot - VERSIÓN ULTRA SIMPLIFICADA
"""

import requests
import json
from datetime import datetime, timedelta
import os
import sys
import time

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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def obtener_datos_meteo(lat, lon, zona_name):
    """Obtiene datos de Open-Meteo de forma SIMPLE"""
    url = "https://api.open-meteo.com/v1/forecast"
    
    # PARÁMETROS MÁS SIMPLES
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "windspeed_10m_max,temperature_2m_max",
        "timezone": "Europe/Madrid"
    }
    
    try:
        print(f"  📍 {zona_name}...", end=" ", flush=True)
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            datos = response.json()
            print("✅")
            return datos
        else:
            print(f"❌ {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ {str(e)[:20]}")
        return None

def calcular_puntuacion_simple(datos, dia_index):
    """Calcula puntuación básica"""
    try:
        if not datos or 'daily' not in datos:
            return 0
        
        daily = datos['daily']
        
        if dia_index >= len(daily['windspeed_10m_max']):
            return 0
        
        viento_ms = daily['windspeed_10m_max'][dia_index]
        viento_nudos = viento_ms * 1.944
        
        puntos = 0
        
        # Viento ideal: 5-12 nudos
        if 5 <= viento_nudos <= 12:
            puntos = 9
        elif 3 <= viento_nudos <= 15:
            puntos = 7
        elif viento_nudos < 3 or 15 < viento_nudos <= 20:
            puntos = 4
        else:
            puntos = 0
        
        # Temperatura bonus
        temp = daily['temperature_2m_max'][dia_index]
        if 18 <= temp <= 24:
            puntos += 1
        
        return min(puntos, 10)
    except:
        return 0

def generar_reporte():
    """Genera reporte simple"""
    
    reporte = "🎣 *RECOMENDACIONES KAYAK OFFSHORE - MALLORCA*\n"
    reporte += f"📅 {datetime.now().strftime('%d/%m/%Y')} | 11:00\n"
    reporte += "═" * 50 + "\n\n"
    
    mejor_dia = None
    mejor_zona = None
    mejor_puntuacion = 0
    
    for dia in range(3):
        fecha_dia = datetime.now() + timedelta(days=dia)
        nombre_dia = fecha_dia.strftime('%A')
        
        dias_traduccion = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        nombre_dia = dias_traduccion.get(nombre_dia, nombre_dia)
        fecha_str = fecha_dia.strftime('%d/%m')
        
        reporte += f"📌 *{nombre_dia.upper()} {fecha_str}*\n"
        
        print(f"\n📅 {nombre_dia} {fecha_str}:")
        
        resultados = []
        
        for zona, coords in ZONAS.items():
            datos = obtener_datos_meteo(coords['lat'], coords['lon'], zona)
            
            if datos:
                puntuacion = calcular_puntuacion_simple(datos, dia)
                
                try:
                    viento = datos['daily']['windspeed_10m_max'][dia] * 1.944
                    temp = datos['daily']['temperature_2m_max'][dia]
                    
                    resultados.append({
                        'zona': zona,
                        'puntos': puntuacion,
                        'viento': viento,
                        'temp': temp
                    })
                except:
                    pass
            
            time.sleep(0.5)  # Pequeña pausa entre peticiones
        
        resultados.sort(key=lambda x: x['puntos'], reverse=True)
        
        # Top 3
        for i, r in enumerate(resultados[:3]):
            emojis = ["🥇", "🥈", "🥉"]
            emoji_pos = emojis[i] if i < 3 else "•"
            
            reporte += f"{emoji_pos} *{r['zona']}*\n"
            reporte += f"   ⭐ {r['puntos']:.0f}/10 | 💨 {r['viento']:.1f} nudos | 🌡️ {r['temp']:.0f}°C\n"
            
            if r['puntos'] > mejor_puntuacion:
                mejor_puntuacion = r['puntos']
                mejor_zona = r['zona']
                mejor_dia = nombre_dia
        
        reporte += "\n"
    
    reporte += "═" * 50 + "\n"
    if mejor_zona:
        reporte += f"🎯 *MEJOR DÍA*: {mejor_dia} - {mejor_zona}\n"
        reporte += f"   ⭐ {mejor_puntuacion:.0f}/10\n\n"
    
    reporte += "💡 *Consejos*: Salida 6:00-7:00 AM | Equipo: Traje 3-5mm, casco, GPS\n"
    
    return reporte

def enviar_telegram(mensaje):
    """Envía a Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Falta TOKEN o CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensaje enviado")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False

if __name__ == "__main__":
    try:
        print("🎣 MallorKayak Weather Bot\n")
        reporte = generar_reporte()
        
        print("\n" + "="*50)
        print(reporte)
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            print("\n📤 Enviando...")
            enviar_telegram(reporte)
        
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
