#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <DHT.h>

#include <TinyGPS++.h>
#include <HardwareSerial.h>

#include <WiFi.h>
#include <WebServer.h>

#include <ESP32Servo.h>


// ============================================================
// WIFI
// ============================================================

const char* ssid = "phone1";
const char* password = "12345678";
volatile bool wifiDisconnected = false;
unsigned long wifiReconnectTime = 0;
WebServer server(80);


// ============================================================
// OLED
// ============================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);


// ============================================================
// MOTORS
// ============================================================

#define IN1 26
#define IN2 27

#define IN3 14
#define IN4 12


// ============================================================
// DHT11
// ============================================================

#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(
  DHTPIN,
  DHTTYPE
);


// ============================================================
// SOIL
// ============================================================

#define SOIL_PIN 34

const int SOIL_THRESHOLD = 3000;


// ============================================================
// PUMP
// ============================================================

#define RELAY_PIN 23

bool pumpOn = false;


// ============================================================
// ULTRASONIC
// ============================================================

#define TRIG 32
#define ECHO 33

float distance = 0;

const float OBSTACLE_DISTANCE = 20.0;

bool obstacleDetected = false;


// ============================================================
// LINE SENSORS
// ============================================================

#define LS 18
#define CS 19
#define RS 5


// ============================================================
// GPS
// ============================================================

TinyGPSPlus gps;

HardwareSerial gpsSerial(2);

#define GPS_RX 16
#define GPS_TX 17

#define GPS_BAUD 9600


// ============================================================
// PAN TILT
// ============================================================

#define PAN_PIN 13
#define TILT_PIN 25

Servo panServo;
Servo tiltServo;


const int PAN_MIN = 30;
const int PAN_MAX = 150;

const int TILT_MIN = 60;
const int TILT_MAX = 120;


const int SERVO_STEP = 10;


int panAngle = 90;
int tiltAngle = 90;


int targetPan = 90;
int targetTilt = 90;


unsigned long lastServoMove = 0;

const unsigned long SERVO_INTERVAL = 20;


// ============================================================
// CAMERA SCAN
// ============================================================

bool scanMode = false;

int scanDirection = 1;


unsigned long lastScanMove = 0;

const unsigned long SCAN_INTERVAL = 60;

const int SCAN_STEP = 2;


// ============================================================
// DRIVE MODE
// ============================================================

bool manualMode = false;


// ============================================================
// SENSOR CACHE
// ============================================================

unsigned long lastSensorUpdate = 0;

const unsigned long SENSOR_INTERVAL = 100;


float cachedTemperature = 0.0;

float cachedHumidity = 0.0;

int cachedSoil = 0;


unsigned long lastDHTRead = 0;

const unsigned long DHT_INTERVAL = 2000;


// ============================================================
// OLED UPDATE
// ============================================================

unsigned long lastOLEDUpdate = 0;

const unsigned long OLED_INTERVAL = 1000;


// ============================================================
// MOTORS
// ============================================================

void forward() {

  if (obstacleDetected) {

    stopMotor();

    return;

  }


  digitalWrite(
    IN1,
    HIGH
  );

  digitalWrite(
    IN2,
    LOW
  );


  digitalWrite(
    IN3,
    HIGH
  );

  digitalWrite(
    IN4,
    LOW
  );

}


void left() {

  if (obstacleDetected) {

    stopMotor();

    return;

  }


  digitalWrite(
    IN1,
    LOW
  );

  digitalWrite(
    IN2,
    HIGH
  );


  digitalWrite(
    IN3,
    HIGH
  );

  digitalWrite(
    IN4,
    LOW
  );

}


void right() {

  if (obstacleDetected) {

    stopMotor();

    return;

  }


  digitalWrite(
    IN1,
    HIGH
  );

  digitalWrite(
    IN2,
    LOW
  );


  digitalWrite(
    IN3,
    LOW
  );

  digitalWrite(
    IN4,
    HIGH
  );

}


