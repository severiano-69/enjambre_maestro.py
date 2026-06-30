import os
import sys
import time
import random
import threading
import json
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Asegura la transmisión de logs en vivo sin retención en búfer
os.environ["PYTHONUNBUFFERED"] = "1"

# ==============================================================================
# 1. PARÁMETROS DE INFRAESTRUCTURA (PRODUCCIÓN REAL)
# ==============================================================================
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SENDER_KEY = os.environ.get("SENDER_TOKEN")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WH_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
EMAIL_REMITENTE = os.environ.get("REMITENTE_EMAIL", "severianobenitez@enjambresaas.online")

try:
    if OPENAI_KEY:
        from openai import OpenAI
        api_openai = OpenAI(api_key=OPENAI_KEY)
    else:
        api_openai = None
except Exception as e:
    print(f"[WARN] Error inicializando OpenAI: {e}", flush=True)
    api_openai = None

try:
    if TAVILY_KEY:
        from tavily import TavilyClient
        api_tavily = TavilyClient(api_key=TAVILY_KEY)
    else:
        api_tavily = None
except Exception as e:
    print(f"[WARN] Error inicializando Tavily: {e}", flush=True)
    api_tavily = None

# ==============================================================================
# 2. GESTIÓN DE ESTADO Y FILTRADOS SOBERANOS
# ==============================================================================
REGISTRO_EMAILS, LOGS_SISTEMA = set(), []
METRICAS_GLOBALES = {
    "status_motor": "Iniciando",
    "ventas_totales_recibidas": 0,
    "ingresos_acumulados_eur": 0.0,
    "leads_unicos_cazados": 0,
    "busquedas_tavily_exitosas": 0,
    "busquedas_tavily_fallidas": 0,
    "emails_enviados_exito": 0,
    "emails_rebotados": 0,
    "productos_mas_vendidos": {}
}

EXPRESIÓN_EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
LISTA_NEGRA_DOMINIOS = {"example.com", "ejemplo.com", "email.com", "test.com", "privacy.com", "noreply.com", "support.com", "wix.com", "wordpress.com"}
LISTA_NEGRA_PALABRAS = {"test", "prueba", "ejemplo", "example", "noreply", "support", "soporte", "admin", "abuse", "spam", "billing", "facturas"}

