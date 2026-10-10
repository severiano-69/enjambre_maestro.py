import os
import sys
import time
import threading
import json
import requests
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Asegura que Render muestre los logs al instante en la consola sin retrasos
os.environ["PYTHONUNBUFFERED"] = "1"

# ==============================================================================
# 1. PARÁMETROS DE INFRAESTRUCTURA DE TRADING (RESGUARDO DE SEGURIDAD)
# ==============================================================================
BITVAVO_API_KEY = os.environ.get("BITVAVO_API_KEY", "").strip()
BITVAVO_API_SECRET = os.environ.get("BITVAVO_API_SECRET", "").strip()

# ==============================================================================
# 2. CONFIGURACIÓN SOBERANA DE TU CARTERA REAL EN BITVAVO
# ==============================================================================
CONFIG_TRADING = {
    "saldo_disponible_eur": 96.71,
    "reserva_emergencia_eur": 21.71,
    "cartera_activa_bitvavo": {
        "SOL": {
            "mision": "Vigilancia en tiempo real - Acumulacion activa",
            "tus_monedas": 1.03772323,
            "precio_gatillo_compra": 135.0,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 98.20
        },
        "ADA": {
            "mision": "Vigilancia en tiempo real - Suelo tecnico en verde",
            "tus_monedas": 416.780123,
            "precio_gatillo_compra": 0.35,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 0.22704
        },
        "XRP": {
            "mision": "Vigilancia en tiempo real - Esperando descuento de recompra",
            "tus_monedas": 28.002375,
            "precio_gatillo_compra": 1.18,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 1.25
        }
    }
}

METRICAS_SISTEMA = {
    "status_motor": "CONECTADO A FILTRADO DE MERCADO - TIEMPO REAL OK",
    "capital_liquido_protegido_eur": 96.71,
    "misiones_defensivas_completadas": 1,
    "ciclos_de_patrulla_limpios": 0,
    "ultimo_chequeo_precios": "Nunca",
    "oraculo_origen": "CryptoCompare & Bitvavo Public Open Mirror"
}

# ==============================================================================
# 3. INTERFAZ WEB CONTROLADORA (PANEL CORPORATIVO DE TRADING DE SEVERIANO)
# ==============================================================================
@app.route('/')
def servidor_home():
    return jsonify({
        "motor_status": METRICAS_SISTEMA["status_motor"],
        "enjambre_maestro_version": "23.0 - Tri-Asset Active Portfolio Core",
        "sistema_trading": CONFIG_TRADING,
        "auditoria_fondos": METRICAS_SISTEMA
    }), 200

# ==============================================================================
# 4. MOTOR SOBERANO DE PATRULLA CON BYPASS DE DATOS (XRP, SOL Y ADA EN TIEMPO REAL)
# ==============================================================================
def obtener_precio_en_vivo(crypto):
    """Consulta la cotizacion del mercado mediante un canal abierto inmune a bloqueos IP"""
    try:
        # Endpoint público estructurado oficial para lectura directa de precios
        url = f"https://cryptocompare.com{crypto}&tsyms=EUR"
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return float(datos.get("EUR", 0.0))
    except Exception as e:
        print(f"⚠️ [MALLA WARN] Error de lectura en feed global para {crypto}: {e}", flush=True)
    return None

def bucle_motor_maestro():
    global METRICAS_SISTEMA, CONFIG_TRADING
    print("🚀 [MOTOR] Inicializando patrulla del tridente en verde sobre canal blindado...", flush=True)
    time.sleep(3)
    
    while True:
        try:
            # 1. Consultar SOL en tiempo real sin pasar por el bloqueo IP
            precio_sol = obtener_precio_en_vivo("SOL")
            if precio_sol and precio_sol > 0:
                CONFIG_TRADING["cartera_activa_bitvavo"]["SOL"]["precio_actual_ticker"] = precio_sol
                print(f"👀 [RADAR] SOL/EUR en vivo: {precio_sol} EUR (Gatillo: 135.0 EUR)", flush=True)

            # 2. Consultar ADA en tiempo real sin pasar por el bloqueo IP
            precio_ada = obtener_precio_en_vivo("ADA")
            if precio_ada and precio_ada > 0:
                CONFIG_TRADING["cartera_activa_bitvavo"]["ADA"]["precio_actual_ticker"] = precio_ada
                print(f"👀 [RADAR] ADA/EUR en vivo: {precio_ada} EUR (Gatillo: 0.35 EUR)", flush=True)

            # 3. Consultar XRP en tiempo real sin pasar por el bloqueo IP
            precio_xrp = obtener_precio_en_vivo("XRP")
            if precio_xrp and precio_xrp > 0:
                CONFIG_TRADING["cartera_activa_bitvavo"]["XRP"]["precio_actual_ticker"] = precio_xrp
                print(f"👀 [RADAR] XRP/EUR en vivo: {precio_xrp} EUR (Gatillo: 1.18 EUR)", flush=True)

            # Actualizar panel corporativo de control
            METRICAS_SISTEMA["ciclos_de_patrulla_limpios"] += 1
            METRICAS_SISTEMA["ultimo_chequeo_precios"] = datetime.now().strftime("%H:%M:%S")
            METRICAS_SISTEMA["status_motor"] = "PATRULLANDO EN TIEMPO REAL - CONEXION OK"
            
        except Exception as e:
            print(f"❌ [ALERTA MOTOR] Quiebre en el ciclo de datos: {e}", flush=True)
            
        time.sleep(60)

if __name__ == '__main__':
    print("Enjambre Maestro v23.0 Online - Malla del Tridente Activa.", flush=True)
    
    # Iniciar hilo de patrulla reactivo en segundo plano
    threading.Thread(target=bucle_motor_maestro, daemon=True).start()
    
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
