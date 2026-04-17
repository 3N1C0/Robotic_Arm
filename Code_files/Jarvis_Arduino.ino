/*
 * 4DOF Robotic Arm — JARVIS Voice Command Controller
 * ====================================================
 * Board:   Arduino Uno
 * Library: Servo (built-in — no install needed)
 *
 * Direct Pin Wiring:
 *   PIN 6  → Base servo     signal (orange/yellow)
 *   PIN 9  → Shoulder servo signal
 *   PIN 10 → Elbow servo    signal
 *   PIN 11 → Wrist servo    signal
 *
 * Power:
 *   All servo VCC (red)   → External 6V supply positive
 *   All servo GND (brown) → External 6V supply negative
 *   External GND          → Arduino GND  (common ground — required)
 *   Arduino               → USB / 5V barrel jack
 *
 * Commands received over Serial at 9600 baud:
 *   WAVE      → Rise into greet pose, wave wrist 4 times
 *   SPIN      → Sweep base left → right → centre
 *   REST      → Return all joints to rest
 *   DANCE     → Full 6-beat choreographed routine
 *   SALUTE    → Military salute, hold, return
 *   STRETCH   → Full range sweep per joint then all together
 *   SHAKE     → Rapid wrist oscillation
 *   REACH     → Extend outward and retract
 *   POINT     → Point, sweep left/right, return
 *   CELEBRATE → Arm pumps, base spin, wrist shake
 */

#include <Servo.h>

// ─── Pin Assignments ───────────────────────────────────────────────────────────
#define PIN_BASE      6
#define PIN_SHOULDER  9
#define PIN_ELBOW     10
#define PIN_WRIST     11

// ─── Servo Objects ─────────────────────────────────────────────────────────────
Servo sBase;
Servo sShoulder;
Servo sElbow;
Servo sWrist;

// ─── Speed Control (ms per step — higher = slower) ────────────────────────────
const int XSLOW  = 25;
const int SLOW   = 18;
const int MEDIUM = 10;
const int FAST   =  5;
const int XFAST  =  2;

// ─── Pose Definitions (degrees) ───────────────────────────────────────────────
const int REST_BASE      = 90;
const int REST_SHOULDER  = 60;
const int REST_ELBOW     = 150;
const int REST_WRIST     = 90;

const int GREET_BASE     = 90;
const int GREET_SHOULDER = 130;
const int GREET_ELBOW    = 60;
const int GREET_WRIST    = 90;
const int WAVE_LEFT      = 50;
const int WAVE_RIGHT     = 130;

const int SALUTE_SHOULDER = 150;
const int SALUTE_ELBOW    = 30;
const int SALUTE_WRIST    = 60;

const int REACH_SHOULDER  = 90;
const int REACH_ELBOW     = 90;
const int REACH_WRIST     = 90;

const int POINT_SHOULDER  = 110;
const int POINT_ELBOW     = 170;
const int POINT_WRIST     = 90;

const int BASE_LEFT       = 30;
const int BASE_RIGHT      = 150;
const int BASE_CENTER     = 90;

// ─── Position Tracking ────────────────────────────────────────────────────────
int posBase = REST_BASE;
int posSh   = REST_SHOULDER;
int posEl   = REST_ELBOW;
int posWr   = REST_WRIST;

// ─── Core Helpers ─────────────────────────────────────────────────────────────

// Smooth single-servo move — updates position tracker
void moveTo(Servo &servo, int &pos, int to, int stepMs) {
  int step = (pos < to) ? 1 : -1;
  while (pos != to) {
    pos += step;
    servo.write(pos);
    delay(stepMs);
  }
}

