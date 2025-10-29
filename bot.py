#!/usr/bin/env python3
"""
🎣 MallorKayak Weather Bot - VERSIÓN MEJORADA
Bot meteorológico para kayak offshore en Mallorca
Peticiones secuenciales + reintentos automáticos
"""

import requests
import json
from datetime import datetime, timedelta
import os
import sys
import time

# ============ CONFIGURACIÓN ============
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

print(f"🤖 Bot iniciando... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📍 Zonas a analizar: {len(ZONAS)}")
print(f"📱 Telegram configurado: {'✅' if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID else '❌'}")

# ============ FUNCIONES ============

def obtener_datos_meteo_con_reintentos(lat, lon, zona_name, intentos=3):
    """
    Obtiene datos de Open-Meteo con reintentos automáticos
    Peticiones SECUENCIALES para no sobrecargar la API
    """
    url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "windspeed_10m,wave_height,wave_direction,visibility",
        "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max,precipitation_sum",
        "timezone": "Europe/Madrid",
        "forecast_days": 3
    }
    
    for intento in range(intentos):
        try:
            print(f"  📊 {zona_name}: intento {intento + 1}/{intentos}...", end=" ", flush=True)
            response = requests.get(url, params=params, timeout=20)  # Aumentar timeout
            
            if response.status_code == 200:
                print("✅")
                return response.json()
            else:
                print(f"⚠️ ({response.status_code})")
                if intento < intentos - 1:
                    time.sleep(2)  # Esperar 2 segundos antes de reintentar
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            if intento < intentos - 1:
                time.sleep(2)
    
    return None

def calcular_puntuacion(datos, dia_index):
    """Calcula puntuación 0-10 para kayak offshore"""
    
    if not datos or dia_index >= len(datos['daily']['windspeed_10m_max']):
        return 0
    
    try:
        puntos = 0
        
        # ===== VIENTO (máx 3 puntos) =====
        viento_ms = datos['daily']['windspeed_10m_max'][dia_index]
        viento_nudos = viento_ms * 1.944
        
        if 5 <= viento_nudos <= 12:
            puntos += 3
        elif 3 <= viento_nudos <= 15:
            puntos += 2
        elif viento_nudos < 3 or 15 < viento_nudos <= 20:
            puntos += 1
        
        # ===== OLAS (máx 2 puntos) =====
        inicio = dia_index * 24
        fin = inicio + 24
        
        if inicio < len(datos['hourly']['wave_height']):
            olas_dia = datos['hourly']['wave_height'][inicio:min(fin, len(datos['hourly']['wave_height']))]
            ola_promedio = sum(olas_dia) / len(olas_dia) if olas_dia else 0
            
            if 0.5 <= ola_promedio <= 1.2:
                puntos += 2
            elif 0.2 <= ola_promedio <= 1.8:
                puntos += 1
        
        # ===== VISIBILIDAD (máx 1.5 puntos) =====
        if inicio < len(datos['hourly']['visibility']):
            visibilidad_dia = datos['hourly']['visibility'][inicio:min(fin, len(datos['hourly']['visibility']))]
            visibilidad_media = sum(visibilidad_dia) / len(visibilidad_dia) if visibilidad_dia else 0
            
            if visibilidad_media > 15000:
                puntos += 1.5
            elif visibilidad_media > 10000:
                puntos += 1
        
        # ===== LLUVIA (penalización -1) =====
        precipitacion = datos['daily']['precipitation_sum'][dia_index]
        if precipitacion > 2:
            puntos -= 1
        
        # ===== TEMPERATURA (bonus +0.5) =====
        temp = datos['daily']['temperature_2m_max'][dia_index]
        if 18 <= temp <= 24:
            puntos += 0.5
        
        return max(0, min(puntos, 10))
    
    except Exception as e:
        print(f"  ❌ Error calculando puntuación: {e}")
        return 0

