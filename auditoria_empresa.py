import subprocess
import re
import urllib.request


def auditoria_final_vanguardia(ip):
    print("\n" + "🛡️ " * 10)
    print(f"  IDENTIFICANDO HARDWARE EN {ip}")
    print("🛡️ " * 10)

    # 1. Despertar el rastro físico
    subprocess.run(f"ping -n 1 {ip}", stdout=subprocess.DEVNULL, shell=True)

    try:
        # 2. Leer la tabla ARP del sistema
        output = subprocess.check_output(f"arp -a {ip}", shell=True).decode('cp1252')
        mac_match = re.search(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})", output)

        if mac_match:
            mac = mac_match.group(0).upper().replace("-", ":")
            print(f"✅ HUELLA FÍSICA (MAC): {mac}")

            # 3. Identificar Marca (API de Fabricantes)
            prefix = mac.replace(":", "")[:6]
            url = f"https://macvendors.com{prefix}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            with urllib.request.urlopen(req) as response:
                vendor = response.read().decode()
                print(f"🏢 FABRICANTE REAL: {vendor}")
                print("\n✅ CONCLUSIÓN TÉCNICA: Identificación exitosa.")
        else:
            print("❌ El dispositivo oculta su MAC. Está en modo sigilo.")

    except Exception as e:
        print(f"⚠️ Error de conexión: {e}")


if __name__ == "__main__":
    auditoria_final_vanguardia('192.168.1.55')
