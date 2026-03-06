#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "OnePlus Nord 3 5G";
const char* password = "Theju1901";

String server = "http://192.168.221.60:5000";   // YOUR FLASK SERVER IP + PORT

#define TRIGGER_BUTTON D2
#define TAKEN_BUTTON D3
#define MISSED_BUTTON D4
#define BUZZER D6

bool alarmActive = false;

void setup() {
  Serial.begin(115200);
  pinMode(TRIGGER_BUTTON, INPUT_PULLUP);
  pinMode(TAKEN_BUTTON, INPUT_PULLUP);
  pinMode(MISSED_BUTTON, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi Connected");
}

void sendData(String status)
{
  if (WiFi.status() == WL_CONNECTED)
  {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, server + "/update");
    http.addHeader("Content-Type", "application/json");
    String json = "{\"status\":\"" + status + "\"}";
    int code = http.POST(json);
    if (code > 0) Serial.println("ESP Data sent: " + status);
    else Serial.println("ESP Error sending data: " + String(code));
    http.end();
  }
}

void loop() {
  if (digitalRead(TRIGGER_BUTTON) == LOW)
  {
    delay(200);  // debounce
    digitalWrite(BUZZER, HIGH);
    alarmActive = true;
    Serial.println("Reminder Triggered");
  }

  if (alarmActive)
  {
    if (digitalRead(TAKEN_BUTTON) == LOW)
    {
      digitalWrite(BUZZER, LOW);
      sendData("taken");
      alarmActive = false;
      delay(200);
    }
    if (digitalRead(MISSED_BUTTON) == LOW)
    {
      digitalWrite(BUZZER, LOW);
      sendData("missed");
      alarmActive = false;
      delay(200);
    }
  }
}