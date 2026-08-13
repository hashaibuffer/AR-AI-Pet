/*
 * Isolated A4950 hardware-baseline test.
 * Source: firmware/arduino-pedestal/sketches/oled-display/R2miniQ_OLED.ino
 *
 * This sketch intentionally remains separate from nanodrive_firmware.ino.
 * Serial protocol: 115200 8N1; A=forward, E=backward, Z=stop.
 */
#include <Arduino.h>

#define AIN1 6
#define AIN2 9
#define BIN1 5
#define BIN2 10
#define ENCODER_R 2
#define DIRECTION_R 7
#define ENCODER_L 3
#define DIRECTION_L 8
#define BATTERY_PIN A7

#define SERIAL_BAUD 115200
#define CONTROL_PERIOD_MS 20UL
#define COMMAND_TIMEOUT_MS 2000UL

volatile long velocity_l = 0;
volatile long velocity_r = 0;
long velocity_left = 0;
long velocity_right = 0;

float velocity_kp = -0.5f;
float velocity_ki = -0.5f;
float target_a = 0.0f;
float target_b = 0.0f;
int velocity = 0;
int turn = 0;
bool safety_stop = true;
bool timeout_reported = false;
unsigned long last_command_ms = 0;
unsigned long last_control_ms = 0;

void readEncoderL() {
  if (digitalRead(ENCODER_L) == LOW) {
    if (digitalRead(DIRECTION_L) == LOW) velocity_l--;
    else velocity_l++;
  } else {
    if (digitalRead(DIRECTION_L) == LOW) velocity_l++;
    else velocity_l--;
  }
}

void readEncoderR() {
  if (digitalRead(ENCODER_R) == LOW) {
    if (digitalRead(DIRECTION_R) == LOW) velocity_r--;
    else velocity_r++;
  } else {
    if (digitalRead(DIRECTION_R) == LOW) velocity_r++;
    else velocity_r--;
  }
}

void setPwm(int motor_a, int motor_b) {
  // Direction/brake truth table is copied from the vendor A4950 example.
  if (motor_a > 0) {
    analogWrite(AIN2, motor_a);
    digitalWrite(AIN1, LOW);
  } else if (motor_a < 0) {
    digitalWrite(AIN2, LOW);
    analogWrite(AIN1, -motor_a);
  } else {
    digitalWrite(AIN1, HIGH);
    digitalWrite(AIN2, HIGH);
  }

  if (motor_b > 0) {
    analogWrite(BIN1, motor_b);
    digitalWrite(BIN2, LOW);
  } else if (motor_b < 0) {
    digitalWrite(BIN1, LOW);
    analogWrite(BIN2, -motor_b);
  } else {
    digitalWrite(BIN1, HIGH);
    digitalWrite(BIN2, HIGH);
  }
}

void kinematicAnalysis(float requested_velocity, float requested_turn) {
  target_a = -requested_velocity + requested_turn;
  target_b = -requested_velocity - requested_turn;
}

int incrementalPiA(int encoder, int target) {
  static float pwm = 0.0f;
  static float last_bias = 0.0f;
  const float bias = encoder - target; // vendor sign convention
  pwm += velocity_kp * (bias - last_bias) + velocity_ki * bias;
  if (pwm > 255.0f) pwm = 255.0f;
  if (pwm < -255.0f) pwm = -255.0f;
  last_bias = bias;
  return (int)pwm;
}

int incrementalPiB(int encoder, int target) {
  static float pwm = 0.0f;
  static float last_bias = 0.0f;
  const float bias = encoder - target; // vendor sign convention
  pwm += velocity_kp * (bias - last_bias) + velocity_ki * bias;
  if (pwm > 255.0f) pwm = 255.0f;
  if (pwm < -255.0f) pwm = -255.0f;
  last_bias = bias;
  return (int)pwm;
}

void controlTick() {
  if (safety_stop) {
    setPwm(0, 0);
    return;
  }

  noInterrupts();
  velocity_left = velocity_l;
  velocity_l = 0;
  velocity_right = velocity_r;
  velocity_r = 0;
  interrupts();

  kinematicAnalysis(velocity, turn);
  setPwm(incrementalPiA((int)velocity_left, (int)target_a),
         incrementalPiB((int)velocity_right, (int)target_b));
}

void reply(const char* text) { Serial.println(text); }

void applyCommand(char command) {
  last_command_ms = millis();
  timeout_reported = false;
  switch (command) {
    case 'A':
      velocity = 30;
      turn = 0;
      safety_stop = false;
      reply("OK:A");
      break;
    case 'E':
      velocity = -30;
      turn = 0;
      safety_stop = false;
      reply("OK:E");
      break;
    // Remaining direction characters are copied from the matching vendor
    // OLED/Bluetooth sketch.  The A4950 pin map and PI loop remain unchanged.
    case 'H':  // front-left
      velocity = 15;
      turn = -5;
      safety_stop = false;
      reply("OK:H");
      break;
    case 'B':  // front-right
      velocity = 15;
      turn = 5;
      safety_stop = false;
      reply("OK:B");
      break;
    case 'G':  // rotate-left
      velocity = 0;
      turn = -10;
      safety_stop = false;
      reply("OK:G");
      break;
    case 'C':  // rotate-right
      velocity = 0;
      turn = 10;
      safety_stop = false;
      reply("OK:C");
      break;
    case 'F':  // rear-left
      velocity = -15;
      turn = 5;
      safety_stop = false;
      reply("OK:F");
      break;
    case 'D':  // rear-right
      velocity = -15;
      turn = -5;
      safety_stop = false;
      reply("OK:D");
      break;
    case 'Z':
      velocity = 0;
      turn = 0;
      safety_stop = true;
      setPwm(0, 0);
      reply("OK:Z");
      break;
    case '\n':
    case '\r':
      break;
    default:
      reply("ERR:UNKNOWN");
      break;
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  setPwm(0, 0);

  pinMode(ENCODER_R, INPUT_PULLUP);
  pinMode(DIRECTION_R, INPUT_PULLUP);
  pinMode(ENCODER_L, INPUT_PULLUP);
  pinMode(DIRECTION_L, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_R), readEncoderR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_L), readEncoderL, CHANGE);
  pinMode(BATTERY_PIN, INPUT);

  last_command_ms = millis();
  last_control_ms = millis();
  reply("NanoDrive A4950 vendor baseline");
  reply("READY:115200");
}

void loop() {
  while (Serial.available() > 0) applyCommand((char)Serial.read());

  const unsigned long now = millis();
  if (!safety_stop && now - last_command_ms >= COMMAND_TIMEOUT_MS) {
    velocity = 0;
    turn = 0;
    safety_stop = true;
    setPwm(0, 0);
    if (!timeout_reported) {
      reply("ERR:TIMEOUT");
      timeout_reported = true;
    }
  }

  if (now - last_control_ms >= CONTROL_PERIOD_MS) {
    last_control_ms = now;
    controlTick();
  }
}