void stopMotor() {

  digitalWrite(
    IN1,
    LOW
  );

  digitalWrite(
    IN2,
    LOW
  );


  digitalWrite(
    IN3,
    LOW
  );

  digitalWrite(
    IN4,
    LOW
  );

}


// ============================================================
// PUMP
// ============================================================

void pumpON() {

  digitalWrite(
    RELAY_PIN,
    LOW
  );

  pumpOn = true;

}


void pumpOFF() {

  digitalWrite(
    RELAY_PIN,
    HIGH
  );

  pumpOn = false;

}
// ============================================================
// PUMP WEB CONTROL
// ============================================================

void handlePumpOn() {

  pumpON();

  server.send(
    200,
    "text/plain",
    "PUMP ON"
  );

}


void handlePumpOff() {

  pumpOFF();

  server.send(
    200,
    "text/plain",
    "PUMP OFF"
  );

}


// ============================================================
// ULTRASONIC
// ============================================================

void updateDistance() {

  digitalWrite(
    TRIG,
    LOW
  );

  delayMicroseconds(2);


  digitalWrite(
    TRIG,
    HIGH
  );

  delayMicroseconds(10);


  digitalWrite(
    TRIG,
    LOW
  );


  long duration = pulseIn(
    ECHO,
    HIGH,
    10000
  );


  if (duration == 0) {

    distance = 0;

    obstacleDetected = false;

  }

  else {

    distance =
      duration * 0.0343 / 2.0;


    if (
      distance > 0 &&
      distance < OBSTACLE_DISTANCE
    ) {

      obstacleDetected = true;

      stopMotor();

    }

    else {

      obstacleDetected = false;

    }

  }

}


// ============================================================
// SENSOR CACHE
// ============================================================

void updateSensorCache() {

  unsigned long now =
    millis();


  if (
    now - lastDHTRead >=
    DHT_INTERVAL
  ) {

    lastDHTRead = now;


    float temp =
      dht.readTemperature();


    float hum =
      dht.readHumidity();


    if (!isnan(temp)) {

      cachedTemperature =
        temp;

    }


    if (!isnan(hum)) {

      cachedHumidity =
        hum;

    }

  }


  cachedSoil =
    analogRead(
      SOIL_PIN
    );


  updateDistance();

}


// ============================================================
// SERVO
// ============================================================

void updateServos() {

  unsigned long now =
    millis();


  // ----------------------------------------------------------
  // SCAN
  // ----------------------------------------------------------

  if (
    scanMode &&
    now - lastScanMove >=
    SCAN_INTERVAL
  ) {

    lastScanMove = now;


    targetPan +=
      scanDirection *
      SCAN_STEP;


    if (
      targetPan >=
      PAN_MAX
    ) {

      targetPan =
        PAN_MAX;

      scanDirection =
        -1;

    }


    if (
      targetPan <=
      PAN_MIN
    ) {

      targetPan =
        PAN_MIN;

      scanDirection =
        1;

    }

  }


  // ----------------------------------------------------------
  // SMOOTH MOVEMENT
  // ----------------------------------------------------------

  if (
    now - lastServoMove <
    SERVO_INTERVAL
  ) {

    return;

  }


  lastServoMove =
    now;


  if (
    panAngle <
    targetPan
  ) {

    panAngle++;

  }

  else if (
    panAngle >
    targetPan
  ) {

    panAngle--;

  }


  if (
    tiltAngle <
    targetTilt
  ) {

    tiltAngle++;

  }

  else if (
    tiltAngle >
    targetTilt
  ) {

    tiltAngle--;

  }


  panServo.write(
    panAngle
  );

  tiltServo.write(
    tiltAngle
  );

}


// ============================================================
// GPS
// ============================================================

void updateGPS() {

  while (
    gpsSerial.available()
  ) {

    gps.encode(
      gpsSerial.read()
    );

  }

}


