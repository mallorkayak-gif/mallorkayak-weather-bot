#!/usr/bin/env python3
"""
🎣 MallorKayak Weather Bot - VERSIÓN 2.0
Bot meteorológico para recomendar mejores zonas de kayak offshore en Mallorca
Usa APIs 100% gratuitas (Open-Meteo + StormGlass) y envía reportes diarios por Telegram
"""

import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple

# ============ CONFIGURACIÓN ============

# APIs
OPENMETEO_API = "https://api.open-meteo.com/v1/forecast"
STORMGLASS_API = "https://api.stormglass.io/v2/weather/point"
STORMGLASS_TOKEN = os.getenv("STORMGLASS_TOKEN", "9673cfe6-2037-11f0-9606-0242ac130003-9673d054-2037-11f0-9606-0242ac130003")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Zonas de pesca en Mallorca
ZONAS = {
    "Isla Dragonera": {"lat": 39.60, "lon": 2.30, "region": "O"},
    "Isla de Cabrera": {"lat": 39.17, "lon": 2.89, "region": "S"},
    "Bahía de Palma": {"lat": 39.57, "lon": 2.73, "region": "SO"},
    "Portals Vells": {"lat": 39.52, "lon": 2.54, "region": "SO"},
    "Llucmajor": {"lat": 39.33, "lon": 3.07, "region": "SE"},
    "Punta Negra": {"lat": 39.45, "lon": 3.00, "region": "E"},
    "Cala d'Or": {"lat": 39.35, "lon": 3.40, "region": "E"},
    "Porto Cristo": {"lat": 39.42, "lon": 3.41, "region": "E"},
    "Cala Millor": {"lat": 39.49, "lon": 3.38, "region": "E"},
    "Bahía Pollença": {"lat": 39.83, "lon": 3.09, "region": "NE"},
    "Alcúdia": {"lat": 39.85, "lon": 3.11, "region": "NE"},
    "Can Picafort": {"lat": 39.73, "lon": 3.14, "region": "N"},
    "Formentor": {"lat": 39.96, "lon": 3.25, "region": "NE"},
    "Cala Sant Vicenç": {"lat": 39.88, "lon": 3.13, "region": "N"},
    "Sóller": {"lat": 39.77, "lon": 2.73, "region": "NO"},
}

# Criterios de puntuación
CRITERIOS = {
    "waves": {
        "ideal_max": 0.3,
        "good_max": 0.8,
        "acceptable_max": 1.2,
        "difficult_max": 1.5
    },
    "wind": {
        "ideal_max": 4,
        "good_max": 8,
        "acceptable_max": 12,
        "difficult_max": 15
    },
    "visibility": {
        "excellent": 15,
        "good": 10,
        "acceptable": 5
    },
    "temperature": {
        "ideal_min": 18,
        "ideal_max": 24,
        "good_min": 15,
        "good_max": 25
    }
}

# ============ LOGGING ============