// Smooth simultaneous 4-joint move — all joints arrive at the same time
void moveAll(int toBase, int toSh, int toEl, int toWr, int stepMs) {
  int dBase = toBase - posBase;
  int dSh   = toSh   - posSh;
  int dEl   = toEl   - posEl;
  int dWr   = toWr   - posWr;
  int steps = max(max(abs(dBase), abs(dSh)), max(abs(dEl), abs(dWr)));
  if (steps == 0) return;
  for (int i = 1; i <= steps; i++) {
    sBase.write    (posBase + (dBase * i / steps));
    sShoulder.write(posSh   + (dSh   * i / steps));
    sElbow.write   (posEl   + (dEl   * i / steps));
    sWrist.write   (posWr   + (dWr   * i / steps));
    delay(stepMs);
  }
  posBase = toBase; posSh = toSh; posEl = toEl; posWr = toWr;
}

// ─── REST ──────────────────────────────────────────────────────────────────────
void doRest() {
  Serial.println("Executing: REST");
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: REST");
}

// ─── WAVE ──────────────────────────────────────────────────────────────────────
void doWave() {
  Serial.println("Executing: WAVE");
  moveAll(GREET_BASE, GREET_SHOULDER, GREET_ELBOW, GREET_WRIST, SLOW);
  delay(300);
  for (int w = 0; w < 4; w++) {
    for (int p = GREET_WRIST; p >= WAVE_LEFT;   p--) { sWrist.write(p); delay(FAST); }
    for (int p = WAVE_LEFT;   p <= WAVE_RIGHT;  p++) { sWrist.write(p); delay(FAST); }
    for (int p = WAVE_RIGHT;  p >= GREET_WRIST; p--) { sWrist.write(p); delay(FAST); }
    delay(60);
  }
  posWr = GREET_WRIST;
  Serial.println("Done: WAVE");
}

// ─── SPIN ──────────────────────────────────────────────────────────────────────
void doSpin() {
  Serial.println("Executing: SPIN");
  moveTo(sBase, posBase, BASE_LEFT,   MEDIUM);
  moveTo(sBase, posBase, BASE_RIGHT,  MEDIUM);
  moveTo(sBase, posBase, BASE_CENTER, MEDIUM);
  Serial.println("Done: SPIN");
}

// ─── SALUTE ────────────────────────────────────────────────────────────────────
void doSalute() {
  Serial.println("Executing: SALUTE");
  moveAll(BASE_CENTER, REST_SHOULDER,    REST_ELBOW,    REST_WRIST,    SLOW);
  delay(200);
  moveAll(BASE_CENTER, SALUTE_SHOULDER,  REST_ELBOW,    REST_WRIST,    MEDIUM);
  delay(150);
  moveAll(BASE_CENTER, SALUTE_SHOULDER,  SALUTE_ELBOW,  SALUTE_WRIST,  MEDIUM);
  delay(900);
  moveAll(BASE_CENTER, GREET_SHOULDER,   GREET_ELBOW,   GREET_WRIST,   MEDIUM);
  delay(300);
  moveAll(REST_BASE,   REST_SHOULDER,    REST_ELBOW,    REST_WRIST,    SLOW);
  Serial.println("Done: SALUTE");
}

