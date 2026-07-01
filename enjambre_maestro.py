import os, sys, time, random, threading, json, re, requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
os.environ["PYTHONUNBUFFERED"] = "1"

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SENDER_KEY = os.environ.get("SENDER_TOKEN")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WH_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
EMAIL_REMITENTE = os.environ.get("REMITENTE_EMAIL", "severianobenitez@enjambresaas.online")

try:
    from openai import OpenAI
    api_openai = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
except: api_openai = None

try:
    from tavily import TavilyClient
    api_tavily = TavilyClient(api_key=TAVILY_KEY) if TAVILY_KEY else None
except: api_tavily = None

REGISTRO_EMAILS, LOGS_SISTEMA = set(), []
METRICAS_GLOBALES = {
    "status_motor": "ONLINE", "ventas_totales_recibidas": 0, "ingresos_acumulados_eur": 0.0,
    "leads_unicos_cazados": 0, "busquedas_tavily_exitosas": 0, "busquedas_tavily_fallidas": 0,
    "emails_enviados_exito": 0, "emails_rebotados": 0, "productos_mas_vendidos": {}
}

EXPRESIÓN_EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
LISTA_NEGRA_DOMINIOS = {"example.com", "ejemplo.com", "email.com", "test.com", "privacy.com", "noreply.com", "support.com", "wix.com", "wordpress.com"}
LISTA_NEGRA_PALABRAS = {"test", "prueba", "ejemplo", "example", "noreply", "support", "soporte", "admin"}

def cargar_mercados_seguros():
    lista = []
    lista.append({"es": "clinica dental", "en": "dentist clinic", "asunto": "Plan de Crecimiento: Resenas de Google de 5 Estrellas", "env_link": "STRIPE_LINK_RESENAS_GOOGLE", "gancho_es": "vimos que tu clinica tiene resenas que podrian mejorar para atraer mas pacientes.", "gancho_en": "google maps reviews improvement."})
    lista.append({"es": "agencia inmobiliaria", "en": "real estate agency", "asunto": "Exclusividad Territorial: Enterprise Omnipresencia 100K", "env_link": "STRIPE_LINK_OMNIPRESENCIA", "gancho_es": "bloqueamos la captacion de propiedades de tu competencia directa mediante automatizacion.", "gancho_en": "intercept property listings."})
    lista.append({"es": "empresa ciberseguridad", "en": "cybersecurity company", "asunto": "Auditoria de Vulnerabilidad Cyber-Shield Gratuita", "env_link": "STRIPE_LINK_CYBER_SHIELD", "gancho_es": "detectamos fugas menores de configuracion en puertos publicos indexados.", "gancho_en": "vulnerability scanning database issues."})
    lista.append({"es": "vendedor amazon", "en": "amazon seller brand", "asunto": "Prueba de 3 dias: Clonador de Productos a Video Vertical IA", "env_link": "STRIPE_LINK_CLONADOR_VIDEO", "gancho_es": "transformamos tus listings estaticos de ASIN en anuncios de TikTok.", "gancho_en": "synthesizes high-converting TikTok creatives."})
    lista.append({"es": "tienda online", "en": "ecommerce store", "asunto": "Alerta de Seguridad: Sistema de Malla Blindada para Fugas de Leads", "env_link": "STRIPE_LINK_FUGAS_LEADS", "gancho_es": "detectamos que estas perdiendo mas del 35% de intencion de compra en el checkout.", "gancho_en": "sales funnel tracking drops."})
    lista.append({"es": "negocio local", "en": "local business", "asunto": "Estrategia Malla Blindada - Generador de Promociones Flash por IA", "env_link": "STRIPE_LINK_PROMOCIONES_FLASH", "gancho_es": "automatizamos ofertas relampago segmentadas segun el stock inactivo.", "gancho_en": "hyper-targeted flash sales."})
    lista.append({"es": "comercio local", "en": "local shop", "asunto": "Optimizador de Ficha Google Maps Automático", "env_link": "STRIPE_LINK_OPTIMIZADOR_MAPS", "gancho_es": "corregimos las palabras clave de tu ficha para posicionarte en el Top 3.", "gancho_en": "restructure your local map parameters."})
    lista.append({"es": "pyme expansion", "en": "growing business", "asunto": "Acceso Prioritario: Malla Blindada 50K", "env_link": "STRIPE_LINK_MALLA_50K", "gancho_es": "desplegamos infraestructura automatizada para capturar volumen de negocio latente.", "gancho_en": "capture unhidden pipeline volume."})
    lista.append({"es": "empresa premium", "en": "premium company", "asunto": "Contrato Corporativo: Malla Blindada Oro", "env_link": "STRIPE_LINK_MALLA_ORO", "gancho_es": "asignamos recursos de computacion prioritarios para blindar tus flujos.", "gancho_en": "fully insulate your acquisition tracks."})
    lista.append({"es": "crypto startup", "en": "web3 platform", "asunto": "Ecosistema de Cobros Malla Blindada Cripto BTC", "env_link": "STRIPE_LINK_MALLA_CRIPTO_BTC", "gancho_es": "conectamos pasarelas de pago alternativas blindadas contra bloqueos.", "gancho_en": "immune to traditional settlement freezes."})
    lista.append({"es": "consultoria profesional", "en": "professional consulting", "asunto": "Rediseno de Infraestructura: Paginas Web & SEO Avanzado", "env_link": "STRIPE_LINK_PAGINAS_WEB_SEO", "gancho_es": "reconstruimos la arquitectura tecnica de tu web para dominar la intencion de busqueda.", "gancho_en": "headless stack to claim search real estate."})
    lista.append({"es": "marca ecom", "en": "amazon trends brand", "asunto": "SaaS Malla Blindada - Tendencias Amazon Pro", "env_link": "STRIPE_LINK_TENDENCIAS_AMAZON", "gancho_es": "inyectamos analisis predictivo para interceptar tendencias de productos.", "gancho_en": "capture product trends before saturation."})
    return lista