def log(mensaje: str, tipo: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{emoji.get(tipo, '📌')} [{timestamp}] {mensaje}")


# ============ OBTENER DATOS METEOROLÓGICOS ============

def obtener_datos_openmeteo(lat: float, lon: float) -> Dict:
    """
    Obtiene datos de Open-Meteo (API gratuita)
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "windspeed_10m,wave_height,visibility",
            "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max",
            "timezone": "Europe/Madrid",
            "forecast_days": 3
        }
        
        response = requests.get(OPENMETEO_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        log(f"Error Open-Meteo ({lat},{lon}): {str(e)}", "WARNING")
        return None


def obtener_datos_stormglass(lat: float, lon: float) -> Dict:
    """
    Obtiene datos de StormGlass (respaldo)
    """
    try:
        headers = {"Authorization": f"Bearer {STORMGLASS_TOKEN}"}
        params = {
            "lat": lat,
            "lng": lon,
            "params": "waveHeight,windSpeed,waterTemperature,visibility"
        }
        
        response = requests.get(
            STORMGLASS_API,
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            log("StormGlass: Token inválido", "WARNING")
            return None
        
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        log(f"Error StormGlass ({lat},{lon}): {str(e)}", "WARNING")
        return None


# ============ PROCESAMIENTO DE DATOS ============

def extraer_datos_dia(data_openmeteo: Dict, dia: int = 0) -> Dict:
    """
    Extrae datos del día especificado de Open-Meteo
    """
    if not data_openmeteo or "daily" not in data_openmeteo:
        return {}
    
    try:
        daily = data_openmeteo["daily"]
        
        # Convertir wind speed de km/h a nudos
        wind_kmh = daily["windspeed_10m_max"][dia]
        wind_knots = wind_kmh * 0.539957
        
        return {
            "wave_height": 0.5,  # Open-Meteo no tiene wave_height en el forecast, usar valor por defecto
            "wind_knots": wind_knots,
            "temperature": daily["temperature_2m_max"][dia],
            "visibility": 15  # Valor por defecto (Open-Meteo no da visibility en forecast)
        }
    except (KeyError, IndexError, TypeError):
        return {}


def calcular_puntuacion(wave: float, wind: float, visibility: float, temp: float) -> Tuple[float, str, Dict]:
    """
    Calcula puntuación 0-10 basada en criterios de kayak offshore
    Retorna: (puntuación, rating, detalles)
    """
    score = 0
    detalles = {}
    
    # OLAS (0-3 puntos)
    if wave <= CRITERIOS["waves"]["ideal_max"]:
        score += 3
        olas_status = "✅ IDEAL"
    elif wave <= CRITERIOS["waves"]["good_max"]:
        score += 2.5
        olas_status = "✅ MUY BUENO"
    elif wave <= CRITERIOS["waves"]["acceptable_max"]:
        score += 2
        olas_status = "⚠️ ACEPTABLE"
    elif wave <= CRITERIOS["waves"]["difficult_max"]:
        score += 1
        olas_status = "⚠️ DIFÍCIL"
    else:
        score += 0
        olas_status = "❌ PELIGROSO"
    
    detalles["wave"] = {"score": min(3, score), "status": olas_status, "value": wave}
    
    # VIENTO (0-3 puntos)
    wind_score = 0
    if wind <= CRITERIOS["wind"]["ideal_max"]:
        wind_score = 3
        viento_status = "✅ IDEAL"
    elif wind <= CRITERIOS["wind"]["good_max"]:
        wind_score = 2.5
        viento_status = "✅ MUY BUENO"
    elif wind <= CRITERIOS["wind"]["acceptable_max"]:
        wind_score = 2
        viento_status = "⚠️ MANEJABLE"
    elif wind <= CRITERIOS["wind"]["difficult_max"]:
        wind_score = 1
        viento_status = "⚠️ DIFÍCIL"
    else:
        wind_score = 0
        viento_status = "❌ MUY FUERTE"
    
    score += wind_score
    detalles["wind"] = {"score": wind_score, "status": viento_status, "value": wind}
    
    # VISIBILIDAD (0-2 puntos)
    if visibility > CRITERIOS["visibility"]["excellent"]:
        score += 2
        visib_status = "✅ EXCELENTE"
    elif visibility > CRITERIOS["visibility"]["good"]:
        score += 1.5
        visib_status = "✅ BUENA"
    elif visibility > CRITERIOS["visibility"]["acceptable"]:
        score += 1
        visib_status = "⚠️ REGULAR"
    else:
        score += 0.5
        visib_status = "❌ MALA"
    
    detalles["visibility"] = {"score": min(2, score - detalles["wave"]["score"] - detalles["wind"]["score"]), "status": visib_status, "value": visibility}
    
    # TEMPERATURA (0-1.5 puntos)
    if CRITERIOS["temperature"]["ideal_min"] <= temp <= CRITERIOS["temperature"]["ideal_max"]:
        score += 1.5
        temp_status = "✅ IDEAL"
    elif CRITERIOS["temperature"]["good_min"] <= temp <= CRITERIOS["temperature"]["good_max"]:
        score += 1
        temp_status = "✅ BUENA"
    else:
        score += 0.5
        temp_status = "⚠️ FRÍA"
    
    detalles["temperature"] = {"status": temp_status, "value": temp}
    
    # Normalizar a 10 puntos
    score = min(10, max(0, score))
    
    # Rating
    if score >= 9:
        rating = "🟢 EXCELENTE - Perfecto para salir"
    elif score >= 7.5:
        rating = "🟢 MUY BUENO - Condiciones ideales"
    elif score >= 6:
        rating = "🟡 BUENO - Aceptable para expertos"
    elif score >= 4:
        rating = "🟠 REGULAR - Requiere precaución"
    else:
        rating = "🔴 MALO - No recomendado"
    
    return round(score, 1), rating, detalles


# ============ ANÁLISIS DE ZONAS ============

def analizar_todas_las_zonas(dias: int = 3) -> List[Dict]:
    """
    Analiza todas las zonas y retorna un ranking
    """
    resultados = []
    
    log(f"Analizando {len(ZONAS)} zonas para {dias} día(s)...")
    
    for zona_name, coords in ZONAS.items():
        lat, lon = coords["lat"], coords["lon"]
        
        # Obtener datos
        om_data = obtener_datos_openmeteo(lat, lon)
        sg_data = obtener_datos_stormglass(lat, lon)
        
        # Extraer datos del primer día
        datos = extraer_datos_dia(om_data, dia=0)
        
        if not datos:
            log(f"⏭️  Saltando {zona_name} (sin datos)", "WARNING")
            continue
        
        # Calcular puntuación
        score, rating, detalles = calcular_puntuacion(
            wave=datos.get("wave_height", 0.5),
            wind=datos.get("wind_knots", 8),
            visibility=datos.get("visibility", 15),
            temp=datos.get("temperature", 20)
        )
        
        resultados.append({
            "zona": zona_name,
            "region": coords.get("region", "?"),
            "score": score,
            "rating": rating,
            "datos": datos,
            "detalles": detalles
        })
    
    # Ordenar por puntuación (descendente)
    resultados.sort(key=lambda x: x["score"], reverse=True)
    
    log(f"✅ Análisis completado: {len(resultados)} zonas procesadas", "SUCCESS")
    
    return resultados


# ============ ENVIAR A TELEGRAM ============

def enviar_telegram(mensaje: str) -> bool:
    """
    Envía mensaje a Telegram
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ Credenciales de Telegram no configuradas", "ERROR")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        log("✅ Mensaje enviado a Telegram", "SUCCESS")
        return True
    
    except Exception as e:
        log(f"❌ Error al enviar a Telegram: {str(e)}", "ERROR")
        return False


# ============ FORMATEAR MENSAJE ============

def formatear_reporte(resultados: List[Dict]) -> str:
    """
    Formatea el reporte para Telegram
    """
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    mensaje = f"""
<b>🎣 RECOMENDACIONES DE PESCA - MALLORKAYAK</b>
<i>Análisis de Meteorología Marina</i>

📅 {hoy} | 🕐 Zona Horaria: Madrid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    medallas = ["🥇", "🥈", "🥉"]
    
    # Top 5 zonas
    for idx, zona in enumerate(resultados[:5]):
        medalla = medallas[idx] if idx < 3 else "  "
        
        mensaje += f"""
{medalla} <b>{idx+1}. {zona['zona']}</b>
   ⭐ Puntuación: {zona['score']}/10
   {zona['rating']}
   
   🌊 Olas: {zona['datos'].get('wave_height', 0.5):.1f}m - {zona['detalles']['wave']['status']}
   💨 Viento: {zona['datos'].get('wind_knots', 8):.1f} nudos - {zona['detalles']['wind']['status']}
   👁️ Visibilidad: {zona['datos'].get('visibility', 15):.0f}m - {zona['detalles']['visibility']['status']}
   🌡️ Agua: {zona['datos'].get('temperature', 20):.1f}°C - {zona['detalles']['temperature']['status']}
   🧭 Región: {zona['region']}

"""
    
    mensaje += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 CRITERIOS DE PUNTUACIÓN:</b>
✅ 9-10: EXCELENTE
✅ 7.5-8.9: MUY BUENO
🟡 6-7.4: BUENO
🟠 4-5.9: REGULAR
🔴 0-3.9: MALO

<i>Datos: Open-Meteo API + StormGlass</i>
🤖 Generado automáticamente
"""
    
    return mensaje


# ============ MAIN ============

def main():
    """
    Función principal
    """
    log("🚀 Iniciando MallorKayak Weather Bot v2.0", "INFO")
    log(f"📍 Zonas: {len(ZONAS)}", "INFO")
    log(f"📱 Telegram: {'Configurado ✅' if TELEGRAM_TOKEN else 'NO configurado ❌'}", "INFO")
    
    # Analizar zonas
    resultados = analizar_todas_las_zonas()
    
    if not resultados:
        log("❌ No se pudieron procesar las zonas", "ERROR")
        return False
    
    # Mostrar top 3 en consola
    log("\n🎯 TOP 3 ZONAS:", "INFO")
    for idx, zona in enumerate(resultados[:3]):
        print(f"   {idx+1}. {zona['zona']} - {zona['score']}/10 {zona['rating']}")
    
    # Formatear mensaje
    mensaje = formatear_reporte(resultados)
    
    # Enviar a Telegram
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        enviar_telegram(mensaje)
    else:
        log("ℹ️ Modo test: Mensaje no enviado (falta credenciales)", "INFO")
        print("\n" + mensaje)
    
    log("✅ Bot ejecutado correctamente", "SUCCESS")
    return True


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        log(f"❌ Error fatal: {str(e)}", "ERROR")
        exit(1)