// ============================================================
// AUTONOMOUS NAVIGATION
// ============================================================

void autonomousNavigation() {

  if (obstacleDetected) {

    stopMotor();

    return;

  }


  int L =
    digitalRead(LS);


  int C =
    digitalRead(CS);


  int R =
    digitalRead(RS);


  // Center

  if (
    L == 0 &&
    C == 1 &&
    R == 0
  ) {

    forward();

  }


  // Left

  else if (
    L == 1 &&
    C == 0
  ) {

    left();

  }


  // Right

  else if (
    R == 1 &&
    C == 0
  ) {

    right();

  }


  else {

    stopMotor();

  }

}


// ============================================================
// OLED
// ============================================================

void updateOLED() {

  unsigned long now =
    millis();


  if (
    now - lastOLEDUpdate <
    OLED_INTERVAL
  ) {

    return;

  }


  lastOLEDUpdate =
    now;


  display.clearDisplay();


  display.setTextColor(
    WHITE
  );


  display.setTextSize(1);


  display.setCursor(
    0,
    0
  );

  display.print(
    "AGRI-VISE"
  );


  display.setCursor(
    75,
    0
  );


  if (
    WiFi.status() ==
    WL_CONNECTED
  ) {

    display.print(
      "WiFi"
    );

  }

  else {

    display.print(
      "OFF"
    );

  }


  // Temperature

  display.setCursor(
    0,
    14
  );

  display.print(
    "T:"
  );

  display.print(
    cachedTemperature,
    1
  );

  display.print(
    "C"
  );


  // Humidity

  display.setCursor(
    65,
    14
  );

  display.print(
    "H:"
  );

  display.print(
    cachedHumidity,
    0
  );

  display.print(
    "%"
  );


  // Soil

  display.setCursor(
    0,
    28
  );

  display.print(
    "Soil:"
  );

  display.print(
    cachedSoil
  );


  // Distance

  display.setCursor(
    65,
    28
  );

  display.print(
    "D:"
  );

  display.print(
    distance,
    0
  );

  display.print(
    "cm"
  );


  // Mode

  display.setCursor(
    0,
    42
  );

  display.print(
    "Mode:"
  );


  if (manualMode) {

    display.print(
      "MANUAL"
    );

  }

  else {

    display.print(
      "AUTO"
    );

  }


  // GPS

  display.setCursor(
    70,
    42
  );


  if (
    gps.location.isValid()
  ) {

    display.print(
      "GPS OK"
    );

  }

  else {

    display.print(
      "GPS --"
    );

  }


  // Pump

  display.setCursor(
    0,
    56
  );

  display.print(
    "Pump:"
  );


  if (pumpOn) {

    display.print(
      "ON"
    );

  }

  else {

    display.print(
      "OFF"
    );

  }


  display.display();

}


// ============================================================
// DATA
// ============================================================

void handleData() {


  String modeState;


  if (manualMode) {

    modeState =
      "MANUAL";

  }

  else {

    modeState =
      "AUTO";

  }


  String pumpState;


  if (pumpOn) {

    pumpState =
      "ON";

  }

  else {

    pumpState =
      "OFF";

  }


  String json = "{";


  json +=
    "\"temperature\":";

  json +=
    String(
      cachedTemperature,
      1
    );

  json += ",";


  json +=
    "\"humidity\":";

  json +=
    String(
      cachedHumidity,
      1
    );

  json += ",";


  json +=
    "\"soil\":";

  json +=
    String(
      cachedSoil
    );

  json += ",";


  json +=
    "\"distance\":";

  json +=
    String(
      distance,
      1
    );

  json += ",";


  json +=
    "\"pump\":\"";

  json +=
    pumpState;

  json += "\",";


  json +=
    "\"mode\":\"";

  json +=
    modeState;

  json += "\",";


  json +=
    "\"pan\":";

  json +=
    String(
      panAngle
    );

  json += ",";


  json +=
    "\"tilt\":";

  json +=
    String(
      tiltAngle
    );


  // GPS

  if (
    gps.location.isValid()
  ) {

    json +=
      ",\"lat\":";

    json +=
      String(
        gps.location.lat(),
        6
      );


    json +=
      ",\"lon\":";

    json +=
      String(
        gps.location.lng(),
        6
      );

  }


  json += "}";


  server.send(
    200,
    "application/json",
    json
  );

}