// ─── STRETCH ───────────────────────────────────────────────────────────────────
void doStretch() {
  Serial.println("Executing: STRETCH");
  moveTo(sBase,     posBase, BASE_LEFT,       SLOW);
  moveTo(sBase,     posBase, BASE_RIGHT,      SLOW);
  moveTo(sBase,     posBase, BASE_CENTER,     SLOW);
  delay(200);
  moveTo(sShoulder, posSh,   30,              SLOW);
  moveTo(sShoulder, posSh,   150,             SLOW);
  moveTo(sShoulder, posSh,   REST_SHOULDER,   SLOW);
  delay(200);
  moveTo(sElbow,    posEl,   30,              SLOW);
  moveTo(sElbow,    posEl,   170,             SLOW);
  moveTo(sElbow,    posEl,   REST_ELBOW,      SLOW);
  delay(200);
  moveTo(sWrist,    posWr,   30,              SLOW);
  moveTo(sWrist,    posWr,   150,             SLOW);
  moveTo(sWrist,    posWr,   REST_WRIST,      SLOW);
  delay(200);
  moveAll(BASE_LEFT,   150,  30,  150, MEDIUM);
  moveAll(BASE_RIGHT,   30, 170,   30, MEDIUM);
  moveAll(BASE_CENTER, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: STRETCH");
}

// ─── SHAKE ─────────────────────────────────────────────────────────────────────
void doShake() {
  Serial.println("Executing: SHAKE");
  moveAll(BASE_CENTER, 110, 80, 90, MEDIUM);
  delay(200);
  for (int s = 0; s < 8; s++) {
    for (int p = 90;  p >= 40;  p -= 3) { sWrist.write(p); delay(XFAST); }
    for (int p = 40;  p <= 140; p += 3) { sWrist.write(p); delay(XFAST); }
    for (int p = 140; p >= 90;  p -= 3) { sWrist.write(p); delay(XFAST); }
  }
  posWr = 90;
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: SHAKE");
}

// ─── REACH ─────────────────────────────────────────────────────────────────────
void doReach() {
  Serial.println("Executing: REACH");
  moveAll(BASE_CENTER, 100, REST_ELBOW, REST_WRIST, MEDIUM);
  delay(200);
  moveAll(BASE_CENTER, REACH_SHOULDER, REACH_ELBOW, REACH_WRIST, SLOW);
  delay(700);
  moveAll(BASE_CENTER, 100, REST_ELBOW, REST_WRIST, MEDIUM);
  delay(200);
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: REACH");
}

// ─── POINT ─────────────────────────────────────────────────────────────────────
void doPoint() {
  Serial.println("Executing: POINT");
  moveAll(BASE_CENTER, POINT_SHOULDER, 90, POINT_WRIST, MEDIUM);
  delay(200);
  moveAll(BASE_CENTER, POINT_SHOULDER, POINT_ELBOW, POINT_WRIST, SLOW);
  delay(1000);
  moveTo(sBase, posBase, BASE_LEFT,   MEDIUM);
  moveTo(sBase, posBase, BASE_RIGHT,  MEDIUM);
  moveTo(sBase, posBase, BASE_CENTER, MEDIUM);
  delay(400);
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: POINT");
}

// ─── CELEBRATE ─────────────────────────────────────────────────────────────────
void doCelebrate() {
  Serial.println("Executing: CELEBRATE");
  moveAll(BASE_CENTER, 140, 50, 90, MEDIUM);
  delay(200);
  for (int pump = 0; pump < 3; pump++) {
    for (int i = 0; i < 30; i++) {
      sShoulder.write(140 - i * 2);
      sWrist.write(90 + i);
      delay(FAST);
    }
    for (int i = 0; i < 30; i++) {
      sShoulder.write(80 + i * 2);
      sWrist.write(120 - i);
      delay(FAST);
    }
    delay(80);
  }
  posSh = 140; posWr = 90;
  moveTo(sBase, posBase, BASE_LEFT,   FAST);
  moveTo(sBase, posBase, BASE_RIGHT,  FAST);
  moveTo(sBase, posBase, BASE_CENTER, FAST);
  for (int s = 0; s < 6; s++) {
    for (int p = 90;  p >= 45;  p -= 3) { sWrist.write(p); delay(XFAST); }
    for (int p = 45;  p <= 135; p += 3) { sWrist.write(p); delay(XFAST); }
    for (int p = 135; p >= 90;  p -= 3) { sWrist.write(p); delay(XFAST); }
  }
  posWr = 90;
  delay(300);
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: CELEBRATE");
}

// ─── DANCE ─────────────────────────────────────────────────────────────────────
void doDance() {
  Serial.println("Executing: DANCE");

  // Beat 1 — rise and open
  moveAll(BASE_CENTER, 140, 50, 90, MEDIUM);
  delay(200);

  // Beat 2 — base sways with elbow pulse, 3 reps
  for (int i = 0; i < 3; i++) {
    moveTo(sBase, posBase, BASE_LEFT,  MEDIUM);
    sElbow.write(80); delay(150);
    sElbow.write(50); delay(150);
    moveTo(sBase, posBase, BASE_RIGHT, MEDIUM);
    sElbow.write(80); delay(150);
    sElbow.write(50); delay(150);
  }
  posEl = 50;
  moveTo(sBase, posBase, BASE_CENTER, MEDIUM);

  // Beat 3 — shoulder and elbow linked arc, 2 reps
  for (int rep = 0; rep < 2; rep++) {
    for (int p = 140; p >= 60; p -= 2) {
      sShoulder.write(p);
      sElbow.write(map(p, 60, 140, 130, 40));
      delay(MEDIUM);
    }
    for (int p = 60; p <= 140; p += 2) {
      sShoulder.write(p);
      sElbow.write(map(p, 60, 140, 130, 40));
      delay(MEDIUM);
    }
  }
  posSh = 140; posEl = 40;

  // Beat 4 — wrist full circles, 3 reps
  for (int circle = 0; circle < 3; circle++) {
    for (int p = 90;  p <= 150; p += 2) { sWrist.write(p); delay(FAST); }
    for (int p = 150; p >= 30;  p -= 2) { sWrist.write(p); delay(FAST); }
    for (int p = 30;  p <= 90;  p += 2) { sWrist.write(p); delay(FAST); }
  }
  posWr = 90;

  // Beat 5 — double base spin in elevated pose
  moveTo(sBase, posBase, BASE_LEFT,   FAST);
  moveTo(sBase, posBase, BASE_RIGHT,  FAST);
  moveTo(sBase, posBase, BASE_LEFT,   FAST);
  moveTo(sBase, posBase, BASE_CENTER, FAST);

  // Beat 6 — all joints coordinated finale, 2 reps
  for (int f = 0; f < 2; f++) {
    moveAll(BASE_LEFT,   60,  130,  50, FAST);
    moveAll(BASE_RIGHT, 140,   40, 130, FAST);
  }
  moveAll(BASE_CENTER, 140, 50, 90, MEDIUM);

  // Finale — rapid wrist shake then return to rest
  for (int s = 0; s < 5; s++) {
    for (int p = 90;  p >= 40;  p -= 4) { sWrist.write(p); delay(XFAST); }
    for (int p = 40;  p <= 140; p += 4) { sWrist.write(p); delay(XFAST); }
    for (int p = 140; p >= 90;  p -= 4) { sWrist.write(p); delay(XFAST); }
  }
  posWr = 90;
  delay(300);
  moveAll(REST_BASE, REST_SHOULDER, REST_ELBOW, REST_WRIST, SLOW);
  Serial.println("Done: DANCE");
}

// ─── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  delay(500);

  sBase.attach    (PIN_BASE,     500, 2400);
  sShoulder.attach(PIN_SHOULDER, 500, 2400);
  sElbow.attach   (PIN_ELBOW,    500, 2400);
  sWrist.attach   (PIN_WRIST,    500, 2400);

  sBase.write    (REST_BASE);
  sShoulder.write(REST_SHOULDER);
  sElbow.write   (REST_ELBOW);
  sWrist.write   (REST_WRIST);

  delay(1000);
  Serial.println("READY");
}

// ─── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if      (cmd == "WAVE")      doWave();
    else if (cmd == "SPIN")      doSpin();
    else if (cmd == "REST")      doRest();
    else if (cmd == "DANCE")     doDance();
    else if (cmd == "SALUTE")    doSalute();
    else if (cmd == "STRETCH")   doStretch();
    else if (cmd == "SHAKE")     doShake();
    else if (cmd == "REACH")     doReach();
    else if (cmd == "POINT")     doPoint();
    else if (cmd == "CELEBRATE") doCelebrate();
    else {
      Serial.print("Unknown: ");
      Serial.println(cmd);
    }
  }
}
