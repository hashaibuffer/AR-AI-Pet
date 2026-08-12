/*
 * Temporary receive-side diagnostic for the vendor Nano UART.
 *
 * This sketch deliberately does not touch motor pins. It reports every byte
 * received on the 115200-baud hardware UART so BLE transparent-transfer bytes
 * can be distinguished from the expected A/E/Z commands.
 */
#include <Arduino.h>

void printByte(unsigned int value) {
  Serial.print("BYTE:");
  if (value < 0x10) Serial.print('0');
  Serial.print(value, HEX);
  Serial.print(':');
  if (value >= 0x20 && value <= 0x7E) {
    Serial.print(static_cast<char>(value));
  } else {
    Serial.print('.');
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("UART_PROBE:115200");
}

void loop() {
  while (Serial.available() > 0) {
    printByte(static_cast<unsigned int>(Serial.read()));
  }
}