def generar_reporte():
    """Genera reporte de 3 días"""
    
    reporte = "🎣 *RECOMENDACIONES KAYAK OFFSHORE - MALLORCA*\n"
    reporte += f"📅 {datetime.now().strftime('%d de %B de %Y')} | 11:00\n"
    reporte += "═" * 50 + "\n\n"
    
    mejor_dia = None
    mejor_zona = None
    mejor_puntuacion = 0
    
    # Procesar 3 días
    for dia in range(3):
        fecha_dia = datetime.now() + timedelta(days=dia)
        nombre_dia = fecha_dia.strftime('%A')
        
        # Traducir días
        dias_traduccion = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        nombre_dia = dias_traduccion.get(nombre_dia, nombre_dia)
        fecha_str = fecha_dia.strftime('%d/%m')
        
        reporte += f"📌 *{nombre_dia.upper()} {fecha_str}*\n"
        reporte += "─" * 50 + "\n"
        
        print(f"\n🔄 Procesando {nombre_dia} {fecha_str}...")
        
        resultados = []
        
        # Obtener datos para TODAS las zonas SECUENCIALMENTE
        for zona, coords in ZONAS.items():
            datos = obtener_datos_meteo_con_reintentos(coords['lat'], coords['lon'], zona, intentos=3)
            
            if datos:
                puntuacion = calcular_puntuacion(datos, dia)
                
                # Extraer datos
                viento_ms = datos['daily']['windspeed_10m_max'][dia]
                viento_nudos = viento_ms * 1.944
                
                inicio = dia * 24
                fin = inicio + 24
                olas_dia = datos['hourly']['wave_height'][inicio:min(fin, len(datos['hourly']['wave_height']))]
                ola_promedio = sum(olas_dia) / len(olas_dia) if olas_dia else 0
                
                temp = datos['daily']['temperature_2m_max'][dia]
                precipitacion = datos['daily']['precipitation_sum'][dia]
                
                resultados.append({
                    'zona': zona,
                    'puntos': puntuacion,
                    'viento': viento_nudos,
                    'ola': ola_promedio,
                    'temp': temp,
                    'lluvia': precipitacion
                })
                
                # Trackear mejor
                if puntuacion > mejor_puntuacion:
                    mejor_puntuacion = puntuacion
                    mejor_zona = zona
                    mejor_dia = nombre_dia
            else:
                print(f"  ⚠️ No se obtuvieron datos para {zona}")
        
        # Ordena por puntuación
        resultados.sort(key=lambda x: x['puntos'], reverse=True)
        
        # Top 3
        for i, r in enumerate(resultados[:3]):
            if i == 0:
                emoji_pos = "🥇"
            elif i == 1:
                emoji_pos = "🥈"
            else:
                emoji_pos = "🥉"
            
            if r['puntos'] >= 8:
                emoji_recomendacion = "✅ EXCELENTE"
            elif r['puntos'] >= 6:
                emoji_recomendacion = "👍 BUENO"
            else:
                emoji_recomendacion = "⚠️ ACEPTABLE"
            
            reporte += f"{emoji_pos} *{r['zona']}* {emoji_recomendacion}\n"
            reporte += f"   ⭐ {r['puntos']:.1f}/10 | 💨 {r['viento']:.1f} nudos | 🌊 {r['ola']:.2f}m | 🌡️ {r['temp']:.0f}°C\n"
            
            if r['lluvia'] > 0:
                reporte += f"   🌧️ Lluvia: {r['lluvia']:.1f}mm\n"
        
        # Zona a evitar
        if resultados and resultados[-1]['puntos'] < 4:
            peor = resultados[-1]
            reporte += f"\n❌ *EVITAR*: {peor['zona']} ({peor['puntos']:.1f}/10)\n"
        
        reporte += "\n"
    
    # Resumen final
    reporte += "═" * 50 + "\n"
    if mejor_zona:
        reporte += f"🎯 *MEJOR DÍA*: {mejor_dia} en {mejor_zona}\n"
        reporte += f"   ⭐ {mejor_puntuacion:.1f}/10\n\n"
    
    reporte += "💡 *CONSEJOS*:\n"
    reporte += "   • Salida: 6:00-7:00 AM (antes del viento)\n"
    reporte += "   • Equipo: Traje 3-5mm, casco, GPS, chaleco\n"
    reporte += "   • Seguridad: Nunca solo en offshore\n"
    reporte += "   • Revisa antes de salir\n"
    
    return reporte

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Faltan credenciales de Telegram")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram correctamente")
            return True
        else:
            print(f"❌ Error Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Excepción en Telegram: {e}")
        return False

# ============ MAIN ============

if __name__ == "__main__":
    try:
        print("\n🔄 Generando reporte...\n")
        reporte = generar_reporte()
        
        print("\n" + "="*50)
        print(reporte)
        print("="*50)
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            print("\n📤 Enviando a Telegram...")
            enviar_telegram(reporte)
        else:
            print("⚠️ Telegram no configurado")
        
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