// ============================================================
// ROOT
// ============================================================

void handleRoot() {

  server.send(
    200,
    "text/plain",
    "AGRI-VISE ESP32 Web Server Working"
  );

}


// ============================================================
// FORWARD
// ============================================================

void handleForward() {

  manualMode = true;


  if (obstacleDetected) {

    stopMotor();


    server.send(
      200,
      "text/plain",
      "BLOCKED - OBSTACLE"
    );


    return;

  }


  forward();


  server.send(
    200,
    "text/plain",
    "FORWARD"
  );

}


// ============================================================
// LEFT
// ============================================================

void handleLeft() {

  manualMode = true;


  if (obstacleDetected) {

    stopMotor();


    server.send(
      200,
      "text/plain",
      "BLOCKED - OBSTACLE"
    );


    return;

  }


  left();


  server.send(
    200,
    "text/plain",
    "LEFT"
  );

}


// ============================================================
// RIGHT
// ============================================================

void handleRight() {

  manualMode = true;


  if (obstacleDetected) {

    stopMotor();


    server.send(
      200,
      "text/plain",
      "BLOCKED - OBSTACLE"
    );


    return;

  }


  right();


  server.send(
    200,
    "text/plain",
    "RIGHT"
  );

}


// ============================================================
// STOP
// ============================================================

void handleStop() {

  stopMotor();


  server.send(
    200,
    "text/plain",
    "STOP"
  );

}


// ============================================================
// AUTO
// ============================================================

void handleAuto() {

  manualMode = false;

  stopMotor();


  server.send(
    200,
    "text/plain",
    "AUTO MODE"
  );

}


// ============================================================
// MANUAL
// ============================================================

void handleManual() {

  manualMode = true;

  stopMotor();


  server.send(
    200,
    "text/plain",
    "MANUAL MODE"
  );

}


// ============================================================
// PAN LEFT
// ============================================================

void handlePanLeft() {

  scanMode = false;


  targetPan =
    constrain(
      targetPan - SERVO_STEP,
      PAN_MIN,
      PAN_MAX
    );


  server.send(
    200,
    "text/plain",
    "PAN LEFT"
  );

}


// ============================================================
// PAN RIGHT
// ============================================================

void handlePanRight() {

  scanMode = false;


  targetPan =
    constrain(
      targetPan + SERVO_STEP,
      PAN_MIN,
      PAN_MAX
    );


  server.send(
    200,
    "text/plain",
    "PAN RIGHT"
  );

}


// ============================================================
// TILT UP
// ============================================================

void handleTiltUp() {

  scanMode = false;


  targetTilt =
    constrain(
      targetTilt + SERVO_STEP,
      TILT_MIN,
      TILT_MAX
    );


  server.send(
    200,
    "text/plain",
    "TILT UP"
  );

}


// ============================================================
// TILT DOWN
// ============================================================

void handleTiltDown() {

  scanMode = false;


  targetTilt =
    constrain(
      targetTilt - SERVO_STEP,
      TILT_MIN,
      TILT_MAX
    );


  server.send(
    200,
    "text/plain",
    "TILT DOWN"
  );

}


// ============================================================
// CENTER
// ============================================================

void handleCenter() {

  scanMode = false;


  targetPan = 90;

  targetTilt = 90;


  server.send(
    200,
    "text/plain",
    "CENTER"
  );

}


// ============================================================
// SCAN
// ============================================================