MERCADOS_OBJETIVO = cargar_mercados_seguros()

@app.route('/')
def index():
    return jsonify({"status": "Motor Operativo", "mercados": len(MERCADOS_OBJETIVO), "metricas": METRICAS_GLOBALES})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": str(datetime.now())}), 200

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    event = request.get_json() or {}
    tipo = event.get('type', '')
    if tipo in ['checkout.session.completed', 'charge.succeeded']:
        data_obj = event.get('data', {}).get('object', {})
        monto = data_obj.get('amount_total', data_obj.get('amount', 0)) / 100.0
        email = data_obj.get('customer_details', {}).get('email', 'anonimo@email.com')
        METRICAS_GLOBALES["ventas_totales_recibidas"] += 1
        METRICAS_GLOBALES["ingresos_acumulados_eur"] += monto
        print(f"[LIVE LOG] Pago exitoso: {monto} EUR de {email}", flush=True)
    return jsonify({"success": True}), 200

@app.route('/prospectar', methods=['POST'])
def ejecutar_prospeccion():
    datos = request.get_json() or {}
    mercado_buscado = datos.get('market', datos.get('mercado', '')).lower()
    limite_leads = int(datos.get('limite', 2))
    mercado_encontrado = next((m for m in MERCADOS_OBJETIVO if m['es'] == mercado_buscado), None)
    
    if not mercado_encontrado or not api_tavily:
        return jsonify({"success": False, "error": "Mercado no mapeado o Tavily caido."}), 400
        
    try:
        res = api_tavily.search(query=f"emails de contacto de {mercado_buscado} en espana", max_results=10)
        METRICAS_GLOBALES["busquedas_tavily_exitosas"] += 1
    except:
        METRICAS_GLOBALES["busquedas_tavily_fallidas"] += 1
        return jsonify({"success": False, "error": "Fallo Tavily"}), 500

    leads_cazados = []
    for texto in [r.get('content', '') for r in res.get('results', [])]:
        for email in re.findall(r'[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', texto):
            em = email.lower().strip()
            if EXPRESIÓN_EMAIL.match(em) and em.split('@')[-1] not in LISTA_NEGRA_DOMINIOS:
                if em not in REGISTRO_EMAILS and len(leads_cazados) < limite_leads:
                    REGISTRO_EMAILS.add(em)
                    leads_cazados.append(em)
                    METRICAS_GLOBALES["leads_unicos_cazados"] += 1

    propuestas = []
    if api_openai and leads_cazados:
        for lead_email in leads_cazados:
            link = os.environ.get(mercado_encontrado['env_link'], "https://stripe.com")
            prompt = f"Redacta cold email para {lead_email}. Gancho: {mercado_encontrado['gancho_es']}. Link: {link}"
            try:
                res_ia = api_openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.7)
                propuestas.append({"email": lead_email, "asunto": mercado_encontrado['asunto'], "cuerpo": res_ia.choices.message.content, "link": link})
                METRICAS_GLOBALES["emails_enviados_exito"] += 1
            except: pass

    return jsonify({"success": True, "mercado": mercado_buscado, "leads_total": len(leads_cazados), "emails": propuestas}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=False)
