/*
 * NanoDrive firmware v0.9
 * Arduino Nano + A4950 differential-drive base
 *
 * UART1 is the Nano hardware serial port (D0/D1), shared with the USB CH340.
 * Flash and diagnose through USB. During StackChan runtime, disconnect Nano USB
 * and use UART1. Commands and responses are newline-delimited at 115200 baud.
 */

#include <Arduino.h>

#define M_L_IN1 5
#define M_L_IN2 10
#define M_R_IN1 6
#define M_R_IN2 9

#define ENC_L_A 2
#define ENC_L_B 7
#define ENC_R_A 3
#define ENC_R_B 8

#define BATTERY_PIN A7

#define DEFAULT_TIMEOUT_MS 2000UL
#define SERIAL_BAUD 115200

volatile long encL = 0;
volatile long encR = 0;
volatile bool encLFired = false;
volatile bool encRFired = false;

bool motorsEnabled = false;
bool emergencyStop = false;
bool motionActive = false;
unsigned long lastMotionCommandMs = 0;
unsigned long commandTimeoutMs = DEFAULT_TIMEOUT_MS;

char commandBuffer[32];
byte commandLength = 0;

void encLIsr() {
  encLFired = true;
  if (digitalRead(ENC_L_A) == LOW) {
    encL += digitalRead(ENC_L_B) == LOW ? -1 : 1;
  } else {
    encL += digitalRead(ENC_L_B) == LOW ? 1 : -1;
  }
}

void encRIsr() {
  encRFired = true;
  if (digitalRead(ENC_R_A) == LOW) {
    encR += digitalRead(ENC_R_B) == LOW ? 1 : -1;
  } else {
    encR += digitalRead(ENC_R_B) == LOW ? -1 : 1;
  }
}

void setLeftMotor(int speed) {
  const int pwm = constrain(abs(speed), 0, 255);
  if (speed > 0) {
    digitalWrite(M_L_IN1, LOW);
    analogWrite(M_L_IN2, pwm);
  } else if (speed < 0) {
    analogWrite(M_L_IN1, pwm);
    digitalWrite(M_L_IN2, LOW);
  } else {
    digitalWrite(M_L_IN1, LOW);
    digitalWrite(M_L_IN2, LOW);
  }
}

void setRightMotor(int speed) {
  const int pwm = constrain(abs(speed), 0, 255);
  if (speed > 0) {
    digitalWrite(M_R_IN2, LOW);
    analogWrite(M_R_IN1, pwm);
  } else if (speed < 0) {
    analogWrite(M_R_IN2, pwm);
    digitalWrite(M_R_IN1, LOW);
  } else {
    digitalWrite(M_R_IN1, LOW);
    digitalWrite(M_R_IN2, LOW);
  }
}

void stopMotors() {
  setLeftMotor(0);
  setRightMotor(0);
  motionActive = false;
}

void respond(const char* message) {
  Serial.println(message);
}

void respondStatus() {
  long left;
  long right;
  noInterrupts();
  left = encL;
  right = encR;
  interrupts();

  const int batteryMv = (int)(analogRead(BATTERY_PIN) * 53.71f);
  char response[56];
  snprintf(response, sizeof(response), "ST:L%ld,R%ld,V%d,E%d,M%d", left, right,
           batteryMv, emergencyStop ? 1 : 0, motionActive ? 1 : 0);
  respond(response);
}

void markMotionCommand() {
  lastMotionCommandMs = millis();
  motionActive = true;
}

bool parseParameters(const char* command, char* operation, int& first, int& second) {
  const char* colon = strchr(command, ':');
  if (colon == nullptr) {
    strncpy(operation, command, 4);
    operation[4] = '\0';
    first = 0;
    second = 0;
    return true;
  }

  const size_t length = min((size_t)4, (size_t)(colon - command));
  memcpy(operation, command, length);
  operation[length] = '\0';
  first = 0;
  second = 0;
  return sscanf(colon + 1, "%d,%d", &first, &second) >= 1;
}

