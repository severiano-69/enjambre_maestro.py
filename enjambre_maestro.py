import os, sys, time, random, threading, json, re, requests, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify

app = Flask(__name__)
os.environ["PYTHONUNBUFFERED"] = "1"

SMTP_SERVER = os.environ.get("SMTP_SERVER", "://dondominio.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
EMAIL_REMITENTE = os.environ.get("REMITENTE_EMAIL", "info@enjambresaas.online")
EMAIL_PASSWORD = os.environ.get("REMITENTE_PASSWORD", "")

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SENDER_KEY = os.environ.get("SENDER_TOKEN")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WH_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

try:
    from openai import OpenAI
    api_openai = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
except: api_openai = None

try:
    from tavily import TavilyClient
    api_tavily = TavilyClient(api_key=TAVILY_KEY) if TAVILY_KEY else None
except: api_tavily = None

REGISTRO_EMAILS = set()
METRICAS_GLOBALES = {
    "status_motor": "ONLINE", "ventas_totales_recibidas": 0, "ingresos_acumulados_eur": 0.0,
    "leads_unicos_cazados": 0, "busquedas_tavily_exitosas": 0, "busquedas_tavily_fallidas": 0,
    "emails_enviados_exito": 0, "emails_fallidos": 0
}

EXPRESIÓN_EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
LISTA_NEGRA_DOMINIOS = {"example.com", "ejemplo.com", "email.com", "test.com", "privacy.com", "noreply.com", "support.com", "wix.com", "wordpress.com"}
LISTA_NEGRA_PALABRAS = {"test", "prueba", "ejemplo", "example", "noreply", "support", "soporte", "admin"}

def cargar_mercados_seguros():
    lista = []
    lista.append({"es": "clinica dental", "env_link": "STRIPE_LINK_RESENAS_GOOGLE", "asunto": "Plan de Crecimiento: Resenas de Google de 5 Estrellas", "gancho_es": "vimos que tu clinica tiene resenas que podrian mejorar para atraer mas pacientes locales."})
    lista.append({"es": "agencia inmobiliaria", "env_link": "STRIPE_LINK_OMNIPRESENCIA", "asunto": "Exclusividad Territorial: Enterprise Omnipresencia 100K", "gancho_es": "bloqueamos la captacion de propiedades de tu competencia directa en tu codigo postal."})
    lista.append({"es": "empresa ciberseguridad", "env_link": "STRIPE_LINK_CYBER_SHIELD", "asunto": "Auditoria de Vulnerabilidad Cyber-Shield Gratuita", "gancho_es": "detectamos fugas menores de configuracion en puertos publicos indexados que comprometen tu infraestructura."})
    lista.append({"es": "vendedor amazon", "env_link": "STRIPE_LINK_CLONADOR_VIDEO", "asunto": "Prueba de 3 dias: Clonador de Productos a Video Vertical IA", "gancho_es": "transformamos tus listings estaticos de ASIN en anuncios de TikTok en menos de 45 segundos."})
    lista.append({"es": "tienda online", "env_link": "STRIPE_LINK_FUGAS_LEADS", "asunto": "Alerta de Seguridad: Sistema de Malla Blindada para Fugas de Leads", "gancho_es": "detectamos que estas perdiendo mas del 35% de intencion de compra en el checkout por falta de persistencia automatica."})
    lista.append({"es": "negocio local", "env_link": "STRIPE_LINK_PROMOCIONES_FLASH", "asunto": "Estrategia Malla Blindada - Generador de Promociones Flash por IA", "gancho_es": "automatizamos ofertas relampago segmentadas segun el stock inactivo de tu inventario local."})
    lista.append({"es": "comercio local", "env_link": "STRIPE_LINK_OPTIMIZADOR_MAPS", "asunto": "Optimizador de Ficha Google Maps Automático", "gancho_es": "corregimos las palabras clave de tu ficha para posicionarte en el Top 3 local de busquedas de Google."})
    lista.append({"es": "pyme expansion", "env_link": "STRIPE_LINK_MALLA_50K", "asunto": "Acceso Prioritario: Malla Blindada 50K", "gancho_es": "desplegamos infraestructura automatizada para capturar hasta 50.000 euros en volumen de negocio latente."})
    lista.append({"es": "empresa premium", "env_link": "STRIPE_LINK_MALLA_ORO", "asunto": "Contrato Corporativo: Malla Blindada Oro", "gancho_es": "asignamos recursos de computacion prioritarios para blindar tus flujos de adquisicion premium."})
    lista.append({"es": "crypto startup", "env_link": "STRIPE_LINK_MALLA_CRIPTO_BTC", "asunto": "Ecosistema de Cobros Malla Blindada Cripto BTC", "gancho_es": "conectamos pasarelas de pago alternativas blindadas contra bloqueos bancarios tradicionales."})
    lista.append({"es": "consultoria profesional", "env_link": "STRIPE_LINK_PAGINAS_WEB_SEO", "asunto": "Rediseno de Infraestructura: Paginas Web & SEO Avanzado", "gancho_es": "reconstruimos la arquitectura tecnica de tu web para dominar la intencion de busqueda comercial."})
    lista.append({"es": "marca ecom", "env_link": "STRIPE_LINK_TENDENCIAS_AMAZON", "asunto": "SaaS Malla Blindada - Tendencias Amazon Pro", "gancho_es": "inyectamos analisis predictivo para interceptar tendencias de productos antes de su saturacion."})
    return lista

MERCADOS_OBJETIVO = cargar_mercados_seguros()

def enviar_correo_smtp(destinatario, asunto, cuerpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=12)
        server.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
        server.sendmail(EMAIL_REMITENTE, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[SMTP ERR] Fallo envio a {destinatario}: {e}", flush=True)
        return False

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
    limite_leads = int(datos.get('limite', 1))
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

    operaciones = []
    if api_openai and leads_cazados:
        for lead_email in leads_cazados:
            link = os.environ.get(mercado_encontrado['env_link'], "https://stripe.com")
            prompt = f"Redacta cold email corto para {lead_email}. Gancho: {mercado_encontrado['gancho_es']}. Link obligatorio: {link}."
            try:
                res_ia = api_openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.7)
                cuerpo = res_ia.choices.message.content
                
                # DISPARO REAL AUTOMÁTICO EN PRODUCCIÓN CON TU CORREO DE DONDOMINIO
                if enviar_correo_smtp(lead_email, mercado_encontrado['asunto'], cuerpo):
                    METRICAS_GLOBALES["emails_enviados_exito"] += 1
                    operaciones.append({"email": lead_email, "status": "Email real disparado con exito", "link": link})
                else:
                    METRICAS_GLOBALES["emails_fallidos"] += 1
            except: pass

    return jsonify({"success": True, "mercado": mercado_buscado, "leads_total": len(leads_cazados), "operaciones": operaciones, "metricas": METRICAS_GLOBALES}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=False)