# ==============================================================================
# 3. CARGA DE MERCADOS ISOLADA
# ==============================================================================
def cargar_mercados_seguros():
    lista = []
    lista.append({
        "es": "clinica dental", "en": "dentist clinic",
        "asunto": "Plan de Crecimiento: Resenas de Google de 5 Estrellas",
        "asunto_en": "Growth Plan: 5-Star Google Reviews Drive",
        "env_link": "STRIPE_LINK_RESENAS_GOOGLE",
        "gancho_es": "vimos que tu clinica tiene resenas que podrian mejorar para atraer mas pacientes locales de forma automatica.",
        "gancho_en": "we noticed your dental practice could unlock massive local revenue by optimization of your Google Maps reviews structure."
    })
    lista.append({
        "es": "agencia inmobiliaria", "en": "real estate agency",
        "asunto": "Exclusividad Territorial: Enterprise Omnipresencia 100K",
        "asunto_en": "Territorial Exclusivity: Enterprise Omnipresence 100K",
        "env_link": "STRIPE_LINK_OMNIPRESENCIA",
        "gancho_es": "bloqueamos la captacion de propiedades de tu competencia directa mediante automatizacion exclusiva en tu codigo postal.",
        "gancho_en": "we enforce strict programmatic deployment to intercept property listings before your local competitors even get a notification."
    })
    lista.append({
        "es": "empresa ciberseguridad", "en": "cybersecurity company",
        "asunto": "Auditoria de Vulnerabilidad Cyber-Shield Gratuita",
        "asunto_en": "Free Cyber-Shield Vulnerability Audit",
        "env_link": "STRIPE_LINK_CYBER_SHIELD",
        "gancho_es": "detectamos fugas menores de configuracion en puertos publicos indexados que comprometen tu infraestructura.",
        "gancho_en": "our passive network mapping flagged open parameters that could expose core databases to external scanning vulnerabilities."
    })
    lista.append({
        "es": "vendedor amazon", "en": "amazon seller brand",
        "asunto": "Prueba de 3 dias: Clonador de Productos a Video Vertical IA",
        "asunto_en": "3-Day Trial: AI Product to Vertical Video Cloner",
        "env_link": "STRIPE_LINK_CLONADOR_VIDEO",
        "gancho_es": "transformamos tus listings estaticos de ASIN en anuncios de TikTok en menos de 45 segundos.",
        "gancho_en": "our pipeline automatically parses your current ASIN metrics and synthesizes high-converting TikTok organic creatives."
    })
    lista.append({
        "es": "tienda online", "en": "ecommerce store",
        "asunto": "Alerta de Seguridad: Sistema de Malla Blindada para Fugas de Leads",
        "asunto_en": "Security Alert: Lead Leak Armor Mesh System",
        "env_link": "STRIPE_LINK_FUGAS_LEADS",
        "gancho_es": "detectamos que estas perdiendo mas del 35% de intencion de compra en el checkout por falta de persistencia automatica.",
        "gancho_en": "our audit shows your sales funnel leaks up to 35% of high-intent traffic due to structural tracking drops."
    })
    lista.append({
        "es": "negocio local", "en": "local business",
        "asunto": "Estrategia Malla Blindada - Generador de Promociones Flash por IA",
        "asunto_en": "AI Flash Promotions Generator Strategy",
        "env_link": "STRIPE_LINK_PROMOCIONES_FLASH",
        "gancho_es": "automatizamos ofertas relampago segmentadas segun el stock inactivo de tu inventario local.",
        "gancho_en": "our model spins real-time hyper-targeted flash sales depending heavily on your unmoving store stock volumes."
    })
    lista.append({
        "es": "comercio local", "en": "local shop",
        "asunto": "Optimizador de Ficha Google Maps Automático",
        "asunto_en": "Automated Google Maps Profile Optimizer",
        "env_link": "STRIPE_LINK_OPTIMIZADOR_MAPS",
        "gancho_es": "corregimos las palabras clave de tu ficha para posicionarte en el Top 3 local de busquedas de Google.",
        "gancho_en": "we restructure your local map parameters to immediately pull your profile into the local Top 3 user searches."
    })
    lista.append({
        "es": "pyme expansion", "en": "growing business",
        "asunto": "Acceso Prioritario: Malla Blindada 50K",
        "asunto_en": "Priority Access: Armor Mesh 50K System",
        "env_link": "STRIPE_LINK_MALLA_50K",
        "gancho_es": "desplegamos infraestructura automatizada para capturar hasta 50.000 euros en volumen de negocio latente.",
        "gancho_en": "we set a robust systemic deployment to capture up to 50k in local hidden operational pipeline volume."
    })
    lista.append({
        "es": "empresa premium", "en": "premium company",
        "asunto": "Contrato Corporativo: Malla Blindada Oro",
        "asunto_en": "Corporate License: Gold Armor Mesh System",
        "env_link": "STRIPE_LINK_MALLA_ORO",
        "gancho_es": "asignamos recursos de computacion prioritarios para blindar tus flujos de adquisicion premium.",
        "gancho_en": "we distribute sovereign priority node allocation to fully insulate your premium user acquisition tracks."
    })
    lista.append({
        "es": "crypto startup", "en": "web3 platform",
        "asunto": "Ecosistema de Cobros Malla Blindada Cripto BTC",
        "asunto_en": "Sovereign Settlement: Crypto BTC Armor Mesh",
        "env_link": "STRIPE_LINK_MALLA_CRIPTO_BTC",
        "gancho_es": "conectamos pasarelas de pago alternativas blindadas contra bloqueos bancarios tradicionales.",
        "gancho_en": "we implement fallback liquidity routing immune to traditional legacy clearing settlement freezes."
    })
    lista.append({
        "es": "consultoria profesional", "en": "professional consulting",
        "asunto": "Rediseno de Infraestructura: Paginas Web & SEO Avanzado",
        "asunto_en": "Infrastructure Redesign: Web & Advanced SEO Integration",
        "env_link": "STRIPE_LINK_PAGINAS_WEB_SEO",
        "gancho_es": "reconstruimos la architecture tecnica de tu web para dominar la intencion de busqueda comercial.",
        "gancho_en": "we build a modern headless tech stack to claim search engine real estate over commercial search intents."
    })
    lista.append({
        "es": "marca ecom", "en": "amazon trends brand",
        "asunto": "SaaS Malla Blindada - Tendencias Amazon Pro",
        "asunto_en": "Armor Mesh SaaS - Amazon Trends Pro Insight",
        "env_link": "STRIPE_LINK_TENDENCIAS_AMAZON",
        "gancho_es": "inyectamos analisis predictivo para interceptar tendencias de productos antes de su saturacion.",
        "gancho_en": "we inject predictive analytical nodes to capture product trends long before volume saturation hits."
    })
    return lista

MERCADOS_OBJETIVO = cargar_mercados_seguros()

# ==============================================================================
# 4. ENDPOINTS DE FLASK ACCESIBLES
# ==============================================================================
@app.route('/')
def index():
    return jsonify({
        "status": "Motor Operativo",
        "mercados": len(MERCADOS_OBJETIVO),
        "metricas": METRICAS_GLOBALES
    })

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    event = request.get_json() or {}
    tipo = event.get('type', '')
    if tipo in ['checkout.session.completed', 'charge.succeeded']:
        data_obj = event.get('data', {}).get('object', {})
        monto = data_obj.get('amount_total', data_obj.get('amount', 0)) / 100.0
        email = data_obj.get('customer_details', {}).get('email', 'anonimo@email.com')
        METRICAS_GLOBALES["ventas_totales_recibidas"] += 1
