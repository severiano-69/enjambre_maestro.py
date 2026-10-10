import os
import sys
import time
import threading
import json
import requests
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Asegura que Render muestre los logs al instante en la consola
os.environ["PYTHONUNBUFFERED"] = "1"

# ==============================================================================
# 1. PARÁMETROS DE INFRAESTRUCTURA DE TRADING (RESGUARDO DE SEGURIDAD)
# ==============================================================================
BITVAVO_API_KEY = os.environ.get("BITVAVO_API_KEY", "").strip()
BITVAVO_API_SECRET = os.environ.get("BITVAVO_API_SECRET", "").strip()

# ==============================================================================
# 2. CONFIGURACIÓN SOBERANA DE FONDOS (96.71 € LIQUIDOS Y DISTRIBUIDOS CON ADA)
# ==============================================================================
CONFIG_TRADING = {
    "saldo_disponible_eur": 96.71,
    "reserva_emergencia_eur": 21.71,
    "estrategia": {
        "XRP": {
            "mision": "Vigilancia en tiempo real para recompra tactica",
            "asignacion_eur": 30.0,
            "precio_gatillo_compra": 1.18,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 0.0
        },
        "SOL_RECOMPRA": {
            "mision": "Monitoreo en tiempo real zona de soporte bajo",
            "asignacion_eur": 25.0,
            "precio_gatillo_compra": 135.0,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 0.0
        },
        "ADA": {
            "mision": "Acumulacion estrategica en suelo tecnico",
            "asignacion_eur": 20.0,
            "precio_gatillo_compra": 0.35,
            "estado": "PATRULLANDO_TIEMPO_REAL",
            "precio_actual_ticker": 0.0
        }
    }
}

METRICAS_SISTEMA = {
    "status_motor": "CONECTADO A ORACULO GLOBAL - TIEMPO REAL OK",
    "capital_liquido_protegido_eur": 96.71,
    "misiones_defensivas_completadas": 1,
    "ciclos_de_patrulla_limpios": 0,
    "ultimo_chequeo_precios": "Nunca",
    "oraculo_origen": "CryptoCompare Public Real-Time Feed"
}

# ==============================================================================
# 3. INTERFAZ WEB CONTROLADORA (PANEL CORPORATIVO DE TRADING DE SEVERIANO)
# ==============================================================================
@app.route('/')
def servidor_home():
    return jsonify({
        "motor_status": METRICAS_SISTEMA["status_motor"],
        "enjambre_maestro_version": "22.0 - Tri-Asset Live Core",
        "sistema_trading": CONFIG_TRADING,
        "auditoria_fondos": METRICAS_SISTEMA
    }), 200

# ==============================================================================
# 4. MOTOR SOBERANO DE PATRULLA CON BYPASS DE DATOS (XRP, SOL Y ADA EN TIEMPO REAL)
# ==============================================================================
def obtener_precio_en_vivo(crypto):
    """Consulta la cotizacion del mercado mediante canal abierto libre de bloqueos"""
    try:
        url = f"https://cryptocompare.com{crypto}&tsyms=EUR"
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return float(datos.get("EUR", 0.0))
    except Exception as e:
        print(f"⚠️ [MALLA WARN] Error de lectura en feed para {crypto}: {e}", flush=True)
    return None

def bucle_motor_maestro():
    global METRICAS_SISTEMA, CONFIG_TRADING
    print("🚀 [MOTOR] Inicializando patrulla de tres activos en el feed inmune...", flush=True)
    time.sleep(3)
    
    while True:
        try:
            # 1. Consultar XRP en tiempo real
            precio_xrp = obtener_precio_en_vivo("XRP")
            if precio_xrp and precio_xrp > 0:
                CONFIG_TRADING["estrategia"]["XRP"]["precio_actual_ticker"] = precio_xrp
                print(f"👀 [ORACULO] XRP/EUR: {precio_xrp} EUR (Gatillo: {CONFIG_TRADING['estrategia']['XRP']['precio_gatillo_compra']} EUR)", flush=True)

            # 2. Consultar SOL en tiempo real
            precio_sol = obtener_precio_en_vivo("SOL")
            if precio_sol and precio_sol > 0:
                CONFIG_TRADING["estrategia"]["SOL_RECOMPRA"]["precio_actual_ticker"] = precio_sol
                print(f"👀 [ORACULO] SOL/EUR: {precio_sol} EUR (Gatillo: {CONFIG_TRADING['estrategia']['SOL_RECOMPRA']['precio_gatillo_compra']} EUR)", flush=True)

            # 3. Consultar ADA en tiempo real
            precio_ada = obtener_precio_en_vivo("ADA")
            if precio_ada and precio_ada > 0:
                CONFIG_TRADING["estrategia"]["ADA"]["precio_actual_ticker"] = precio_ada
                print(f"👀 [ORACULO] ADA/EUR: {precio_ada} EUR (Gatillo: {CONFIG_TRADING['estrategia']['ADA']['precio_gatillo_compra']} EUR)", flush=True)

            # Actualizar panel corporativo de Severiano
            METRICAS_SISTEMA["ciclos_de_patrulla_limpios"] += 1
            METRICAS_SISTEMA["ultimo_chequeo_precios"] = datetime.now().strftime("%H:%M:%S")
            METRICAS_SISTEMA["status_motor"] = "PATRULLANDO EN TIEMPO REAL - CONEXION OK"
            
        except Exception as e:
            print(f"❌ [ALERTA MOTOR] Quiebre en el ciclo de datos: {e}", flush=True)
            
        time.sleep(60)

if __name__ == '__main__':
    print("Enjambre Maestro v22.0 Online - Tri-Asset Shield Desplegado.", flush=True)
    
    # Iniciar hilo de patrulla reactivo
    threading.Thread(target=bucle_motor_maestro, daemon=True).start()
    
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
