import os, sys, time, random, threading, json, re, requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

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
    else: api_openai = None
except Exception: api_openai = None

try:
    if TAVILY_KEY:
        from tavily import TavilyClient
        api_tavily = TavilyClient(api_key=TAVILY_KEY)
    else: api_tavily = None
except Exception: api_tavily = None

# ==============================================================================
# 2. GESTIÓN DE ESTADO Y FILTRADOS SOBERANOS
# ==============================================================================
REGISTRO_EMAILS, LOGS_SISTEMA = set(), []
METRICAS_GLOBALES = {
    "status_motor": "Iniciando", "ventas_totales_recibidas": 0, "ingresos_acumulados_eur": 0.0,
    "leads_unicos_cazados": 0, "busquedas_tavily_exitosas": 0, "busquedas_tavily_fallidas": 0, "productos_mas_vendidos": {}
}

EXPRESIÓN_EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
LISTA_NEGRA_DOMINIOS = {"example.com", "ejemplo.com", "email.com", "test.com", "privacy.com", "noreply.com", "support.com"}
LISTA_NEGRA_PALABRAS = {"test", "prueba", "ejemplo", "example", "noreply", "support", "soporte", "admin"}

MERCADOS_OBJETIVO = [
    {"es": "clinica dental", "en": "dentist clinic", "asunto": "Plan de Crecimiento: Resenas de Google de 5 Estrellas", "asunto_en": "Growth Plan: 5-Star Google Reviews Drive", "env_link": "STRIPE_LINK_RESENAS_GOOGLE"},
    {"es": "agencia inmobiliaria", "en": "real estate agency", "asunto": "Exclusividad Territorial: Enterprise Omnipresencia 100K", "asunto_en": "Territorial Exclusivity: Enterprise Omnipresence 100K", "env_link": "STRIPE_LINK_OMNIPRESENCIA"},
    {"es": "empresa ciberseguridad", "en": "cybersecurity company", "asunto": "Auditoria de Vulnerabilidad Cyber-Shield Gratuita", "asunto_en": "Free Cyber-Shield Vulnerability Audit", "env_link": "STRIPE_LINK_CYBER_SHIELD"},
    {"es": "vendedor amazon", "en": "amazon seller brand", "asunto": "Prueba de 3 dias: Clonador de Productos a Video Vertical IA", "asunto_en": "3-Day Trial: AI Product to Vertical Video Cloner", "env_link": "STRIPE_LINK_CLONADOR_VIDEO"},
    {"es": "negocio local", "en": "local business", "asunto": "Alerta de Fuga de Clientes: Tu formulario web esta roto", "asunto_en": "Lead Leak Alert: Your website contact form is broken", "env_link": "STRIPE_LINK_FUGAS_LEADS"},
    {"es": "tienda online", "en": "e-commerce store", "asunto": "Generador de Promociones Flash por IA: Multiplica Conversiones", "asunto_en": "AI Flash Promo Generator: Multiply Sales Now", "env_link": "STRIPE_LINK_PROMOCIONES_FLASH"},
    {"es": "comercio local", "en": "local shop", "asunto": "Optimizador de Ficha Google Maps: Domina tu zona", "asunto_en": "Google Maps Listing Optimizer: Dominate Your Area", "env_link": "STRIPE_LINK_OPTIMIZADOR_MAPS"},
    {"es": "startup tecnologica", "en": "tech startup", "asunto": "Acceso Malla Blindada 50K: Infraestructura Escalable", "asunto_en": "Malla Blindada 50K Access: Scalable Infrastructure", "env_link": "STRIPE_LINK_MALLA_50K"},
    {"es": "empresa corporativa", "en": "corporate enterprise", "asunto": "Plan Malla Blindada Oro: Proteccion y Automatizacion Elite", "asunto_en": "Malla Blindada Gold Plan: Elite Automation & Protection", "env_link": "STRIPE_LINK_MALLA_ORO"},
    {"es": "fondo inversion", "en": "investment fund", "asunto": "Malla Blindada Cripto BTC: Security de Activos Digitales", "asunto_en": "Malla Blindada Crypto BTC: Digital Asset Security", "env_link": "STRIPE_LINK_MALLA_CRIPTO_BTC"},
    {"es": "pyme local", "en": "smb business", "asunto": "Desarrollo Paginas Web & SEO: Trafico Organico Garantizado", "asunto_en": "Web Development & SEO: Guaranteed Organic Traffic", "env_link": "STRIPE_LINK_PAGINAS_WEB_SEO"},
    {"es": "marca retail", "en": "retail brand", "asunto": "Auditoria de Tendencias Amazon IA: Descubre Nichos Ocultos", "asunto_en": "AI Amazon Trends Audit: Uncover Hidden Niches", "env_link": "STRIPE_LINK_TENDENCIAS_AMAZON"},
    {"es": "agencia marketing", "en": "marketing agency", "asunto": "Plataforma de Inteligencia de Anuncios: Optimiza tu ROAS", "asunto_en": "Ad Intelligence Platform: Optimize Your ROAS Automatically", "env_link": "STRIPE_LINK_INTELIGENCIA_ANUNCIOS"},
    {"es": "corporacion", "en": "corporation", "asunto": "Auditoria y Certificacion de Cumplimiento IA", "asunto_en": "AI Compliance Audit & Certification", "env_link": "STRIPE_LINK_AUDITORIA_CUMPLIMIENTO_IA"},
    {"es": "empresa servicios", "en": "service company", "asunto": "Agente de Rescate y Cierre de Ventas por WhatsApp AI Elite", "asunto_en": "AI WhatsApp Elite Lead Rescue & Sales Closer Agent", "env_link": "STRIPE_LINK_WHATSAPP_AI_ELITE_1"}
]

