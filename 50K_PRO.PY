import sys
import time
from datetime import datetime
import MetaTrader5 as mt5

symbol = "EURUSD"

# --- 🛡️ CONFIGURACIÓN BLINDADA PARA CUENTA 50K MT5 (REGLAS FTMO) ---
BALANCE_INICIAL_挑战 = 50000.0
MAX_PERDIDA_DIARIA_PERMITIDA = 2000.0
MAX_OPERACIONES_SIMULTANEAS = 5

# --- ⚙️ PARÁMETROS DE DISEÑO DEL ALGORITMO AUTO-AJUSTABLE ---
RANGO_PIPS_COBERTURA = 150  # Cubre 150 pips arriba y abajo desde el precio actual
num_grillas = 10  # Escalones en la malla geométrica
intervalo_monitoreo = 5  # Monitoreo constante a través de tu cable Cat 6

# --- 📊 SEGUIMIENTO DE OPERACIONES Y FINANZAS ---
registro_ordenes = {"compras": {}, "ventas": {}}
precios_malla = []
beneficio_acumulado_usd = 0.0
OBJETIVO_FTMO_FASE1 = 5000.0
contador_latidos = 0  # Control técnico de verificación visual


def consola_forzada(texto):
    sys.stdout.write(f"[{datetime.now().strftime('%H:%M:%S')}] {texto}\n")
    sys.stdout.flush()


def verificar_blindaje_ftmo(equity_actual):
    flotante = equity_actual - BALANCE_INICIAL_挑战
    if flotante <= -MAX_PERDIDA_DIARIA_PERMITIDA:
        consola_forzada(f"🚨 CIRCUIT BREAKER! Flotante: {flotante:.2f} USD. Cierre masivo de emergencia...")
        posiciones = mt5.positions_get(symbol=symbol)
        if posiciones:
            for pos in posiciones:
                ticket = pos.ticket
                tipo_cierre = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                precio_cierre = mt5.symbol_info_tick(
                    symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": tipo_cierre,
                    "position": ticket,
                    "price": precio_cierre,
                    "deviation": 10,
                    "magic": 123456,
                    "comment": "Cierre Emergencia FTMO",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                }
                mt5.order_send(request)
        mt5.shutdown()
        sys.exit("\n[SISTEMA APAGADO] Proceso detenido para evitar descalificación.")
    return flotante


def calcular_malla_dinamica(precio_origen):
    pips_en_decimal = RANGO_PIPS_COBERTURA * 0.0001
    precio_min_malla = precio_origen - pips_en_decimal
    precio_max_malla = precio_origen + pips_en_decimal

    consola_forzada(f"🎯 Rango Calculado de Forma Automática:")
    consola_forzada(f"   🔹 Límite Inferior (Piso): {precio_min_malla:.5f}")
    consola_forzada(f"   🔸 Límite Superior (Techo): {precio_max_malla:.5f}")

    factor_geometrico = (precio_max_malla / precio_min_malla) ** (1 / (num_grillas - 1))
    return [precio_min_malla * (factor_geometrico ** i) for i in range(num_grillas)]


def inicializar_malla_blindada():
    global precios_malla
    consola_forzada("🏦 CONECTANDO CON METATRADER 5 FTMO REAL-TIME...")
    if not mt5.initialize():
        consola_forzada(f"❌ Fallo al conectar MT5: {mt5.last_error()}")
        sys.exit()

    mt5.symbol_select(symbol, True)

    # Purgar órdenes antiguas obsoletas
    orders = mt5.orders_get(symbol=symbol)
    if orders:
        for o in orders:
            mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket})
        consola_forzada("🧹 Órdenes fuera de rango purgadas con éxito.")

    # Lectura directa del precio vivo en el bróker
    tick = mt5.symbol_info_tick(symbol)
    precio_actual = tick.last if tick.last != 0 else tick.ask
    consola_forzada(f"📈 Precio Detectado en Tiempo Real: {precio_actual:.5f}")

    # Autoajuste de la grilla geométrica
    precios_malla = calcular_malla_dinamica(precio_actual)

    monto_lote = 0.1
    ordenes_puestas = 0

    # Inyección de órdenes límite según la nueva grilla adaptada
    for p in precios_malla:
        if ordenes_puestas >= MAX_OPERACIONES_SIMULTANEAS:
            break
        if p < precio_actual:
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": monto_lote,
                "type": mt5.ORDER_TYPE_BUY_LIMIT,
                "price": float(p),
                "deviation": 10,
                "magic": 123456,
                "comment": "Malla AutoAjustable FTMO",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            resultado = mt5.order_send(request)
            if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                registro_ordenes["compras"][resultado.order] = p
                ordenes_puestas += 1

    return monto_lote


# --- ARRANQUE AUTOMÁTICO ---
lotes_fijos = inicializar_malla_blindada()
consola_forzada("✅ ENTORNO ADAPTATIVO GENERANDO BENEFICIOS OPERATIVO 24/7.")

# --- BUCLE PRINCIPAL DE OPERACIONES CON MÉTRICAS EN VIVO ---
while True:
    try:
        info_cuenta = mt5.account_info()
        if info_cuenta is None:
            time.sleep(5)
            continue

        verificar_blindaje_ftmo(info_cuenta.equity)
        orders_mt5 = mt5.orders_get(symbol=symbol)
        ids_abiertas = [o.ticket for o in orders_mt5] if orders_mt5 else []

        # ❤️ MONITOR VISUAL: Envía un latido de sistema cada 60 segundos (12 ciclos de 5s)
        contador_latidos += 1
        if contador_latidos >= 12:
            consola_forzada(
                f"💚 Latido de sistema: Enjambre activo... Cuenta: 50K | Equidad: {info_cuenta.equity:.2f} USD | Órdenes en libro: {len(ids_abiertas)}")
            contador_latidos = 0

        # Transición 1: Compra ejecutada -> Coloca Venta Limit
        for id_compra, precio_nivel in list(registro_ordenes["compras"].items()):
            if id_compra not in ids_abiertas:
                consola_forzada(f"🛒 COMPRA EJECUTADA en {precio_nivel:.5f}. Armando toma de ganancias...")
                index_actual = min(range(len(precios_malla)), key=lambda i: abs(precios_malla[i] - precio_nivel))
                if index_actual < len(precios_malla) - 1:
                    precio_venta = precios_malla[index_actual + 1]
                    request = {
                        "action": mt5.TRADE_ACTION_PENDING,
                        "symbol": symbol,
                        "volume": lotes_fijos,
                        "type": mt5.ORDER_TYPE_SELL_LIMIT,
                        "price": float(precio_venta),
                        "deviation": 10,
                        "magic": 123456,
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                    resultado = mt5.order_send(request)
                    if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                        registro_ordenes["ventas"][resultado.order] = precio_venta
                del registro_ordenes["compras"][id_compra]

        # Transición 2: Cobro de beneficio completado -> Coloca Recompra Limit inferior
        for id_venta, precio_nivel in list(registro_ordenes["ventas"].items()):
            if id_venta not in ids_abiertas:
                index_actual = min(range(len(precios_malla)), key=lambda i: abs(precios_malla[i] - precio_nivel))
                precio_compra_origen = precios_malla[index_actual - 1] if index_actual > 0 else precio_nivel

                # Fórmula de beneficio estándar de pips en MT5 para 0.1 lotes
                ganancia_operacion = (precio_nivel - precio_compra_origen) * 100000 * lotes_fijos
                beneficio_acumulado_usd += ganancia_operacion

                faltante_objetivo = OBJETIVO_FTMO_FASE1 - beneficio_acumulado_usd
                porcentaje_progreso = (beneficio_acumulado_usd / OBJETIVO_FTMO_FASE1) * 100

                consola_forzada("================================================================")
                consola_forzada(f"💰 VENTA EJECUTADA en {precio_nivel:.5f}.")
                consola_forzada(f"   💸 Ganancia del Trade: +{ganancia_operacion:.2f} USD")
                consola_forzada(f"   📊 Beneficio Total Acumulado: {beneficio_acumulado_usd:.2f} USD")
                consola_forzada(
                    f"   🎯 Progreso Examen: {porcentaje_progreso:.2f}% | Faltan: {max(0.0, faltante_objetivo):.2f} USD")
                consola_forzada("================================================================")

                if index_actual > 0:
                    precio_recompra = precios_malla[index_actual - 1]
                    posiciones_actuales = mt5.positions_get(symbol=symbol)
                    total_activas = len(posiciones_actuales) if posiciones_actuales else 0

                    if total_activas < MAX_OPERACIONES_SIMULTANEAS:
                        request = {
                            "action": mt5.TRADE_ACTION_PENDING,
                            "symbol": symbol,
                            "volume": lotes_fijos,
                            "type": mt5.ORDER_TYPE_BUY_LIMIT,
                            "price": float(precio_recompra),
                            "deviation": 10,
                            "magic": 123456,
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_RETURN,
                        }
                        resultado = mt5.order_send(request)
                        if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                            registro_ordenes["compras"][resultado.order] = precio_recompra
                del registro_ordenes["ventas"][id_venta]

        time.sleep(intervalo_monitoreo)

    except Exception as e:
        consola_forzada(f"⚠️ Error controlado en monitor: {str(e)}")
        time.sleep(5)
