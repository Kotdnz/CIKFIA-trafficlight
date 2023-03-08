#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
 
//const char* ssid = "KartingSystemV1";
//const char* password =  "6jBwdfHrMgNvxe32JaMB";
//const char* mqttServer = "172.20.20.1";

const char* ssid = "My-home-TP-LINK";
const char* password =  "kostya-secret";
const char* mqttServer = "10.0.0.237";
const int   mqttPort = 1883;
const char* mqttUser = "point";
const char* mqttPassword = "mqtt";
const char* mqttTopic = "cloud";
const int GREEN = D5;
const int YELLOW = D6;
const int RED = D7;
const int BLUE = D8;      // for future
int toggle = 0;           // blinker

unsigned long previousMillis = 0;        // will store last time LED was updated
const long interval = 1000;           // interval at which to blink (milliseconds)
 
WiFiClient espClient;
PubSubClient client(espClient);
char payload[128];

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi connected.");
  randomSeed(micros());
  // Serial.println(WiFi.localIP());
}
 
void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback); 
  
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); 
  pinMode(RED, OUTPUT);
  digitalWrite(RED, LOW); 
  pinMode(YELLOW, OUTPUT);
  digitalWrite(YELLOW, LOW); 
  pinMode(GREEN, OUTPUT);
  digitalWrite(GREEN, LOW); 
}
 
void callback(char* topic, byte* payload, unsigned int pLength) {
    Serial.println("msg received");
    StaticJsonBuffer<200> jsonBuffer;

    char* msg = new char[pLength+1]();
    memcpy(msg, payload, pLength);
    Serial.println(msg);
    JsonObject& root = jsonBuffer.parseObject(msg);
    if (!root.success())
    {
      Serial.println("Parsing failed");
      delete msg;
      return;
    }
    if (root.containsKey("RED")){
            root["RED"] == "ON"?
                    digitalWrite(RED, HIGH): 
                    digitalWrite(RED, LOW);
    }
    if (root.containsKey("YELLOW")){
            root["YELLOW"] == "ON"?
                    digitalWrite(YELLOW, HIGH):
                    digitalWrite(YELLOW, LOW);
    }
    if (root.containsKey("GREEN")){
            root["GREEN"] == "ON"?
                    digitalWrite(GREEN, HIGH):
                    digitalWrite(GREEN, LOW);
    }
    if (root.containsKey("OFF")){
            if(root["OFF"] == "ON"){
                    digitalWrite(RED, LOW);
                    digitalWrite(YELLOW, LOW);
                    digitalWrite(GREEN, LOW);
            }
    }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  } 
  client.loop();
    unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    // save the last time you blinked the LED
    previousMillis = currentMillis;
    toggle ^= 1;
    digitalWrite(LED_BUILTIN, toggle);  
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(),mqttUser, mqttPassword)) {
      Serial.println("MQTT connected.");
      // Once connected, publish an announcement...
      //client.publish(mqttTopic, "hello MQTT");
      // ... and resubscribe
      client.subscribe(mqttTopic);
    } else {
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