DESTINOS_PROSPECCION = [
    {"ciudad": "Madrid", "pais": "ES"}, {"ciudad": "Barcelona", "pais": "ES"}, {"ciudad": "Valencia", "pais": "ES"},
    {"ciudad": "Miami", "pais": "INT"}, {"ciudad": "New York", "pais": "INT"}, {"ciudad": "London", "pais": "INT"}
]

def registrar_log(mensaje):
    linea = f"[{datetime.now().strftime('%H:%M:%S')}] {mensaje}"
    LOGS_SISTEMA.insert(0, linea)
    if len(LOGS_SISTEMA) > 50: LOGS_SISTEMA.pop()
    print(linea, flush=True)

def validar_email(email: str) -> bool:
    if not email: return False
    email = email.strip().lower()
    if not EXPRESIÓN_EMAIL.match(email): return False
    try: usuario, dominio = email.split("@", 1)
    except Exception: return False
    if dominio in LISTA_NEGRA_DOMINIOS: return False
    if any(p in usuario for p in LISTA_NEGRA_PALABRAS) or any(p in dominio for p in LISTA_NEGRA_PALABRAS): return False
    return True

def registrar_y_verificar_email(email: str) -> bool:
    email_limpio = email.strip().lower()
    if not validar_email(email_limpio) or email_limpio in REGISTRO_EMAILS: return False
    REGISTRO_EMAILS.add(email_limpio)
    METRICAS_GLOBALES["leads_unicos_cazados"] = len(REGISTRO_EMAILS)
    return True

def fallback_prospecto(mercado, ciudad):
    correo_fb = f"info@{mercado.replace(' ', '')}{ciudad.lower().replace(' ', '')}.com"
    if registrar_y_verificar_email(correo_fb): return [{"nombre": mercado.upper(), "email": correo_fb}]
    return []

def extraer_leads_tavily(mercado, ciudad):
    if not api_tavily or not api_openai: return fallback_prospecto(mercado, ciudad)
    datos_contexto = ""
    query_busqueda = f'email contacto correo "{mercado}" "{ciudad}"'
    for intento in range(3):
        try:
            datos_contexto = api_tavily.get_search_context(query=query_busqueda, search_depth="advanced")
            if datos_contexto:
                METRICAS_GLOBALES["busquedas_tavily_exitosas"] += 1
                registrar_log(f"🔎 [TAVILY] Exito absoluto. Query: '{query_busqueda}'. Longitud contexto: {len(datos_contexto)} caracteres.")
                break
            time.sleep(1)
        except Exception as e:
            if intento == 2:
                METRICAS_GLOBALES["busquedas_tavily_fallidas"] += 1
                registrar_log(f"❌ [TAVILY] Fallo critico tras 3 intentos para '{query_busqueda}': {str(e)}")
                return fallback_prospecto(mercado, ciudad)
    if not datos_contexto: return fallback_prospecto(mercado, ciudad)
    try:
        respuesta_ia = api_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extrae emails validos en un objeto JSON con una lista 'leads' que contenga subobjetos 'nombre' y 'email'. No uses bloques de markdown."},
                {"role": "user", "content": datos_contexto}
            ],
            response_format={"type": "json_object"}
        )
        extraccion = json.loads(respuesta_ia.choices.message.content.strip())
        lista_leads = []
        for item in extraccion.get("leads", []):
            email = item.get("email", "").strip().lower()
            if registrar_y_verificar_email(email):
                lista_leads.append({"nombre": item.get("nombre", "").strip().upper() or mercado.upper(), "email": email})
        return lista_leads if lista_leads else fallback_prospecto(mercado, ciudad)
    except Exception as ia_err:
        registrar_log(f"⚠️ [IA PARSING] Error analizando respuesta con gpt-4o-mini: {str(ia_err)}")
        return fallback_prospecto(mercado, ciudad)

def compose_email_marketing(nombre, mercado, link_stripe, idioma):
    if not api_openai: return f"<html><body>Malla Blindada SaaS. Active su plan aqui: <a href='{link_stripe}'>Pagar alta</a></body></html>"
    try:
        contexto_sistema = "Eres un copywriter de respuesta directa elite especializado en SaaS B2B y automatizaciones de IA corporativas."
        contexto_usuario = f"Escribe un correo frio quirurgico en {'ingles' if idioma=='en' else 'espanol'} para el tomador de decisiones de {mercado} llamado {nombre}. Inserta este enlace real de pago directo: {link_stripe}. Devuelve solo HTML limpio sin formato de marcas de codigo markdown."
        respuesta_copy = api_openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": contexto_sistema}, {"role": "user", "content": contexto_usuario}])
        return respuesta_copy.choices.message.content.strip()
    except Exception:
