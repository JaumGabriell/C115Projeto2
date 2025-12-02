#include "mbed.h"
#include "MMA8451Q.h" // Biblioteca para o acelerômetro embutido

// 1. Inicializa a comunicação Serial (USB)
// UnbufferedSerial é a classe correta no Mbed OS 6
UnbufferedSerial pc(USBTX, USBRX, 115200);

// 2. Inicializa o Acelerômetro (Endereço I2C 0x1d é o padrão do MMA8451Q na FRDM)
MMA8451Q acc(PTE25, PTE24, 0x1d); // PTE25=SDA, PTE24=SCL

// Variáveis para armazenar as leituras
float x, y, z;
float inclinacao_graus;

// Função auxiliar para imprimir via serial
void print_serial(const char* str) {
    pc.write(str, strlen(str));
}

// Função para calcular inclinação total (detecta tombamento em qualquer direção)
float calcular_inclinacao_total() {
    // Lê os valores X, Y e Z do acelerômetro (valores brutos de 14-bit)
    int16_t raw_x = acc.getRawX();
    int16_t raw_y = acc.getRawY();
    int16_t raw_z = acc.getRawZ();
    
    // Converte para g (gravidade) - MMA8451Q retorna valores de -8192 a +8191 para ±2g
    x = (float)raw_x / 4096.0;
    y = (float)raw_y / 4096.0;
    z = (float)raw_z / 4096.0;
    
    // Calcula o ângulo de inclinação em relação à vertical (eixo Z quando plano)
    // Quando plano e horizontal com a face para cima, Z deve ser positivo (~1g)
    // Se de cabeça para baixo, Z será negativo
    
    // Magnitude do vetor horizontal (X e Y)
    float horizontal = sqrt(x*x + y*y);
    
    // Ângulo de inclinação em relação à vertical
    // Usa Z sem abs() para detectar orientação
    float radianos = atan2(horizontal, z);
    
    // Converte para graus
    return radianos * (180.0 / M_PI);
}

int main() {
    char buffer[100];
    
    // Mensagem inicial
    sprintf(buffer, "Iniciando Monitoramento de Tombamento...\r\n");
    print_serial(buffer);

    // Loop principal
    while (true) {
        
        inclinacao_graus = calcular_inclinacao_total();
        
        // Debug: mostra valores brutos
        int x_int = (int)(x * 100);
        int y_int = (int)(y * 100);
        int z_int = (int)(z * 100);
        sprintf(buffer, "X=%d Y=%d Z=%d | ", x_int, y_int, z_int);
        print_serial(buffer);
        
        // --- 3. Lógica de Tombamento ---
        const char* status;

        // Exemplo de limite: 45 graus (pode ser ajustado)
        if (inclinacao_graus > 45.0 || inclinacao_graus < -45.0) {
            status = "TOMBADO";
        } else {
            status = "OK";
        }

        // --- 4. Envio pela Serial (o que a RPi 4 vai ler) ---
        // Enviamos o status e o valor da inclinação
        int parte_inteira = (int)inclinacao_graus;
        int parte_decimal = (int)((inclinacao_graus - parte_inteira) * 100);
        if (parte_decimal < 0) parte_decimal = -parte_decimal;
        sprintf(buffer, "%s, %d.%02d\r\n", status, parte_inteira, parte_decimal);
        print_serial(buffer);
        
        // Aguarda 1 segundo antes de nova leitura
        ThisThread::sleep_for(1000ms);
    }
}
