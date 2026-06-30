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
    "leads_unicos_cazados": 0, "busquedas_tavily_exitosas": 0, "busquedas_tavily_fallidas": 0, 
    "emails_enviados_exito": 0, "emails_rebotados": 0, "productos_mas_vendidos": {}
}

EXPRESIÓN_EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
LISTA_NEGRA_DOMINIOS = {"example.com", "ejemplo.com", "email.com", "test.com", "privacy.com", "noreply.com", "support.com", "wix.com", "wordpress.com"}
LISTA_NEGRA_PALABRAS = {"test", "prueba", "ejemplo", "example", "noreply", "support", "soporte", "admin", "abuse", "spam", "billing", "facturas"}

MERCADOS_OBJETIVO = [
    {
        "es": "clinica dental", "en": "dentist clinic", 
        "asunto": "Plan de Crecimiento: Resenas de Google de 5 Estrellas", 
        "asunto_en": "Growth Plan: 5-Star Google Reviews Drive", 
        "env_link": "STRIPE_LINK_RESENAS_GOOGLE",
        "gancho_es": "vimos que tu clínica tiene reseñas que podrían mejorar para atraer más pacientes locales de forma automática.",
        "gancho_en": "we noticed your dental practice could unlock massive local revenue by optimization of your Google Maps reviews structure."
    },
    {
        "es": "agencia inmobiliaria", "en": "real estate agency", 
        "asunto": "Exclusividad Territorial: Enterprise Omnipresencia 100K", 
        "asunto_en": "Territorial Exclusivity: Enterprise Omnipresence 100K", 
        "env_link": "STRIPE_LINK_OMNIPRESENCIA",
        "gancho_es": "bloqueamos la captación de propiedades de tu competencia directa mediante automatización exclusiva en tu código postal.",
        "gancho_en": "we enforce strict programmatic deployment to intercept property listings before your local competitors even get a notification."
    },
    {
        "es": "empresa ciberseguridad", "en": "cybersecurity company", 
        "asunto": "Auditoria de Vulnerabilidad Cyber-Shield Gratuita", 
        "asunto_en": "Free Cyber-Shield Vulnerability Audit", 
        "env_link": "STRIPE_LINK_CYBER_SHIELD",
        "gancho_es": "detectamos fugas menores de configuración en puertos públicos indexados que comprometen tu infraestructura.",
        "gancho_en": "our passive network mapping flagged open parameters that could expose core databases to external scanning vulnerabilities."
    },
    {
        "es": "vendedor amazon", "en": "amazon seller brand", 
        "asunto": "Prueba de 3 dias: Clonador de Productos a Video Vertical IA", 
        "asunto_en": "3-Day Trial: AI Product to Vertical Video Cloner", 
        "env_link": "STRIPE_LINK_CLONADOR_VIDEO",
        "gancho_es": "transformamos tus listings estáticos de ASIN en anuncios de TikTok estructurados en menos de 45 segundos.",
        "gancho_en": "our pipeline automatically parses your current ASIN metrics and synthesizes high-converting TikTok organic creatives."
    }
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
    correo_fb = f"contacto@{mercado.replace(' ', '')}{ciudad.lower().replace(' ', '')}.com"
    if registrar_y_verificar_email(correo_fb): 
        return [{"nombre": mercado.upper(), "email": correo_fb, "web": "Fallback Automático", "fuente": "Algoritmo Generativo"}]
    return []

# ==============================================================================
# 3. [MEJORADO] COMPONENTE AVANZADO DE EXTRACCIÓN DE CLIENTES (TAVILY + IA)
# ==============================================================================
def extraer_leads_tavily(mercado, ciudad):
    if not api_tavily or not api_openai: return fallback_prospecto(mercado, ciudad)
    
    # Queries diversificadas de alta intención para barrer correos y metadata real
    queries = [
        f'"{mercado}" "{ciudad}" email OR correo OR contacto',
        f'site:://linkedin.com "{mercado}" "{ciudad}"',
        f'"{mercado}" "{ciudad}" "@gmail.com" OR "@" "contacto"'
    ]
    
    datos_contexto = ""
    for query_busqueda in queries:
        try:
            # depth="advanced" para forzar raspado profundo de URLs de empresas
            raw_context = api_tavily.get_search_context(query=query_busqueda, search_depth="advanced")
            if raw_context and len(raw_context) > 200:
                datos_contexto += f"\n--- Resultado Consulta [{query_busqueda}] ---\n" + raw_context
                METRICAS_GLOBALES["busquedas_tavily_exitosas"] += 1
        except Exception as e:
            registrar_log(f"⚠️ [TAVILY MULTI-QUERY] Error parcial barriendo query '{query_busqueda}': {str(e)}")
            
    if not datos_contexto.strip():
        METRICAS_GLOBALES["busquedas_tavily_fallidas"] += 1
        return fallback_prospecto(mercado, ciudad)
    
    try:
        prompt_sistema = (
            "Eres un agente scraper experto en OSINT corporativo. Tu misión es extraer leads empresariales verídicos.\n"
            "Analiza el contexto y devuelve un objeto JSON estructurado con una lista de 'leads'.\n"
            "Cada lead DEBE contener obligatoriamente:\n"
            "- 'nombre': Razón social de la empresa o nombre del profesional.\n"
            "- 'email': Dirección de correo corporativo verificable.\n"
            "- 'web': URL del sitio o perfil de red social de donde se extrajo.\n"
            "- 'contexto_empresa': Una breve frase describiendo a qué se dedican de forma específica.\n\n"
            "Regla estricta: No inventes datos. Si no hay correos reales, devuelve la lista vacía. No uses bloques markdown ```json."
        )
        
        respuesta_ia = api_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Datos capturados en tiempo real:\n{datos_contexto}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        res_json = json.loads(respuesta_ia.choices.message.content)
        leads_filtrados = []
        
        for l in res_json.get("leads", []):
            correo = l.get("email", "").strip().lower()
            if registrar_y_verificar_email(correo):
                l["email"] = correo
                leads_filtrados.append(l)
                registrar_log(f"🎯 [LEAD EXTRAÍDO] Encontrado: {l['nombre']} ({correo}) de {l.get('web', 'Desconocido')}")
                
        return leads_filtrados if leads_filtrados else fallback_prospecto(mercado, ciudad)
        
    except Exception as e:
        registrar_log(f"❌ [EXTRACTOR IA] Error de parseo crítico en extracción: {str(e)}")
        return fallback_prospecto(mercado, ciudad)

# ==============================================================================
# 4. [MEJORADO] SISTEMA DE ENVÍO DE CORREOS HIPER-PERSONALIZADOS
# ==============================================================================
def enviar_cold_email_real(lead, mercado_info, idioma, stripe_link):
    if not SENDER_KEY:
        registrar_log(f"🚫 [EMAIL SIMULADO] Lead: {lead['email']} - Token no configurado.")
        return False
        
    # Construcción de plantilla ultra-personalizada basada en metadata inyectada
    nombre_target = lead.get("nombre", "Director").title()
    meta_contexto = lead.get("contexto_empresa", "tu presencia comercial en el sector")
    gancho = mercado_info["gancho_es"] if idioma == "es" else mercado_info["gancho_en"]
    
    if idioma == "es":
