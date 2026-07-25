#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <WiFi.h>
#include <WebServer.h>
const char* ssid = "phone1";
const char* password = "12345678";

WebServer server(80);
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
// Motors
#define IN1 26
#define IN2 27
#define IN3 14
#define IN4 12
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// DHT11
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Soil + Relay
#define SOIL_PIN 34
#define RELAY_PIN 23

// Ultrasonic
#define TRIG 32
#define ECHO 33
float distance = 0;
bool manualMode = false;
// Line Sensors
#define LS 18
#define CS 19
#define RS 5

// GPS
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
void handleData()
{
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  int soil = analogRead(SOIL_PIN);
  String modeState;

if(manualMode)
  modeState = "MANUAL";
else
  modeState = "AUTO";
  String pumpState;

  if(soil > 3000)
    pumpState = "ON";
  else
    pumpState = "OFF";

String json = "{";

json += "\"temperature\":" + String(temp) + ",";
json += "\"humidity\":" + String(hum) + ",";
json += "\"soil\":" + String(soil) + ",";
json += "\"distance\":" + String(distance) + ",";
json += "\"pump\":\"" + pumpState + "\",";
json += "\"mode\":\"" + modeState + "\"";

if(gps.location.isValid())
{
  json += ",\"lat\":" + String(gps.location.lat(),6);
  json += ",\"lon\":" + String(gps.location.lng(),6);
}

json += "}";

  server.send(
    200,
    "application/json",
    json
  );
}
void handleRoot()
{
  server.send(
    200,
    "text/plain",
    "ESP32 Web Server Working"
  );
}
void handleForward()
{
  forward();
  server.send(200, "text/plain", "FORWARD");
}

void handleLeft()
{
  left();
  server.send(200, "text/plain", "LEFT");
}

void handleRight()
{
  right();
  server.send(200, "text/plain", "RIGHT");
}

void handleStop()
{
  stopMotor();
  server.send(200, "text/plain", "STOP");
}
void handleAuto()
{
  manualMode = false;
  server.send(200, "text/plain", "AUTO MODE");
}

void handleManual()
{
  manualMode = true;
  stopMotor();

  server.send(200, "text/plain", "MANUAL MODE");
}
void setup() {
    Serial.begin(115200);
  WiFi.begin(ssid, password);

Serial.print("Connecting to WiFi");

while (WiFi.status() != WL_CONNECTED)
{
  delay(500);
  Serial.print(".");
}

Serial.println();
Serial.println("WiFi Connected!");
Serial.print("IP Address: ");
Serial.println(WiFi.localIP());
server.on("/", handleRoot);
server.on("/data", handleData);
server.begin();
server.on("/forward", handleForward);
server.on("/left", handleLeft);
server.on("/right", handleRight);
server.on("/stop", handleStop);
server.on("/auto", handleAuto);
server.on("/manual", handleManual);
  dht.begin();

  pinMode(RELAY_PIN, OUTPUT);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(LS, INPUT);
  pinMode(CS, INPUT);
  pinMode(RS, INPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  Wire.begin(21,22);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED Failed");
    while(1);
  }

  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(10,20);
  display.println("ROVER");
  display.display();

  delay(2000);
}
void forward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void left() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void right() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
void loop() {
  server.handleClient();

  while(gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  int soil = analogRead(SOIL_PIN);

  if(soil > 3000)
    digitalWrite(RELAY_PIN, HIGH);
  else
    digitalWrite(RELAY_PIN, LOW);

  // Ultrasonic
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG, LOW);

  long duration = pulseIn(ECHO, HIGH, 20000);
  distance = duration * 0.034 / 2.0;

  // Line Sensors
  int L = digitalRead(LS);
  int C = digitalRead(CS);
  int R = digitalRead(RS);
//  if (L==0 && C==1 && R==0)
// {
//     forward();
// }
// else if (L==1 && C==0)
// {
//     left();
// }
// else if (R==1 && C==0)
// {
//     right();
// }
// else
// {
//     stopMotor();
// }
// if(distance < 20)
// {
//     stopMotor();
// }
if(!manualMode)
{
    if(distance > 0 && distance < 20)
{
    stopMotor();
}
else
{
    if (L==0 && C==1 && R==0)
    {
        forward();
    }
    else if (L==1 && C==0)
    {
        left();
    }
    else if (R==1 && C==0)
    {
        right();
    }
    else
    {
        stopMotor();
    }
}
}
while (gpsSerial.available()) {
    Serial.write(gpsSerial.read());
  }
  // Serial Monitor
  Serial.print("Temp=");
  Serial.print(temp);

  Serial.print(" Hum=");
  Serial.print(hum);

  Serial.print(" Soil=");
  Serial.print(soil);

  Serial.print(" Dist=");
  Serial.print(distance);

  Serial.print(" L=");
  Serial.print(L);

  Serial.print(" C=");
  Serial.print(C);

  Serial.print(" R=");
  Serial.println(R);
  Serial.print("Satellites: ");
Serial.println(gps.satellites.value());



  // OLED
  display.clearDisplay();

  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.setCursor(0,0);
  display.print("T:");
  display.print(temp,0);
  display.print(" H:");
  display.print(hum,0);

  display.setCursor(0,10);
  display.print("S:");
  display.print(soil);

  display.print(" P:");
  if(soil > 3000)
    display.print("ON");
  else
    display.print("OFF");

  display.setCursor(0,20);
  display.print("D:");
  display.print(distance,0);
  display.print("cm");
display.setCursor(0,30);
display.print("L");
display.print(L);

display.print(" C");
display.print(C);

display.print(" R");
display.print(R);
display.setCursor(70,20);

if(manualMode)
  display.print("MAN");
else
  display.print("AUTO");

display.setCursor(70,30);

if (L==0 && C==1 && R==0)
  display.print("FWD");
else if (L==1 && C==0)
  display.print("LEFT");
else if (R==1 && C==0)
  display.print("RIGHT");
else
  display.print("STOP");
display.setCursor(0,40);
  if(gps.location.isValid()) {
    display.print("LAT:");
    display.print(gps.location.lat(),6);
  }
  else {
    display.print("GPS Searching");
  }

  display.setCursor(0,50);

  if(gps.location.isValid()) {
    display.print("LON:");
    display.print(gps.location.lng(),6);
  }
  else {
    display.print("Wait...");
  }

  display.display();

  delay(10);
}