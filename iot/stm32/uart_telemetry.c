// STM32H7 — UART telemetry example
// Sends: M:42,T:31,H:68,PH:64,R:0  every 5 minutes
// PH is pH*10 to avoid float in UART string. Keep protocol simple; add checksum later.

#include "main.h"
extern UART_HandleTypeDef huart2; // to ESP32

void send_telemetry(float moisture, float temp, float hum, float ph, uint8_t rain) {
    char buf[64];
    int ph10 = (int)(ph * 10 + 0.5f);
    int len = snprintf(buf, sizeof(buf), "M:%d,T:%d,H:%d,PH:%d,R:%d\n",
        (int)moisture, (int)temp, (int)hum, ph10, rain);
    HAL_UART_Transmit(&huart2, (uint8_t*)buf, len, 1000);
}

void loop_example(void) {
    // Read sensors (replace with real ADC/I2C reads)
    float moisture = 42; // from capacitive sensor via ADC
    float temp = 31;     // from DHT/SHT
    float hum = 68;
    float ph = 6.4f;     // from pH probe via ADC
    uint8_t rain = 0;
    send_telemetry(moisture, temp, hum, ph, rain);
    HAL_Delay(300000); // 5 min
}
