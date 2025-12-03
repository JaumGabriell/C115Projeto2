# 🚗 Sistema IoT de Detecção de Tombamento

Projeto desenvolvido para a disciplina C115 - Laboratório de Sistemas Embarcados (INATEL), implementando um sistema completo de monitoramento de tombamento de veículo usando IoT.

## 📋 Sobre o Projeto

Sistema de detecção de tombamento em tempo real que integra:
- **FRDM-KL25Z**: Leitura do acelerômetro MMA8451Q
- **Raspberry Pi 4**: Processamento e broker MQTT
- **Dashboard Web**: Visualização em tempo real via WebSocket

O sistema monitora continuamente a inclinação do veículo e alerta quando detecta tombamento (inclinação > 45°).

## 🛠️ Componentes

### Hardware
- **FRDM-KL25Z**: Microcontrolador ARM Cortex-M0+ com acelerômetro MMA8451Q integrado
- **Raspberry Pi 4**: Processador principal rodando Raspberry Pi OS
- Cabo USB para comunicação serial

### Software
- **Mbed OS 6**: Firmware do microcontrolador (C++)
- **Python 3**: Script de leitura serial e publicação MQTT
- **Mosquitto**: Broker MQTT
- **HTML/JavaScript**: Dashboard web com Paho MQTT

## 📁 Estrutura do Projeto

```
C115Projeto2/
├── src/
│   └── main.cpp              # Firmware FRDM-KL25Z (Mbed OS)
├── frdm_mqtt_reader.py       # Script Python (Raspberry Pi)
├── dashboard.html            # Dashboard web
└── README.md                 # Este arquivo
```

## 🚀 Funcionalidades

### FRDM-KL25Z (`main.cpp`)
- ✅ Leitura do acelerômetro MMA8451Q (eixos X, Y, Z)
- ✅ Cálculo de inclinação total em graus
- ✅ Detecção de tombamento (limite: 45°)
- ✅ Transmissão via serial USB (115200 bps)
- ✅ Atualização a cada 1 segundo

### Raspberry Pi (`frdm_mqtt_reader.py`)
- ✅ Leitura de dados da porta serial `/dev/ttyACM0`
- ✅ Parse de dados do acelerômetro
- ✅ Publicação via MQTT no tópico `carrinho/telemetria`
- ✅ Detecção e alerta de tombamento
- ✅ Compatibilidade com paho-mqtt v1.x e v2.x
- ✅ Tratamento robusto de erros

### Dashboard Web (`dashboard.html`)
- ✅ Conexão WebSocket MQTT (porta 9001)
- ✅ Visualização em tempo real dos 3 eixos (X, Y, Z)
- ✅ Indicador de inclinação total
- ✅ Alerta visual de tombamento
- ✅ Indicador de status de conexão
- ✅ Interface responsiva e moderna

## 🔧 Configuração e Instalação

### 1. FRDM-KL25Z

#### Compilar e Gravar
1. Abra o projeto no Mbed Studio ou use Mbed CLI
2. Compile o código em `src/main.cpp`
3. Grave o arquivo `.bin` na FRDM-KL25Z (modo bootloader)
4. Conecte via USB ao Raspberry Pi

### 2. Raspberry Pi 4

#### Instalar Dependências
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e pip
sudo apt install python3 python3-pip -y

# Instalar bibliotecas Python
pip3 install pyserial paho-mqtt

# Instalar Mosquitto MQTT Broker
sudo apt install mosquitto mosquitto-clients -y
```

#### Configurar Mosquitto para WebSocket
```bash
# Editar configuração
sudo nano /etc/mosquitto/mosquitto.conf
```

Adicionar as seguintes linhas:
```
listener 1883
protocol mqtt

listener 9001
protocol websockets

allow_anonymous true
```

Reiniciar Mosquitto:
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

#### Configurar Porta Serial
```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Ou dar permissão temporária
sudo chmod 666 /dev/ttyACM0
```

### 3. Dashboard Web

Editar `dashboard.html` e ajustar o IP do broker MQTT:
```javascript
const MQTT_BROKER = "192.168.4.1"; // IP do seu Raspberry Pi
```

Abrir o arquivo em qualquer navegador moderno (Chrome, Firefox, Edge).

## ▶️ Executando o Sistema

### 1. Iniciar o Script Python no Raspberry Pi
```bash
python3 frdm_mqtt_reader.py
```

### 2. Abrir o Dashboard
Abrir `dashboard.html` em um navegador web.

### 3. Testar o Sistema
- Mover a FRDM-KL25Z e observar as leituras
- Inclinar mais de 45° para ativar o alerta de tombamento

## 📊 Formato dos Dados

### Serial (FRDM → Raspberry Pi)
```
X=12 Y=34 Z=98 | OK, 23.45
X=-45 Y=67 Z=-12 | TOMBADO, 67.89
```

### MQTT (Raspberry Pi → Dashboard)
```json
{
  "timestamp": 1701234567.89,
  "acelerometro": {
    "x": 12,
    "y": 34,
    "z": 98
  },
  "inclinacao": 23.45,
  "status": "Online",
  "alerta": "Normal"
}
```

Quando há tombamento:
```json
{
  "alerta": "TOMBAMENTO DETECTADO!",
  "inclinacao": 67.89
}
```

## 🎯 Parâmetros Configuráveis

### `main.cpp` (FRDM-KL25Z)
- `const float LIMITE_TOMBAMENTO = 45.0`: Ângulo de detecção de tombamento
- `ThisThread::sleep_for(1000ms)`: Intervalo de leitura

### `frdm_mqtt_reader.py`
- `SERIAL_PORT = '/dev/ttyACM0'`: Porta serial
- `BAUD_RATE = 115200`: Taxa de comunicação
- `MQTT_BROKER = "192.168.4.1"`: IP do broker
- `MQTT_PORT = 1883`: Porta MQTT
- `LIMITE_TOMBAMENTO_GRAUS = 45`: Limite de inclinação

### `dashboard.html`
- `MQTT_BROKER = "192.168.4.1"`: IP do broker
- `MQTT_PORT = 9001`: Porta WebSocket

## 🐛 Troubleshooting

### Erro: Porta Serial não encontrada
```bash
# Verificar portas disponíveis
ls -la /dev/ttyACM*

# Adicionar permissões
sudo usermod -a -G dialout $USER
# Fazer logout e login novamente
```

### Dashboard não conecta ao MQTT
- Verificar se Mosquitto está rodando: `sudo systemctl status mosquitto`
- Verificar se a porta 9001 está configurada para WebSocket
- Conferir o IP do Raspberry Pi: `hostname -I`
- Testar conexão: `mosquitto_sub -h localhost -t carrinho/telemetria`

### Sem dados no Dashboard
- Verificar se o script Python está rodando
- Conferir logs do script Python
- Testar publicação manual: `mosquitto_pub -h localhost -t carrinho/telemetria -m '{"teste": 123}'`

## 📝 Tópicos MQTT

- `carrinho/telemetria`: Dados de telemetria em JSON
- `carrinho/cmd`: Comandos para o carrinho (implementação futura)


---

**Data de Desenvolvimento**: Dezembro 2025  
**Disciplina**: C115 
**Alunos**: Eduardo Augusto Fonseca Rezende-1938 & João Gabriel de Carvalho Barbosa-1937 