void parseCommand(const char* command) {
  char operation[5] = {0};
  int first = 0;
  int second = 0;
  if (!parseParameters(command, operation, first, second)) {
    respond("ERR:FORMAT");
    return;
  }

  if (strcmp(operation, "PING") == 0) {
    respond("OK:PONG:v0.9");
    return;
  }

  if (strcmp(operation, "EN") == 0) {
    motorsEnabled = first != 0;
    stopMotors();
    emergencyStop = false;
    respond(motorsEnabled ? "OK:EN:1" : "OK:EN:0");
    return;
  }

  if (strcmp(operation, "ST") == 0) {
    stopMotors();
    emergencyStop = true;
    respond("OK:ST");
    return;
  }

  if (strcmp(operation, "GS") == 0) {
    respondStatus();
    return;
  }

  if (strcmp(operation, "TO") == 0) {
    commandTimeoutMs = constrain((unsigned long)first, 0UL, 10000UL);
    char response[24];
    snprintf(response, sizeof(response), "OK:TO:%lu", commandTimeoutMs);
    respond(response);
    return;
  }

  if (strcmp(operation, "RS") == 0) {
    noInterrupts();
    encL = 0;
    encR = 0;
    encLFired = false;
    encRFired = false;
    interrupts();
    respond("OK:RS:0");
    return;
  }

  if (strcmp(operation, "DI") == 0) {
    char response[24];
    snprintf(response, sizeof(response), "DI:L%d,R%d", encLFired ? 1 : 0,
             encRFired ? 1 : 0);
    respond(response);
    return;
  }

  if (!motorsEnabled) {
    respond("ERR:DISABLED");
    return;
  }
  if (emergencyStop) {
    respond("ERR:ESTOP");
    return;
  }

  if (strcmp(operation, "FW") == 0) {
    const int speed = constrain(first, 0, 255);
    setLeftMotor(speed);
    setRightMotor(speed);
  } else if (strcmp(operation, "BW") == 0) {
    const int speed = constrain(first, 0, 255);
    setLeftMotor(-speed);
    setRightMotor(-speed);
  } else if (strcmp(operation, "TL") == 0) {
    const int speed = constrain(first, 0, 255);
    setLeftMotor(-speed);
    setRightMotor(speed);
  } else if (strcmp(operation, "TR") == 0) {
    const int speed = constrain(first, 0, 255);
    setLeftMotor(speed);
    setRightMotor(-speed);
  } else if (strcmp(operation, "VL") == 0) {
    setLeftMotor(constrain(first, -255, 255));
    setRightMotor(constrain(second, -255, 255));
  } else {
    respond("ERR:UNKNOWN");
    return;
  }

  markMotionCommand();
  respondStatus();
}

void readSerial() {
  while (Serial.available() > 0) {
    const char value = (char)Serial.read();
    if (value == '\n' || value == '\r') {
      if (commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        parseCommand(commandBuffer);
        commandLength = 0;
      }
    } else if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = value;
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  pinMode(M_L_IN1, OUTPUT);
  pinMode(M_L_IN2, OUTPUT);
  pinMode(M_R_IN1, OUTPUT);
  pinMode(M_R_IN2, OUTPUT);
  stopMotors();

  pinMode(ENC_L_A, INPUT_PULLUP);
  pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT_PULLUP);
  pinMode(ENC_R_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_L_A), encLIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_R_A), encRIsr, CHANGE);

  pinMode(BATTERY_PIN, INPUT);
  delay(100);
  respond("NanoDrive v0.9");
  respond("READY");
}

void loop() {
  readSerial();
  if (motionActive && commandTimeoutMs > 0 &&
      millis() - lastMotionCommandMs > commandTimeoutMs) {
    stopMotors();
    emergencyStop = true;
    respond("ERR:TIMEOUT");
  }
}