void handleScan() {

  scanMode =
    !scanMode;


  if (scanMode) {

    scanDirection = 1;

    lastScanMove =
      millis();


    server.send(
      200,
      "text/plain",
      "SCAN ON"
    );

  }

  else {

    server.send(
      200,
      "text/plain",
      "SCAN OFF"
    );

  }

}


// ============================================================
// WIFI
// ============================================================

void connectWiFi() {

  Serial.println();

  Serial.println(
    "Connecting to WiFi..."
  );


  WiFi.mode(
    WIFI_STA
  );

  WiFi.setAutoReconnect(true);
  WiFi.begin(
    ssid,
    password
  );


  unsigned long startTime =
    millis();


  while (

    WiFi.status() !=
    WL_CONNECTED

    &&

    millis() - startTime <
    20000

  ) {

    delay(500);

    Serial.print(
      "."
    );

  }


  Serial.println();


  if (
    WiFi.status() ==
    WL_CONNECTED
  ) {

    Serial.println(
      "WiFi connected"
    );


    Serial.print(
      "ESP32 IP: "
    );


    Serial.println(
      WiFi.localIP()
    );

  }

  else {

    Serial.println(
      "WiFi connection failed"
    );

  }

}

void WiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {

  if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {

    Serial.print("WiFi disconnected. Reason: ");
    Serial.println(info.wifi_sta_disconnected.reason);

    wifiDisconnected = true;
    wifiReconnectTime = millis() + 20000;
  }

  else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {

    Serial.println("WiFi reconnected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    wifiDisconnected = false;
  }
}
// ============================================================
// SETUP
// ============================================================

void setup() {

  Serial.begin(
    115200
  );


  delay(500);


  // ----------------------------------------------------------
  // MOTORS
  // ----------------------------------------------------------

  pinMode(
    IN1,
    OUTPUT
  );

  pinMode(
    IN2,
    OUTPUT
  );

  pinMode(
    IN3,
    OUTPUT
  );

  pinMode(
    IN4,
    OUTPUT
  );


  stopMotor();


  // ----------------------------------------------------------
  // LINE SENSORS
  // ----------------------------------------------------------

  pinMode(
    LS,
    INPUT
  );

  pinMode(
    CS,
    INPUT
  );

  pinMode(
    RS,
    INPUT
  );


  // ----------------------------------------------------------
  // ULTRASONIC
  // ----------------------------------------------------------

  pinMode(
    TRIG,
    OUTPUT
  );

  pinMode(
    ECHO,
    INPUT
  );


  digitalWrite(
    TRIG,
    LOW
  );


  // ----------------------------------------------------------
  // SOIL
  // ----------------------------------------------------------

  pinMode(
    SOIL_PIN,
    INPUT
  );


  // ----------------------------------------------------------
  // RELAY
  // ----------------------------------------------------------

  pinMode(
    RELAY_PIN,
    OUTPUT
  );


  pumpOFF();


  // ----------------------------------------------------------
  // DHT
  // ----------------------------------------------------------

  dht.begin();


  // ----------------------------------------------------------
  // OLED I2C
  // ----------------------------------------------------------

  Wire.begin(
    21,
    22
  );


  if (
    !display.begin(
      SSD1306_SWITCHCAPVCC,
      0x3C
    )
  ) {

    Serial.println(
      "OLED initialization failed"
    );

  }

  else {

    display.clearDisplay();

    display.setTextColor(
      WHITE
    );

    display.setTextSize(2);

    display.setCursor(
      10,
      20
    );

    display.println(
      "ROVER"
    );

    display.display();

    delay(1000);

  }


  // ----------------------------------------------------------
  // GPS
  // ----------------------------------------------------------

  gpsSerial.begin(

    GPS_BAUD,

    SERIAL_8N1,

    GPS_RX,

    GPS_TX

  );


  Serial.println(
    "GPS serial started"
  );


  // ----------------------------------------------------------
  // SERVOS
  // ----------------------------------------------------------

  panServo.setPeriodHertz(
    50
  );


  tiltServo.setPeriodHertz(
    50
  );


  panServo.attach(
    PAN_PIN,
    500,
    2400
  );


  tiltServo.attach(
    TILT_PIN,
    500,
    2400
  );


  panServo.write(
    panAngle
  );


  tiltServo.write(
    tiltAngle
  );


  // ----------------------------------------------------------
  // WIFI
  // ----------------------------------------------------------
  WiFi.onEvent(WiFiEvent);

  WiFi.setAutoReconnect(false);
  connectWiFi();
  // ============================================================


  // ----------------------------------------------------------
  // ROUTES
  // ----------------------------------------------------------

  server.on(
    "/",
    handleRoot
  );


  server.on(
    "/data",
    handleData
  );


  server.on(
    "/forward",
    handleForward
  );


  server.on(
    "/left",
    handleLeft
  );


  server.on(
    "/right",
    handleRight
  );


  server.on(
    "/stop",
    handleStop
  );


  server.on(
    "/auto",
    handleAuto
  );


  server.on(
    "/manual",
    handleManual
  );


  server.on(
    "/panLeft",
    handlePanLeft
  );


  server.on(
    "/panRight",
    handlePanRight
  );


  server.on(
    "/tiltUp",
    handleTiltUp
  );


  server.on(
    "/tiltDown",
    handleTiltDown
  );


  server.on(
    "/center",
    handleCenter
  );


  server.on(
    "/scan",
    handleScan
  );
  server.on(
  "/pumpOn",
  handlePumpOn
);


  server.on(
  "/pumpOff",
  handlePumpOff
);

  // ----------------------------------------------------------
  // START SERVER
  // ----------------------------------------------------------

  server.begin();


  Serial.println(
    "HTTP server started"
  );


  if (
    WiFi.status() ==
    WL_CONNECTED
  ) {

    Serial.print(
      "Open: http://"
    );


    Serial.print(
      WiFi.localIP()
    );


    Serial.println(
      "/"
    );

  }


  // ----------------------------------------------------------
  // INITIAL SENSORS
  // ----------------------------------------------------------

  cachedSoil =
    analogRead(
      SOIL_PIN
    );


  updateDistance();


  float initialTemp =
    dht.readTemperature();


  float initialHum =
    dht.readHumidity();


  if (
    !isnan(initialTemp)
  ) {

    cachedTemperature =
      initialTemp;

  }


  if (
    !isnan(initialHum)
  ) {

    cachedHumidity =
      initialHum;

  }


  lastDHTRead =
    millis();


  updateOLED();

}

// ============================================================
// WIFI AUTO RECONNECT
// ============================================================

// void maintainWiFi() {

//   static unsigned long lastAttempt = 0;

//   if (WiFi.status() == WL_CONNECTED) {
//     return;
//   }

//   if (millis() - lastAttempt < 15000) {
//     return;
//   }

//   lastAttempt = millis();

//   Serial.println("WiFi disconnected. Restarting connection...");

//   WiFi.disconnect(true);
//   delay(100);

//   WiFi.mode(WIFI_STA);
//   WiFi.begin(ssid, password);
// }
// ============================================================
// LOOP
// ============================================================

void loop() {
 if (wifiDisconnected &&
      millis() >= wifiReconnectTime &&
      WiFi.status() != WL_CONNECTED) {

    Serial.println("Attempting WiFi reconnect...");

    WiFi.begin();

    wifiReconnectTime = millis() + 20000;
  }
  // maintainWiFi();
  server.handleClient();


  updateGPS();


  unsigned long now =
    millis();


  if (
    now - lastSensorUpdate >=
    SENSOR_INTERVAL
  ) {

    lastSensorUpdate =
      now;


    updateSensorCache();

  }


  updateServos();


  if (!manualMode) {

    autonomousNavigation();

  }


  updateOLED();


  delay(2);

}