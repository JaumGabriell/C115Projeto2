#!/usr/bin/env python3
"""
Script para ler dados do acelerômetro FRDM-KL25Z via serial e publicar via MQTT
Versão integrada com MQTT compatível com paho-mqtt v1.x e v2.x
"""

import serial
import time
from datetime import datetime
import json
import paho.mqtt.client as mqtt

# ==================== CONFIGURAÇÕES ====================
# Serial
SERIAL_PORT = '/dev/ttyACM0'  # Porta serial da FRDM-KL25Z
BAUD_RATE = 115200

# MQTT
MQTT_BROKER = "192.168.4.1"  # IP da própria Raspberry Pi
MQTT_PORT = 1883
TOPIC_TELEMETRIA = "carrinho/telemetria"
TOPIC_COMANDO = "carrinho/cmd"
CLIENT_ID = "RaspberryPiFRDM"

# Limite de tombamento
LIMITE_TOMBAMENTO_GRAUS = 45

# ==================== FUNÇÕES DE CALLBACK MQTT ====================
def on_connect(client, userdata, flags, rc):
    """Chamado quando o cliente se conecta ao broker."""
    if rc == 0:
        print("✅ Conectado ao broker MQTT com sucesso!")
        client.subscribe(TOPIC_COMANDO)
        print(f"📡 Subscrito ao tópico de comandos: {TOPIC_COMANDO}")
        # Publica o status inicial
        client.publish(TOPIC_TELEMETRIA, '{"status": "Online e Pronto"}', retain=True)
    else:
        print(f"❌ Falha na conexão MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    """Chamado quando uma mensagem é recebida no tópico de comando."""
    comando = msg.payload.decode().lower()
    print(f"📥 Comando Recebido [{msg.topic}]: {comando}")
    
    # Lógica de controle do carrinho (A SER IMPLEMENTADA)
    if "frente" in comando:
        print("➡️  Movendo carrinho para frente...")
    elif "parar" in comando:
        print("🛑 Parando o carrinho.")

# ==================== INICIALIZAÇÃO ====================
print("=" * 60)
print("🚀 FRDM-KL25Z + MQTT - Sistema de Telemetria")
print("=" * 60)
print(f"📌 Porta Serial: {SERIAL_PORT} @ {BAUD_RATE} bps")
print(f"📌 Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
print(f"📌 Tópico Telemetria: {TOPIC_TELEMETRIA}")
print("=" * 60)

# Verifica versão do paho-mqtt e configura o cliente adequadamente
try:
    # Tenta usar a API v2 (paho-mqtt >= 2.0.0)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, CLIENT_ID)
    print("📦 Usando paho-mqtt API v1")
except:
    # Fallback para API v1 (paho-mqtt < 2.0.0)
    client = mqtt.Client(CLIENT_ID)
    print("📦 Usando paho-mqtt API legacy")

client.on_connect = on_connect
client.on_message = on_message

# Conecta ao Broker MQTT
try:
    print(f"\n🔄 Conectando ao broker MQTT {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(1)  # Aguarda conexão
except Exception as e:
    print(f"❌ Erro ao conectar ao MQTT: {e}")
    print("⚠️  Continuando apenas com leitura serial (sem MQTT)...")
    client = None

# Abre conexão serial
ser = None
try:
    print(f"\n🔄 Conectando à porta serial {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"✅ Conectado à porta serial com sucesso!\n")
    
    # Aguarda estabilização
    time.sleep(2)
    ser.reset_input_buffer()
    
    print("=" * 60)
    print("📡 INICIANDO LEITURA E PUBLICAÇÃO DE DADOS")
    print("=" * 60)
    print("⌨️  Pressione Ctrl+C para sair\n")
    
    contador = 0
    
    # ==================== LOOP PRINCIPAL ====================
    while True:
        try:
            # Verifica se há dados disponíveis
            if ser.in_waiting > 0:
                # Lê linha da serial
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if linha:
                    contador += 1
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    print(f"[{contador:04d}] [{timestamp}] {linha}")
                    
                    # Tenta fazer parse dos dados
                    try:
                        if '|' in linha:
                            partes = linha.split('|')
                            xyz_parte = partes[0].strip()
                            status_parte = partes[1].strip()
                            
                            # Extrai valores
                            x = int(xyz_parte.split('X=')[1].split()[0])
                            y = int(xyz_parte.split('Y=')[1].split()[0])
                            z = int(xyz_parte.split('Z=')[1].split()[0])
                            status = status_parte.split(',')[0].strip()
                            inclinacao = float(status_parte.split(',')[1].strip())
                            
                            print(f"      └─> X={x:4d}  Y={y:4d}  Z={z:4d}  |  Status: {status:8s}  |  Inclinação: {inclinacao:+7.2f}°")
                            
                            # Prepara dados de telemetria
                            dados_telemetria = {
                                "timestamp": time.time(),
                                "acelerometro": {
                                    "x": x,
                                    "y": y,
                                    "z": z
                                },
                                "inclinacao": inclinacao,
                                "status": "Online"
                            }
                            
                            # Verifica tombamento
                            if status == "TOMBADO" or abs(inclinacao) > LIMITE_TOMBAMENTO_GRAUS:
                                dados_telemetria["alerta"] = "TOMBAMENTO DETECTADO!"
                                print(f"      ⚠️  🚨 TOMBAMENTO DETECTADO! 🚨")
                                
                                # Publica alerta de alta prioridade
                                if client:
                                    client.publish(TOPIC_TELEMETRIA, 
                                                 json.dumps({"alerta": "TOMBOU!", "inclinacao": inclinacao}), 
                                                 retain=True)
                            else:
                                dados_telemetria["alerta"] = "Normal"
                            
                            # Publica telemetria completa via MQTT
                            if client:
                                mensagem_json = json.dumps(dados_telemetria)
                                client.publish(TOPIC_TELEMETRIA, mensagem_json)
                                print(f"      📤 Publicado via MQTT")
                            
                            print()  # Linha em branco
                    
                    except Exception as e:
                        print(f"      └─> ⚠️  Erro ao fazer parse: {e}\n")
            
            # Pequeno delay para não sobrecarregar CPU
            time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("⏹️  INTERROMPIDO PELO USUÁRIO")
            print("=" * 60)
            print(f"📊 Total de mensagens recebidas: {contador}")
            break
        
        except Exception as e:
            print(f"\n❌ Erro durante leitura: {e}")
            time.sleep(1)

except serial.SerialException as e:
    print(f"\n❌ ERRO ao abrir porta serial: {e}")
    print("\n💡 POSSÍVEIS SOLUÇÕES:")
    print("   1. Verifique se a FRDM-KL25Z está conectada:")
    print("      ls -la /dev/ttyACM*")
    print()
    print("   2. Adicione seu usuário ao grupo dialout:")
    print("      sudo usermod -a -G dialout $USER")
    print("      Depois faça logout e login novamente")
    print()
    print("   3. Ou dê permissão temporária:")
    print("      sudo chmod 666 /dev/ttyACM0")
    print()

except Exception as e:
    print(f"\n❌ ERRO inesperado: {e}")

finally:
    # Fecha conexões
    if ser and ser.is_open:
        ser.close()
        print("\n🔌 Porta serial fechada")
    
    if client:
        print("🔄 Desconectando do MQTT...")
        client.loop_stop()
        client.disconnect()
        print("🔌 Desconectado do MQTT")
    
    print("\n👋 Programa encerrado")
